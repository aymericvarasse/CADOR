from pulp import *
import time
import math
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
HC_min_r = [1, 2, 1, 4, 2, 1, 2]  # special conditions for some partial contracts to respect their working hours
# In fact, we allow some working cycles to be define on more than one week
HC_r = [eff if eff >= HC_min_r[r] or eff == 0 else HC_min_r[r] for r, eff in enumerate(Eff)]

# Allowing constraints by type of contracts + others adjustments instance-dependent
hard_constraint_1_e = [False, False, False, False, False, False, False]
hard_constraint_1_c = [True, True, True, True, True, True, True]
nb_sunday_jca_removed = 2
HC_r_analysed = [None, None, 6, None, None, 2, None]
for r, hc_r in enumerate(HC_r_analysed):
    if hc_r is not None:
        HC_r[r] = hc_r

# Overall work cycle length -> Horizon of the plannings creation = HC * len(Week)
HC = int(np.lcm.reduce(list(filter(lambda hc: hc > 0, HC_r))))

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
# y[n][e1] = 1 if the n-th week-end of the full-time agent e1 is REPOS (saturday and sunday), 0 otherwise
y = [[LpVariable("y" + str(n) + "_" + str(e1), 0, 1, cat=LpInteger) for e1 in range(Eff[0])]
     for n in range(1, HC_r[0] + 1)]
# w[r][e_r][j] = 1 if (24 - c[j][r][e_r] + t[j + 2][r][e_r] >= (36 - 24)), 0 otherwise (for constraint 2.b.ii)
w = [[[LpVariable("w" + str(j) + "_" + str(r) + "_" + str(e_r), 0, 1, cat=LpInteger)
       for j in range(1, len(Week) * HC_r[r] + 1)] for e_r in range(Eff[r])] for r in range(len(T))]
# z[r][e_r][j] = rest[j + 1][r][e_r] * w[r][e_r][j] in {0, 1} (for constraint 2.b.ii)
z = [[[LpVariable("z" + str(j) + "_" + str(r) + "_" + str(e_r), 0, 1, cat=LpInteger)
       for j in range(1, len(Week) * HC_r[r] + 1)] for e_r in range(Eff[r])] for r in range(len(T))]
# v[r][e_r][j] = 1 if (24 + t[j + 1][r][e_r] - c[j][r][e_r] >= 36), 0 otherwise (for constraint 2.b.ii)
v = [[[LpVariable("v" + str(j) + "_" + str(r) + "_" + str(e_r), 0, 1, cat=LpInteger)
       for j in range(1, len(Week) * HC_r[r] + 1)] for e_r in range(Eff[r])] for r in range(len(T))]
M = 100000
epsilon = 0.001

# Objective variable
equity_pos = LpVariable("equity_max_pos", lowBound=0, cat=LpInteger)
equity_neg = LpVariable("equity_max_neg", lowBound=0, cat=LpInteger)
equity = LpVariable("equity_max", lowBound=0, cat=LpInteger)

# Problem
cador = LpProblem("CADOR", LpMinimize)

# Constraints

# Hard Constraints

