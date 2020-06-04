#!usr/bin/env python37
# coding:utf-8
# Author: Maxincer
# Create Datetime: 20200413T112000 +0800
# Update Datetime: 20200503T170000 +0800

"""
Update:
Apply to protocol FIX 5.0 sp2

出于开发速度及借鉴国际做法，暂将持仓数据分为 capital 与 holding 两类表

DataBase "trddata" maintenance.

Maintained DataBase:
    1. DB: trddata
        1. col: 各账户structured data
        2. col: 上传的原始数据
        3. All trading data is in the database.

Naming Convention:
    1. 代码中的命名，遵循缩写可作为形容词，与其他名称连拼的规则；
    2. 数据库中的命名，出于阅读便利考虑， 不可连拼，严格遵循蛇底式拼读法。
    3. the collection should be named as f"{prdcode}_{accttype}_{acctid}_{content}}
        1. content include:
            1. b/s_sheet
            2. holding
            3. trade
            4. transfer serial

Input:
    0. basic_info.xlsx
    1. downloaded data from trading software.
    2. manually patched data.

Process:
    循环遍历account basic info, 进行如下处理：
        1. raw data upload.
            1. read and upload downloaded data.
                1. read general format: capital + security holding
                2. read specific format: distinguished by broker and trading software.
            2. read and upload patched data.
            3. download and upload api data.

        2. raw data to structured data.
            1. structure cash account data.
            2. structure margin account data.
            3. structure future account data.

"""

from datetime import datetime
import os

import pandas as pd
import pymongo
from WindPy import w

from trader import Trader


