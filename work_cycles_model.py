from pulp import *
import time
import numpy as np
from src.utils import *
from src.constants import JCA_key as JCA, REPOS_key as REPOS

# Loading planning csv data file
planning_data_file_path = sys.argv[1]
exportation_path = sys.argv[2]
export_results = bool(int(sys.argv[3]))

# Loading Parameters + Instance dependant Parameters
instance_id, year, bw, annual_hours_fix, annual_hours_var, Pp, P80, T, ratios, costs, A, a, Day_Shifts, Night_Shifts, \
    week_days, Week, N, beginningTime_t, completionTime_c, duration_D, breakDuration = \
    read_planning_data_from_csv(planning_data_file_path)
Eff = read_team_composition_results(exportation_path, instance_id)  # team composition

number_of_shifts = len(Day_Shifts) + len(Night_Shifts)
Work_Shifts = {**Night_Shifts, **Day_Shifts}  # all types of work shifts with special needs
Work_Shifts_And_Jca = {**Work_Shifts, JCA: number_of_shifts}  # all types of work shifts + Jca
Shifts = {**Work_Shifts_And_Jca, REPOS: number_of_shifts + 1}  # all types of shifts (including the off/rest shift)

# Work cycles length (not a variable in this model)
HC_r = [eff for eff in Eff]
# Overall work cycle length
HC = int(np.lcm.reduce(list(filter(lambda hc: hc > 0, HC_r))))
# Horizon of the plannings creation

# Variables
X = [[[[LpVariable("x" + str(i) + "_" + str(j) + "_" + str(r) + "_" + str(e_r), 0, 1, cat=LpInteger)
        for e_r in range(Eff[r])] for r in range(len(T))] for j in range(1, len(Week) * HC + 1)]
     for i in range(len(Shifts))]

t = [[[LpVariable("t" + str(j) + "_" + str(r) + "_" + str(e_r), 0, 48, cat=LpInteger)
       for e_r in range(Eff[r])] for r in range(len(T))] for j in range(1, len(Week) * HC + 1)]
c = [[[LpVariable("c" + str(j) + "_" + str(r) + "_" + str(e_r), 0, 48, cat=LpInteger)
       for e_r in range(Eff[r])] for r in range(len(T))] for j in range(1, len(Week) * HC + 1)]
rest = [[[LpVariable("r" + str(j) + "_" + str(r) + "_" + str(e_r), 0, 1, cat=LpInteger)
          for e_r in range(Eff[r])] for r in range(len(T))] for j in range(1, len(Week) * HC + 1)]
# y[j][e1] = 1 if the shift is REPOS for the day j and the day j + 1 for the full time agent e1, 0 otherwise
y = [[LpVariable("y" + str(j) + "_" + str(e1), 0, 1, cat=LpInteger) for e1 in range(Eff[0])]
     for j in range(1, len(Week) * HC_r[0])]
# w[r][e_r][j] = 1 if (24 - c[j][r][e_r] + t[j + 2][r][e_r] >= (36 - 24)), 0 otherwise (for constraint 2.b.ii)
w = [[[LpVariable("w" + str(j) + "_" + str(r) + "_" + str(e_r), 0, 1, cat=LpInteger)
       for j in range(1, len(Week) * HC_r[r] - 1)] for e_r in range(Eff[r])] for r in range(len(T))]
# z[r][e_r][j] = rest[j + 1][r][e_r] * w[r][e_r][j] in {0,1} (for constraint 2.b.ii)
z = [[[LpVariable("z" + str(j) + "_" + str(r) + "_" + str(e_r), 0, 1, cat=LpInteger)
       for j in range(1, len(Week) * HC_r[r] - 1)] for e_r in range(Eff[r])] for r in range(len(T))]
# v[r][e_r][j] = 1 if (24 + t[j + 1][r][e_r] - c[j][r][e_r] >= 36), 0 otherwise (for constraint 2.b.ii)
v = [[[LpVariable("v" + str(j) + "_" + str(r) + "_" + str(e_r), 0, 1, cat=LpInteger)
       for j in range(1, len(Week) * HC_r[r])] for e_r in range(Eff[r])] for r in range(len(T))]
M = 100000
epsilon = 0.001

# Problem
cador = LpProblem("CADOR", LpMinimize)

# Constraints
# TODO : update constraints in the doc (0.b, 2.a.i, 2.a.ii, ...)
# Hard Constraints

