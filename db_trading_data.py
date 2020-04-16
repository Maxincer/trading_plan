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

from trader import Trader


class DBTradingData:
    def __init__(self):
        self.str_today = datetime.strftime(datetime.today(), '%Y%m%d')
        self.str_today = '20200415'
        self.client_mongo = pymongo.MongoClient('mongodb://localhost:27017/')
        self.db_basicinfo = self.client_mongo['basicinfo']
        self.col_myacctsinfo = self.db_basicinfo['myacctsinfo']
        self.db_trddata = self.client_mongo['db_trddata']
        self.dirpath_raw_data = 'D:/data/A_trading_data/1500+/A_result'

    @staticmethod
    def read_lines(fpath, skiprows=0, nrows=0):
        with open(fpath, 'rb') as f:
            list_list_datainline = []
            list_lines = f.readlines()
            if nrows:
                for line in list_lines[skiprows:skiprows + nrows]:
                    line = line.decode(encoding='gbk', errors='replace').replace('=', '').replace('"', '')
                    list_datainline = line.split('\t')
                    list_list_datainline.append(list_datainline)
            else:
                for line in list_lines[skiprows:]:
                    line = line.decode(encoding='gbk', errors='replace').replace('=', '').replace('"', '')
                    list_datainline = line.split('\t')
                    list_list_datainline.append(list_datainline)
            df_ret = pd.DataFrame(list_list_datainline[1:], columns=list_list_datainline[0])
            return df_ret

    @staticmethod
    def read_xlsx(fpath):
        """
        本函数为业务函数， 面向读取xlsx格式的一揽子方案。
        1. 正常情况下，xlsx正常读取；
        2. 如925的情况，xlsx格式，首行为合并单元格： 资金

        :param fpath:
        :return:
        """
        df_capital = pd.read_excel(fpath, nrows=1)
        df_holding = pd.read_excel(fpath, skiprows=3)
        if 'Unnamed' in list(df_capital.columns)[1]:
            df_capital = pd.read_excel(fpath, nrows=1, skiprows=1)
            df_holding = pd.read_excel(fpath, skiprows=10)
        return df_capital, df_holding

    @staticmethod
    def seccode2bsitem(str_code):
        """
        Transfer the code into b/s item of the account
        :param str_code: 6-digit code
        :return:
        str
            {
            'st': stock, 股票
            'ce': 现金及一般等价物,
            'unknown': others
            }
        :note:
        无B股股东账户， 在清洗持仓数据时，为考虑B股代码问题。

        """
        str_code = str_code.zfill(6)
        if str_code[:3] in ['600', '601', '603', '688', '689']:  # 未考虑B股
            return 'st'
        elif str_code[:2] in ['00', '30']:
            return 'st'
        elif str_code[:3] in ['204', '511', '159', '519', '521', '660']:
            return 'ce'
        elif str_code[:2] in ['13']:
            return 'ce'
        else:
            print(f'New security type found, please check {str_code} type and update the function "seccode2bsitem".')
            return 'unknown'

    def process_manually_downloaded_data(self, fpath_holding):
        """
        将指定路径人工下载的交易数据文件转换为dataframe，格式为数据文件原格式。

        :param fpath_holding:
        :return: DataFrame
        """
        str_ext = os.path.splitext(fpath_holding)[1]
        if str_ext == '.xlsx':
            df_capital, df_holding = self.read_xlsx(fpath_holding)
        elif str_ext == '.xls':
            df_capital = self.read_lines(fpath_holding, nrows=2)
            df_holding = self.read_lines(fpath_holding, skiprows=3)
        elif str_ext == '.csv':
            df_capital = pd.read_csv(fpath_holding, nrows=1, encoding='gbk',
                                     dtype={'资产账户': str, '总资产': float, '总负债': float,
                                            '净资产': float, '资金可用金': float})
            df_holding = pd.read_csv(fpath_holding, skiprows=3, encoding='gbk', dtype={'证券代码': str, '市值': float})
        else:
            raise TypeError('Unknown file type!')
        return df_capital, df_holding

    def update_manually_downloaded_data(self):
        """
        出于数据处理留痕及增强robust考虑，将原始数据按照原格式上传到mongoDB中备份
        """
        col_manually_downloaded_rawdata_capital = self.db_trddata['manually_downloaded_rawdata_capital']
        col_manually_downloaded_rawdata_holding = self.db_trddata['manually_downloaded_rawdata_holding']
        for _ in self.col_myacctsinfo.find({'date': self.str_today, 'rptmark': '1'}):
            fpath_holding = _['fpath_holding']
            acctid = _['acctid']
            prdcode = _['prdcode']
            if '/' in fpath_holding:
                fpath_holding = self.dirpath_raw_data + f'/{self.str_today}' + fpath_holding
                df_capital, df_holding = self.process_manually_downloaded_data(fpath_holding)
                list_dicts_capital = df_capital.to_dict('record')
                for _ in list_dicts_capital:
                    _['date'] = self.str_today
                    _['acctid'] = acctid
                col_manually_downloaded_rawdata_capital.delete_many({'date': self.str_today, 'acctid': acctid})
                col_manually_downloaded_rawdata_capital.insert_many(list_dicts_capital)
                print(f'{prdcode}: col manually downloaded data of capital updated.')
                list_dicts_holding = df_holding.to_dict('record')
                for _ in list_dicts_holding:
                    _['date'] = self.str_today
                    _['acctid'] = acctid
                col_manually_downloaded_rawdata_holding.delete_many({'date': self.str_today, 'acctid': acctid})
                col_manually_downloaded_rawdata_holding.insert_many(list_dicts_holding)
                print(f'{prdcode}: col manually downloaded data of holding updated.')

    def update_trddata_f(self):
        """
        f"{prdcode}_{accttype}_{acctid}_{content}}
        # todo 可用装饰器优化
        """
        cursor_find = self.col_myacctsinfo.find({'date': self.str_today, 'accttype': 'f', 'rptmark': '1'})
        for _ in cursor_find:
            prdcode = _['prdcode']
            accttype = _['accttype']
            acctid = _['acctid']
            colname_capital = f'{prdcode}_{accttype}_{acctid}_b/s'
            trader = Trader(acctid)
            dict_res_capital = trader.query_account()
            if dict_res_capital['success'] == 1:
                dict_capital_to_be_update = dict_res_capital['list'][0]
                dict_capital_to_be_update['date'] = self.str_today
                col_f_capital = self.db_trddata[colname_capital]
                col_f_capital.delete_many({'date': self.str_today})
                col_f_capital.insert_one(dict_capital_to_be_update)
                print(f'Query capital data of {acctid}({accttype}) succeed.')
            else:
                print(f'Query capital data of {acctid}({accttype}) failed.')

            colname_holding = f'{prdcode}_{accttype}_{acctid}_holding'
            dict_res_holding = trader.query_holding()
            if dict_res_holding['success'] == 1:
                list_dicts_holding_to_be_update = dict_res_holding['list']
                for dict_holding_to_be_update in list_dicts_holding_to_be_update:
                    dict_holding_to_be_update['date'] = self.str_today
                    dict_holding_to_be_update['acctid'] = acctid
                col_f_holding = self.db_trddata[colname_holding]
                col_f_holding.delete_many({'date': self.str_today})
                if list_dicts_holding_to_be_update:
                    col_f_holding.insert_many(list_dicts_holding_to_be_update)
                else:
                    pass
                print(f'Query holding data of {acctid}({accttype}) succeed.')

            else:
                print(f'Query holding data of {acctid}({accttype}) succeed.')

            colname_trading = f'{prdcode}_{accttype}_{acctid}_trading'
            dict_res_trading = trader.query_trading()
            if dict_res_trading['success'] == 1:
                list_dicts_trading_to_be_update = dict_res_trading['list']
                for dict_trading_to_be_update in list_dicts_trading_to_be_update:
                    dict_trading_to_be_update['date'] = self.str_today
                    dict_trading_to_be_update['acctid'] = acctid
                col_f_trading = self.db_trddata[colname_trading]
                col_f_trading.delete_many({'date': self.str_today})
                if list_dicts_trading_to_be_update:
                    col_f_trading.insert_many(list_dicts_trading_to_be_update)
                else:
                    pass
                print(f'Query trading data of {acctid}({accttype}) succeed.')

            else:
                print(f'Query trading data of {acctid}({accttype}) succeed.')


if __name__ == '__main__':
    a = DBTradingData()
    a.update_manually_downloaded_data()
    # a.update_trddata_f()