# Constraint 0.a: repetition of the cycle patterns for each type of contract
for r in range(len(T)):
    for e_r in range(Eff[r]):
        for i in range(len(Shifts)):
            for j in range(HC_r[r] * len(Week)):
                if HC_r[r] != HC and HC_r[r] > 0:
                    for k in range(1, HC // HC_r[r]):
                        cador += X[i][j][r][e_r] == X[i][j + k * HC_r[r] * len(Week)][r][e_r]

# Constraint 0.b: rotation of the week (or more) patterns between agents with the same type of contract through a cycle
for r in range(len(T)):
    for e_r in range(Eff[r]):
        for i in range(len(Shifts)):
            pattern_length = (HC_r[r] // Eff[r]) * len(Week)
            for j in range(pattern_length):
                for k in range(1, Eff[r]):
                    cador += X[i][j][r][e_r] \
                             == X[i][j + k * pattern_length][r][(e_r - k) % Eff[r]]

# Constraint 1.a: respect of needs
for s in Work_Shifts:
    for j in Week:
        for k in range(HC):
            cador += lpSum([lpSum([X[Work_Shifts[s]][j + k * len(Week)][r][e_r] for e_r in range(Eff[r])])
                            for r in range(len(T))]) == N[j][s]

# Constraint 1.b: only one shift per day per person
for r in range(len(T)):
    for e_r in range(Eff[r]):
        for j in range(len(Week) * HC):
            cador += lpSum([X[i][j][r][e_r] for i in range(len(Shifts))]) == 1

# Constraint 1.c: no single work day
for r in range(len(T)):
    if hard_constraint_1_c[r]:
        for e_r in range(Eff[r]):
            for j in range(len(Week) * HC - 2):
                cador += lpSum([X[Shifts[s]][j + 1][r][e_r] for s in Work_Shifts_And_Jca]) <= \
                         lpSum([X[Shifts[s]][j][r][e_r] for s in Work_Shifts_And_Jca]) + \
                         lpSum([X[Shifts[s]][j + 2][r][e_r] for s in Work_Shifts_And_Jca])

# Constraint 1.d: maximum of 5 consecutive days of work
for r in range(len(T)):
    for e_r in range(Eff[r]):
        for j in range(len(Week) * HC - 5):
            cador += lpSum([lpSum([X[Shifts[s]][j + k][r][e_r]
                                   for s in Work_Shifts_And_Jca]) for k in range(6)]) <= 5

# Constraint 1.e: same shift on Saturdays and Sundays
for r in range(len(T)):
    if hard_constraint_1_e[r]:
        for e_r in range(Eff[r]):
            for s in Work_Shifts:
                for k in range(HC):
                    cador += X[Shifts[s]][5 + k * len(Week)][r][e_r] == X[Shifts[s]][6 + k * len(Week)][r][e_r]

# Constraint 2.a.i: working time per week (non-sliding) may not exceed 45 hours
for r in range(len(T)):
    for e_r in range(Eff[r]):
        for k in range(HC):
            cador += lpSum([lpSum([X[Shifts[s]][k * len(Week) + j][r][e_r] * duration_D[s]
                                   for j in Week]) for s in Work_Shifts]) \
                     + lpSum([X[Shifts[JCA]][k * len(Week) + j][r][e_r] * 8 for j in Week]) <= 45

# Constraint 2.a.ii: employees cannot work more than 48h within 7 sliding days
for r in range(len(T)):
    for e_r in range(Eff[r]):
        for j in range(len(Week) * (HC - 1) + 1):
            cador += lpSum([lpSum([X[Shifts[s]][j + k][r][e_r] * duration_D[s]
                                   for k in range(len(Week))]) for s in Work_Shifts]) \
                     + lpSum([X[Shifts[JCA]][j + k][r][e_r] * 8 for k in range(len(Week))]) <= 48

# Constraints 2.b:

# Constraint 2.b.o: definition of the variables t (beginning time)
beginningTime_Jca = min([item[1] for item in beginningTime_t.items() if item[0] in Day_Shifts])
for r in range(len(T)):
    for e_r in range(Eff[r]):
        for j in range(len(Week) * HC):
            cador += t[j][r][e_r] == lpSum([beginningTime_t[s] * X[Shifts[s]][j][r][e_r] for s in Work_Shifts]) \
                     + beginningTime_Jca * X[Shifts[JCA]][j][r][e_r] + 24 * X[Shifts[REPOS]][j][r][e_r]

# Constraint 2.b.oo: definition of the variables c (completion time)
completionTime_Jca = max([item[1] for item in completionTime_c.items() if item[0] in Day_Shifts])
for r in range(len(T)):
    for e_r in range(Eff[r]):
        for j in range(len(Week) * HC):
            cador += c[j][r][e_r] == lpSum([(beginningTime_t[s] + duration_D[s]) * X[Shifts[s]][j][r][e_r]
                                            for s in Work_Shifts]) + completionTime_Jca * X[Shifts[JCA]][j][r][e_r]

# Constraint 2.b.ooo: definition of the variables r (rest/off day or not)
for r in range(len(T)):
    for e_r in range(Eff[r]):
        for j in range(len(Week) * HC):
            cador += rest[j][r][e_r] == X[Shifts[REPOS]][j][r][e_r]

# Constraint 2.b.i: minimum daily rest time of 12 hours
for r in range(len(T)):
    for e_r in range(Eff[r]):
        for j in range(1, len(Week) * HC):
            cador += 24 + t[j][r][e_r] - c[j - 1][r][e_r] >= 12

# Constraint 2.b.ii: minimum of 36 consecutive hours for weekly rest (sliding)
# Note: a < b is equivalent to a <= epsilon + b with e << 1
for r in range(len(T)):
    for e_r in range(Eff[r]):
        for j in range(len(Week) * HC_r[r]):
            cador += (24 - c[j][r][e_r] + t[(j + 2) % (HC_r[r] * len(Week))][r][e_r]) \
                     >= (36 - 24) - M * (1 - w[r][e_r][j])
            cador += (24 - c[j][r][e_r] + t[(j + 2) % (HC_r[r] * len(Week))][r][e_r]) \
                     <= epsilon + (36 - 24) + M * w[r][e_r][j]
            cador += z[r][e_r][j] <= rest[(j + 1) % (HC_r[r] * len(Week))][r][e_r]  # UB (Upper Bound)
            cador += z[r][e_r][j] <= w[r][e_r][j]  # UB
            cador += z[r][e_r][j] >= rest[(j + 1) % (HC_r[r] * len(Week))][r][e_r] + w[r][e_r][j] - 1  # LB
            cador += (24 + t[(j + 1) % (HC_r[r] * len(Week))][r][e_r] - c[j][r][e_r]) >= 36 - M * (1 - v[r][e_r][j])
            cador += (24 + t[(j + 1) % (HC_r[r] * len(Week))][r][e_r] - c[j][r][e_r]) <= epsilon + 36 + M * v[r][e_r][j]
for r in range(len(T)):
    for e_r in range(Eff[r]):
        for j in range(len(Week) * HC_r[r]):
            cador += lpSum([z[r][e_r][(j-1 + k) % (HC_r[r] * len(Week))] + v[r][e_r][(j-1 + k) % (HC_r[r] * len(Week))]
                            for k in range(6)]) + v[r][e_r][(j + 5) % (HC_r[r] * len(Week))] >= 1

# Constraint 2.b.iii:
# at least 4 days, in which 2 successive days including a sunday of break within each fortnight for full time contracts
for e1 in range(Eff[0]):
    for n in range(HC_r[0]):
        cador += y[n][e1] <= X[Shifts[REPOS]][5 + n * len(Week)][0][e1]
        cador += y[n][e1] <= X[Shifts[REPOS]][6 + n * len(Week)][0][e1]
        cador += y[n][e1] >= X[Shifts[REPOS]][5 + n * len(Week)][0][e1] + X[Shifts[REPOS]][6 + n * len(Week)][0][e1] - 1
for e1 in range(Eff[0]):
    for j in range(len(Week) * HC_r[0]):
        # First part of constraint 2.b.iii
        cador += lpSum([X[Shifts[REPOS]][(j + k) % (HC_r[0] * len(Week))][0][e1] for k in range(2 * len(Week))]) >= 4
    for n in range(HC_r[0]):
        # Second part of constraint 2.b.iii
        cador += y[n][e1] + y[(n + 1) % HC_r[0]][e1] >= 1
# Additional constraint for partial time contracts (two successive working sundays are forbidden)
for r in range(1, len(T)):
    for e_r in range(Eff[r]):
        for k in range(HC):
            cador += X[Shifts[REPOS]][6 + k * len(Week)][r][e_r] + \
                     X[Shifts[REPOS]][6 + ((k + 1) % HC) * len(Week)][r][e_r] >= 1

# Constraint 3.a: respect of the working hours for each type of contracts
for r in range(len(T)):
    for e_r in range(Eff[r]):
        cador += (lpSum([lpSum([X[Shifts[s]][j][r][e_r] for j in range(HC * len(Week))])
                         * (duration_D[s] * 10 - (0 if breakDuration[s] is None else breakDuration[s] * 10))
                         for s in Work_Shifts]) +
                  lpSum([X[Shifts[JCA]][j][r][e_r] * 7.5 * 10
                         for j in range(HC * len(Week))])) * 100 <= (37.5 * 10) * HC * (ratios[r] * 100)

# Constraint 3.b: respect of the number of working days for each type of contracts
for r in range(len(T)):
    for e_r in range(Eff[r]):
        cador += lpSum([lpSum([X[Shifts[s]][j][r][e_r] for s in Work_Shifts_And_Jca])
                        for j in range(HC * len(Week))]) <= 5 * HC * ratios[r]

# Soft constraints

# Constraint 1: number of Jca at least equals to 20% of total number of staff members
team_size = sum([Eff[r] for r in range(len(T))])
for j in range(len(Week) * HC):
    # The constraint is relaxed via the inferior round on the number of Jca needed and special case on sundays
    # To compensate for this relaxation, the target function maximise the number of JCA (in particular on sundays)
    cador += lpSum([lpSum([X[Shifts[JCA]][j][r][e_r] for e_r in range(Eff[r])]) for r in range(len(T))]) \
             >= math.floor(0.2 * team_size) - (nb_sunday_jca_removed if j % len(Week) == 6 else 0)
    cador += lpSum([lpSum([X[Shifts[JCA]][j][r][e_r] for e_r in range(Eff[r])]) for r in range(len(T))]) <= 3
cador += lpSum([lpSum([lpSum([X[Shifts[JCA]][j][r][e_r] for e_r in range(Eff[r])]) for r in range(len(T))])
                for j in range(len(Week) * HC) if j % len(Week) == 6]) >= 0.25 * HC

# Constraint 3.c: number of sundays worked by partial-time agents vs those worked by full-time agents
# Note : all full-time agents are working the same number of sundays : the first one of them is taken as a reference
for r in range(1, len(T)):
    prop = 1 if r in [1, 2] else (0.75 if r in [3, 4] else 0.60)  # 0.6 (r in [5, 6])
    for e_r in range(Eff[r]):
        cador += lpSum([lpSum([X[Shifts[s]][k * len(Week) + 6][r][e_r] for s in Work_Shifts_And_Jca])
                        for k in range(HC)]) <= prop * lpSum([lpSum([X[Shifts[s]][k * len(Week) + 6][0][0]
                                                                     for s in Work_Shifts_And_Jca]) for k in range(HC)])

# Equity definition
# for s in Work_Shifts_And_Jca:
#     for r in range(1, len(T)):
#         if Eff[r] > 0:
#             cador += equity_pos >= 0
#             cador += equity_pos >= lpSum([X[Shifts[s]][j][r][0] for j in range(HC * len(Week))]) * 100 - \
#                      lpSum([X[Shifts[s]][j][0][0] for j in range(HC * len(Week))]) * ratios[r] * 100
#             cador += equity_neg >= 0
#             cador += equity_neg >= lpSum([X[Shifts[s]][j][0][0] for j in range(HC * len(Week))]) * ratios[r] * 100 - \
#                      lpSum([X[Shifts[s]][j][r][0] for j in range(HC * len(Week))]) * 100
# cador += equity >= equity_neg
# cador += equity >= equity_pos

# Target Function
# Satisfy the constraints without a specific target function to minimise
# cador += 1
# Maximise the number of JCA (in priority on sundays) in the planning
cador += (-1) * lpSum([lpSum([lpSum([X[Shifts[JCA]][j][r][e_r] for j in range(HC * len(Week))])
                              for e_r in range(Eff[r])]) for r in range(len(T))])
# Maximise the equity (define as in the previous definition)
# cador += - equity

# Solving
start_time = time.time()
cplex_path = "C:\\Program Files\\IBM\\ILOG\\CPLEX_Studio1210\\cplex\\bin\\x64_win64\\cplex.exe"
status = cador.solve(CPLEX(path=cplex_path))
solving_time = time.time() - start_time

if export_results:
    if LpStatus[status] == 'Optimal':
        OrderedShifts = [s for s in sorted(Shifts.items(), key=lambda shift: shift[1])]
        work_cycles = [[[OrderedShifts[[int(round(value(X[i][j][r][e_r]))) for i in range(len(Shifts))].index(1)][0]
                         for j in range(len(Week) * HC)] for e_r in range(Eff[r])] for r in range(len(T))]
        export_work_cycles_results_as_csv(exportation_path, instance_id, LpStatus[status], solving_time, ratios,
                                          week_days, Day_Shifts, Night_Shifts, duration_D, breakDuration, N,
                                          work_cycles)
    else:
        export_work_cycles_results_as_csv(exportation_path, instance_id, LpStatus[status], solving_time, ratios,
                                          week_days, Day_Shifts, Night_Shifts, duration_D, breakDuration, N, None)
