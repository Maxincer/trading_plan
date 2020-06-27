#!usr/bin/env python37
# coding:utf-8
# Author: Maxincer
# Create Datetime: 20200626T112000 +0800
# Update Datetime: 20200626T170000 +0800

"""
思路：
    1. 将每个账户抽象为类
    2. 将每个产品抽象为类
"""
from datetime import datetime

from math import ceil
import pandas as pd
import pymongo
from WindPy import w


class GlobalVariable:
    def __init__(self):
        self.str_today = datetime.today().strftime('%Y%m%d')
        self.str_today = '20200624'
        self.list_items_2b_adjusted = []
        self.dict_index_future_windcode2close = {}
        self.mongodb_local = pymongo.MongoClient('mongodb://localhost:27017/')
        self.db_basicinfo = self.mongodb_local['basicinfo']
        self.db_trddata = self.mongodb_local['trddata']
        self.col_acctinfo = self.db_basicinfo['acctinfo']
        self.col_bs_by_prdcode = self.db_trddata['b/s_by_prdcode']
        self.col_exposure_analysis_by_prdcode = self.db_trddata['exposure_analysis_by_prdcode']
        self.col_bs_by_acctidbymxz = self.db_trddata['b/s_by_acctidbymxz']
        iter_dicts_acctinfo_rpt = self.col_acctinfo.find({'DataDate': self.str_today, 'RptMark': 1})
        set_prdcodes = set()
        for dict_acctinfo in iter_dicts_acctinfo_rpt:
            prdcode = dict_acctinfo['PrdCode']
            set_prdcodes.add(prdcode)
        self.list_prdcodes = list(set_prdcodes)
        self.list_prdcodes.sort()
        self.dict_index_future2multiplier = {'IC': 200, 'IF': 300, 'IH': 300}

        w.start()
        set_ic_windcode = set(w.wset("sectorconstituent", f"date={self.str_today};sectorid=1000014872000000").Data[1])
        set_if_windcode = set(w.wset("sectorconstituent", f"date={self.str_today};sectorid=a599010102000000").Data[1])
        set_ih_windcode = set(w.wset("sectorconstituent", f"date={self.str_today};sectorid=1000014871000000").Data[1])
        set_index_future_windcodes = set_ic_windcode | set_if_windcode | set_ih_windcode
        str_query_close = ','.join(set_index_future_windcodes)
        wss_close = w.wss(str_query_close, "close", f"tradeDate={self.str_today};priceAdj=U;cycle=D")
        list_codes = wss_close.Codes
        list_data = wss_close.Data[0]
        self.dict_index_future_windcode2close = dict(zip(list_codes, list_data))


class Product:
    def __init__(self, gv, prdcode):
        # todo 注意区分属性：产品的/子账户的
        self.gv = gv
        self.str_today = self.gv.str_today
        self.prdcode = prdcode
        self.iter_col_acctinfo_find = (self.gv.col_acctinfo
                                       .find({'PrdCode': self.prdcode, 'RptMark': 1, 'DataDate': self.str_today}))
        dict_bs_by_prdcode = self.gv.col_bs_by_prdcode.find_one({'PrdCode': self.prdcode, 'DataDate': self.str_today})
        dict_exposure_analysis_by_prdcode = (self.gv.col_exposure_analysis_by_prdcode
                                             .find_one({'PrdCode': self.prdcode, 'DataDate': self.str_today}))
        self.prd_long_exposure = dict_exposure_analysis_by_prdcode['LongExposure']
        self.prd_short_exposure = dict_exposure_analysis_by_prdcode['ShortExposure']
        self.prd_net_exposure = dict_exposure_analysis_by_prdcode['NetExposure']
        self.prd_approximate_na = dict_bs_by_prdcode['ApproximateNetAsset']
        self.prd_ttasset = dict_bs_by_prdcode['TotalAsset']

    def check_exception(self):
        for acctinfo in self.iter_col_acctinfo_find:
            acctidbymxz = acctinfo['AcctIDByMXZ']
            acct = Account(self.gv, acctidbymxz)
            if acct.accttype == 'f':
                acct.check_margin_in_f_acct()


