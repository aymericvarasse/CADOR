import csv
from src.constants import JCA_key as JCA, REPOS_key as REPOS


def read_needs_from_csv(file_path, row_index=0, column_index=0):
    """
    :param file_path: path of the csv file in which there is the table of the needs by shifts, by days of the week
    :param row_index: index of the row in the csv file of the case containing the first shift label
    :param column_index: index of the column in the csv file of the case containing the first shift label
    :return: tuple (table of the needs by shifts by days of the week, the list of the shifts)
    """
    weeks = ['L', 'Ma', 'Me', 'J', 'V', 'S', 'D']
    shifts = {}
    shift_index = 0
    needs_by_shifts = {}
    needs_by_days = []
    with open(file_path, 'r') as csv_file:
        reader = csv.reader(csv_file, delimiter=';')
        for index, row in enumerate(reader):
            if index >= row_index:
                shift_id = row[column_index]
                end_reading = (shift_id == '')
                if not end_reading:
                    needs_by_shift = {}
                    for j, day in enumerate(weeks):
                        needs_by_shift[day] = int(row[column_index + j + 1])
                    shifts[shift_id] = shift_index
                    needs_by_shifts[shift_id] = needs_by_shift
                    shift_index += 1
                else:
                    break
        for day in weeks:
            needs_by_day = {}
            for s in shifts:
                needs_by_day[s] = needs_by_shifts[s][day]
            needs_by_days.append(needs_by_day)
        csv_file.close()
    return needs_by_days, shifts


def export_team_composition_results_as_csv(exportation_repository_path, instance_id, status, solving_time,
                                           contract_types, contract_ratios, workforce, total_cost):
    file_path = exportation_repository_path + "team_composition_" + instance_id + ".csv"
    with open(file_path, 'w+') as csv_file:
        writer = csv.writer(csv_file, delimiter=';', lineterminator='\n')
        instance_row = ['instance_id', instance_id]
        time_row = ['solving_time', str(solving_time)]
        status_row = ['status', status]
        total_cost_row = ['total_cost', str(total_cost)]
        all_rows = [instance_row, time_row, status_row, total_cost_row]
        if status == 'Optimal':
            all_rows.append([str(t) for t in contract_types])
            all_rows.append([str(r_t) for r_t in contract_ratios])
            all_rows.append([str(w) for w in workforce])
        writer.writerows(all_rows)
    csv_file.close()


def read_team_composition_results(exportation_repository_path, instance_id):
    file_path = exportation_repository_path + "team_composition_" + instance_id + ".csv"
    with open(file_path, 'r') as csv_file:
        reader = csv.reader(csv_file, delimiter=';')
        for index, row in enumerate(reader):
            if index == 2:
                status = row[1]
                if status != 'Optimal':
                    raise Exception('The status after solving the team composition ({}) phase is un-managed'
                                    .format(status))
            elif index == 6:
                workforce_by_contract_types = [int(w) for w in row if w != '']
    csv_file.close()
    return workforce_by_contract_types


