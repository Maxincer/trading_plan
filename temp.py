# 算法： perfect shape
# coding:utf-8

from sympy import linsolve, Symbol, solve



spot_905 = 6525 * 200 / 10000
print(spot_905)
na_perlot = spot_905/5
print(na_perlot)

# 1109
# 500万CTA
cpslongamt = Symbol('cpslongamt')
iclots = Symbol('iclots', real=True)
ce = Symbol('ce', real=True)
liability = 0
ttasset = 2119
na = ttasset - liability

eq_cpslongamt = cpslongamt - na * 0.77 * 0.7
eq_na = ce + cpslongamt * 1.088 + na_perlot * abs(iclots) - ttasset
eq_exposure = cpslongamt + iclots * spot_905

solved = solve([eq_cpslongamt, eq_na, eq_exposure], ce, cpslongamt, iclots)
print(solved)

#
# 1501
cpslongamt = Symbol('cpslongamt')
iclots = Symbol('iclots', real=True)
ce = Symbol('ce', real=True)
liability = 0
ttasset = 2889
na = ttasset - liability

eq_cpslongamt = cpslongamt - na * 0.77 * 0.7
eq_na = ce + cpslongamt * 1.088 + na_perlot * abs(iclots) - ttasset
eq_exposure = cpslongamt + iclots * spot_905

solved = solve([eq_cpslongamt, eq_na, eq_exposure], ce, cpslongamt, iclots)
print(solved)

# 628
print('628')
cpslongamt = Symbol('cpslongamt')
iclots = Symbol('iclots', real=True)
ce = Symbol('ce', real=True)
liability = 0
ttasset = 12603
na = ttasset - liability

eq_cpslongamt = cpslongamt - na * 0.9 * 0.6
eq_na = ce + cpslongamt * 1.088 + na_perlot * abs(iclots) - ttasset
eq_exposure = cpslongamt + iclots * spot_905 - ttasset * 0.99

solved = solve([eq_cpslongamt, eq_na, eq_exposure], ce, cpslongamt, iclots)
print(solved)

# 630
print('630')
cpslongamt = Symbol('cpslongamt')
iclots = Symbol('iclots', real=True)
ce = Symbol('ce', real=True)
liability = 0
ttasset = 5213
na = ttasset - liability

eq_cpslongamt = cpslongamt - na * 0.9 * 0.6
eq_na = ce + cpslongamt * 1.088 + na_perlot * abs(iclots) - ttasset
eq_exposure = cpslongamt + iclots * spot_905 - ttasset * 0.99

solved = solve([eq_cpslongamt, eq_na, eq_exposure], ce, cpslongamt, iclots)
print(solved)

# 7072
print('7072')
cpslongamt = Symbol('cpslongamt')
iclots = Symbol('iclots', real=True)
ce = Symbol('ce', real=True)
liability = 0
ttasset = 4109
na = ttasset - liability

eq_cpslongamt = cpslongamt - na * 0.7
eq_na = ce + cpslongamt * 1.088 + na_perlot * abs(iclots) - ttasset
eq_exposure = cpslongamt + iclots * spot_905 - ttasset * 0.99

solved = solve([eq_cpslongamt, eq_na, eq_exposure], ce, cpslongamt, iclots)
print(solved)
#
# 913
print('913')
x = Symbol('x')
y = Symbol('y', real=True)
solved = solve([x * 1.088 + na_perlot * abs(y) - 35053 - 4078 + 4000, x + (y - 130) * spot_905], x, y)
print(solved)
#
# 707
print('707')
x = Symbol('x')
y = Symbol('y', real=True)
ce = Symbol('ce', real=True)

solved = solve([500 + ce + x * 1.088 + na_perlot * abs(y) - 9907, x + y * spot_905 - 9907 * 0.99, y - 22], x, y, ce)
print(solved)
#
# 930
print('930')

x = Symbol('x')
y = Symbol('y', real=True)
ce = Symbol('ce', real=True)
solved = solve([ce + x * 1.088 + na_perlot * abs(y) - 11140, x + y * spot_905 - 11140 * 0.297, y + 28], x, y, ce)
print(solved)
#
# # 2
# x = Symbol('x')
# y = Symbol('y', real=True)
# solved = solve([2308 + x * 1.088 + na_perlot * abs(y) - 765 - 5830, x + y * spot_905 - 2821], x, y)
# print(solved)
#
# # 929
# x = Symbol('x')
# y = Symbol('y', real=True)
# solved = solve([x * 1.088 + na_perlot * abs(y) - 8445, x + y * spot_905 - 8445], x, y)
# print(solved)