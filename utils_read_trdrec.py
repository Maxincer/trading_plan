#!usr/bin/env python37
# coding:utf-8
# Author: Maxincer
# Create Datetime: 20200503T170000 +0800
# Update Datetime: 20200503T170000 +0800

"""
Read downloaded holding files from different broker and trading software.

根据券商+交易软件判定读取函数
现金按照000000处理为position表中的条目

Note:
    1. 核新仅txt格式有资金和持仓；
    2. 通达信仅可存为xls格式，为假格式；xls格式有=赋值。

"""

from os.path import splitext
from functools import wraps

import pandas as pd

fpath_tgt = 'C:/Users/maxinzhe/Desktop/20200504.txt'
fpath1_tgt = 'C:/Users/maxinzhe/Desktop/20200505资金股份查询.xls'


def decorate_read_position(func):
    """
    inner func的参数，可以来自于装饰器。
    """
    @wraps(func)
    def read_position(fpath):
        list_list_capital_data, list_list_holding_data = func(fpath)
        list_dicts_capital_data = [dict(zip(list_list_capital_data[0], list_capital_data))
                                   for list_capital_data in list_list_capital_data[1:]]
        list_dicts_holding_data = [dict(zip(list_list_holding_data[0], list_holding_data))
                                   for list_holding_data in list_list_holding_data[1:]]
        return list_dicts_capital_data, list_dicts_holding_data
    return read_position


@decorate_read_position
def read_sw_tdx(fpath):
    with open(fpath, 'rb') as f:
        list_readlines = f.readlines()
        list_capital_line_data = list_readlines[0].decode('ANSI').strip()[5:].split()
        list_list_capital_data_key = [[capital_line_data.split(':')[0] for capital_line_data in list_capital_line_data]]
        list_list_capital_data_value = [[capital_line_data.split(':')[1] for capital_line_data in list_capital_line_data]]
        list_list_capital_data = list_list_capital_data_key + list_list_capital_data_value
        list_list_holding_data = [line.decode('ANSI').strip().split() for line in list_readlines[3:]]
        return list_list_capital_data, list_list_holding_data


@decorate_read_position
def read_df_ths(fpath):
    with open(fpath, encoding='ANSI') as f:
        list_readlines = f.readlines()
        list_capital_data = []
        for data in list_readlines[3:6]:
            list_capital_data += [_.strip().split('：') for _ in data.strip().split('\t')]
        list_capital_data_key = []
        list_capital_data_value = []
        for _ in list_capital_data:
            if _[0] == '总 资 产':
                _[0] = '总资产'
            list_capital_data_key.append(_[0])
            list_capital_data_value.append(_[1])
        list_list_capital_data = [list_capital_data_key, list_capital_data_value]
        list_list_holding_data = []
        for data in list_readlines[8:]:
            list_holding_data = data.strip().split()
            list_list_holding_data.append(list_holding_data)
        list_list_holding_data = list_list_holding_data[:-3]
        return list_list_capital_data, list_list_holding_data


print(read_df_ths('D:/data/trddata/903c_00350580.txt'))
