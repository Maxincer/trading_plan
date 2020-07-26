# 算法： perfect shape
# coding:utf-8

from sympy import linsolve, Symbol, solve
import pandas as pd

x = Symbol('x')
y = Symbol('y')

solved = solve([x * 1.088 + 25.1 * y - 55450 - 1937, x - (y + 365) * 125.7], x, y)
print(solved)