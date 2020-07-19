# 算法： perfect shape
# coding:utf-8

from sympy import linsolve, Symbol, solve
import pandas as pd


x = Symbol('x', real=True)
y = Symbol('y', real=True)
# solve = solve([x * 1.088 + y * 26.5 - 11528 - 920, x + 133 * y - (11528 + 920) * 0.99], x, y)
ret = linsolve([35965 - x - 3 * (12102 - x) - 2410], x)
print(ret)


repay = Symbol('repay', real=True)
withdraw = 2404

na = 23862
liability = 12102

ret1 = solve([((na + liability - repay - withdraw) / (liability - repay)) - 3], repay)

print(ret1)

with open(r'D:\projects\trading_plan\data\trdrec_from_trdclient\1207_c_db_3756.txt', 'rb') as f:
    list_datalines = f.readlines()
    for dataline in list_datalines:
        print(dataline)
