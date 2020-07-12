# 算法： perfect shape
# coding:utf-8

from sympy import solve, Symbol
import pandas as pd


x = Symbol('x')
y = Symbol('y')
z = 100
solve = solve([z + 3000 + 1.09 * x + 26.8 * (y+1) - 10134, x + 134 * (y+1) - 10134 * 0.8], x, y, z)
print(solve)
# print(solve([x**2 + y -2, y**2 - 4], x, y, set=True))

s_a = pd.Series([1,2,3,5])
print(type(s_a.max()))

