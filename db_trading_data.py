#!usr/bin/env python3
# coding:utf8
# Author: Maxincer
# Datetime: 20200413T112000 +0800

"""
DataBase "trddata" maintenance script.
input:
    1. MongoDB: localhost:27017, database: basicinfo
naming convention:
    1. all trading data is in Database trddata;
    2. the collection should be named as f"{prdcode}_{accttype}_{acctid}_{content}}
        1. content include:
            1. b/s_sheet
            2. holding
            3. trade
            4. transfer serial
function:
    1. initialize
    2. update
"""

from datetime import datetime
import os


import pandas as pd
import pymongo


STR_DATE = '20200410'  # todo 该常量目前开发用，实测时应更改为 self.str_today


class DBTradingData:
    def __init__(self):
        self.client_mongo = pymongo.MongoClient('mongodb://localhost:27017/')
        self.db_basicinfo = self.client_mongo['basicinfo']
        self.col_myacctsinfo = self.db_basicinfo['myacctsinfo']
        self.db_trddata = self.client_mongo['db_trddata']
        self.today = datetime.strftime(datetime.today(), '%Y%m%d')
        self.dirpath_raw_data = 'D:/data/A_trading_data/1500+/A_result'

    @staticmethod
    def __process_raw_data_cash(fpath_holding):
        str_ext = os.path.splitext(fpath_holding)[1]
        if str_ext in ['.xlsx', '.xls']:
            df_capital = pd.read_excel(fpath_holding, nrows=1)
            df_holding = pd.read_excel(fpath_holding, skiprows=3)
        elif str_ext == '.csv':
            df_capital = pd.read_csv(fpath_holding, nrows=1, encoding='gbk',
                                     dtype={'资产账户': str, '总资产': float, '总负债': float, '净资产': float,
                                            '资金可用金': float})
            df_holding = pd.read_csv(fpath_holding, skiprows=3, encoding='gbk',
                                     dtype={'证券代码': str, '市值': float})
        else:
            raise TypeError('Unknown file type!')
        print(df_capital)
        print(df_holding)



    def update_all_trddata(self):
        """
        f"{prdcode}_{accttype}_{acctid}_{content}}
        :return:
        """
        cursor_find = self.col_myacctsinfo.find({'date': STR_DATE, 'accttype': 'c', 'rptmark': '1'})
        for _ in cursor_find:
            prdcode = _['prdcode']
            accttype = _['accttype']
            acctid = _['acctid']
            colname = f'{prdcode}_{accttype}_{acctid}_b/s'
            col_bs = self.db_trddata[colname]

            fpath_holding = self.dirpath_raw_data + f'/{STR_DATE}' + _['fpath_holding']
            dict_data_to_be_updated = self.__process_raw_data_cash(fpath_holding)
            if col_bs.find_one({'date': STR_DATE, 'acctid': acctid}):
                col_bs.update(dict_data_to_be_updated)
            else:
                col_bs.insert_one(dict_data_to_be_updated)