# Constraint 0.a: repetition of the cycle patterns for each type of contract
for r in range(len(T)):
    for e_r in range(Eff[r]):
        for i in range(len(Shifts)):
            for j in range(HC_r[r] * len(Week)):
                if HC_r[r] != HC and HC_r[r] > 0:
                    for k in range(1, HC // HC_r[r]):
                        cador += X[i][j][r][e_r] == X[i][j + k * HC_r[r] * len(Week)][r][e_r]

# Constraint 0.b: rotation of the week patterns between agents with the same type of contract through a cycle
# TODO: to add in the doc
for r in range(len(T)):
    for e_r in range(Eff[r]):
        for i in range(len(Shifts)):
            for j in Week:
                for k in range(1, HC_r[r]):
                    cador += X[i][j][r][e_r] \
                             == X[i][(j + k * len(Week)) % (HC_r[r] * len(Week))][r][(e_r - k) % HC_r[r]]

# Constraint 1.a: respect of needs
for s in Work_Shifts:
    for j in range(len(Week)):
        for k in range(HC):
            cador += lpSum([lpSum([X[Work_Shifts[s]][j + k * len(Week)][r][e_r] for e_r in range(Eff[r])])
                            for r in range(len(T))]) >= N[j][s]  # == ?

# Constraint 1.b: only one shift per day per person
for r in range(len(T)):
    for e_r in range(Eff[r]):
        for j in range(len(Week) * HC):
            cador += lpSum([X[i][j][r][e_r] for i in range(len(Shifts))]) == 1

# Constraint 1.c: no single work day
for r in range(len(T)):
    for e_r in range(Eff[r]):
        for j in range(1, len(Week) * HC_r[r] - 2):
            cador += lpSum([X[Shifts[s]][j + 1][r][e_r] for s in Work_Shifts_And_Jca]) <= \
                     lpSum([X[Shifts[s]][j][r][e_r] for s in Work_Shifts_And_Jca]) + \
                     lpSum([X[Shifts[s]][j + 2][r][e_r] for s in Work_Shifts_And_Jca])

# Constraint 1.d: maximum of 5 consecutive days of work
for r in range(len(T)):
    for e_r in range(Eff[r]):
        for j in range(len(Week) * HC_r[r] - 5):
            cador += lpSum([lpSum([X[Shifts[s]][j + k][r][e_r]
                                   for s in Work_Shifts_And_Jca]) for k in range(6)]) <= 5

# Constraint 1.e: same shift on Saturdays and Sundays # TODO: just full time agent ?
for r in range(len(T)):
    for e_r in range(Eff[r]):
        for s in Work_Shifts:
            for k in range(HC):
                cador += X[Shifts[s]][5 + k * len(Week)][r][e_r] == X[Shifts[s]][6 + k * len(Week)][r][e_r]

# Constraint 2.a.i: working time per week (non-sliding) may not exceed 45 hours
for r in range(len(T)):
    for e_r in range(Eff[r]):
        for k in range(HC_r[r]):
            cador += lpSum([lpSum([X[Shifts[s]][k * len(Week) + j][r][e_r] * duration_D[s]
                                   for j in Week]) for s in Work_Shifts]) \
                    + lpSum([X[Shifts[JCA]][k * len(Week) + j][r][e_r] * 8 for j in Week]) <= 45

# Constraint 2.a.ii: employees cannot work more than 48h within 7 sliding days
for r in range(len(T)):
    for e_r in range(Eff[r]):
        for j in range(len(Week) * (HC_r[r] - 1) + 1):
            cador += lpSum([lpSum([X[Shifts[s]][j + k][r][e_r] * duration_D[s]
                                   for k in range(len(Week))]) for s in Work_Shifts]) \
                     + lpSum([X[Shifts[JCA]][j + k][r][e_r] * 8 for k in range(len(Week))]) <= 48

# Constraints 2.b:

# Constraint 2.b.o: definition of the variables t (beginning time)  # todo : JCA ?
for r in range(len(T)):
    for e_r in range(Eff[r]):
        for j in range(len(Week) * HC):
            cador += t[j][r][e_r] == lpSum([beginningTime_t[s] * X[Shifts[s]][j][r][e_r] for s in Work_Shifts]) \
                     + 24 * (1 - lpSum([X[Shifts[s]][j][r][e_r] for s in Work_Shifts]))

# Constraint 2.b.oo: definition of the variables c (completion time)  # todo : JCA ?
for r in range(len(T)):
    for e_r in range(Eff[r]):
        for j in range(len(Week) * HC):
            cador += c[j][r][e_r] == lpSum([(beginningTime_t[s] + duration_D[s])
                                            * X[Shifts[s]][j][r][e_r] for s in Work_Shifts])

# Constraint 2.b.ooo: definition of the variables r (rest/off day or not)
for r in range(len(T)):
    for e_r in range(Eff[r]):
        for j in range(len(Week) * HC):
            cador += rest[j][r][e_r] == 1 - lpSum([X[Shifts[s]][j][r][e_r] for s in Work_Shifts_And_Jca])

# Constraint 2.b.i: minimum daily rest time of 12 hours
for r in range(len(T)):
    for e_r in range(Eff[r]):
        for j in range(1, len(Week) * HC_r[r] - 1):
            cador += 24 + t[j][r][e_r] + c[j - 1][r][e_r] >= 12

# Constraint 2.b.ii: minimum of 36 consecutive hours for weekly rest (sliding)
for r in range(len(T)):
    for e_r in range(Eff[r]):
        for j in range(len(Week) * HC_r[r] - 1):
            if j < len(Week) * HC_r[r] - 2:
                cador += (24 - c[j][r][e_r] + t[j + 2][r][e_r]) >= (36 - 24) - M * (1 - w[r][e_r][j])
                cador += (24 - c[j][r][e_r] + t[j + 2][r][e_r]) <= epsilon + (36 - 24) + M * w[r][e_r][j]  # <
                cador += z[r][e_r][j] <= rest[j + 1][r][e_r]  # UB (Upper Bound)
                cador += z[r][e_r][j] <= w[r][e_r][j]  # UB
                cador += z[r][e_r][j] >= rest[j + 1][r][e_r] + w[r][e_r][j] - 1  # LB
            cador += (24 + t[j + 1][r][e_r] - c[j][r][e_r]) >= 36 - M * (1 - v[r][e_r][j])
            cador += (24 + t[j + 1][r][e_r] - c[j][r][e_r]) <= epsilon + 36 + M * v[r][e_r][j]  # <
for r in range(len(T)):
    for e_r in range(Eff[r]):
        for j in range(1, len(Week) * HC_r[r] - 5):
            cador += lpSum([z[r][e_r][j - 1 + k] + v[r][e_r][j - 1 + k] for k in range(5)]) + v[r][e_r][j + 4] >= 1
"""
# Constraint 2.b.iii:
# at least 4 days, in which 2 successive days including a sunday of break within each fortnight for full time contracts
for e1 in range(Eff[0]):
    for j in range(len(Week) * HC_r[0] - 1):
        cador += y[j][e1] <= X[Shifts[REPOS]][j][0][e1]
        cador += y[j][e1] <= X[Shifts[REPOS]][j + 1][0][e1]
        cador += y[j][e1] >= X[Shifts[REPOS]][j][0][e1] + X[Shifts[REPOS]][j + 1][0][e1] - 1
for e1 in range(Eff[0]):
    for j in range(len(Week) * (HC_r[0] - 2) + 1):
        # First part of constraint 2.b.iii
        cador += lpSum([X[Shifts[REPOS]][j + k][0][e1] for k in range(2 * len(Week))]) >= 4
        # Second part of constraint 2.b.iii
        cador += lpSum([y[j + k][e1] for k in range(2 * len(Week) - 1)]) >= 1
        # Third part of constraint 2.b.iii
        cador += lpSum([X[Shifts[REPOS]][j + k][0][e1] for k in range(2 * len(Week))
                        if (j + k) % len(Week) == 6]) >= 1
"""
# Constraint 3.a: Respect of the working hours for each type of contracts
for r in range(len(T)):
    for e_r in range(Eff[r]):
        cador += lpSum([lpSum([X[Shifts[s]][j][r][e_r] for j in range(HC * len(Week))])
                        * (duration_D[s] - (0 if breakDuration[s] is None else breakDuration[s]))
                        for s in Work_Shifts]) + \
                 lpSum([X[Shifts[JCA]][j][r][e_r] * 7.5
                        for j in range(HC * len(Week))]) >= 37.5 * HC * ratios[r]  # <=, == ?

# Constraint 3.b: Respect of the number of working days for each type of contracts
for r in range(len(T)):
    for e_r in range(Eff[r]):
        cador += lpSum([lpSum([X[Shifts[s]][j][r][e_r] for s in Work_Shifts_And_Jca])
                        for j in range(HC * len(Week))]) >= 5 * HC * ratios[r]  # <=, == ?

# Soft constraints

# Constraint 1: number of Jca at least equals to 20% of total number of staff members
for j in range(len(Week) * HC):
    cador += lpSum([lpSum([X[Shifts[JCA]][j][r][e_r] for e_r in range(Eff[r])]) for r in range(len(T))]) \
             >= 0.2 * lpSum([Eff[r] for r in range(len(T))])

# Constraint 2.a.i :


# Target Function
cador += 1

# Solving
start_time = time.time()
cplex_path = "C:\\Program Files\\IBM\\ILOG\\CPLEX_Studio1210\\cplex\\bin\\x64_win64\\cplex.exe"
status = cador.solve(CPLEX(path=cplex_path))
solving_time = time.time() - start_time

if export_results:
    if LpStatus[status] == 'Optimal':
        OrderedShifts = [s for s in sorted(Shifts.items(), key=lambda shift: shift[1])]
        work_cycles = [[[OrderedShifts[[int(value(X[i][j][r][e_r])) for i in range(len(Shifts))].index(1)][0]
                         for j in range(len(Week) * HC)] for e_r in range(Eff[r])] for r in range(len(T))]
        export_work_cycles_results_as_csv(exportation_path, instance_id, LpStatus[status], solving_time, ratios,
                                          week_days, Day_Shifts, Night_Shifts, duration_D, breakDuration, N,
                                          work_cycles)
    else:
        export_work_cycles_results_as_csv(exportation_path, instance_id, LpStatus[status], solving_time, ratios,
                                          week_days, Day_Shifts, Night_Shifts, duration_D, breakDuration, N, None)
