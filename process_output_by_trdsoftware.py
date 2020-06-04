#!usr/bin/python3
# coding:utf-8
# Author: Maxincer
# Update: 20200421T103000 +0800

"""
This file provides tools to clean data according to different broker trading software.
Note:
    1. 决定输出格式的为：经纪商+交易软件（不考虑交易软件本身升级的情况， 若升级，则做升级处理）；
    2. 建立经纪商交易软件及账户映射表；
    3. 出于manually download的运行速度考虑，优先选择体积小的交易软件；但一些账户要求特定交易软件交易；
    4. 目前只需要处理holding数据，及capital持仓及position明细。
Convention:
    1. manually download 的数据的通用格式为：
        1.前两行为capital，第三行为空行， 第四行开始为持仓数据，尾行无其他信息。
"""

from datetime import datetime
import os

import pandas as pd
import pymongo

dirpath_manually_downloaded = 'D:/data/'
fpath_output = 'D:/data/A_trading_data/1500+/A_result/20200415/dld_omo/903csw_2419033778_capital.xlsx'
df_temp = pd.read_excel(fpath_output)
dict_temp = df_temp.to_dict('record')
client_mongo = pymongo.MongoClient('mongodb://localhost:27017/')
db_basicinfo = client_mongo['basicinfo']
col_myacctsinfo = db_basicinfo['myacctsinfo']


def prcs_sw_alphabee(acctid):



def process_output(fpath_output, method='general'):
    """
    本脚本主函数，将各函数打包。
    """
    pass







