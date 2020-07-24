# 算法： perfect shape
# coding:utf-8

from sympy import linsolve, Symbol, solve
import pandas as pd


x = Symbol('x', real=True)
y = Symbol('y', real=True)
# solve = solve([x * 1.088 + y * 26.5 - 11528 - 920,. x + 133 * y - (11528 + 920) * 0.99], x, y)
ret = solve([1.088 * x + 26.4 * y - 4560, x + 132.4 * y - 4500 - 4057], x, y)
print(ret)