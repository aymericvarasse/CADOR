import csv


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


def read_team_composition_data_from_csv(file_path):
    """
    Note: The team composition csv data file has to respect a special format
    :param file_path: path of the file containing the team composition data
    :return:    - instance id of the team composition data
                - budgeted workforce
                - proportion of partial time contracts
                - proportion of 80% contracts in total partial contracts
                - types of contracts
                - ratio of each type of contract
                - cost of each type of contract
                - availability for every type of contract
                - number of employees already affected for each type of contract
                - day codes (str) of the days of a week
                - indices (int) of the days of a week
                - workforce needs for every shifts of every day in week
    """
    shifts = {}
    shift_index = 0
    needs_by_shifts = {}
    with open(file_path, 'r') as csv_file:
        reader = csv.reader(csv_file, delimiter=';')
        for index, row in enumerate(reader):
            if index == 0:
                instance_id = int(row[1])
            elif index == 1:
                budgeted_workforce = float(row[1])
            elif index == 2:
                partial_time_contracts_prop = float(row[1])
            elif index == 3:
                eighty_percent_contracts_prop = float(row[1])
            elif index == 4:
                contracts_type = [int(row[i]) for i in range(1, 8)]
            elif index == 5:
                contracts_ratios = [float(row[i]) for i in range(1, 8)]
            elif index == 6:
                contracts_costs = [float(row[i]) for i in range(1, 8)]
            elif index == 7:
                contracts_availability = [int(row[i]) for i in range(1, 8)]
            elif index == 8:
                contracts_affected = [int(row[i]) for i in range(1, 8)]
            elif index == 9:
                week_days = [row[i] for i in range(1, 8)]
            elif index == 10:
                week_indices = [int(row[i]) for i in range(1, 8)]
            elif index >= 11:
                shift_id = row[0]
                end_reading = (shift_id == '')
                if not end_reading:
                    needs_by_shift = {}
                    for j, day in enumerate(week_days):
                        needs_by_shift[day] = int(row[j + 1])
                    shifts[shift_id] = shift_index
                    needs_by_shifts[shift_id] = needs_by_shift
                    shift_index += 1
                else:
                    break
        needs_by_days = []
        for day in week_days:
            needs_by_day = {}
            for s in shifts:
                needs_by_day[s] = needs_by_shifts[s][day]
            needs_by_days.append(needs_by_day)
        csv_file.close()
    return instance_id, budgeted_workforce, partial_time_contracts_prop, eighty_percent_contracts_prop, \
           contracts_type, contracts_ratios, contracts_costs, contracts_availability, contracts_affected, week_days, \
           week_indices, needs_by_days, shifts


def export_team_composition_results_as_csv(exportation_repository_path, instance_id, status, solving_time,
                                           contract_types, contract_ratios, workforce):
    file_path = exportation_repository_path + "team_composition_" + str(instance_id)
    with open(file_path, 'w+') as csv_file:
        writer = csv.writer(csv_file, delimiter=';', lineterminator='\n')
        instance_row = ['instance_id', str(instance_id)]
        time_row = ['solving_time', str(solving_time)]
        if status == 'Optimal':
            types_row = [str(t) for t in contract_types]
            ratios_row = [str(r_t) for r_t in contract_ratios]
            workforce_row = [str(w) for w in workforce]
            all_rows = [instance_row, time_row, types_row, ratios_row, workforce_row]
        else:
            status_row = ['status', status]
            all_rows = [instance_row, time_row, status_row]
        writer.writerows(all_rows)
    csv_file.close()