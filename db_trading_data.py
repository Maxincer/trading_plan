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

import os

from openpyxl import load_workbook
import pandas as pd
import pymongo
from WindPy import *
from xlrd import open_workbook

from trader import Trader


class DBTradingData:
    def __init__(self):
        self.str_today = datetime.strftime(datetime.today(), '%Y%m%d')
        self.str_today = '20200624'
        w.start()
        self.df_mktdata_from_wind = self.get_close_from_wind()
        self.client_mongo = pymongo.MongoClient('mongodb://localhost:27017/')
        self.col_acctinfo = self.client_mongo['basicinfo']['acctinfo']
        self.db_trddata = self.client_mongo['trddata']
        self.dirpath_data_from_trdclient = 'data/trdrec_from_trdclient'
        self.fpath_datapatch_relative = 'data/data_patch.xlsx'
        self.dict_future2multiplier = {'IC': 200, 'IH': 300, 'IF': 300}

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
            if data_source_type in ['huat_hx', 'hait_hx', 'zhes_hx', 'tf_hx', 'db_hx', 'wk_hx'] and accttype == 'c':
                with open(fpath, 'rb') as f:
                    list_datalines = f.readlines()[0:6]
                    for dataline in list_datalines:
                        list_data = dataline.strip().split(b'\t')
                        for data in list_data:
                            list_recdata = data.strip().decode('gbk').split('：')
                            dict_rec_capital[list_recdata[0].strip()] = list_recdata[1].strip()

            elif data_source_type in ['yh_hx'] and accttype in ['c']:
                with open(fpath, 'rb') as f:
                    list_datalines = f.readlines()
                    list_keys = list_datalines[5].decode('gbk').split()
                    list_values = list_datalines[6].decode('gbk').split()
                    dict_rec_capital.update(dict(zip(list_keys, list_values)))

            elif data_source_type in ['huat_hx', 'hait_hx', 'wk_hx'] and accttype == 'm':
                with open(fpath, 'rb') as f:
                    list_datalines = f.readlines()[5:14]
                    for dataline in list_datalines:
                        if dataline.strip():
                            list_data = dataline.strip().split(b'\t')
                        else:
                            continue
                        for data in list_data:
                            list_recdata = data.strip().decode('gbk').split(':')
                            if len(list_recdata) != 2:
                                list_recdata = data.strip().decode('gbk').split('：')
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

            elif data_source_type in ['xc_tdx', 'zx_tdx', 'ms_tdx', 'hf_tdx',
                                      'zhaos_tdx', 'huat_tdx'] and accttype in ['c', 'm']:
                with open(fpath, 'rb') as f:
                    list_datalines = f.readlines()
                    dataline = list_datalines[0][8:]
                    list_recdata = dataline.strip().decode('gbk').split()
                    for recdata in list_recdata:
                        list_recdata = recdata.split(':')
                        dict_rec_capital.update({list_recdata[0]: list_recdata[1]})

            elif data_source_type in ['zxjt_alphabee', 'swhy_alphabee'] and accttype in ['c', 'm']:
                fpath = fpath.replace('<YYYYMMDD>', self.str_today)
                with open(fpath, 'rb') as f:
                    list_datalines = f.readlines()
                    list_keys = list_datalines[0].decode('gbk').split()
                    list_values = list_datalines[1].decode('gbk').split()
                    dict_rec_capital.update(dict(zip(list_keys, list_values)))

            elif data_source_type in ['swhy_alphabee_dbf2csv']:
                with open(fpath, 'rb') as f:
                    list_datalines = f.readlines()
                    list_keys = list_datalines[0].decode('gbk').split(',')
                    list_values = list_datalines[1].decode('gbk').split(',')
                    dict_rec_capital.update(dict(zip(list_keys, list_values)))

            elif data_source_type in ['patch']:
                pass

            else:
                raise ValueError('Field data_source_type not exist in basic info!')
            list_ret.append(dict_rec_capital)

        elif str_c_h_t_mark == 'holding':
            if (data_source_type in ['huat_hx', 'hait_hx', 'zhes_hx',
                                     'wk_hx', 'db_hx', 'tf_hx', 'yh_hx']) and (accttype in ['c', 'm']):
                with open(fpath, 'rb') as f:
                    list_datalines = f.readlines()
                    start_index_holding = None
                    for index, dataline in enumerate(list_datalines):
                        if '证券代码' in dataline.decode('gbk'):
                            start_index_holding = index
                    list_keys = [x.decode('gbk') for x in list_datalines[start_index_holding].strip().split(b'\t')]
                    i_list_keys_length = len(list_keys)

                    for dataline in list_datalines[start_index_holding + 1:]:
                        list_data = dataline.strip().split(b'\t')
                        if len(list_data) == i_list_keys_length:
                            list_values = [x.decode('gbk') for x in list_data]
                            dict_rec_holding = dict(zip(list_keys, list_values))
                            list_ret.append(dict_rec_holding)

            elif data_source_type in ['xc_tdx', 'zx_tdx', 'ms_tdx', 'hf_tdx', 'huat_tdx'] and accttype in ['c', 'm']:
                with open(fpath, 'rb') as f:
                    list_datalines = f.readlines()
                    start_index_holding = None
                    for index, dataline in enumerate(list_datalines):
                        if '证券代码' in dataline.decode('gbk'):
                            start_index_holding = index
                    list_keys = [x.decode('gbk') for x in list_datalines[start_index_holding].strip().split(b'\t')]
                    i_list_keys_length = len(list_keys)

                    for dataline in list_datalines[start_index_holding + 1:]:
                        list_data = dataline.strip().split()
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
                    str_values = ','.join(list_values)
                    if '合计' in str_values:
                        continue
                    dict_rec_holding = dict(zip(list_keys, list_values))
                    # 以下为不规则补充, todo
                    if accttype == 'm':
                        if '证券代码' in dict_rec_holding:
                            secid = dict_rec_holding['证券代码']
                            if secid[0] in ['0', '1', '3']:
                                dict_rec_holding['交易市场'] = '深A'
                            else:
                                dict_rec_holding['交易市场'] = '沪A'
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

            elif data_source_type in ['zxjt_alphabee', 'swhy_alphabee'] and accttype in ['c', 'm']:
                fpath = fpath.replace('<YYYYMMDD>', self.str_today)
                with open(fpath, 'rb') as f:
                    list_datalines = f.readlines()
                    list_keys = list_datalines[0].decode('gbk').split()
                    for dataline in list_datalines[1:]:
                        list_values = dataline.decode('gbk').split()
                        if len(list_values) == len(list_keys):
                            dict_rec_holding = dict(zip(list_keys, list_values))
                            list_ret.append(dict_rec_holding)

            elif data_source_type in ['swhy_alphabee_dbf2csv'] and accttype in ['c', 'm']:
                with open(fpath, 'rb') as f:
                    list_datalines = f.readlines()
                    list_keys = list_datalines[3].decode('gbk').split(',')
                    for dataline in list_datalines[4:]:
                        list_values = dataline.decode('gbk').split(',')
                        if len(list_values) == len(list_keys):
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
        col_manually_rawdata_capital = self.db_trddata['manually_rawdata_capital']
        col_manually_rawdata_holding = self.db_trddata['manually_rawdata_holding']
        for _ in self.col_acctinfo.find({'DataDate': self.str_today, 'RptMark': 1}, {'_id': 0}):
            datafilepath = _['DataFilePath']
            if datafilepath:
                list_fpath_data = _['DataFilePath'][1:-1].split(',')
                acctidbymxz = _['AcctIDByMXZ']
                data_source_type = _['DataSourceType']
                accttype = _['AcctType']

                for ch in ['capital', 'holding']:
                    if ch == 'capital':
                        fpath_relative = list_fpath_data[0]
                        col_manually_rawdata = col_manually_rawdata_capital
                    elif ch == 'holding':
                        fpath_relative = list_fpath_data[1]
                        col_manually_rawdata = col_manually_rawdata_holding
                    else:
                        raise ValueError('Value input not exist in capital and holding.')

                    col_manually_rawdata.delete_many({'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz})
                    fpath_absolute = os.path.join(self.dirpath_data_from_trdclient, fpath_relative)
                    list_dicts_rec = self.read_rawdata_from_trdclient(fpath_absolute, ch,
                                                                      data_source_type, accttype)
                    for _ in list_dicts_rec:
                        _['DataDate'] = self.str_today
                        _['AcctIDByMXZ'] = acctidbymxz
                        _['AcctType'] = accttype
                    if list_dicts_rec:
                        col_manually_rawdata.insert_many(list_dicts_rec)
        print('Update raw data finished.')

    def update_trddata_f(self):
        cursor_find = list(self.col_acctinfo.find({'DataDate': self.str_today, 'AcctType': 'f', 'RptMark': 1}))
        for _ in cursor_find:
            list_future_data_capital = []
            list_future_data_holding = []
            prdcode = _['PrdCode']
            acctidbymxz = _['AcctIDByMXZ']
            acctidbybroker = _['AcctIDByBroker']
            trader = Trader(acctidbybroker)
            dict_res_capital = trader.query_account()
            if dict_res_capital['success']:
                dict_capital_to_be_update = dict_res_capital['list'][0]
                dict_capital_to_be_update['DataDate'] = self.str_today
                dict_capital_to_be_update['AcctIDByMXZ'] = acctidbymxz
                dict_capital_to_be_update['PrdCode'] = prdcode
                list_future_data_capital.append(dict_capital_to_be_update)
                self.db_trddata['future_api_capital'].delete_many({'DataDate': self.str_today,
                                                                   'AcctIDByMXZ': acctidbymxz})
                if list_future_data_capital:
                    self.db_trddata['future_api_capital'].insert_many(list_future_data_capital)

            dict_res_holding = trader.query_holding()
            if dict_res_holding['success']:
                list_dicts_holding_to_be_update = dict_res_holding['list']
                for dict_holding_to_be_update in list_dicts_holding_to_be_update:
                    dict_holding_to_be_update['DataDate'] = self.str_today
                    dict_holding_to_be_update['AcctIDByMXZ'] = acctidbymxz
                    dict_holding_to_be_update['PrdCode'] = prdcode
                    list_future_data_holding.append(dict_holding_to_be_update)

                self.db_trddata['future_api_holding'].delete_many({'DataDate': self.str_today,
                                                                   'AcctIDByMXZ': acctidbymxz})
                if list_future_data_holding:
                    self.db_trddata['future_api_holding'].insert_many(list_future_data_holding)

    def update_manually_patchdata(self):
        """
        从data_patch中读取当日数据。
        注意，data_patch中只记录最新的当日数据
        注意，此步骤处理了原数据，将加工后的数据上传至数据库
        证券市值净值：SecurityMarketValue_vec: 是矢量，有正负
        """
        # 上传holding data
        dict_windcode2mktdata_from_wind = self.df_mktdata_from_wind.set_index('WindCode').to_dict()
        df_datapatch_holding = pd.read_excel(self.fpath_datapatch_relative, sheet_name='holding',
                                             dtype={'AcctIDByMXZ': str, 'SecurityID': str, 'Symbol': str,
                                                    'LongQty': float, 'ShortQty': float, 'PosCost_vec': float,
                                                    'LiabilityType': str,
                                                    'LiabilityQty': float, 'LiabilityAmt': float, 'InterestRate': float,
                                                    'DatedDate': str, 'UnderlyingSecurityID': str,
                                                    'UnderlyingSecurityIDSource': str, 'UnderlyingSymbol': str,
                                                    'UnderlyingQty': float, 'UnderlyingStartValue_vec': float,
                                                    'Note': str},
                                             converters={'SecurityIDSource': str.upper})
        df_datapatch_holding = df_datapatch_holding.where(df_datapatch_holding.notnull(), None)
        list_dicts_datapatch_holding = df_datapatch_holding.to_dict('records')
        dict_exchange_wcode = {'SSE': '.SH', 'SZSE': '.SZ', 'CFFEX': '.CFE'}
        list_dicts_datapatch_holding_to_be_inserted = []
        for dict_datapatch_holding in list_dicts_datapatch_holding:
            acctidbymxz = dict_datapatch_holding['AcctIDByMXZ']
            secid = dict_datapatch_holding['SecurityID']
            secidsrc = dict_datapatch_holding['SecurityIDSource']
            symbol = dict_datapatch_holding['Symbol']
            secid_secidsrc = secid + '.' + secidsrc
            if secidsrc == 'ITN':
                secid_windcode = None
            else:
                secid_windcode = secid + dict_exchange_wcode[secidsrc]
            longqty = dict_datapatch_holding['LongQty']
            shortqty = dict_datapatch_holding['ShortQty']
            sectype = self.get_mingshi_sectype_from_code(secid_secidsrc)
            poscost_vec = dict_datapatch_holding['PosCost_vec']
            liability_sec_qty = dict_datapatch_holding['LiabilityQty']
            liability_margin_amt = dict_datapatch_holding['LiabilityAmt']
            liability_type = dict_datapatch_holding['LiabilityType']
            interest_rate = dict_datapatch_holding['InterestRate']
            dateddate = dict_datapatch_holding['DatedDate']
            liability = 0
            note = dict_datapatch_holding['Note']

            underlying_secid = None
            underlying_secidsrc = None
            underlying_symbol = None
            underlying_sectype = None
            underlying_qty = None
            underlying_close = None
            underlying_amt = None
            underlying_start_value_vec = None
            otc_contract_unit_mv = None

            if sectype in ['SWAP']:
                underlying_secid = dict_datapatch_holding['UnderlyingSecurityID']
                underlying_secidsrc = dict_datapatch_holding['UnderlyingSecurityIDSource']
                underlying_sec_windcode = underlying_secid + dict_exchange_wcode[underlying_secidsrc]
                underlying_symbol = dict_windcode2mktdata_from_wind['Symbol'][underlying_sec_windcode]
                underlying_sectype = self.get_mingshi_sectype_from_code(underlying_sec_windcode)
                underlying_close = dict_windcode2mktdata_from_wind['Close'][underlying_sec_windcode]
                underlying_qty = dict_datapatch_holding['UnderlyingQty']
                underlying_amt = underlying_close * underlying_qty
                underlying_start_value_vec = dict_datapatch_holding['UnderlyingStartValue_vec']
                otc_contract_unit_mv = underlying_amt - underlying_start_value_vec
                close = otc_contract_unit_mv
            elif sectype in ['CE', 'CS', 'ETF']:
                close = dict_windcode2mktdata_from_wind['Close'][secid_windcode]
                if sectype in ['CS', 'ETF']:
                    int_accumulated_interested_days = w.tdayscount(dateddate, self.str_today, "Days=Alldays").Data[0][0]
                    if liability_type == 'capital':
                        interest_1day = liability_margin_amt * interest_rate / 365
                        liability_accrual_interest = int_accumulated_interested_days * interest_1day
                        liability = liability_margin_amt + liability_accrual_interest
                    elif liability_type == 'security':  # todo 不标准的表述, 需改进; 出于开发成本考虑，此处简化融券应付利息算法
                        liability_sec_amt = liability_sec_qty * close
                        interest_1day = liability_sec_amt * interest_rate / 365
                        liability = liability_sec_amt + int_accumulated_interested_days * interest_1day
                    else:
                        raise ValueError('Unknown liability type when compute liability')
            else:
                raise ValueError('Unknown sectype when update manually data.')

            longamt = close * longqty
            shortamt = close * shortqty
            netamt = longamt - shortamt

            dict_datapatch_holding_2b_inserted = {
                'DataDate': self.str_today,
                'AcctIDByMXZ': acctidbymxz,
                'SecurityID': secid,
                'SecurityIDSource': secidsrc,
                'Symbol': symbol,
                'SecurityType': sectype,
                'LongQty': longqty,
                'ShortQty': shortqty,
                'LongAmt': longamt,
                'ShortAmt': shortamt,
                'NetAmt': netamt,
                'PosCost_vec': poscost_vec,
                'LiabilityType': liability_type,
                'LiabilityQty': liability_sec_qty,
                'LiabilityAmt': liability_margin_amt,
                'InterestRate': interest_rate,
                'DatedDate': dateddate,
                'Liability': liability,
                'UnderlyingSecurityID': underlying_secid,
                'UnderlyingSecurityIDSource': underlying_secidsrc,
                'UnderlyingSymbol': underlying_symbol,
                'UnderlyingSecurityType': underlying_sectype,
                'UnderlyingQty': underlying_qty,
                'UnderlyingClose': underlying_close,
                'UnderlyingAmt': underlying_amt,
                'UnderlyingStartValue_vec': underlying_start_value_vec,
                'OTCContractUnitMarketValue': otc_contract_unit_mv,
                'Note': note
            }
            list_dicts_datapatch_holding_to_be_inserted.append(dict_datapatch_holding_2b_inserted)
        self.db_trddata['manually_patchdata_holding'].delete_many({'DataDate': self.str_today})
        self.db_trddata['manually_patchdata_holding'].insert_many(list_dicts_datapatch_holding_to_be_inserted)

        # 上传capital data
        df_datapatch_capital = pd.read_excel(self.fpath_datapatch_relative, sheet_name='capital',
                                             dtype={'AcctIDByMXZ': str, 'Cash': float, 'CashEquivalent': float,
                                                    'ETFLongAmt': float, 'CompositeLongAmt': float, 'OTCAmt': float,
                                                    'TotalAsset': float, 'ETFShortAmt': float,
                                                    'CompositeSHortAmt': float, 'Liability': float,
                                                    'ApproximateNetAsset': float})
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
        list_wcodes_query_patch = ['510500.SH', '000905.SH', '000300.SH', '000016.SH']
        list_str_wcodes_astock += list_wcodes_query_patch
        str_wcodes_astock = ','.join(list_str_wcodes_astock)
        wss_astock = w.wss(str_wcodes_astock, 'sec_name,close', f'tradeDate={self.str_today};priceAdj=U;cycle=D')
        df_mktdata_from_wind = pd.DataFrame(
            wss_astock.Data, index=wss_astock.Fields, columns=wss_astock.Codes
        ).T.reset_index().rename(columns={'index': 'WindCode', 'SEC_NAME': 'Symbol', 'CLOSE': 'Close'})
        list_dicts_mktpatch = [
            {'WindCode': '204001.SH', 'Symbol': 'GC001', 'Close': 100},
            {'WindCode': '511990.SH', 'Symbol': '华宝添益', 'Close': 100}
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
        :param str_code: SecurityID.SecurityIDSource
            1. SecuritySource:
                1. SSE: 上交所
                2. SZSE: 深交所
                3. ITN: internal id
        :return:
            1. CE, Cash Equivalent, 货基，质押式国债逆回购
            2. CS, Common Stock, 普通股
            3. ETF, ETF, 注意：货币类ETF归类为CE，而不是ETF
            4. SWAP, swap
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
            elif secid in ['510500', '000905']:
                return 'ETF'
            else:
                return 'IrrelevantItem'

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
                return 'IrrelevantItem'

        elif exchange == 'ITN':
            sectype = secid.split('_')[0]
            return sectype

        else:
            raise ValueError(f'{str_code} has unknown exchange or digit number is not 6.')

    def update_formatted_holding_and_balance_sheet_and_exposure_analysis(self):
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
        循环嵌套：
            对每个账户遍历
                1. 求单账户风险暴露： [c,m,f,o]
                2. 求单账户持仓状况和资产负债表
                3. 求单账户现金管理
        todo：
            1. 新股的市值的处理（目前: 找出并删除），需要观察经纪商是如何处理的
        """

        dict_wcode2close = self.df_mktdata_from_wind.set_index('WindCode').to_dict()['Close']

        list_dicts_acctinfo = list(self.col_acctinfo.find({'DataDate': self.str_today, 'RptMark': 1}, {'_id': 0}))
        for dict_acctinfo in list_dicts_acctinfo:
            prdcode = dict_acctinfo['PrdCode']
            acctidbymxz = dict_acctinfo['AcctIDByMXZ']
            accttype = dict_acctinfo['AcctType']
            if accttype in ['c', 'm', 'o']:
                patchmark = dict_acctinfo['PatchMark']
                # 1.整理holding
                # 1.1 rawdata
                list_dicts_holding = list(self.db_trddata['manually_rawdata_holding'].find(
                    {'AcctIDByMXZ': acctidbymxz, 'DataDate': self.str_today}, {'_id': 0}
                ))
                list_fields_secid = ['证券代码']
                list_fields_symbol = ['证券名称']
                list_fields_shareholder_acctid = ['股东帐户', '股东账号', '股东代码']
                list_fields_exchange = ['交易市场', '交易板块', '板块']
                list_fields_positionqty = ['股票余额', '拥股数量', '证券余额', '库存数量', '证券数量', '参考持股']
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

                    for field_exchange in list_fields_exchange:
                        if field_exchange in dict_holding:
                            exchange = dict_holding[field_exchange]
                            dict_exchange2secidsrc = {'深A': 'SZSE', '沪A': 'SSE',
                                                      '深Ａ': 'SZSE', '沪Ａ': 'SSE',
                                                      '上海Ａ': 'SSE', '深圳Ａ': 'SZSE',
                                                      '00': 'SZSE', '10': 'SSE',
                                                      '上海Ａ股': 'SSE', '深圳Ａ股': 'SZSE',
                                                      '上海A股': 'SSE', '深圳A股': 'SZSE',
                                                      }
                            secidsrc = dict_exchange2secidsrc[exchange]

                    for field_symbol in list_fields_symbol:
                        if field_symbol in dict_holding:
                            symbol = str(dict_holding[field_symbol])

                    for field_positionqty in list_fields_positionqty:
                        if field_positionqty in dict_holding:
                            longqty = float(dict_holding[field_positionqty])

                    windcode_suffix = {'SZSE': '.SZ', 'SSE': '.SH'}[secidsrc]
                    windcode = secid + windcode_suffix
                    sectype = self.get_mingshi_sectype_from_code(windcode)
                    if sectype == 'IrrelevantItem':
                        continue
                    close = dict_wcode2close[windcode]
                    longamt = close * longqty
                    shortamt = close * shortqty
                    netamt = longamt - shortamt

                    dict_holding_fmtted = {
                        'DataDate': self.str_today,
                        'AcctIDByMXZ': acctidbymxz,
                        'SecurityID': secid,
                        'SecurityType': sectype,
                        'Symbol': symbol,
                        'SecurityIDSource': secidsrc,
                        'LongQty': longqty,
                        'ShortQty': shortqty,
                        'LongAmt': longamt,
                        'ShortAmt': shortamt,
                        'NetAmt': netamt,
                        'PosCost_vec': None,
                        'OTCContractUnitMarketValue': None,
                        'LiabilityType': None,
                        'Liability': 0,
                        'LiabilityQty': None,
                        'LiabilityAmt': None,
                        'InterestRate': None,
                        'DatedDate': None,
                        'UnderlyingSecurityID': None,
                        'UnderlyingSecurityIDSource': None,
                        'UnderlyingSecurityType': None,
                        'UnderlyingSymbol': None,
                        'UnderlyingQty': None,
                        'UnderlyingAmt': 0,
                        'UnderlyingClose': None,
                        'UnderlyingStartValue_vec': None,
                        'Note': None
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
                underlying_amt = 0
                if patchmark:
                    list_dicts_holding_patchdata = list(self.db_trddata['manually_patchdata_holding'].find(
                        {'AcctIDByMXZ': acctidbymxz, 'DataDate': self.str_today}
                    ))
                    # todo 需改进自定义标的持仓价格和持仓金额的情况（eg.场外非标, 下层基金）
                    for dict_holding_patchdata in list_dicts_holding_patchdata:
                        underlying_sectype = dict_holding_patchdata['UnderlyingSecurityType']
                        if underlying_sectype in ['CS', 'ETF', 'INDEX']:
                            underlying_amt = dict_holding_patchdata['UnderlyingAmt']
                        list_dicts_holding_patchdata_fmtted.append(dict_holding_patchdata)
                list_dicts_holding_fmtted_patched = list_dicts_holding_fmtted + list_dicts_holding_patchdata_fmtted
                self.db_trddata['formatted_holding'].delete_many({'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz})
                if list_dicts_holding_fmtted_patched:
                    self.db_trddata['formatted_holding'].insert_many(list_dicts_holding_fmtted_patched)
                underlying_exposure_long = 0
                underlying_exposure_short = 0
                if underlying_amt >= 0:
                    underlying_exposure_long = underlying_amt
                else:
                    underlying_exposure_short = -underlying_amt

                # 2.整理b/s: 出于稳健性考量，股票市值由持仓数据计算得出: holding data + raw data + patch data
                # 用现金代替可用，重点计算
                # Cash, CashEquivalent, CompositeLongAmt, Asset, ShortAmt, Liability, ApproximateNetAsset
                # patch data采用余额覆盖模式。（holding data采用增量添加模式）

                # 2.1 holding data
                stock_longamt = 0
                etf_longamt = 0
                ce_longamt = 0
                swap_longamt = 0
                stock_shortamt = 0
                etf_shortamt = 0
                df_holding_fmtted_patched = pd.DataFrame(list_dicts_holding_fmtted_patched)
                if df_holding_fmtted_patched.empty:
                    df_holding_fmtted_patched = pd.DataFrame(
                        columns=['DataDate', 'AcctIDByMXZ', 'SecurityID', 'SecurityType', 'Symbol', 'SecurityIDSource',
                                 'Symbol', 'SecurityIDSource',
                                 'LongQty', 'ShortQty', 'LongAmt', 'ShortAmt', 'NetAmt', 'PosCost_vec',
                                 'OTCContractUnitMarketValue', 'LiabilityType', 'Liability', 'LiabilityQty', 'LiabilityAmt',
                                 'InterestRate', 'DatedDate', 'UnderlyingSecurityID', 'UnderlyingSecurityIDSource',
                                 'UnderlyingSecurityType', 'UnderlyingSymbol', 'UnderlyingQty', 'UnderlyingAmt',
                                 'UnderlyingClose', 'UnderlyingStartValue_vec', 'Note'])
                else:
                    df_holding_amt_sum_by_sectype = df_holding_fmtted_patched.groupby(by='SecurityType').sum()
                    dict_amt2dict_sectype2amt = df_holding_amt_sum_by_sectype.to_dict()
                    if 'LongAmt' in dict_amt2dict_sectype2amt:
                        dict_sectype2longamt = dict_amt2dict_sectype2amt['LongAmt']
                        if 'CS' in dict_sectype2longamt:
                            stock_longamt = dict_sectype2longamt['CS']
                        if 'ETF' in dict_sectype2longamt:
                            etf_longamt = dict_sectype2longamt['ETF']
                        if 'CE' in dict_sectype2longamt:
                            ce_longamt = dict_sectype2longamt['CE']
                        if 'SWAP' in dict_sectype2longamt:
                            swap_longamt = dict_sectype2longamt['SWAP']
                    if 'ShortAmt' in dict_amt2dict_sectype2amt:
                        dict_sectype2shortamt = dict_amt2dict_sectype2amt['ShortAmt']
                        if 'CS' in dict_sectype2shortamt:
                            stock_shortamt = dict_sectype2shortamt['CS']
                        if 'ETF' in dict_sectype2shortamt:
                            etf_shortamt = dict_sectype2shortamt['ETF']

                # 2.2 求cash
                dict_capital = self.db_trddata['manually_rawdata_capital'].find_one(
                    {'AcctIDByMXZ': acctidbymxz, 'DataDate': self.str_today}, {'_id': 0}
                )
                if dict_capital is None:
                    dict_capital = {}
                list_fields_af = ['可用', '可用金额', '资金可用金', '可用余额']
                list_fields_ttasset = ['总资产', '资产', '总 资 产', '账户总资产', '担保资产']
                flt_ttasset = None
                flt_cash = None

                # 分两种情况： 1. cash acct: 至少要有cash 2. margin acct: 至少要有ttasset
                if accttype in ['c']:
                    for field_af in list_fields_af:
                        if field_af in dict_capital:
                            flt_cash = float(dict_capital[field_af])
                        else:
                            if patchmark:
                                dict_patchdata_capital = (self.db_trddata['manually_patchdata_capital'].find_one(
                                    {'AcctIDByMXZ': acctidbymxz, 'DataDate': self.str_today}, {'_id': 0}
                                ))
                                if dict_patchdata_capital:
                                    if 'Cash' in dict_patchdata_capital:
                                        flt_cash = dict_patchdata_capital['Cash']

                elif accttype == 'm':
                    for field_ttasset in list_fields_ttasset:
                        if field_ttasset in dict_capital:
                            flt_ttasset = float(dict_capital[field_ttasset])
                    if patchmark:
                        dict_patchdata_capital = (self.db_trddata['manually_patchdata_capital'].find_one(
                            {'AcctIDByMXZ': acctidbymxz, 'DataDate': self.str_today}, {'_id': 0}
                        ))
                        if dict_patchdata_capital:
                            if 'TotalAsset' in dict_patchdata_capital:
                                flt_ttasset = dict_patchdata_capital['TotalAsset']
                    flt_cash = flt_ttasset - stock_longamt - etf_longamt - ce_longamt

                elif accttype == 'o':
                    dict_patchdata_capital = (self.db_trddata['manually_patchdata_capital'].find_one(
                        {'AcctIDByMXZ': acctidbymxz, 'DataDate': self.str_today}, {'_id': 0}
                    ))
                    if dict_patchdata_capital:
                        if 'Cash' in dict_patchdata_capital:
                            flt_cash = dict_patchdata_capital['Cash']

                else:
                    raise ValueError('Unknown accttype')

                # 2.3 cash equivalent: ce_longamt
                flt_ce = ce_longamt

                # 2.4 etf
                flt_etf_long_amt = etf_longamt

                # 2.4 CompositeLongAmt
                flt_composite_long_amt = stock_longamt

                # 2.5 SwapAmt
                flt_swap_amt = swap_longamt

                # 2.5 Asset
                flt_ttasset = flt_cash + flt_ce + flt_etf_long_amt + flt_composite_long_amt + flt_swap_amt

                # 2.6 etf_shortamt
                flt_etf_short_amt = etf_shortamt

                # 2.7 stock_shortamt
                flt_composite_short_amt = stock_shortamt

                # 2.8 liability
                flt_liability = float(df_holding_fmtted_patched['Liability'].sum())

                # 2.9 net_asset
                flt_approximate_na = flt_ttasset - flt_liability

                # 2.10 读取patchdata对rawdata进行修正: 余额覆盖模式
                if patchmark:
                    dict_patchdata_capital = (self.db_trddata['manually_patchdata_capital'].find_one(
                        {'AcctIDByMXZ': acctidbymxz, 'DataDate': self.str_today}, {'_id': 0}
                    ))
                    if dict_patchdata_capital:
                        if 'Cash' in dict_patchdata_capital:
                            if dict_patchdata_capital['Cash']:
                                flt_cash = float(dict_patchdata_capital['Cash'])
                        if 'CashEquivalent' in dict_patchdata_capital:
                            if dict_patchdata_capital['CashEquivalent']:
                                flt_ce = float(dict_patchdata_capital['CashEquivalent'])
                        if 'ETFLongAmt' in dict_patchdata_capital:
                            if dict_patchdata_capital['ETFLongAmt']:
                                flt_etf_long_amt = float(dict_patchdata_capital['ETFLongAmt'])
                        if 'CompositeLongAmt' in dict_patchdata_capital:
                            if dict_patchdata_capital['CompositeLongAmt']:
                                flt_composite_long_amt = float(dict_patchdata_capital['CompositeLongAmt'])
                        if 'TotalAsset' in dict_patchdata_capital:
                            if dict_patchdata_capital['TotalAsset']:
                                flt_ttasset = float(dict_patchdata_capital['TotalAsset'])
                        if 'ETFShortAmt' in dict_patchdata_capital:
                            if dict_patchdata_capital['ETFShortAmt']:
                                flt_etf_short_amt = float(dict_patchdata_capital['ETFShortAmt'])
                        if 'CompositeShortAmt' in dict_patchdata_capital:
                            if dict_patchdata_capital['CompositeShortAmt']:
                                flt_composite_short_amt = float(dict_patchdata_capital['CompositeShortAmt'])
                        if 'Liability' in dict_patchdata_capital:
                            if dict_patchdata_capital['Liability']:
                                flt_liability = float(dict_patchdata_capital['Liability'])
                        if 'ApproximateNetAmt' in dict_patchdata_capital:
                            if dict_patchdata_capital['ApproximateNetAmt']:
                                flt_approximate_na = float(dict_patchdata_capital['ApproximateNetAmt'])
                dict_bs = {
                    'DataDate': self.str_today,
                    'PrdCode': prdcode,
                    'AcctIDByMXZ': acctidbymxz,
                    'AcctType': accttype,
                    'Cash': flt_cash,
                    'CashEquivalent': flt_ce,
                    'ETFLongAmt': flt_etf_long_amt,
                    'CompositeLongAmt': flt_composite_long_amt,
                    'SwapLongAmt': flt_swap_amt,
                    'TotalAsset': flt_ttasset,
                    'ETFShortAmt': flt_etf_short_amt,
                    'CompositeShortAmt': flt_composite_short_amt,
                    'Liability': flt_liability,
                    'ApproximateNetAsset': flt_approximate_na,
                }
                self.db_trddata['b/s_by_acct'].delete_many({'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz})
                list_dict_bs = [dict_bs]
                if dict_bs:
                    self.db_trddata['b/s_by_acct'].insert_many(list_dict_bs)

                exposure_long_amt = flt_etf_long_amt + flt_composite_long_amt + underlying_exposure_long
                exposure_short_amt = flt_etf_short_amt + flt_composite_short_amt + underlying_exposure_short
                exposure_net_amt = exposure_long_amt - exposure_short_amt

            elif accttype in ['f']:
                # 按账户整理 exposure数据
                list_dicts_holding_future = list(self.db_trddata['future_api_holding']
                                                 .find({'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz}))
                list_dicts_holding_future_exposure_draft = []
                for dict_holding_future in list_dicts_holding_future:
                    secid = dict_holding_future['instrument_id']
                    secid_first_part = secid[:-4]
                    dict_future2spot_windcode = {'IC': '000905.SH', 'IH': '000016.SH', 'IF': '000300.SH'}
                    windcode = dict_future2spot_windcode[secid_first_part]
                    close = dict_wcode2close[windcode]
                    qty = dict_holding_future['position']
                    direction = dict_holding_future['direction']
                    future_long_qty = 0
                    future_short_qty = 0
                    future_long_amt = 0
                    future_short_amt = 0

                    if direction == 'long':
                        future_long_qty = qty
                        future_long_amt = close * future_long_qty * self.dict_future2multiplier[secid_first_part]
                    elif direction == 'short':
                        future_short_qty = qty
                        future_short_amt = future_short_qty * close * self.dict_future2multiplier[secid_first_part]
                    else:
                        raise ValueError('Unknown direction in future respond.')
                    future_net_qty = future_long_qty - future_short_qty
                    future_net_amt = future_long_amt - future_short_amt
                    dict_holding_future_exposure_draft = {
                        'SecurityID': secid,
                        'direction': direction,
                        'position': qty,
                        'LongQty': future_long_qty,
                        'ShortQty': future_short_qty,
                        'NetQty': future_net_qty,
                        'LongAmt': future_long_amt,
                        'ShortAmt': future_short_amt,
                        'NetAmt': future_net_amt,
                    }
                    list_dicts_holding_future_exposure_draft.append(dict_holding_future_exposure_draft)
                if list_dicts_holding_future_exposure_draft:
                    df_holding_future_exposure_draft = pd.DataFrame(list_dicts_holding_future_exposure_draft)
                    exposure_long_amt = float(df_holding_future_exposure_draft['LongAmt'].sum())
                    exposure_short_amt = float(df_holding_future_exposure_draft['ShortAmt'].sum())
                    exposure_net_amt = exposure_long_amt - exposure_short_amt
                else:
                    exposure_long_amt = 0
                    exposure_short_amt = 0
                    exposure_net_amt = 0
                dict_capital_future = (self.db_trddata['future_api_capital']
                                       .find_one({'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz}))
                flt_approximate_na = (dict_capital_future['pre_balance']
                                      + dict_capital_future['deposit']
                                      - dict_capital_future['withdraw']
                                      + dict_capital_future['close_profit']
                                      + dict_capital_future['position_profit']
                                      - dict_capital_future['commission'])
                dict_future_bs = {
                    'DataDate': self.str_today,
                    'AcctIDByMXZ': acctidbymxz,
                    'AcctType': 'f',
                    'ApproximateNetAsset': flt_approximate_na,
                    'Cash': flt_approximate_na,
                    'CashEquivalent': 0,
                    'CompositeLongAmt': 0,
                    'CompositeShortAmt': 0,
                    'ETFLongAmt': 0,
                    'ETFShortAmt': 0,
                    'Liability': 0,
                    'PrdCode': prdcode,
                    'SwapLongAmt': 0,
                    'TotalAsset': flt_approximate_na,
                }
                self.db_trddata['b/s_by_acct'].delete_many({'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz})
                if dict_future_bs:
                    self.db_trddata['b/s_by_acct'].insert_one(dict_future_bs)

            else:
                raise ValueError('Unknown account type in basic account info.')

            dict_exposure_analysis = {
                'DataDate': self.str_today,
                'AcctIDByMXZ': acctidbymxz,
                'PrdCode': prdcode,
                'LongExposure': exposure_long_amt,
                'ShortExposure': exposure_short_amt,
                'NetExposure': exposure_net_amt,
                'ApproximateNetAsset': flt_approximate_na,
            }
            self.db_trddata['exposure_analysis_by_acct'].delete_many({'DataDate': self.str_today,
                                                                      'AcctIDByMXZ': acctidbymxz})
            if dict_exposure_analysis:
                self.db_trddata['exposure_analysis_by_acct'].insert_one(dict_exposure_analysis)

        print('Update capital and holding formatted by internal style finished.')

    def update_bs_by_prdcode_and_exposure_analysis_by_prdcode(self):
        list_dicts_bs_by_acct = list(self.db_trddata['b/s_by_acct'].find({'DataDate': self.str_today}, {'_id': 0}))
        df_bs_by_acct = pd.DataFrame(list_dicts_bs_by_acct)
        df_bs_by_prdcode = df_bs_by_acct.groupby(by='PrdCode').sum().reset_index()
        df_bs_by_prdcode['DataDate'] = self.str_today
        list_dicts_bs_by_prdcode = df_bs_by_prdcode.to_dict('records')
        self.db_trddata['b/s_by_prdcode'].delete_many({'DataDate': self.str_today})
        if list_dicts_bs_by_prdcode:
            self.db_trddata['b/s_by_prdcode'].insert_many(list_dicts_bs_by_prdcode)

        list_dicts_exposure_analysis_by_acct = list(self.db_trddata['exposure_analysis_by_acct']
                                                    .find({'DataDate': self.str_today}, {'_id': 0}))
        df_exposure_analysis_by_acct = pd.DataFrame(list_dicts_exposure_analysis_by_acct)
        df_exposure_analysis_by_prdcode = df_exposure_analysis_by_acct.groupby(by='PrdCode').sum().reset_index()
        df_exposure_analysis_by_prdcode['DataDate'] = self.str_today
        df_exposure_analysis_by_prdcode['NetExposure(%)'] = (df_exposure_analysis_by_prdcode['NetExposure']
                                                             / df_exposure_analysis_by_prdcode['ApproximateNetAsset'])
        list_dicts_exposure_analysis_by_prdcode = df_exposure_analysis_by_prdcode.to_dict('records')
        self.db_trddata['exposure_analysis_by_prdcode'].delete_many({'DataDate': self.str_today})
        if list_dicts_exposure_analysis_by_prdcode:
            self.db_trddata['exposure_analysis_by_prdcode'].insert_many(list_dicts_exposure_analysis_by_prdcode)
        print('Update b/s by prdcode and exposure analysis by prdcode finished')

    def run(self):
        # self.update_trddata_f()
        self.update_rawdata()
        self.update_manually_patchdata()
        self.update_formatted_holding_and_balance_sheet_and_exposure_analysis()
        self.update_bs_by_prdcode_and_exposure_analysis_by_prdcode()


if __name__ == '__main__':
    task = DBTradingData()
    task.run()














