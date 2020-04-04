from jours_feries_france.compute import JoursFeries
from datetime import date, timedelta

# Library to install : https://pypi.org/project/jours-feries-france/ (pip install jours-feries-france)


def compute_required_workforce(needs, day_shifts, night_shifts, shift_durations, shift_break_durations,
                               annual_hours_fix, annual_hours_var, week_indices, year, include_alsace_moselle=False):
    """
    Computes the required workforce (FTER) in full-time equivalent for the given staff scheduling
    Notes:  - Indices of the days of the week: 0:Monday, 1:Tuesday, ..., 6:Sunday
            - FTER = Full-Time Equivalent Required (in french, ETPR = Equivalent Temps Plein Requis)
            - NbSB = Number of Sundays and Bank holidays (in french, NbDF = Nombre de Dimanches et jours Fériés)
    :param needs: workforce needs for every shifts of every day in week
    :param day_shifts: types of day shifts
    :param night_shifts: types of night shifts
    :param shift_durations: durations of some shifts
    :param shift_break_durations: break durations of some shifts
    :param annual_hours_fix: number of annual working hours for workforce in FIXED rest (for day and night shifts)
    :param annual_hours_var: number of annual working hours for workforce in VARIABLE rest (for day and night shifts)
    :param week_indices: indices (int) of the days of a week
    :param year: year (format yyyy) for the hospital staff scheduling
    :param include_alsace_moselle: boolean true if the hospital is in Alsace-Moselle, false other (for bank holidays)
    :return: the FTER for the given staff scheduling instance
    """
    # Note : the other variables returned are two booleans (true if all the workforce on day shifts (resp night shifts)
    # are in fixed rest, false other (in variable rest)
    fter_day, fter_night, _, _ = \
        compute_required_workforce_details(needs, day_shifts, night_shifts, shift_durations, shift_break_durations,
                                           annual_hours_fix, annual_hours_var, week_indices, year,
                                           include_alsace_moselle)
    return fter_day + fter_night


def compute_required_workforce_details(needs, day_shifts, night_shifts, shift_durations, shift_break_durations,
                                       annual_hours_fix, annual_hours_var, week_indices, year, include_alsace_moselle):
    # Getting the number of each day of the week in a year
    s = get_nb_of_each_week_day_in_a_year(year)

    # Getting all the french bank holidays of the given year (except those on sundays)
    bank_holidays = JoursFeries.for_year(year, include_alsace=include_alsace_moselle)
    # Note: the next weekday() function returns the day of the week as an integer, where Monday is 0 and Sunday is 6
    bank_holidays_days = list(filter(lambda day: day < 6, [datetime.weekday() for datetime in bank_holidays.values()]))

    break_durations = shift_break_durations.copy()
    for shift in {**night_shifts, **day_shifts}:
        if shift not in shift_break_durations or shift_break_durations[shift] is None:
            break_durations[shift] = 0

    # Overall FTER computation
    # Hypothesis : all the workforce are in fixed rest
    fter_day = sum([sum([needs[day][shift] * s[day] * (shift_durations[shift] - break_durations[shift])
                         for day in week_indices]) for shift in day_shifts]) / annual_hours_fix['day']
    fter_night = sum([sum([needs[day][shift] * s[day] * (shift_durations[shift] - break_durations[shift])
                           for day in week_indices]) for shift in night_shifts]) / annual_hours_fix['night']

    # Verification of the hypothesis : if true -> END, else all the workforce are in VARIABLE rest -> compute again
    nb_sb_day = (s[6] * sum([needs[6][shift] for shift in day_shifts])
                 + sum([sum([needs[day][shift] for day in bank_holidays_days]) for shift in day_shifts])) / fter_day
    nb_sb_night = (s[6] * sum([needs[6][shift] for shift in night_shifts])
                   + sum([sum([needs[day][shift] for day in bank_holidays_days]) for shift in night_shifts]))
    nb_sb_night /= fter_night
    if nb_sb_day > 10:
        # All the workforce on day shifts are in variable rest
        fter_day = sum([sum([needs[day][shift] * s[day] * (shift_durations[shift] - break_durations[shift])
                             for day in week_indices]) for shift in day_shifts]) / annual_hours_var['day']
    if nb_sb_night > 10:
        # All the workforce on night shifts are in variable rest
        fter_night = sum([sum([needs[day][shift] * s[day] * (shift_durations[shift] - break_durations[shift])
                               for day in week_indices]) for shift in night_shifts]) / annual_hours_var['night']
    return fter_day, fter_night, nb_sb_day <= 10, nb_sb_night <= 10


def get_nb_of_each_week_day_in_a_year(year):
    """
    Computes the number of each day of the week in the given year.
    :param year: year (format yyyy)
    :return: list containing at the index i (corresponding to the day i of the week with 0:Monday, ..., 6:Sunday), the
    number of this day in the given year
    """
    days_counter = [0] * 7
    current_date = date(year, 1, 1)  # January 1st of the given year
    while current_date.year == year:
        days_counter[current_date.weekday()] += 1
        current_date += timedelta(days=1)
    return days_counter
