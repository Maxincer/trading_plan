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
        # self.str_today = datetime.strftime(datetime.today(), '%Y%m%d')
        self.str_today = '20200415'
        self.client_mongo = pymongo.MongoClient('mongodb://localhost:27017/')
        self.db_basicinfo = self.client_mongo['basicinfo']
        self.col_myacctsinfo = self.db_basicinfo['myacctsinfo']
        self.db_trddata = self.client_mongo['trddata']
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
        将指定路径人工下载的交易数据文件转换为DataFrame，格式为数据文件原格式。

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
            colname_capital = f'{prdcode}_{accttype}_{acctid}_capital'
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

    def get_dict_capital_for_cash_acct(self, acctid):
        """
        获取self.today指定的acctid的capital数据, 被update_trddata_c调用
        :param acctid: 账户名
        :return:
        dict
            dict data for mongodb
        """
        col_manually_downloaded_data_capital = self.db_trddata['manually_downloaded_rawdata_capital']
        dict_capital_findone = col_manually_downloaded_data_capital.find_one({'date': self.str_today, 'acctid': acctid})
        dict_capital = {'date': dict_capital_findone['date'], 'acctid': dict_capital_findone['acctid'], }
        list_fields_af = ['可用', '可用金额', '资金可用金']
        for field_af in list_fields_af:
            if field_af in dict_capital_findone:
                dict_capital['available_fund'] = float(dict_capital_findone[field_af])
        list_fields_mv = ['参考市值', '市值', '总市值']
        for field_mv in list_fields_mv:
            if field_mv in dict_capital_findone:
                dict_capital['sec_mv'] = float(dict_capital_findone[field_mv])
        list_fields_ttasset = ['总资产', '资产']
        for field_ttasset in list_fields_ttasset:
            if field_ttasset in dict_capital_findone:
                dict_capital['ttasset'] = float(dict_capital_findone[field_ttasset])
        return dict_capital

    def get_list_dicts_holding(self, acctid):
        col_manually_downloaded_data_holding = self.db_trddata['manually_downloaded_rawdata_holding']
        list_dicts_holding = []
        for _ in col_manually_downloaded_data_holding.find({'date': self.str_today, 'acctid': acctid}):
            list_values = [str(_value) for _value in list(_.values())]
            str_joined_values = ''.join(list_values)
            if '没有' in str_joined_values:
                continue
            dict_holding = {'date': _['date'], 'acctid': _['acctid']}
            list_fields_seccode = ['证券代码', '代码']
            for field_seccode in list_fields_seccode:
                if field_seccode in _:
                    dict_holding['sec_code'] = str(_[field_seccode]).zfill(6)
            list_fields_secname = ['证券名称']
            for field_secname in list_fields_secname:
                if field_secname in _:
                    dict_holding['sec_name'] = _[field_secname]
            list_fields_secmv = ['最新市值', '市值']
            for field_secmv in list_fields_secmv:
                if field_secmv in _:
                    dict_holding['sec_mv'] = float(_[field_secmv])
            list_fields_secvol = ['证券数量', '证券余额', '持股数量']
            for field_secvol in list_fields_secvol:
                if field_secvol in _:
                    dict_holding['sec_vol'] = int(_[field_secvol])
            list_dicts_holding.append(dict_holding)
        return list_dicts_holding

    def update_trddata_c(self):
        """
        更新cash account的两类col： 1. capital， 2. holding
        :return:
        """
        colfind_c_acctid = self.col_myacctsinfo.find({'date': self.str_today, 'accttype': 'c', 'rptmark': '1'})
        for _ in colfind_c_acctid:
            if '/' in _['fpath_holding']:
                acctid = _['acctid']
                prdcode = _['prdcode']
                accttype = _['accttype']
                colname_capital = f'{prdcode}_{accttype}_{acctid}_capital'
                dict_capital = self.get_dict_capital_for_cash_acct(acctid)
                col_c_capital = self.db_trddata[colname_capital]
                col_c_capital.delete_many({'date': self.str_today, 'acctid': acctid})
                col_c_capital.insert_one(dict_capital)
                colname_holding = f'{prdcode}_{accttype}_{acctid}_holding'
                list_dicts_holding = self.get_list_dicts_holding(acctid)
                col_c_holding = self.db_trddata[colname_holding]
                col_c_holding.delete_many({'date': self.str_today, 'acctid': acctid})
                if list_dicts_holding:
                    col_c_holding.insert_many(list_dicts_holding)
                else:
                    pass
        print('Cash account data update finished.')

    def get_dict_capital_for_margin_acct(self, acctid):
        """
        todo 需要询问是如何下载数据的
        todo 需设计自定义表单 解决margin account的问题
        核心：总资产, 总负债, 净资产
        华泰（hexin委托）可在查询收市负债中找到信息

        """

        col_manually_downloaded_data_capital = self.db_trddata['manually_downloaded_rawdata_capital']
        dict_capital_find = col_manually_downloaded_data_capital.find_one({'date': self.str_today, 'acctid': acctid})
        dict_capital = {'date': dict_capital_find['date'], 'acctid': dict_capital_find['acctid']}
        list_fields_af = ['可用', '可用金额', '资金可用金']
        for field_af in list_fields_af:
            if field_af in dict_capital_find:
                dict_capital['available_fund'] = float(dict_capital_find[field_af])
        list_fields_mv = ['证券市值', '参考市值', '市值', '总市值']
        for field_mv in list_fields_mv:
            if field_mv in dict_capital_find:
                dict_capital['sec_mv'] = float(dict_capital_find[field_mv])
        list_fields_ttasset = ['总资产', '资产']
        for field_ttasset in list_fields_ttasset:
            if field_ttasset in dict_capital_find:
                dict_capital['ttasset'] = float(dict_capital_find[field_ttasset])
        list_fields_ttliability = ['总负债', '负债']
        for field_ttliability in list_fields_ttliability:
            if field_ttliability in dict_capital_find:
                dict_capital['ttliability'] = float(dict_capital_find[field_ttliability])
        list_fields_na = ['净资产']
        for field_na in list_fields_na:
            if field_na in dict_capital_find:
                dict_capital['na'] = float(dict_capital_find[field_na])
        return dict_capital

    def update_trddata_m(self):
        """
        更新margin account的两类col：1. capital 2. holding
        :return:
        """
        colfind_m_acctid = self.col_myacctsinfo.find({'date': self.str_today, 'accttype': 'm', 'rptmark': '1'})
        for _ in colfind_m_acctid:
            if '/' in _['fpath_holding']:
                acctid = _['acctid']
                prdcode = _['prdcode']
                accttype = _['accttype']
                colname_capital = f'{prdcode}_{accttype}_{acctid}_capital'
                dict_capital = self.get_dict_capital_for_margin_acct(acctid)
                col_m_capital = self.db_trddata[colname_capital]
                col_m_capital.delete_many({'date': self.str_today, 'acctid': acctid})
                col_m_capital.insert_one(dict_capital)
                colname_holding = f'{prdcode}_{accttype}_{acctid}_holding'
                list_dicts_holding = self.get_list_dicts_holding(acctid)
                col_m_holding = self.db_trddata[colname_holding]
                col_m_holding.delete_many({'date': self.str_today, 'acctid': acctid})
                if list_dicts_holding:
                    col_m_holding.insert_many(list_dicts_holding)
                else:
                    pass
        print('Margin account data update finished.')


if __name__ == '__main__':
    a = DBTradingData()
    # a.update_manually_downloaded_data()
    # a.update_trddata_f()
    # a.update_trddata_c()
    a.update_trddata_m()












