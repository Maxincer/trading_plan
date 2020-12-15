# 算法： perfect shape
# coding:utf-8

from sympy import linsolve, Symbol, solve

spot_905 = 6353.84 * 200 / 10000
spot_016 = 3295.58 * 300 / 10000
print(spot_905)
print(spot_016)
na_perlot_ic = spot_905 / 5
na_perlot_ih = spot_016 / 5
print(na_perlot_ic)
print(na_perlot_ih)

#
# # 1109
# # 500万CTA
# cpslongamt = Symbol('cpslongamt')
# iclots = Symbol('iclots', real=True)
# ce = Symbol('ce', real=True)
# liability = 0
# ttasset = 2119
# na = ttasset - liability
#
# eq_cpslongamt = cpslongamt - na * 0.77 * 0.7
# eq_na = ce + cpslongamt * 1.088 + na_perlot_ic * abs(iclots) - ttasset
# eq_exposure = cpslongamt + iclots * spot_905
#
# solved = solve([eq_cpslongamt, eq_na, eq_exposure], ce, cpslongamt, iclots)
# print(solved)
#
# #
# # 1501
# cpslongamt = Symbol('cpslongamt')
# iclots = Symbol('iclots', real=True)
# ce = Symbol('ce', real=True)
# liability = 0
# ttasset = 2889
# na = ttasset - liability
#
# eq_cpslongamt = cpslongamt - na * 0.77 * 0.7
# eq_na = ce + cpslongamt * 1.088 + na_perlot * abs(iclots) - ttasset
# eq_exposure = cpslongamt + iclots * spot_905
#
# solved = solve([eq_cpslongamt, eq_na, eq_exposure], ce, cpslongamt, iclots)
# print(solved)
#
# # 628
# print('628')
# cpslongamt = Symbol('cpslongamt')
# iclots = Symbol('iclots', real=True)
# ce = Symbol('ce', real=True)
# liability = 0
# ttasset = 12603
# na = ttasset - liability
#
# eq_cpslongamt = cpslongamt - na * 0.9 * 0.6
# eq_na = ce + cpslongamt * 1.088 + na_perlot * abs(iclots) - ttasset
# eq_exposure = cpslongamt + iclots * spot_905 - ttasset * 0.99
#
# solved = solve([eq_cpslongamt, eq_na, eq_exposure], ce, cpslongamt, iclots)
# print(solved)
#
# # 630
# print('630')
# cpslongamt = Symbol('cpslongamt')
# iclots = Symbol('iclots', real=True)
# ce = Symbol('ce', real=True)
# liability = 0
# ttasset = 5213
# na = ttasset - liability
#
# eq_cpslongamt = cpslongamt - na * 0.9 * 0.6
# eq_na = ce + cpslongamt * 1.088 + na_perlot * abs(iclots) - ttasset
# eq_exposure = cpslongamt + iclots * spot_905 - ttasset * 0.99
#
# solved = solve([eq_cpslongamt, eq_na, eq_exposure], ce, cpslongamt, iclots)
# print(solved)
#
# # 7072
# print('7072')
# cpslongamt = Symbol('cpslongamt')
# iclots = Symbol('iclots', real=True)
# ce = Symbol('ce', real=True)
# liability = 0
# ttasset = 4109
# na = ttasset - liability
#
# eq_cpslongamt = cpslongamt - na * 0.7
# eq_na = ce + cpslongamt * 1.088 + na_perlot * abs(iclots) - ttasset
# eq_exposure = cpslongamt + iclots * spot_905 - ttasset * 0.99
#
# solved = solve([eq_cpslongamt, eq_na, eq_exposure], ce, cpslongamt, iclots)
# print(solved)
# #
# # 913
# print('913')
# x = Symbol('x')
# y = Symbol('y', real=True)
# solved = solve([x * 1.088 + na_perlot * abs(y) - 35053 - 4078 + 4000, x + (y - 130) * spot_905], x, y)
# print(solved)
# #
# # 707
print('707')
x = Symbol('x')
y = Symbol('y', real=True)
ce = Symbol('ce', real=True)