class Account(Product):
    def __init__(self, gv, acctidbymxz):
        self.acctidbymxz = acctidbymxz
        self.prdcode = self.acctidbymxz.split('_')[0]
        super().__init__(gv, self.prdcode)
        self.dict_acctinfo = self.gv.col_acctinfo.find_one({'AcctIDByMXZ': acctidbymxz, 'RptMark': 1,
                                                            'DataDate': self.str_today})
        self.accttype = self.dict_acctinfo['AcctType']
        self.dict_bs_by_acctidbymxz = self.gv.col_bs_by_acctidbymxz.find_one({'AcctIDByMXZ': self.acctidbymxz,
                                                                              'DataDate': self.str_today})
        self.acct_cash = self.dict_bs_by_acctidbymxz['Cash']
        self.acct_ce = self.dict_bs_by_acctidbymxz['CashEquivalent']
        self.acct_composite_long_amt = self.dict_bs_by_acctidbymxz['CompositeLongAmt']
        self.acct_approximate_na = self.dict_bs_by_acctidbymxz['ApproximateNetAsset']

    def check_margin_in_f_acct(self, margin_rate_in_perfect_shape=0.2):
        # todo 假设持仓均为股指
        # 参考： 中金所 “跨品种” 单向大边保证金制度，上期所，单向大边保证金制度
        # 资料来源：上海期货交易所结算细则
        # 同一客户在同一会员处的同品种期货合约双向持仓（期货合约进入最后交易日前第五个交易日闭市后除外）
        # 对IC、IH、IF跨品种双向持仓，按照交易保证金单边较大者收取交易保证金
        iter_dicts_future_api_holding = self.gv.db_trddata['future_api_holding'].find({'DataDate': self.str_today,
                                                                                       'AcctIDByMXZ': self.acctidbymxz})
        list_dicts_future_api_holding = list(iter_dicts_future_api_holding)
        margin_required_in_perfect_shape = 0
        if list_dicts_future_api_holding:
            for dict_future_api_holding in iter_dicts_future_api_holding:
                instrument_id = dict_future_api_holding['instrument_id']
                instrument_id_first_2 = instrument_id[:2]
                if instrument_id_first_2 not in ['IC', 'IF', 'IH']:
                    item_2b_adjusted = f'Contract that is not a Index Future Found in {self.acctidbymxz}: ' \
                                       f'{instrument_id_first_2}'
                    self.gv.list_items_2b_adjusted.append(item_2b_adjusted)
            df_future_api_holding = pd.DataFrame(list_dicts_future_api_holding)
            df_future_api_holding['index'] = df_future_api_holding['instrument_id'].apply(lambda x: x[:2])
            df_future_api_holding['multiplier'] = df_future_api_holding['index'].map(self.gv.dict_index_future2multiplier)
            df_future_api_holding['windcode'] = df_future_api_holding['instrument_id'] + '.CFE'
            df_future_api_holding['close'] = df_future_api_holding['windcode'].map(self.gv.dict_index_future_windcode2close)
            df_future_api_holding['margin_required_in_perfect_shape'] = (df_future_api_holding['position']
                                                                         * df_future_api_holding['multiplier']
                                                                         * df_future_api_holding['close']
                                                                         * margin_rate_in_perfect_shape)
            # 跨品种单向大边保证金制度
            dicts_future_api_holding_sum_by_direction = (df_future_api_holding
                                                         .loc[:, ['direction', 'margin_required_in_perfect_shape']]
                                                         .groupby(by='direction')
                                                         .sum()
                                                         .to_dict())
            dict_direction2margin_required_in_perfect_shape = \
                dicts_future_api_holding_sum_by_direction['margin_required_in_perfect_shape']
            if 'long' not in dict_direction2margin_required_in_perfect_shape:
                dict_direction2margin_required_in_perfect_shape['long'] = 0
            if 'short' not in dict_direction2margin_required_in_perfect_shape:
                dict_direction2margin_required_in_perfect_shape['short'] = 0

            margin_required_by_long = dict_direction2margin_required_in_perfect_shape['long']
            margin_required_by_short = dict_direction2margin_required_in_perfect_shape['short']
            margin_required_in_perfect_shape = max(margin_required_by_long, margin_required_by_short)

        dict_bs_by_acctidbymxz = self.gv.db_trddata['b/s_by_acctidbymxz'].find_one({'DataDate': self.str_today,
                                                                                    'AcctIDByMXZ': self.acctidbymxz})
        approximate_na = dict_bs_by_acctidbymxz['ApproximateNetAsset']
        dif_margin_required_in_perfect_shape_approximate_na = approximate_na - margin_required_in_perfect_shape
        print(self.acctidbymxz, dif_margin_required_in_perfect_shape_approximate_na)
        if dif_margin_required_in_perfect_shape_approximate_na < 0:
            item_2b_adjusted = f'Insufficient Fund for {self.acctidbymxz}: Net Asset({approximate_na}) ' \
                               f'less than {margin_required_in_perfect_shape} margin rate required.' \
                               f'Need to deposit at least ' \
                               f'{ceil(abs(dif_margin_required_in_perfect_shape_approximate_na)/10000):d}万).'
            self.gv.list_items_2b_adjusted.append(item_2b_adjusted)


class MainFrameWork:
    def __init__(self):
        self.gv = GlobalVariable()
        self.list_prdcodes = self.gv.list_prdcodes

    def run(self):
        for prdcode in self.list_prdcodes:
            prd = Product(self.gv, prdcode)
            prd.check_exception()
        print(self.gv.list_items_2b_adjusted)


if __name__ == '__main__':
    mfw = MainFrameWork()
    mfw.run()