def read_planning_data_from_csv(file_path):
    """
    Note: The planning csv data file has to respect a special format
    :param file_path: path of the file containing the planning data
    :return:    - instance id of the team composition data
                - year for the planning instance
                - budgeted workforce
                - number of annual working hours for workforce in FIXED rest (for day and night shifts)
                - number of annual working hours for workforce in VARIABLE rest (for day and night shifts)
                - proportion of partial time contracts
                - proportion of 80% contracts in total partial contracts
                - types of contracts
                - ratio of each type of contract
                - cost of each type of contract
                - availability for every type of contract
                - number of employees already affected for each type of contract
                - types of day shifts
                - types of night shifts
                - day codes (str) of the days of a week
                - indices (int) of the days of a week
                - workforce needs for every shifts of every day in a week
                - beginning times of some shifts
                - completion times of some shifts
                - durations of some shifts
                - break durations of some shifts
    """
    shifts_with_needs, shift_index = [], 0
    needs_by_shifts = {}
    shift_beginning_times, shift_completion_times, shift_durations, shift_break_durations = {}, {}, {}, {}
    with open(file_path, 'r') as csv_file:
        reader = csv.reader(csv_file, delimiter=';')
        for index, row in enumerate(reader):
            if index == 0:
                instance_id = row[1]  # type str
            elif index == 1:
                year = int(row[1])
            elif index == 2:
                budgeted_workforce = None if row[1] == "" else float(row[1])
            elif index == 3:
                annual_hours_fix = {'day': int(row[1]), 'night': int(row[2])}
            elif index == 4:
                annual_hours_var = {'day': int(row[1]), 'night': int(row[2])}
            elif index == 5:
                partial_time_contracts_prop = float(row[1])
            elif index == 6:
                eighty_percent_contracts_prop = float(row[1])
            elif index == 7:
                contracts_type = [int(row[i]) for i in range(1, 8)]
            elif index == 8:
                contracts_ratios = [float(row[i]) for i in range(1, 8)]
            elif index == 9:
                contracts_costs = [float(row[i]) for i in range(1, 8)]
            elif index == 10:
                contracts_availability = [int(row[i]) for i in range(1, 8)]
            elif index == 11:
                contracts_affected = [int(row[i]) for i in range(1, 8)]
            elif index == 12:
                day_shifts, i = {}, 1
                while row[i] != '':
                    day_shifts[row[i]] = shift_index
                    shift_index += 1
                    i += 1
            elif index == 13:
                night_shifts, i = {}, 1
                while row[i] != '':
                    night_shifts[row[i]] = shift_index
                    shift_index += 1
                    i += 1
            elif index == 14:
                week_days = [row[i] for i in range(1, 8)]
            elif index == 15:
                week_indices = [int(row[i]) for i in range(1, 8)]
            elif index >= 16:
                shift_id = row[0]
                end_reading = (shift_id == '')
                if not end_reading:
                    shifts_with_needs.append(shift_id)
                    needs_by_shift = {}
                    for j, day in enumerate(week_days):
                        needs_by_shift[day] = int(row[j + 1])
                    needs_by_shifts[shift_id] = needs_by_shift
                    shift_beginning_times[shift_id] = int(row[8])
                    shift_completion_times[shift_id] = int(row[9])
                    shift_durations[shift_id] = int(row[10])
                    shift_break_durations[shift_id] = None if len(row) < 12 or row[11] == '' else float(row[11])
                else:
                    break
        needs_by_days = []
        for day in week_days:
            needs_by_day = {}
            for s in shifts_with_needs:
                needs_by_day[s] = needs_by_shifts[s][day]
            needs_by_days.append(needs_by_day)
        csv_file.close()
    return (instance_id, year, budgeted_workforce, annual_hours_fix, annual_hours_var, partial_time_contracts_prop,
            eighty_percent_contracts_prop, contracts_type, contracts_ratios, contracts_costs, contracts_availability,
            contracts_affected, day_shifts, night_shifts, week_days, week_indices, needs_by_days, shift_beginning_times,
            shift_completion_times, shift_durations, shift_break_durations)


