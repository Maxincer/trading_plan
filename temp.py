# 算法： perfect shape
# coding:utf-8

from sympy import linsolve, Symbol, solve
import pandas as pd

x = Symbol('x')
y = Symbol('y', real=True)
solved = solve([x * 1.088 + 26 * y - 22261, x + y * 130.2 - 22261 * 0.99], x, y)
print(solved)

print(1 == True)