# coding: utf8

import pandas as pd
fpath_ax = r'D:\data\A_trading_data\A_result\702hao\holding.xlsx'
df_temp = pd.read_excel(fpath_ax, encoding='utf-8', skiprows=3, dtype={'证券代码': str})
print(df_temp)