solved = solve([500 + ce + x * 1.088 + 25.8 * abs(y) - 8302, x + y * spot_905 - 8302 * 0.99, ce], x, y, ce)
print(solved)
# #
# # 930
# print('930')
#
# x = Symbol('x')
# y = Symbol('y', real=True)
# ce = Symbol('ce', real=True)
# solved = solve([ce + x * 1.088 + na_perlot * abs(y) - 11140, x + y * spot_905 - 11140 * 0.297, y + 28], x, y, ce)
# print(solved)
# #
# # # 2
# # x = Symbol('x')
# # y = Symbol('y', real=True)
# # solved = solve([2308 + x * 1.088 + na_perlot * abs(y) - 765 - 5830, x + y * spot_905 - 2821], x, y)
# # print(solved)
# #
# # # 929
# # x = Symbol('x')
# # y = Symbol('y', real=True)
# # solved = solve([x * 1.088 + na_perlot * abs(y) - 8445, x + y * spot_905 - 8445], x, y)
# # print(solved)

# # 11022
# print('11022')
#
# cpslongamt_ei = Symbol('cpslongamt_ei')
# cpslongamt_ssipo = Symbol('cpslongamt_ssipo')
# ce = 0
# iclots = Symbol('iclots', real=True)
# ihlots = Symbol('ihlots', real=True)
# ttasset = 13987
# ssipo_threshold = 8000
#
# # 假设IC多头比IH空头多-影响保证金占用
# # 列方程计算IC与IH的保证金占用
#
# eq_ei_ssipo = cpslongamt_ei * 0.35 + cpslongamt_ssipo - ssipo_threshold
# eq_na = ce + cpslongamt_ei * 1.089 + margin_required_in_faccts + cpslongamt_ssipo - ttasset
# eq_exposure_ei = cpslongamt_ei + iclots * spot_905 - ttasset * 0.99
# eq_exposure_ssipo = cpslongamt_ssipo + ihlots * spot_016
#
# solved = solve([eq_ei_ssipo, eq_na, eq_exposure_ei, eq_exposure_ssipo], cpslongamt_ei, cpslongamt_ssipo, iclots, ihlots)
# print(solved)

# 715
print('715')

cpslongamt_ei = Symbol('cpslongamt_ei')
cpslongamt_ssipo = Symbol('cpslongamt_ssipo')
ce = 0
iclots = Symbol('iclots', real=True)
ihlots = Symbol('ihlots', real=True)
ttasset = 14444
ssipo_threshold = 8000

# 假设IC多头比IH空头多-影响保证金占用
# 列方程计算IC与IH的保证金占用
eq_ei_ssipo = cpslongamt_ei * 0.35 + cpslongamt_ssipo - ssipo_threshold
eq_na = ce + cpslongamt_ei * 1.089 + abs(iclots) * na_perlot_ic + cpslongamt_ssipo - ttasset
eq_exposure_ei = cpslongamt_ei + iclots * spot_905 - ttasset * 0.99
eq_exposure_ssipo = cpslongamt_ssipo + ihlots * spot_016

solved = solve([eq_ei_ssipo, eq_na, eq_exposure_ei, eq_exposure_ssipo], cpslongamt_ei, cpslongamt_ssipo, iclots, ihlots)
print(solved)
iclots = solved[0][2]
ihlots = solved[0][3]
if abs(ihlots) * na_perlot_ih > abs(iclots) * na_perlot_ic:
    print('IH保证金占用大于IC')
    print(f'IC: {abs(iclots) * na_perlot_ic}')
    print(f'IH: {abs(ihlots) * na_perlot_ih}')

# 807
print('807')

cpslongamt_ei = Symbol('cpslongamt_ei')
cpslongamt_ssipo = Symbol('cpslongamt_ssipo')
ce = 0
iclots = Symbol('iclots', real=True)
ihlots = Symbol('ihlots', real=True)
ttasset = 13999
ssipo_threshold = 8000

# 假设IC多头比IH空头多-影响保证金占用
# 列方程计算IC与IH的保证金占用
eq_ei_ssipo = cpslongamt_ei * 0.35 + cpslongamt_ssipo - ssipo_threshold
eq_na = ce + cpslongamt_ei * 1.089 + abs(iclots) * na_perlot_ic + cpslongamt_ssipo - ttasset
eq_exposure_ei = cpslongamt_ei + iclots * spot_905 - ttasset * 0.99
eq_exposure_ssipo = cpslongamt_ssipo + ihlots * spot_016

solved = solve([eq_ei_ssipo, eq_na, eq_exposure_ei, eq_exposure_ssipo], cpslongamt_ei, cpslongamt_ssipo, iclots, ihlots)
print(solved)
iclots = solved[0][2]
ihlots = solved[0][3]
if abs(ihlots) * na_perlot_ih > abs(iclots) * na_perlot_ic:
    print('IH保证金占用大于IC')
    print(f'IC: {abs(iclots) * na_perlot_ic}')
    print(f'IH: {abs(ihlots) * na_perlot_ih}')

# 计算还负债取款

