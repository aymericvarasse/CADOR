from pulp import *
import numpy as np
from time import time

# Parameters
Week = [i for i in range(7)]  # days of week
T = [i for i in range(7)]  # types of contracts
Night_Shifts = {"N": 3}  # types of night shifts
Day_Shifts = {"M": 0, "J": 1, "S": 2}  # types of day shifts
Off_Shifts = {"Jca": 4, "Repos": 5}  # types of off shifts
Work_Shifts = {**Night_Shifts, **Day_Shifts}
Shifts = {**Night_Shifts, **Day_Shifts, **Off_Shifts}

# Instance dependant Parameters
beginningTime_t = {"M": 6, "J": 9, "S": 14, "N": 20}
completionTime_c = {"M": 14, "J": 17, "S": 22, "N": 6}
duration_D = {"M": 8, "J": 8, "S": 8, "N": 10}
breakDuration = {"M": 0.5, "J": 0.5, "S": 0.5}
N = [{"M": 2, "J": 1, "S": 2, "N": 1} for j in Week]  # workforce needs for every shifts of every day in week
Eff = [3 for i in T]  # number of employees already affected for each type of contract
# Work cycles length (not a variable in this model)
HC_r = [eff for eff in Eff]
# Overall work cycle length
HC = int(np.lcm.reduce(HC_r))
# Horizon of the plannings creation

# Variables
# X2 = [[[[LpVariable("x" + str(i) + "_" + str(j) + "_" + str(r) + "_" + str(e_r), 0, 1, cat=LpInteger)
#          for i in range(len(Shifts))] for j in range(1, len(Week) * HC + 1)] for e_r in range(Eff[r])]
#       for r in range(len(T))]
X = [[[[LpVariable("x" + str(i) + "_" + str(j) + "_" + str(r) + "_" + str(e_r), 0, 1, cat=LpInteger)
        for e_r in range(Eff[r])] for r in range(len(T))] for j in range(1, len(Week) * HC + 1)]
     for i in range(len(Shifts))]
# t2 = [[[LpVariable("t" + str(j) + "_" + str(r) + "_" + str(e_r), 0, 48, cat=LpInteger)
#        for j in range(1, len(Week) * HC + 1)] for e_r in range(Eff[r])] for r in range(len(T))]
t = [[[LpVariable("t" + str(j) + "_" + str(r) + "_" + str(e_r), 0, 48, cat=LpInteger)
       for e_r in range(Eff[r])] for r in range(len(T))] for j in range(1, len(Week) * HC + 1)]
# c2 = [[[LpVariable("c" + str(j) + "_" + str(r) + "_" + str(e_r), 0, 48, cat=LpInteger)
#         for j in range(1, len(Week) * HC + 1)] for e_r in range(Eff[r])] for r in range(len(T))]
c = [[[LpVariable("c" + str(j) + "_" + str(r) + "_" + str(e_r), 0, 48, cat=LpInteger)
       for e_r in range(Eff[r])] for r in range(len(T))] for j in range(1, len(Week) * HC + 1)]
# rest2 = [[[LpVariable("r" + str(j) + "_" + str(r) + "_" + str(e_r), 0, 1, cat=LpInteger)
#            for j in range(1, len(Week) * HC + 1)] for e_r in range(Eff[r])] for r in range(len(T))]
rest = [[[LpVariable("r" + str(j) + "_" + str(r) + "_" + str(e_r), 0, 1, cat=LpInteger)
          for e_r in range(Eff[r])] for r in range(len(T))] for j in range(1, len(Week) * HC + 1)]

# Problem
cador = LpProblem("CADOR", LpMinimize)

# Constraints

# Hard Constraints

