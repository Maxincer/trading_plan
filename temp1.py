# coding: utf8

import pandas as pd
fpath_ax = '//192.168.2.149/ax_auto_export_data/普通账户持仓20200811.csv'
df_temp = pd.read_csv(fpath_ax, encoding='ansi')
print(df_temp)