# 算法： perfect shape
# coding:utf-8

from sympy import linsolve, Symbol, solve
import pandas as pd

x = Symbol('x')
y = Symbol('y', real=True)
solved = solve([x * 1.088 + 26.3 * abs(y) - 8946, x + (y) * 131.6 - 8733], x, y)
print(solved)
print('asd'.replace('e', 'f'))