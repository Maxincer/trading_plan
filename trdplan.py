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
import pymongo
from WindPy import w

str_today = '20200624'


class Product:
    def __init__(self, prdcode):
        # todo 注意区分属性：产品的/子账户的
        mongodb_local = pymongo.MongoClient('mongodb://localhost:27017/')
        self.db_basicinfo = mongodb_local['basicinfo']
        self.col_acctinfo = self.db_basicinfo['acctinfo']
        iter_col_acctinfo_find = self.col_acctinfo.find({'PrdCode': prdcode, 'RptMark': 1, 'DataDate': str_today})
        list_acctidsbymxz = [dict_find['AcctIDByMXZ'] for dict_find in iter_col_acctinfo_find]

        self.i_rptaccts = len(list_acctidsbymxz)
        self.db_trddata = mongodb_local['trddata']
        col_bs_by_prdcode = self.db_trddata['b/s_by_prdcode']
        dict_bs_by_prdcode = col_bs_by_prdcode.find_one({'PrdCode': prdcode, 'DataDate': str_today})
        col_exposure_analysis_by_prdcode = self.db_trddata['exposure_analysis_by_prdcode']
        dict_exposure_analysis_by_prdcode = col_exposure_analysis_by_prdcode.find_one({'PrdCode': prdcode,
                                                                                       'DataDate': str_today})
        self.prd_long_exposure = dict_exposure_analysis_by_prdcode['LongExposure']
        self.prd_short_exposure = dict_exposure_analysis_by_prdcode['ShortExposure']
        self.prd_net_exposure = dict_exposure_analysis_by_prdcode['NetExposure']
        self.prd_approximate_na = dict_bs_by_prdcode['ApproximateNetAsset']
        self.prd_ttasset = dict_bs_by_prdcode['TotalAsset']
        self.list_exception = []


class Account(Product):
    def __init__(self, acctidbymxz):
        self.acctidbymxz = acctidbymxz
        prdcode = self.acctidbymxz.split('_')[0]
        super().__init__(prdcode)
        dict_acctinfo = self.col_acctinfo.find_one({'AcctIDByMXZ': acctidbymxz, 'RptMark': 1, 'DataDate': str_today})
        self.accttype = dict_acctinfo['AcctType']
        self.prdcode = prdcode
        col_bs_by_acctidbymxz = self.db_trddata['b/s_by_acctidbymxz']
        self.dict_bs_by_acctidbymxz = col_bs_by_acctidbymxz.find_one({'AcctIDByMXZ': acctidbymxz,
                                                                      'DataDate': str_today})
        self.acct_cash = self.dict_bs_by_acctidbymxz['Cash']
        self.acct_ce = self.dict_bs_by_acctidbymxz['CashEquivalent']
        self.acct_composite_long_amt = self.dict_bs_by_acctidbymxz['CompositeLongAmt']
        self.acct_approximate_na = self.dict_bs_by_acctidbymxz['ApproximateNetAsset']

    def check_margin_in_f_acct(self, margin_rate_in_perfect_shape=0.2):
        # 参考： 中金所 “跨品种” 单向大边保证金制度，上期所，单向大边保证金制度
        # 资料来源：上海期货交易所结算细则
        # 同一客户在同一会员处的同品种期货合约双向持仓（期货合约进入最后交易日前第五个交易日闭市后除外）
        # 对IC、IH、IF跨品种双向持仓，按照交易保证金单边较大者收取交易保证金
        pass











