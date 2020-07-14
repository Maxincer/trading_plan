# 算法： perfect shape
# coding:utf-8

from sympy import solve, Symbol
import pandas as pd


x = Symbol('x')
y = Symbol('y')
solve = solve([x * 1.088 + 27.6 * y - 59907 - 2453 - 5785, x - 138*(y+365)], x, y)
print(solve)
# print(solve([x**2 + y -2, y**2 - 4], x, y, set=True))

s_a = pd.Series([1,2,3,5])
print(type(s_a.max()))

dict_1 = {1:'1', 2: '2'}
print([x for x in zip(*[dict_1])])