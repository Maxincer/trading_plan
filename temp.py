# 算法： perfect shape
# coding:utf-8

from sympy import linsolve, Symbol, solve
import pandas as pd

# x = Symbol('x')
# y = Symbol('y', real=True)
# solved = solve([x * 1.088 + 26.3 * abs(y) - 60476, x + (y) * 131.6 - 8733], x, y)
# print(solved)

spot_905 = 6623 * 200 /10000
print(spot_905)
na_perlot = spot_905/5
print(na_perlot)

# 913
x = Symbol('x')
y = Symbol('y', real=True)
solved = solve([x * 1.088 + na_perlot * abs(y) - 58856 - 2062, x + (y - 365) * spot_905], x, y)
print(solved)

# 707
x = Symbol('x')
y = Symbol('y', real=True)
solved = solve([500 + x * 1.088 + na_perlot * abs(y) - 9948, x + y * spot_905 - 9948 * 0.99], x, y)
print(solved)

# 930
x = Symbol('x')
y = Symbol('y', real=True)
solved = solve([x * 1.088 + na_perlot * abs(y) - 3451, x + y * spot_905 - 3451 * 0.99], x, y)
print(solved)

# 2
x = Symbol('x')
y = Symbol('y', real=True)
solved = solve([2308 + x * 1.088 + na_perlot * abs(y) - 765 - 5830, x + y * spot_905 - 2821], x, y)
print(solved)

# 929
x = Symbol('x')
y = Symbol('y', real=True)
solved = solve([x * 1.088 + na_perlot * abs(y) - 8445, x + y * spot_905 - 8445], x, y)
print(solved)