# Constraint 0: repetition of the patterns for each type of contract
for r in T:
    for e_r in range(Eff[r]):
        for i in range(len(Shifts)):
            for j in range(HC_r[r]):
                if HC_r[r] != HC:
                    for k in range(HC // HC_r[r]):
                        cador += X[i][j][r][e_r] == X[i][j + k * HC_r[r]][r][e_r]

# Constraint 1.a: respect of needs
for s in Work_Shifts:
    for j in range(len(Week)):
        for k in range(HC):
            cador += lpSum([lpSum([X[Work_Shifts[s]][j + k * len(Week)][r][e_r] for r in T]) for e_r in range(Eff[r])]) \
                     >= N[j][s]

# Constraint 1.b: only one shift per day per person
for r in T:
    for e_r in range(Eff[r]):
        for j in range(1, len(Week) * HC_r[r]):
            cador += lpSum([X[i][j][r][e_r] for i in range(len(Shifts))]) == 1

# Constraint 1.c: no single work day
for r in T:
    for e_r in range(Eff[r]):
        for j in range(1, len(Week) * HC_r[r] - 2):
            cador += lpSum([X[Shifts[s]][j + 1][r][e_r] for s in Work_Shifts]) <= \
                     lpSum([X[Shifts[s]][j][r][e_r] for s in Work_Shifts]) + \
                     lpSum([X[Shifts[s]][j + 2][r][e_r] for s in Work_Shifts])

# Constraint 1.d: maximum of 5 consecutive days of work
for r in T:
    for e_r in range(Eff[r]):
        for j in range(len(Week) * HC_r[r] - 5):
            cador += lpSum([lpSum([X[Shifts[s]][j + k][r][e_r]
                                   for s in Work_Shifts]) for k in range(6)]) <= 5

# Constraint 1.e: same shift on Saturdays and Sundays
for r in T:
    for e_r in range(Eff[r]):
        for s in Work_Shifts:
            for n in range(1, HC_r[r] + 1):
                j = 5 * n
                cador += X[Shifts[s]][j][r][e_r] == X[Shifts[s]][j + 1][r][e_r]

# Constraint 2.a.i: working time per week (non-sliding) may not exceed 45 hours
for r in T:
    for e_r in range(Eff[r]):
        for q in range(HC_r[r]):
            cador += lpSum([lpSum([X[Shifts[s]][q + len(Week) + k][r][e_r] * duration_D[s]
                                   for k in range(len(Week))]) for s in Work_Shifts]) <= 45

# Constraint 2.a.ii: employees cannot work more than 48h within 7 sliding days
for r in T:
    for e_r in range(Eff[r]):
        for j in range(len(Week) * (e_r - 1) + 1):
            cador += lpSum([lpSum([X[Shifts[s]][j + k][r][e_r] * duration_D[s]
                                   for k in range(7)]) for s in Work_Shifts]) <= 48

# Constraints 2.b:

# Constraint 2.b.o: definition of the variables t (beginning time)
for r in T:
    for e_r in range(Eff[r]):
        for j in range(len(Week) * HC_r[r]):
            cador += t[j][r][e_r] == lpSum([beginningTime_t[s] * X[Shifts[s]][j][r][e_r] for s in Work_Shifts])\
                     + 24 * (1 - lpSum([X[Shifts[s]][j][r][e_r] for s in Work_Shifts]))

# Constraint 2.b.oo: definition of the variables c (completion time)
for r in T:
    for e_r in range(Eff[r]):
        for j in range(1, len(Week) * HC_r[r] + 1):
            cador += c[j][e_r][r] == lpSum([(beginningTime_t[s] + duration_D[s])
                                            * X[Shifts[s]][j][r][e_r] for s in Work_Shifts])

# Constraint 2.b.ooo: definition of the variables r (rest/off day or not)
for r in T:
    for e_r in range(Eff[r]):
        for j in range(1, len(Week) * HC_r[r] + 1):
            cador += rest[j][e_r][r] == 1 - lpSum([X[Shifts[s]][j][r][e_r] for s in Work_Shifts])

# Constraint 2.b.i: minimum daily rest time of 12 hours
for r in T:
    for e_r in range(Eff[r]):
        for j in range(1, len(Week) * HC_r[r] - 1):
            cador += (24 + t[j][e_r][r]) + c[j][e_r][r] <= 12

# Constraint 2.b.ii: minimum of 36 consecutive hours for weekly rest (sliding)
for r in T:
    for e_r in range(Eff[r]):
        for j in range(1, len(Week) * HC_r[r] - 5):
            cador += lpSum([rest[j + k][e_r][r] * ((24 - c[j + k - 1][e_r][r]) + t[j + k + 1][e_r][r] >= (36 - 24))
                            + (24 + t[j + k][e_r][r] - c[j + k - 1][e_r][r] >= 36) for k in range(5)]) \
                     + (24 + t[j + 5][e_r][r] - c[j + 4][e_r][r] >= 36) >= 1

# Constraint 2.b.iii: at least 4 days, in which 2 successive days including a sunday of break within each fortnight for
# full time contracts
for e1 in range(Eff[0]):
    for j in range(len(Week) * (HC_r[0] - 2) + 1):
        cador += lpSum([X[Shifts["Repos"]][j + k][0][e1] for k in range(2 * len(Week))]) >= 4
        cador += lpSum([X[Shifts["Repos"]][j + 2 * k][0][e1] == X[Shifts["Repos"]][j + 2 * k + 1][0][e1]
                        for k in range(len(Week))]) >= 1
        cador += lpSum([X[Shifts["Repos"]][j + k][0][e1] for k in range(2 * len(Week)) if j + k == 6]) >= 1

# Soft constraints

# Constraint 1: number of Jca at least equals to 20% of total number of staff members
for j in range(len(Week) * HC):
    cador += lpSum([lpSum([X[Shifts["Jca"]][j][0][e_r] for e_r in range(Eff[r])]) for r in T]) \
             <= 0.2 * lpSum([lpSum([e_r for e_r in range(Eff[r])]) for r in T])

# Target Function
cador += 1

# Solving
start_time = time()
status = cador.solve()
print("Problem solved in " + str(round(time() - start_time, 3)) + " seconds")
print(LpStatus[status])