class DBTradingData:
    def __init__(self):
        self.str_today = datetime.strftime(datetime.today(), '%Y%m%d')
        self.str_today = '20200603'
        self.client_mongo = pymongo.MongoClient('mongodb://localhost:27017/')
        self.col_myacctsinfo = self.client_mongo['basicinfo']['myacctsinfo']
        self.db_trddata = self.client_mongo['trddata']
        self.dirpath_data_from_trdclient = 'D:/data/data_from_trdclient'
        self.list_active_prdcodes = ['905', '906', '907', '908', '913', '914', '917',
                                     '918', '919', '920', '922', '925', '928', '930']
        w.start()

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

    def read_data_from_trdclient(self, fpath_capital, str_c_h_t_mark, data_source_type, accttype):
        """
        :param accttype: c: cash, m: margin, f: future
        :param fpath_capital:
        :param str_c_h_t_mark: ['capital', 'holding']
        :param data_source_type:
        :return:
        """
        if str_c_h_t_mark == 'capital':
            if data_source_type == 'huat_hx' and accttype=='c':



            else:
                raise ValueError('Wrong data_source_type input in basic info!')


        elif str_c_h_t_mark == 'holding':
            pass
        else:
            raise ValueError('Wrong str_c_h_t_mark input!')








    def update_manually_downloaded_data(self):
        """
        1. 出于数据处理留痕及增强robust考虑，将原始数据按照原格式上传到mongoDB中备份
        2. 定义DataFilePath = ['fpath_capital_data'(source), 'fpath_holding_data'(source), 'fpath_trdrec_data(source)',]
        3. acctinfo数据库中DataFilePath存在文件路径即触发文件数据的上传。
        """
        col_manually_downloaded_rawdata_capital = self.db_trddata['manually_downloaded_rawdata_capital']
        col_manually_downloaded_rawdata_holding = self.db_trddata['manually_downloaded_rawdata_holding']
        for _ in self.col_myacctsinfo.find({'date': self.str_today, 'rptmark': 1}):
            list_fpath_data = _['DataFilePath'][1:-1].split(',')
            fpath_capital_relative = list_fpath_data[0]
            fpath_holding_relative = list_fpath_data[1]
            acctid = _['AcctID']
            fpath_capital = os.path.join(self.dirpath_data_from_trdclient, fpath_capital_relative)
            fpath_holding = os.path.join(self.dirpath_data_from_trdclient, fpath_holding_relative)
            prdcode = _['PrdCode']
            data_source_type = _['DataSourceType']
            accttype = _['AcctType']

            if prdcode in self.list_active_prdcodes:
                if os.path.isfile(fpath_capital):
                    df_capital = self.read_data_from_trdclient(fpath_capital, 'capital', data_source_type, accttype)
                    df_capital, df_holding = self.process_manually_downloaded_data(fpath_capital)
                    list_dicts_capital = df_capital.to_dict('record')
                    for _ in list_dicts_capital:
                        _['date'] = self.str_today
                        _['acctid'] = acctid
                    col_manually_downloaded_rawdata_capital.delete_many({'date': self.str_today, 'acctid': acctid})
                    col_manually_downloaded_rawdata_capital.insert_many(list_dicts_capital)
                    list_dicts_holding = df_holding.to_dict('record')
                    for _ in list_dicts_holding:
                        _['date'] = self.str_today
                        _['acctid'] = acctid
                    col_manually_downloaded_rawdata_holding.delete_many({'date': self.str_today, 'acctid': acctid})
                    col_manually_downloaded_rawdata_holding.insert_many(list_dicts_holding)

                if os.path.isfile(fpath_holding):
                    df_capital, df_holding = self.process_manually_downloaded_data(fpath_holding)
                    list_dicts_capital = df_capital.to_dict('record')
                    for _ in list_dicts_capital:
                        _['date'] = self.str_today
                        _['acctid'] = acctid
                    col_manually_downloaded_rawdata_capital.delete_many({'date': self.str_today, 'acctid': acctid})
                    col_manually_downloaded_rawdata_capital.insert_many(list_dicts_capital)
                    list_dicts_holding = df_holding.to_dict('record')
                    for _ in list_dicts_holding:
                        _['date'] = self.str_today
                        _['acctid'] = acctid
                    col_manually_downloaded_rawdata_holding.delete_many({'date': self.str_today, 'acctid': acctid})
                    col_manually_downloaded_rawdata_holding.insert_many(list_dicts_holding)



    def update_trddata_f(self):
        """
        f"{prdcode}_{accttype}_{acctid}_{content}}
        # todo 可用装饰器优化
        """
        cursor_find = self.col_myacctsinfo.find({'date': self.str_today, 'accttype': 'f', 'rptmark': 1})
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
        colfind_c_acctid = self.col_myacctsinfo.find({'date': self.str_today, 'accttype': 'c', 'rptmark': 1})
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
        colfind_m_acctid = self.col_myacctsinfo.find({'date': self.str_today, 'accttype': 'm', 'rptmark': 1})
        for _ in colfind_m_acctid:
            if '/' in _['fpath_holding']:
                acctid = _['acctid']
                prdcode = _['prdcode']
                accttype = _['accttype']
                colname_capital = f'{prdcode}_{accttype}_{acctid}_capital'
                dict_capital = self.get_dict_capital_for_margin_acct(acctid)
                dict_m_capital = {
                    'date': self.str_today,
                    'acctid': acctid,
                    'ttasset': dict_capital['ttasset'],
                    'af': dict_capital['available_fund'],
                    'secmv': dict_capital['sec_mv']
                }
                if dict_capital['ttliability']:
                    dict_m_capital['ttliability'] = dict_capital['ttliability']
                else:
                    dict_m_capital['ttliability'] = 'unknown'
                if dict_capital['na']:
                    dict_m_capital['nav'] = dict_capital['na']
                else:
                    dict_m_capital['nav'] = 'unknown'
                col_m_capital = self.db_trddata[colname_capital]
                col_m_capital.delete_many({'date': self.str_today, 'acctid': acctid})
                col_m_capital.insert_one(dict_m_capital)
                colname_holding = f'{prdcode}_{accttype}_{acctid}_holding'
                list_dicts_holding = self.get_list_dicts_holding(acctid)
                col_m_holding = self.db_trddata[colname_holding]
                col_m_holding.delete_many({'date': self.str_today, 'acctid': acctid})
                if list_dicts_holding:
                    col_m_holding.insert_many(list_dicts_holding)
                else:
                    pass
        print('Margin account data update finished.')

    def get_dict_capital_from_data_patch(self, acctid):
        col_patch = self.db_trddata['manually_patch_rawdata_capital']
        dict_patch = col_patch.find_one({'date': self.str_today, 'acctid': acctid})
        return dict_patch

    def update_manually_patch_rawdata(self):
        fpath_data_patch = 'D:/data/A_trading_data/data_patch.xlsx'
        df_data_patch_capital = pd.read_excel(fpath_data_patch, sheet_name='capital', dtype={'acctid': str})
        list_dicts_patch_capital = df_data_patch_capital.to_dict('record')
        for dict_patch_capital in list_dicts_patch_capital:
            dict_patch_capital['date'] = self.str_today
        self.db_trddata['manually_patch_rawdata_capital'].delete_many({'date': self.str_today})
        if list_dicts_patch_capital:
            self.db_trddata['manually_patch_rawdata_capital'].insert_many(list_dicts_patch_capital)
        else:
            pass
        self.db_trddata['manually_patch_rawdata_holding'].delete_many({'date': self.str_today})
        df_data_patch_holding = pd.read_excel(fpath_data_patch, sheet_name='holding',
                                              dtype={'acctid': str, 'sec_code': str, 'sec_vol': float})
        dict_exchange_wcode = {'sse': '.SH', 'szse': '.SZ', 'cffex': '.CFE'}
        if df_data_patch_holding.empty:
            pass
        else:
            df_data_patch_holding['date'] = self.str_today
            df_data_patch_holding['windcode_exchange'] = \
                df_data_patch_holding['exchange'].apply(lambda x: dict_exchange_wcode[x.lower()])
            df_data_patch_holding['windcode'] = \
                df_data_patch_holding['sec_code'] + df_data_patch_holding['windcode_exchange']
            list_windcodes = list(df_data_patch_holding['windcode'].values)
            wss_close = w.wss(list_windcodes, 'close', f'tradeDate={self.str_today}')
            list_closes = wss_close.Data[0]
            df_data_patch_holding['close'] = list_closes
            df_data_patch_holding['sec_mv'] = df_data_patch_holding['sec_vol'] * df_data_patch_holding['close']
            list_dicts_patch_holding = df_data_patch_holding.to_dict('record')
            self.db_trddata['manually_patch_rawdata_holding'].insert_many(list_dicts_patch_holding)
        print('Collection manually_patch_rawdata_capital and collection manually_patch_rawdata_holding updated.')

    def get_list_dicts_holding_from_data_patch(self, acctid):
        """
        需要load行情数据， 计算市值
        :param acctid:
        :return:
        """
        col_patch = self.db_trddata['manually_patch_rawdata_holding']
        list_dicts_holding_from_data_patch = list(col_patch.find({'date': self.str_today, 'acctid': acctid}))
        return list_dicts_holding_from_data_patch

    def update_col_data_patch(self):
        """
        1. 上传A_data_patch.xlsx数据至mongo;
        2. 从mongo中读取数据，整理至产品的正式数据表中（所以此步一定要置后执行）
        col_data_patch: 数据补丁。主要补充下载数据中没有体现的重要数据。当日截面数据日更算法。
        3. A_data_patch.xlsx中的数据，sec_code带有交易所编码，方便在行情数据库中查询行情。更好的做法是添加股东代码字段，区分市场。可优化。
        """
        colfind_patch_in_basicinfo = self.col_myacctsinfo.find({'date': self.str_today, 'rptmark': 1, 'patch_mark': 1})
        for _ in colfind_patch_in_basicinfo:
            acctid = _['acctid']
            prdcode = _['prdcode']
            accttype = _['accttype']
            colname_capital = f'{prdcode}_{accttype}_{acctid}_capital'
            col_capital = self.db_trddata[colname_capital]
            dict_capital_patch = self.get_dict_capital_from_data_patch(acctid)
            if dict_capital_patch:
                del dict_capital_patch['_id']
                col_capital.update_one({'date': self.str_today, 'acctid': acctid}, {'$set': dict_capital_patch})
            else:
                pass
            colname_holding = f'{prdcode}_{accttype}_{acctid}_holding'
            col_holding = self.db_trddata[colname_holding]
            list_dicts_holding = self.get_list_dicts_holding_from_data_patch(acctid)
            col_holding.delete_many({'date': self.str_today, 'acctid': acctid, 'patch_mark': 1})
            if list_dicts_holding:
                for dict_holding in list_dicts_holding:
                    dict_holding['patch_mark'] = 1
                col_holding.insert_many(list_dicts_holding)
        print('Update patch data finished.')

    def run(self):
        self.update_manually_downloaded_data()
        # update_manually_patch_rawdata()
        # update_trddata_f()
        # update_trddata_c()
        # update_trddata_m()
        # update_col_data_patch()


if __name__ == '__main__':
    task = DBTradingData()
    task.run()














