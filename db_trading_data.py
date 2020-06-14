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

Note:
    1. AcctType: cash, margin, future
    2. ColType: capital, holding


"""

from datetime import datetime
import os

from openpyxl import load_workbook
import pandas as pd
import pymongo
from WindPy import *

from xlrd import open_workbook

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
                wb = open_workbook(fpath, encoding_override='gbk')
                ws = wb.sheet_by_index(0)
                list_keys = ws.row_values(5)
                list_values = ws.row_values(6)
                dict_rec_capital.update(dict(zip(list_keys, list_values)))

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
                wb = open_workbook(fpath, encoding_override='gbk')
                ws = wb.sheet_by_index(0)
                list_keys = ws.row_values(8)
                for i in range(9, ws.nrows):
                    list_values = ws.row_values(i)
                    dict_rec_holding = dict(zip(list_keys, list_values))
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

    def update_rawdata(self):
        """
        1. 出于数据处理留痕及增强robust考虑，将原始数据按照原格式上传到mongoDB中备份
        2. 定义DataFilePath = ['fpath_capital_data'(source), 'fpath_holding_data'(source), 'fpath_trdrec_data(source)',]
        3. acctinfo数据库中DataFilePath存在文件路径即触发文件数据的上传。
        """
        col_manually_downloaded_rawdata_capital = self.db_trddata['manually_rawdata_capital']
        col_manually_downloaded_rawdata_holding = self.db_trddata['manually_rawdata_holding']
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
        colfind_c_acctid = self.col_acctinfo.find({'date': self.str_today, 'accttype': 'c', 'rptmark': 1})
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
        注意，此步骤处理了原数据，将加工后的数据上传至数据库
        证券市值净值：SecurityMarketValue_vec: 是矢量，有正负
        """
        # 上传holding data
        df_datapatch_holding = pd.read_excel(self.fpath_datapatch_relative, sheet_name='holding',
                                             dtype={'AcctIDByMXZ': str, 'SecurityID': str, 'Symbol': str,
                                                    'LongQty': float, 'ShortQty': float, 'PostCost': float,
                                                    'SecurityType': str},
                                             converters={'SecurityIDSource': str.upper})
        df_datapatch_holding = df_datapatch_holding.where(df_datapatch_holding.notnull(), None)
        dict_exchange_wcode = {'SSE': '.SH', 'SZSE': '.SZ', 'CFFEX': '.CFE'}
        self.db_trddata['manually_patchdata_holding'].delete_many({'DataDate': self.str_today})
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
            df_datapatch_holding['LongAmt'] = df_datapatch_holding['Close'] * df_datapatch_holding['LongQty']
            df_datapatch_holding['ShortAmt'] = df_datapatch_holding['Close'] * df_datapatch_holding['ShortQty']
            list_dicts_patch_holding = df_datapatch_holding.to_dict('record')
            self.db_trddata['manually_patchdata_holding'].insert_many(list_dicts_patch_holding)

        # 上传capital data
        df_datapatch_capital = pd.read_excel(self.fpath_datapatch_relative, sheet_name='capital',
                                             dtype={'AcctIDByMXZ': str, 'NetAssetValue': float, 'TotalAsset': float,
                                                    'TotalLiability': float, 'Cash': float,
                                                    'SecurityMarketValue': float})
        df_datapatch_capital['DataDate'] = self.str_today
        df_datapatch_capital = df_datapatch_capital.where(df_datapatch_capital.notnull(), None)
        list_dicts_patch_capital = df_datapatch_capital.to_dict('record')

        self.db_trddata['manually_patchdata_capital'].delete_many({'DataDate': self.str_today})
        if list_dicts_patch_capital:
            self.db_trddata['manually_patchdata_capital'].insert_many(list_dicts_patch_capital)

        print('Collection manually_patchdata_capital and collection manually_patchdata_holding updated.')

    def get_close_from_wind(self):
        """
        停牌股票为前收价
        """
        wset_astock = w.wset("sectorconstituent", f"date={self.str_today};sectorid=a001010100000000")
        list_str_wcodes_astock = wset_astock.Data[1]
        list_str_wcodes_astock.append('510500.SH')  # 添加需要查询wind行情数据的标的
        str_wcodes_astock = ','.join(list_str_wcodes_astock)
        wss_astock = w.wss(str_wcodes_astock, 'sec_name,close', f'tradeDate={self.str_today};priceAdj=U;cycle=D')
        df_mktdata_from_wind = pd.DataFrame(
            wss_astock.Data, index=wss_astock.Fields, columns=wss_astock.Codes
        ).T.reset_index().rename(columns={'index': 'WindCode', 'SEC_NAME': 'Symbol', 'CLOSE': 'Close'})
        list_dicts_mktpatch = [
            {'WindCode': '204001.SH', 'Symbol': 'GC001', 'Close': 100},
            {'WindCode': '510500.SH', 'Symbol': '中证500ETF', 'Close': 100}
        ]
        df_mktdata_from_wind = df_mktdata_from_wind.append(list_dicts_mktpatch)
        return df_mktdata_from_wind

    @staticmethod
    def get_official_sectype_from_code(str_code):
        """
        未使用的函数，当作留底参考
        输入windcode， 返回该标的类型
        参考：
            1.上海证券交易所证券代码分配指南
            2.深圳证券交易所数据接口规范ver 4.72_201505
        """
        list_split_wcode = str_code.split('.')
        secid = list_split_wcode[0]
        exchange = list_split_wcode[1]
        if exchange in ['SH', 'SSE'] and len(secid) == 6:
            if secid[0] == '0':
                return '指数、国债'
            elif secid[0] == '1':
                return '债券'
            elif secid[0] == '2':
                return '债券回购'
            elif secid[0] == '3':
                return '优先股'
            elif secid[0] == '5':
                dict_map = {'500': '契约型封闭式基金', '501': '上市开放式基金', '502': '上市开放式基金',
                            '505': '创新型封闭式证券投资基金', '510': '交易型开放式指数证券投资基金',
                            '511': '债券交易型开放式指数基金、交易型货币市场基金', '512': '交易型开放式指数证券投资基金',
                            '513': '交易型开放式指数证券投资基金', '515': '交易型开放式指数证券投资基金',
                            '518': '商品交易型开放式证券投资基金', '519': '开放式基金申赎', '521': '开放式基金跨市场转托管',
                            '522': '开放式基金跨市场转托管', '523': '开放式基金分红', '524': '开放式基金基金转换',
                            '550': '基金', '580': '权证', '582': '权证行权'}
                return dict_map[secid[:3]]
            elif secid[:3] in ['600', '601', '603', '688']:
                return 'A股'
            elif secid[:3] == '689':
                return '存托凭证'
            elif secid[0] == '7':
                return '非交易业务'
            elif secid[0] == '8':
                return '标准券、备用'
            elif secid[0] == '9':
                return 'B股'
        elif exchange in ['SZ', 'SZSE'] and len(secid) == 6:
            dict_map = {
                '000': '主板A股',
                '001': '主板A股',
                '002': '中小企业板股票',
                '003': '中小企业板股票',
                '004': '中小企业板股票',
                '030': '主板A股及中小企业板股票认购权证',
                '031': '主板A股及中小企业板股票认购权证',
                '032': '主板A股及中小企业板股票认购权证',
                '036': '创业板股权激励计划涉及的员工认股权',
                '037': '员工认股权',
                '038': '员工认股权',
                '039': '员工认股权',
                '070': '主板A股增发,主板可转换公司债券申购',
                '071': '主板A股增发,主板可转换公司债券申购',
                '072': '中小企业板股票增发,中小企业板可转换公司债券申购',
                '073': '中小企业板股票增发,中小企业板可转换公司债券申购',
                '074': '中小企业板股票增发,中小企业板可转换公司债券申购',
                '080': '主板A股配股优先权,主板可转换公司债券的优先权认购',
                '081': '主板A股配股优先权,主板可转换公司债券的优先权认购',
                '082': '中小企业板配股优先权,中小企业板可转换公司债券的优先权认购',
                '083': '中小企业板配股优先权,中小企业板可转换公司债券的优先权认购',
                '084': '中小企业板配股优先权,中小企业板可转换公司债券的优先权认购',
                '115': '可分离交易的可转换公司债',
                '120': '可转换公司债券',
                '121': '可转换公司债券',
                '122': '可转换公司债券',
                '123': '可转换公司债券',
                '124': '可转换公司债券',
                '125': '可转换公司债券',
                '126': '可转换公司债券',
                '127': '可转换公司债券',
                '128': '可转换公司债券',
                '129': '可转换公司债券',
                '131': '债券回购',
                '140': '优先股',
                '150': '分级基金子基金',
                '151': '分级基金子基金',
                '159': 'ETF',
                '160': '开放式基金',
                '161': '开放式基金',
                '162': '开放式基金',
                '163': '开放式基金',
                '164': '开放式基金',
                '165': '开放式基金',
                '166': '开放式基金',
                '167': '开放式基金',
                '168': '开放式基金',
                '169': '开放式基金',
                '184': '封闭式证券投资基金',
                '300': '创业板股票',
                '301': '创业板股票',
                '302': '创业板股票',
                '303': '创业板股票',
                '304': '创业板股票',
                '305': '创业板股票',
                '306': '创业板股票',
                '307': '创业板股票',
                '308': '创业板股票',
                '309': '创业板股票',
                '370': '创业板股票增发,创业板可转换公司债券申购',
                '371': '创业板股票增发,创业板可转换公司债券申购',
                '372': '创业板股票增发,创业板可转换公司债券申购',
                '373': '创业板股票增发,创业板可转换公司债券申购',
                '374': '创业板股票增发,创业板可转换公司债券申购',
                '375': '创业板股票增发,创业板可转换公司债券申购',
                '376': '创业板股票增发,创业板可转换公司债券申购',
                '377': '创业板股票增发,创业板可转换公司债券申购',
                '378': '创业板股票增发,创业板可转换公司债券申购',
                '379': '创业板股票增发,创业板可转换公司债券申购',
                '399': '指数'
            }
            return dict_map[secid[:3]]
        else:
            raise ValueError(f'Cannot get security type from code input: {str_code}')

    @staticmethod
    def get_mingshi_sectype_from_code(str_code):
        """
        实际使用的函数
        :param str_code:
        :return:
            1. CE, Cash Equivalent, 货基，质押式国债逆回购
            2. CS, Common Stock, 普通股
        """

        list_split_wcode = str_code.split('.')
        secid = list_split_wcode[0]
        exchange = list_split_wcode[1]
        if exchange in ['SH', 'SSE'] and len(secid) == 6:
            if secid in ['511990', '511830', '511880', '511850', '511660', '511810', '511690']:
                return 'CE'
            elif secid in ['204001']:
                return 'CE'
            elif secid[:3] in ['600', '601', '603', '688']:
                return 'CS'
            elif secid in ['510500']:
                return '500ETF'
            else:
                raise ValueError(f'Cannot infer the security type of {str_code}.')

        elif exchange in ['SZ', 'SZSE'] and len(secid) == 6:
            if secid[:3] in ['000', '001', '002', '003', '004', '300', '301', '302', '303', '304', '305', '306', '307',
                             '308', '309']:
                return 'CS'
            elif secid[:3] in ['115', '120', '121', '122', '123', '124', '125', '126', '127', '128', '129']:
                return '可转债'
            elif secid[:3] in ['131']:
                return 'CE'
            elif secid in ['159001', '159005', '159003']:
                return 'CE'
            else:
                raise ValueError(f'Cannot get security type from code input: {str_code}')

        else:
            raise ValueError(f'{str_code} has unknown exchange or digit number is not 6.')

    def update_capital_and_holding_formatted_by_internal_style(self):
        """
        从原始数据表中读取数据，转换为内部格式并入库，以AcctIDByMXZ作为表名
        需要找到字段名称的映射
        操作层上，以实体账户为单位进行上传， 对于单个账户：
            1. 传入rawdata，并format
            2. 根据acctinfo中的patchmark判定是否需要patch
            3. 从数据库中读取patchdata
            4. 整理patchdata并对formatted data进行修正
            3. 整合并格式化

        内部格式数据库字段说明：
            1. col_capital:
                1. AvailableFund: 可用资金
                2. SecurityMarketValue: 证券市值
                3. TotalAsset: 总资产
                4. TotalLiability: 总负债
                5. NetAsset: 净资产  (计算得出)

            2. col_holding:
                0. DataDate
                1. AcctIDByMXZ
                1. SecurityID
                2. SecurityIDSource
                3. SecurityType
                4. Close
                5. LongQty
                6. ShortQty
                7. LongAmt
                8. ShortAmt
        """
        df_mktdata_from_wind = self.get_close_from_wind()
        dict_wcode2close = df_mktdata_from_wind.set_index('WindCode').to_dict()['Close']

        list_dicts_acctinfo = list(self.col_acctinfo.find({'DataDate': self.str_today, 'RptMark': 1}, {'_id': 0}))
        for dict_acctinfo in list_dicts_acctinfo:
            prdcode = dict_acctinfo['PrdCode']
            acctidbymxz = dict_acctinfo['AcctIDByMXZ']
            accttype = dict_acctinfo['AcctType']
            patchmark = dict_acctinfo['PatchMark']

            # 1.整理holding
            # 1.1 rawdata
            list_dicts_holding = list(self.db_trddata['manually_rawdata_holding'].find(
                {'AcctIDByMXZ': acctidbymxz, 'DataDate': self.str_today}, {'_id': 0}
            ))
            list_fields_secid = ['证券代码']
            list_fields_symbol = ['证券名称']
            list_fields_shareholder_acctid = ['股东帐户', '股东账号']
            list_fields_positionqty = ['股票余额', '拥股数量', '证券余额']
            list_dicts_holding_fmtted = []
            for dict_holding in list_dicts_holding:
                secid = None
                secidsrc = None
                symbol = None
                longqty = 0
                shortqty = 0
                for field_secid in list_fields_secid:
                    if field_secid in dict_holding:
                        secid = str(dict_holding[field_secid])

                for field_shareholder_acctid in list_fields_shareholder_acctid:
                    if field_shareholder_acctid in dict_holding:
                        shareholder_acctid = dict_holding[field_shareholder_acctid]
                        if shareholder_acctid[0].isalpha():
                            secidsrc = 'SSE'
                        if shareholder_acctid[0].isdigit():
                            secidsrc = 'SZSE'

                for field_symbol in list_fields_symbol:
                    if field_symbol in dict_holding:
                        symbol = str(dict_holding[field_symbol])

                for field_positionqty in list_fields_positionqty:
                    if field_positionqty in dict_holding:
                        longqty = float(dict_holding[field_positionqty])

                dict_holding_fmtted = {
                    'DataDate': self.str_today,
                    'AcctIDByMXZ': acctidbymxz,
                    'SecurityID': secid,
                    'Symbol': symbol,
                    'SecurityIDSource': secidsrc,
                    'LongQty': longqty,
                    'ShortQty': shortqty,
                }
                list_dicts_holding_fmtted.append(dict_holding_fmtted)

            # 1.2 patchdata
            # patchdata 逻辑： 是增量补充，而不是余额覆盖
            #   1. 检验是否有patchmark，有则进入patch算法，无则跳过。
            #   2. 格式化patch数据
            #   3. 将 patch data添加至holding中
            #   3. 检查capital中各字段是否为NoneType，是则使用由holding_patchdata中推算出来的值，否则使用当前值（capital）。
            #   4. 将rawdata 与 patchdata 相加，得到patched data。

            list_dicts_holding_patchdata_fmtted = []
            if patchmark:
                list_dicts_holding_patchdata = list(self.db_trddata['manually_patchdata_holding'].find(
                    {'AcctIDByMXZ': acctidbymxz, 'DataDate': self.str_today}
                ))
                # todo 需改进自定义标的持仓价格和持仓金额的情况（eg.场外非标, 下层基金）
                for dict_holding_patchdata in list_dicts_holding_patchdata:
                    secid = dict_holding_patchdata['SecurityID']
                    secidsrc = dict_holding_patchdata['SecurityIDSource']
                    symbol = None
                    if 'Symbol' in dict_holding_patchdata:
                        symbol = dict_holding_patchdata
                    longqty = 0
                    if 'LongQty' in dict_holding_patchdata:
                        longqty = dict_holding_patchdata['LongQty']
                    shortqty = 0
                    if 'ShortQty' in dict_holding_patchdata:
                        shortqty = dict_holding_patchdata['ShortQty']
                    note = None
                    if 'Note' in dict_holding_patchdata:
                        note = str(dict_holding_patchdata['Note'])
                    dict_holding_patchdata_fmtted = {
                        'DataDate': self.str_today,
                        'AcctIDByMXZ': acctidbymxz,
                        'SecurityID': secid,
                        'Symbol': symbol,
                        'SecurityIDSource': secidsrc,
                        'LongQty': longqty,
                        'ShortQty': shortqty,
                        'Note': note
                    }
                    list_dicts_holding_patchdata_fmtted.append(dict_holding_patchdata_fmtted)
            list_dicts_holding_fmtted_patched = list_dicts_holding + list_dicts_holding_patchdata_fmtted
            df_holding_fmtted_patched = pd.DataFrame(list_dicts_holding_fmtted_patched)
            df_holding_fmtted_patched['WindCode_suffix'] = (df_holding_fmtted_patched['SecurityIDSource']
                                                            .map({'SZSE': '.SZ', 'SSE': '.SH'}))
            df_holding_fmtted_patched['WindCode'] = (df_holding_fmtted_patched['SecurityID']
                                                     + df_holding_fmtted_patched['WindCode_suffix'])
            df_holding_fmtted_patched['SecurityType'] = (df_holding_fmtted_patched['WindCode']
                                                         .apply(self.get_mingshi_sectype_from_code))
            df_holding_fmtted_patched['Close'] = df_holding_fmtted_patched['WindCode'].map(dict_wcode2close)
            df_holding_fmtted_patched['LongAmt'] = (df_holding_fmtted_patched['LongQty']
                                                    * df_holding_fmtted_patched['Close'])
            df_holding_fmtted_patched['ShortAmt'] = (df_holding_fmtted_patched['ShortAmt']
                                                     * df_holding_fmtted_patched['Close'])
            df_holding_fmtted_patched['NetAmt'] = (df_holding_fmtted_patched['LongAmt']
                                                   - df_holding_fmtted_patched['ShortAmt'])
            list_dicts_holding_fmtted_patched = df_holding_fmtted_patched.to_dict('records')
            self.db_trddata['formatted_holding'].delete_many({'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz})
            self.db_trddata['formatted_holding'].insert_many(list_dicts_holding_fmtted_patched)

            # 1.整理capital: 出于稳健性考量，股票市值由持仓数据计算得出
            # 1.1 raw data, holding data
            # 1.2 patch data
            df_holding_sectype_netamt = df_holding_fmtted_patched.loc[:, ['SecurityType', 'NetAmt']].copy()
            df_holding_amt_sum_by_sectype = df_holding_sectype_netamt.groupby(by='SecurityType').sum()
            dict_longamt2dict_sectype2amt = df_holding_amt_sum_by_sectype.to_dict()

            stock_amt = 0
            etf500_amt = 0
            ce_amt = 0
            if 'NetAmt' in dict_longamt2dict_sectype2amt:
                dict_sectype2amt = dict_longamt2dict_sectype2amt['NetAmt']
                if 'CS' in dict_sectype2amt:
                    stock_amt = dict_sectype2amt['CS']
                if '500ETF' in dict_sectype2amt:
                    etf500_amt = dict_sectype2amt['500ETF']
                if 'CE' in dict_sectype2amt:
                    ce_amt = dict_sectype2amt['CE']

                stock_amt_patch = 0
                etf500_amt_patch = 0
                ce_amt_patch = 0










                if not df_holding_patchdata.empty:

                    df_holding_patchdata_fmtted =
                    df_holding_patchdata_sum_by_sectype = df_holding_patchdata.groupby('SecurityType').sum()
                    dict_sectype2amt_patch = df_holding_patchdata_sum_by_sectype['SecurityMarketValue_vector']
                    if 'CS' in dict_sectype2amt_patch:
                        stock_amt_patch = dict_sectype2amt_patch['CS']
                    if '500ETF' in dict_sectype2amt_patch:
                        etf500_amt_patch = dict_sectype2amt_patch['500ETF']
                    if 'CE' in dict_sectype2amt_patch:
                        ce_amt_patch = dict_sectype2amt_patch['CE']




            stock_amt_patched = stock_amt + stock_amt_patch
            etf500_amt_patched = etf500_amt + etf500_amt_patch
            ce_amt_patched = ce_amt + ce_amt_patch

            # 2.整理capital
            # 2.1 rawdata
            # 2.2 patchdata


            list_dicts_capital = self.db_trddata['manually_downloaded_rawdata_capital'].find(
                {'AcctIDByMXZ': acctidbymxz, 'DataDate': self.str_today}, {'_id': 0}
            )

            list_dicts_capital_fmtted = []
            list_fields_af = ['可用', '可用金额', '资金可用金', '可用余额']
            list_fields_secmv = ['证券市值', '参考市值', '市值', '总市值', '股票市值', ]
            list_fields_ttasset = ['总资产', '资产', '总 资 产', '账户总资产']
            list_fields_ttliability = ['总负债', '负债', '合约负债总额']
            list_fields_na = ['净资产']
            flt_available_fund = None
            flt_secmv = None
            flt_ttasset = None
            if accttype == 'c':
                flt_ttliability = 0
            else:
                flt_ttliability = None
            if accttype == 'c':
                flt_net_asset = flt_ttasset
            else:
                flt_net_asset = None

            for dict_capital in list_dicts_capital:
                for field_af in list_fields_af:
                    if field_af in dict_capital:
                        flt_available_fund = float(dict_capital[field_af])
                for field_secmv in list_fields_secmv:
                    if field_secmv in dict_capital:
                        flt_secmv = float(dict_capital[field_secmv])
                for field_ttasset in list_fields_ttasset:
                    if field_ttasset in dict_capital:
                        flt_ttasset = float(dict_capital[field_ttasset])
                for field_ttliability in list_fields_ttliability:
                    if field_ttliability in dict_capital:
                        flt_ttliability = float(dict_capital[field_ttliability])
                for field_na in list_fields_na:
                    if field_na in dict_capital:
                        flt_net_asset = float(dict_capital[field_na])
                    else:
                        flt_net_asset = flt_ttasset - flt_ttliability

                dict_capital_fmtted = {
                    'PrdCode': prdcode,
                    'AcctIDByMXZ': acctidbymxz,
                    'DataDate': self.str_today,
                    'AvailableFund': flt_available_fund,
                    'SecurityMarketValue': flt_secmv,
                    'TotalAsset': flt_ttasset,
                    'TotalLiability': flt_ttliability,
                    'NetAsset': flt_net_asset,
                }
            # 1.2 读取patchdata对rawdata进行修正
            if patchmark:
                list_dicts_patchdata_capital = list(self.db_trddata['manually_patchdata_capital'].find(
                    {'AcctIDByMXZ': acctidbymxz, 'DataDate': self.str_today}, {'_id': 0}
                ))
                df_patchdata_holding = pd.DataFrame(self.db_trddata['manually_patchdata_holding'].find(
                    {'AcctIDByMXZ': acctidbymxz, 'DataDate': self.str_today}, {'_id': 0}
                ))
                df_patchdata_holding_sum_by_acctidbymxz = df_patchdata_holding.groupby(
                    by=['AcctIDByMXZ', 'SecurityType']).sum()
                dict_capital_field2dict_acctidbymxz_and_sectype2data = df_patchdata_holding_sum_by_acctidbymxz.to_dict()

                for dict_patchdata_capital in list_dicts_patchdata_capital:
                    acctidbymxz = dict_patchdata_capital['AcctIDByMXZ']
                    if dict_patchdata_capital['Cash'] is None:
                        raise ValueError(f'{acctidbymxz} has no Cash data!')
                    else:
                        cash = dict_patchdata_capital['Cash']
                    if dict_patchdata_capital['CashEquivalent'] is None:
                        acctidbymxz_and_sectype = (acctidbymxz, 'CE')  # cash equivalent
                        cash_equivalent = \
                            dict_capital_field2dict_acctidbymxz_and_sectype2data['LongAmt'][acctidbymxz_and_sectype]
                    else:
                        cash_equivalent = dict_patchdata_capital['CashEquivalent']
                    if dict_patchdata_capital['LongAmt'] is None:
                        acctidbymxz_and_sectype = (acctidbymxz, 'CS')  # common stock
                        longamt = dict_capital_field2dict_acctidbymxz_and_sectype2data['LongAmt'][
                            acctidbymxz_and_sectype]
                    else:
                        longamt = dict_patchdata_capital['LongAmt']
                    if dict_patchdata_capital['TotalLiability'] is None:
                        acctidbymxz_and_sectype = (acctidbymxz, 'ETF')
                        ttliability = dict_capital_field2dict_acctidbymxz_and_sectype2data['ShortAmt'][
                            acctidbymxz_and_sectype]
                    else:
                        ttliability = dict_patchdata_capital['TotalLiability']
                    if dict_patchdata_capital['TotalAsset'] is None:
                        ttasset = cash + cash_equivalent + longamt
                    else:
                        ttasset = dict_patchdata_capital['TotalAsset']
                    if dict_patchdata_capital['NetAsset'] is None:
                        netasset = ttasset - ttliability
                    else:
                        netasset = dict_patchdata_capital['NetAsset']

                    dict_patchdata_capital.update({
                        'NetAsset': netasset,
                        'TotalAsset': ttasset,
                        'TotalLiability': ttliability,
                        'Cash': cash,
                        'CashEquivalent': cash_equivalent,
                        'LongAmt': longamt
                    })


            # 2. 证券账户计算
            # 2.1 交易客户端下载数据计算
            # 2.2 patch data数据处理
            # 3. 插入数据库
            self.db_trddata['capital_data_formatted_by_internal_style'].delete_many(
                {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz}
            )
            if list_dicts_capital_fmtted:
                self.db_trddata['capital_data_formatted_by_internal_style'].insert_many(list_dicts_capital_fmtted)

            self.db_trddata['holding_data_formatted_by_internal_style'].delete_many(
                {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz}
            )
            # if list_dicts_holding_fmtted:
            #     self.db_trddata['holding_data_formatted_by_internal_style'].insert_many(list_dicts_capital_fmtted)

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
        colfind_patch_in_basicinfo = self.col_acctinfo.find({'date': self.str_today, 'rptmark': 1, 'patch_mark': 1})
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
        # self.update_rawdata()
        # self.update_manually_patchdata()
        self.update_capital_and_holding_formatted_by_internal_style()
        # update_trddata_f()
        # update_trddata_c()
        # update_trddata_m()
        # update_col_data_patch()


if __name__ == '__main__':
    task = DBTradingData()
    task.run()














