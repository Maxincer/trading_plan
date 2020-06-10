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
123456
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

from openpyxl import load_workbook
import pandas as pd
import pymongo
from WindPy import *

# from trader import Trader


class DBTradingData:
    def __init__(self):
        self.str_today = datetime.strftime(datetime.today(), '%Y%m%d')
        w.start()
        self.str_today = '20200603'
        self.client_mongo = pymongo.MongoClient('mongodb://localhost:27017/')
        self.col_acctinfo = self.client_mongo['basicinfo']['acctinfo']
        self.db_trddata = self.client_mongo['trddata']
        self.dirpath_data_from_trdclient = 'data/trdrec_from_trdclient'
        self.fpath_datapatch_relative = 'data/data_patch.xlsx'
        self.list_active_prdcodes = ['905', '906', '907', '908', '913', '914', '917',
                                     '918', '919', '920', '922', '925', '928', '930']

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

    @staticmethod
    def get_recdict_from_two_adjacent_lines(list_datalines, i_row, encoding='utf-8'):
        """

        :param list_datalines: consists of bytes
        :param i_row: position of the columns
        :param encoding:
        :return: recdict
        """
        dict_rec = {}
        list_keys = [data.decode(encoding) for data in list_datalines[i_row].strip().split(b',')]
        if list_datalines[i_row] and list_datalines[i_row + 1]:
            list_values = [data.decode(encoding) for data in list_datalines[i_row + 1].strip().split(b',')]
            dict_rec.update(dict(zip(list_keys, list_values)))
        return dict_rec

    def read_rawdata_from_trdclient(self, fpath, str_c_h_t_mark, data_source_type, accttype):
        """
        从客户端下载数据，并进行初步清洗。为字符串格式。
        已更新券商处理格式：
            华泰: hexin, txt, cash, margin, capital, holding
            国君: 富易, csv
            海通: ehtc, xlsx, cash, capital, holding
            申宏: alphabee, txt
            建投: alphabee, txt
            中信: tdx, txt, vip, cash, capital, holding,
            民生: tdx, txt
            华福: tdx, txt

        :param fpath:
        :param accttype: c: cash, m: margin, f: future
        :param str_c_h_t_mark: ['capital', 'holding']
        :param data_source_type:
        :return: list: 由dict rec组成的list
        """
        list_ret = []
        if str_c_h_t_mark == 'capital':
            dict_rec_capital = {}
            if data_source_type in ['huat_hx', 'hait_hx'] and accttype == 'c':
                with open(fpath, 'rb') as f:
                    list_datalines = f.readlines()[0:6]
                    for dataline in list_datalines:
                        list_data = dataline.strip().split(b'\t')
                        for data in list_data:
                            list_recdata = data.strip().decode('gbk').split('：')
                            dict_rec_capital[list_recdata[0].strip()] = list_recdata[1].strip()

            elif data_source_type in ['huat_hx', 'hait_hx'] and accttype == 'm':
                with open(fpath, 'rb') as f:
                    list_datalines = f.readlines()[5:14]
                    for dataline in list_datalines:
                        list_data = dataline.strip().split(b'\t')
                        for data in list_data:
                            list_recdata = data.strip().decode('gbk').split(':')
                            dict_rec_capital[list_recdata[0].strip()] = \
                                (lambda x: x if x.strip() in ['人民币'] else list_recdata[1].strip())(list_recdata[1])

            elif data_source_type in ['gtja_fy'] and accttype in ['c', 'm']:
                with open(fpath, 'rb') as f:
                    list_datalines = f.readlines()
                    for dataline in list_datalines[0:4]:
                        list_recdata = dataline.strip().decode('gbk').split('：')
                        dict_rec_capital[list_recdata[0].strip()] = list_recdata[1].strip()
                    dict_rec_capital.update(self.get_recdict_from_two_adjacent_lines(list_datalines, 4, encoding='gbk'))

            elif data_source_type in ['hait_ehtc'] and accttype == 'c':
                df_read = pd.read_excel(fpath, skiprows=1, nrows=1)
                dict_rec_capital = df_read.to_dict('records')[0]

            elif data_source_type in ['xc_tdx', 'zx_tdx', 'ms_tdx', 'hf_tdx'] and accttype == 'c':
                with open(fpath, 'rb') as f:
                    list_datalines = f.readlines()
                    dataline = list_datalines[0][8:]
                    list_recdata = dataline.strip().decode('gbk').split()
                    for recdata in list_recdata:
                        list_recdata = recdata.split(':')
                        dict_rec_capital.update({list_recdata[0]: list_recdata[1]})

            # todo 检查tdx margin (1105)
            elif data_source_type in ['zx_tdx'] and accttype == 'm':
                pass

            elif data_source_type in ['zxjt_alphabee', 'swhy_alphabee'] and accttype in ['c', 'm']:
                fpath = fpath.replace('<YYYYMMDD>', self.str_today)
                with open(fpath, 'rb') as f:
                    list_datalines = f.readlines()
                    list_keys = list_datalines[0].decode('gbk').split()
                    list_values = list_datalines[1].decode('gbk').split()
                    dict_rec_capital.update(dict(zip(list_keys, list_values)))
            else:
                raise ValueError('Field data_source_type not exist in basic info!')
            list_ret.append(dict_rec_capital)

        elif str_c_h_t_mark == 'holding':
            if data_source_type in ['huat_hx', 'hait_hx'] and accttype == 'c':
                with open(fpath, 'rb') as f:
                    list_datalines = f.readlines()[8:]
                    list_keys = [x.decode('gbk') for x in list_datalines[0].strip().split(b'\t')]
                    i_list_keys_length = len(list_keys)
                    for dataline in list_datalines[1:]:
                        list_data = dataline.strip().split(b'\t')
                        if len(list_data) == i_list_keys_length:
                            list_values = [x.decode('gbk') for x in list_data]
                            dict_rec_holding = dict(zip(list_keys, list_values))
                            list_ret.append(dict_rec_holding)

            elif data_source_type in ['huat_hx', 'hait_hx'] and accttype == 'm':
                with open(fpath, 'rb') as f:
                    list_datalines = f.readlines()[16:]
                    list_keys = [x.decode('gbk') for x in list_datalines[0].strip().split(b'\t')]
                    i_list_keys_length = len(list_keys)
                    for dataline in list_datalines[1:]:
                        list_data = dataline.strip().split(b'\t')
                        if len(list_data) == i_list_keys_length:
                            list_values = [x.decode('gbk') for x in list_data]
                            dict_rec_holding = dict(zip(list_keys, list_values))
                            list_ret.append(dict_rec_holding)

            elif data_source_type in ['gtja_fy'] and accttype in ['c', 'm']:
                with open(fpath, 'rb') as f:
                    list_datalines = f.readlines()[6:]
                    list_keys = [x.decode('gbk') for x in list_datalines[0].strip().split(b',')]
                    i_list_keys_length = len(list_keys)
                    for dataline in list_datalines[1:]:
                        list_data = dataline.strip().split(b',')
                        if len(list_data) == i_list_keys_length:
                            list_values = [x.decode('gbk') for x in list_data]
                            dict_rec_holding = dict(zip(list_keys[2:], list_values[2:]))
                            list_ret.append(dict_rec_holding)

            elif data_source_type in ['hait_ehtc'] and accttype == 'c':
                wb_ehtc = load_workbook(fpath)
                ws = wb_ehtc.active
                i_target_row = 10
                for row in ws.rows:
                    for cell in row:
                        if cell.value == '持仓':
                            i_target_row = cell.row
                df_holding = pd.read_excel(fpath, skiprows=i_target_row)
                list_dicts_rec_holding = df_holding.to_dict('records')
                list_ret = list_dicts_rec_holding

            elif data_source_type in ['xc_tdx', 'zx_tdx', 'ms_tdx', 'hf_tdx'] and accttype == 'c':
                with open(fpath, 'rb') as f:
                    list_datalines = f.readlines()[3:]
                    list_keys = [x.decode('gbk') for x in list_datalines[0].strip().split()]
                    i_list_keys_length = len(list_keys)
                    for dataline in list_datalines[1:]:
                        list_data = dataline.strip().split()
                        if len(list_data) == i_list_keys_length:
                            list_values = [x.decode('gbk') for x in list_data]
                            dict_rec_holding = dict(zip(list_keys, list_values))
                            list_ret.append(dict_rec_holding)

        else:
            raise ValueError('Wrong str_c_h_t_mark input!')
        return list_ret

    def update_manually_downloaded_data(self):
        """
        1. 出于数据处理留痕及增强robust考虑，将原始数据按照原格式上传到mongoDB中备份
        2. 定义DataFilePath = ['fpath_capital_data'(source), 'fpath_holding_data'(source), 'fpath_trdrec_data(source)',]
        3. acctinfo数据库中DataFilePath存在文件路径即触发文件数据的上传。
        """
        col_manually_downloaded_rawdata_capital = self.db_trddata['manually_downloaded_rawdata_capital']
        col_manually_downloaded_rawdata_holding = self.db_trddata['manually_downloaded_rawdata_holding']
        for _ in self.col_acctinfo.find({'DataDate': self.str_today, 'RptMark': 1}, {'_id': 0}):
            prdcode = _['PrdCode']
            datafilepath = _['DataFilePath']
            if prdcode in self.list_active_prdcodes:
                if datafilepath:
                    list_fpath_data = _['DataFilePath'][1:-1].split(',')
                    acctidbymxz = _['AcctIDByMXZ']
                    data_source_type = _['DataSourceType']
                    accttype = _['AcctType']

                    for ch in ['capital', 'holding']:
                        if ch == 'capital':
                            fpath_relative = list_fpath_data[0]
                            col_manually_downloaded_rawdata = col_manually_downloaded_rawdata_capital
                        elif ch == 'holding':
                            fpath_relative = list_fpath_data[1]
                            col_manually_downloaded_rawdata = col_manually_downloaded_rawdata_holding
                        else:
                            raise ValueError('Value input not exist in capital and holding.')
                        fpath_absolute = os.path.join(self.dirpath_data_from_trdclient, fpath_relative)
                        list_dicts_rec = self.read_rawdata_from_trdclient(fpath_absolute, ch, data_source_type,accttype)
                        for _ in list_dicts_rec:
                            _['DataDate'] = self.str_today
                            _['AcctIDByMXZ'] = acctidbymxz

                        col_manually_downloaded_rawdata.delete_many({'DataDate': self.str_today,
                                                                     'AcctIDByMXZ': acctidbymxz})
                        if list_dicts_rec:
                            col_manually_downloaded_rawdata.insert_many(list_dicts_rec)
                        else:
                            pass



    # def update_trddata_f(self):
    #     """
    #     f"{prdcode}_{accttype}_{acctid}_{content}}
    #     # todo 可用装饰器优化
    #     """
    #     cursor_find = self.col_myacctsinfo.find({'date': self.str_today, 'accttype': 'f', 'rptmark': 1})
    #     for _ in cursor_find:
    #         prdcode = _['prdcode']
    #         accttype = _['accttype']
    #         acctid = _['acctid']
    #         colname_capital = f'{prdcode}_{accttype}_{acctid}_capital'
    #         trader = Trader(acctid)
    #         dict_res_capital = trader.query_account()
    #         if dict_res_capital['success'] == 1:
    #             dict_capital_to_be_update = dict_res_capital['list'][0]
    #             dict_capital_to_be_update['date'] = self.str_today
    #             col_f_capital = self.db_trddata[colname_capital]
    #             col_f_capital.delete_many({'date': self.str_today})
    #             col_f_capital.insert_one(dict_capital_to_be_update)
    #             print(f'Query capital data of {acctid}({accttype}) succeed.')
    #         else:
    #             print(f'Query capital data of {acctid}({accttype}) failed.')
    #
    #         colname_holding = f'{prdcode}_{accttype}_{acctid}_holding'
    #         dict_res_holding = trader.query_holding()
    #         if dict_res_holding['success'] == 1:
    #             list_dicts_holding_to_be_update = dict_res_holding['list']
    #             for dict_holding_to_be_update in list_dicts_holding_to_be_update:
    #                 dict_holding_to_be_update['date'] = self.str_today
    #                 dict_holding_to_be_update['acctid'] = acctid
    #             col_f_holding = self.db_trddata[colname_holding]
    #             col_f_holding.delete_many({'date': self.str_today})
    #             if list_dicts_holding_to_be_update:
    #                 col_f_holding.insert_many(list_dicts_holding_to_be_update)
    #             else:
    #                 pass
    #             print(f'Query holding data of {acctid}({accttype}) succeed.')
    #
    #         else:
    #             print(f'Query holding data of {acctid}({accttype}) succeed.')
    #
    #         colname_trading = f'{prdcode}_{accttype}_{acctid}_trading'
    #         dict_res_trading = trader.query_trading()
    #         if dict_res_trading['success'] == 1:
    #             list_dicts_trading_to_be_update = dict_res_trading['list']
    #             for dict_trading_to_be_update in list_dicts_trading_to_be_update:
    #                 dict_trading_to_be_update['date'] = self.str_today
    #                 dict_trading_to_be_update['acctid'] = acctid
    #             col_f_trading = self.db_trddata[colname_trading]
    #             col_f_trading.delete_many({'date': self.str_today})
    #             if list_dicts_trading_to_be_update:
    #                 col_f_trading.insert_many(list_dicts_trading_to_be_update)
    #             else:
    #                 pass
    #             print(f'Query trading data of {acctid}({accttype}) succeed.')
    #
    #         else:
    #             print(f'Query trading data of {acctid}({accttype}) succeed.')

    def get_dict_capital_for_cash_acct(self, acctid):
        """
        获取self.today指定的acctid的capital数据, 被update_trddata_c调用
        :param acctid: 账户名
        :return:
        dicts
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

    def update_manually_patchdata(self):
        """
        从data_patch中读取当日数据。
        注意，data_patch中只记录最新的当日数据
        证券市值：SecurityMarketValue: 有正负
        """
        df_datapatch_capital = pd.read_excel(self.fpath_datapatch_relative, sheet_name='capital',
                                             dtype={'AcctIDByMXZ': str, 'NetAssetValue': float, 'TotalAsset': float,
                                                    'TotalLiability': float, 'AvailableFund': float,
                                                    'SecurityMarketValue': float})
        df_datapatch_capital = df_datapatch_capital.where(df_datapatch_capital.notnull(), None)
        list_dicts_patch_capital = df_datapatch_capital.to_dict('record')
        for dict_patch_capital in list_dicts_patch_capital:
            dict_patch_capital['DataDate'] = self.str_today
        self.db_trddata['manually_patchdata_capital'].delete_many({'DataDate': self.str_today})
        if list_dicts_patch_capital:
            self.db_trddata['manually_patchdata_capital'].insert_many(list_dicts_patch_capital)

        self.db_trddata['manually_patch_rawdata_holding'].delete_many({'DataDate': self.str_today})
        df_datapatch_holding = pd.read_excel(self.fpath_datapatch_relative, sheet_name='holding',
                                             dtype={'AcctIDByMXZ': str, 'SecurityID': str, 'Symbol': str,
                                                    'LongQty': float, 'ShortQty': float, 'PostCost': float},
                                             converters={'SecurityIDSource': str.upper})
        dict_exchange_wcode = {'SSE': '.SH', 'SZSE': '.SZ', 'CFFEX': '.CFE'}
        if df_datapatch_holding.empty:
            pass
        else:
            df_datapatch_holding['DataDate'] = self.str_today
            df_datapatch_holding['WindCode_suffix'] = \
                df_datapatch_holding['SecurityIDSource'].map(dict_exchange_wcode)
            df_datapatch_holding['WindCode'] = \
                df_datapatch_holding['SecurityID'] + df_datapatch_holding['WindCode_suffix']
            list_windcodes = list(set(df_datapatch_holding['WindCode'].values))
            str_windcodes = ','.join(list_windcodes)
            wss_close = w.wss(str_windcodes, 'close', f'tradeDate={self.str_today}')
            list_closes = wss_close.Data[0]
            dict_windcodes2close = dict(zip(list_windcodes, list_closes))
            df_datapatch_holding['Close'] = df_datapatch_holding['WindCode'].map(dict_windcodes2close)
            df_datapatch_holding['SecurityMarketValue_vector'] = (df_datapatch_holding['LongQty']
                                                                  * df_datapatch_holding['Close']
                                                                  - df_datapatch_holding['ShortQty']
                                                                  * df_datapatch_holding['Close'])
            list_dicts_patch_holding = df_datapatch_holding.to_dict('record')
            self.db_trddata['manually_patch_rawdata_holding'].insert_many(list_dicts_patch_holding)
        print('Collection manually_patchdata_capital and collection manually_patchdata_holding updated.')

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
        # self.update_manually_downloaded_data()
        self.update_manually_patchdata()
        # update_trddata_f()
        # update_trddata_c()
        # update_trddata_m()
        # update_col_data_patch()


if __name__ == '__main__':
    task = DBTradingData()
    task.run()