def export_work_cycles_results_as_csv(exportation_repository_path, instance_id, status, solving_time,
                                      contract_ratios, week_days, day_shifts, night_shifts, shift_durations,
                                      shift_break_durations, needs_by_days, work_cycles):
    file_path = exportation_repository_path + "work_cycles_" + instance_id + ".csv"
    with open(file_path, 'w+') as csv_file:
        writer = csv.writer(csv_file, delimiter=';', lineterminator='\n')
        instance_row = ['instance_id', instance_id]
        time_row = ['solving_time', str(solving_time)]
        status_row = ['status', status]
        all_rows = [instance_row, time_row, status_row]
        if status == 'Optimal':
            work_shifts_and_jca = {**day_shifts, **night_shifts, JCA: len(night_shifts) + len(day_shifts)}
            # Labels of the work cycles table
            horizon = len(work_cycles[0][0])
            nb_of_weeks = int(horizon / 7)
            legend_row_1 = ['Prenom', '%', 'J/N']
            legend_row_2 = ['Agent', '%', 'J/N']
            for week in range(nb_of_weeks):
                legend_row_1 += ['Semaine {}'.format(week + 1)] + ['' for _ in range(6)]
                legend_row_2 += week_days
            all_rows.append(legend_row_1)
            all_rows.append(legend_row_2)
            # Work cycles table content
            agent = 1
            for r in range(len(work_cycles)):
                for e_r in range(len(work_cycles[r])):
                    agent_cat = get_agent_category(work_cycles[r][e_r], day_shifts, night_shifts)
                    all_rows.append([str(agent), str(int(contract_ratios[r] * 100)), agent_cat] + work_cycles[r][e_r])
                    agent += 1
            # Work cycles analysis (needs)
            shifts = list(shift for shift, i in sorted(work_shifts_and_jca.items(), key=lambda item: item[1]))
            for s in shifts:
                row_s = [sum([sum([int(work_cycles[r][e_r][j] == s) for e_r in range(len(work_cycles[r]))])
                              for r in range(len(work_cycles))]) for j in range(horizon)]
                all_rows.append(['Total ' + s, '', ''] + row_s)
            all_rows.append([])
            all_rows.append(['Rappel des besoins de la maquette'])
            all_rows.append(3 * [''] + week_days)
            for s in shifts:
                if s != JCA:
                    all_rows.append(['', '', s] + [needs_by_days[j][s] for j in range(len(week_days))])
            # Work cycles analysis (shifts by agent)
            all_rows.append([])
            all_rows.append(['Resultats', 'Nombre de postes de travail effectues par chaque agent']
                            + (len(shifts) + 5) * [''] + ['Equite'])
            all_rows.append(['Agent', '%'] + shifts + ['', 'T', 'D', 'Df', '', '%'] + shifts)
            agent = 1
            row_r1_e1 = [work_cycles[0][0].count(s) for s in shifts]
            for r in range(len(work_cycles)):
                for e_r in range(len(work_cycles[r])):
                    row_r_er = [work_cycles[r][e_r].count(s) for s in shifts]
                    hours_worked = sum([row_r_er[i] * (shift_durations[s] - (0 if shift_break_durations[s] is None
                                                                             else shift_break_durations[s])
                                                       if s != JCA else 7.5) for i, s in enumerate(shifts)])
                    if row_r1_e1:
                        equity_r_er = ['x' if ref == 0
                                       else str(round(row_r_er[i] / (ref * contract_ratios[r]) * 100)) + '%'
                                       for i, ref in enumerate(row_r1_e1)]
                    hours_expected = 37.5 * (horizon // len(week_days)) * contract_ratios[r]
                    hours_gap = hours_expected - hours_worked
                    all_rows.append([str(agent), str(int(contract_ratios[r] * 100))] + row_r_er +
                                    ['', hours_worked, hours_expected, hours_gap] +
                                    ['', str(int(contract_ratios[r] * 100))] + equity_r_er)
                    agent += 1
            # Work cycles analysis (days of the week by agent)
            all_rows.append([])
            all_rows.append(['Resultats', 'Nombre de jours de la semaine travailles par agent'])
            all_rows.append(['Agent', '%'] + week_days)  # Monday: 0, Tuesday: 1, ..., Sunday: 6
            agent = 1
            for r in range(len(work_cycles)):
                for e_r in range(len(work_cycles[r])):
                    row_r_er = [str(sum([int(work_cycles[r][e_r][i] != REPOS)
                                         for i in range(horizon) if (i - day) % len(week_days) == 0]))
                                for day in range(len(week_days))]
                    all_rows.append([str(agent), str(int(contract_ratios[r] * 100))] + row_r_er)
                    agent += 1
        writer.writerows(all_rows)
    csv_file.close()


def get_agent_category(work_cycles_r_er, day_shifts, night_shifts):
    day_agent, night_agent = False, False
    for s in {**day_shifts, JCA: len(day_shifts) + len(night_shifts)}:
        if s in work_cycles_r_er:
            day_agent = True
            break
    for s in night_shifts:
        if s in work_cycles_r_er:
            night_agent = True
            break
    return 'J/N' if day_agent and night_agent else \
        ('J' if day_agent and not night_agent else ('N' if not day_agent and night_agent else ''))
