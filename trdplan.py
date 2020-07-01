#!usr/bin/env python37
# coding:utf-8
# Author: Maxincer
# Create Datetime: 20200626T112000 +0800
# Update Datetime: 20200626T170000 +0800

"""
思路：
    1. 将每个账户抽象为类
    2. 将每个产品抽象为类
Note:
    1. ETF: exchange traded fund: 交易所交易基金，不存在场外ETF。 重要假设
Abbr.:
    1. cps: composite
    2. MN: Market Neutral
    3. EI: Enhanced Index
    4. cpspct: composite percentage: composite amt / net asset value
"""
from datetime import datetime
from math import ceil, floor

import pandas as pd
import pymongo
from WindPy import w


class GlobalVariable:
    def __init__(self):
        self.str_today = datetime.today().strftime('%Y%m%d')
        # self.str_today = '20200624'
        self.list_items_2b_adjusted = []
        self.dict_index_future_windcode2close = {}
        self.mongodb_local = pymongo.MongoClient('mongodb://localhost:27017/')
        self.db_basicinfo = self.mongodb_local['basicinfo']
        self.db_trddata = self.mongodb_local['trddata']
        self.col_acctinfo = self.db_basicinfo['acctinfo']
        self.col_prdinfo = self.db_basicinfo['prdinfo']
        self.col_bs_by_prdcode = self.db_trddata['b/s_by_prdcode']
        self.col_exposure_analysis_by_prdcode = self.db_trddata['exposure_analysis_by_prdcode']
        self.col_exposure_analysis_by_acctidbymxz = self.db_trddata['exposure_analysis_by_acctidbymxz']
        self.col_bs_by_acctidbymxz = self.db_trddata['b/s_by_acctidbymxz']
        self.col_future_api_holding = self.db_trddata['future_api_holding']
        iter_dicts_acctinfo_rpt = self.col_acctinfo.find({'DataDate': self.str_today, 'RptMark': 1})
        set_prdcodes = set()
        for dict_acctinfo in iter_dicts_acctinfo_rpt:
            prdcode = dict_acctinfo['PrdCode']
            set_prdcodes.add(prdcode)
        self.list_prdcodes = list(set_prdcodes)
        self.list_prdcodes.sort()
        self.dict_index_future2multiplier = {'IC': 200, 'IF': 300, 'IH': 300}
        self.dict_index_future2spot = {'IC': '000905.SH', 'IF': '000300.SH', 'IH': '000016.SH'}
        self.flt_facct_internal_required_margin_rate = 0.2

        w.start()
        set_ic_windcode = set(w.wset("sectorconstituent", f"date={self.str_today};sectorid=1000014872000000").Data[1])
        set_if_windcode = set(w.wset("sectorconstituent", f"date={self.str_today};sectorid=a599010102000000").Data[1])
        set_ih_windcode = set(w.wset("sectorconstituent", f"date={self.str_today};sectorid=1000014871000000").Data[1])
        set_custom = {'000905.SH', '000300.SH', '000016.SH'}
        set_index_future_windcodes = set_ic_windcode | set_if_windcode | set_ih_windcode | set_custom
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
        self.dict_prdinfo = self.gv.col_prdinfo.find_one({'DataDate': self.str_today, 'PrdCode': self.prdcode})
        if self.dict_prdinfo['StrategiesAllocation']:
            self.dict_strategies_allocation = self.dict_prdinfo['StrategiesAllocation']
        else:
            self.dict_strategies_allocation = None
        self.dict_na_allocation = self.dict_prdinfo['NetAssetAllocation']
        self.tgt_cpspct = self.dict_prdinfo['TargetCompositePercentage']
        self.tgt_items = self.dict_prdinfo['TargetItems']
        self.prd_long_exposure = dict_exposure_analysis_by_prdcode['LongExposure']
        self.prd_short_exposure = dict_exposure_analysis_by_prdcode['ShortExposure']
        self.prd_net_exposure = dict_exposure_analysis_by_prdcode['NetExposure']
        self.prd_approximate_na = dict_bs_by_prdcode['ApproximateNetAsset']
        self.prd_ttasset = dict_bs_by_prdcode['TotalAsset']
        self.dict_upper_limit_cpspct = {'MN': 0.77, 'EI': 0.9}

    def check_exposure(self):
        dict_exposure_analysis_by_prdcode = self.gv.col_exposure_analysis_by_prdcode.find_one(
            {'DataDate': self.str_today, 'PrdCode': self.prdcode}
        )
        net_exposure = dict_exposure_analysis_by_prdcode['NetExposure']
        net_exposure_pct = dict_exposure_analysis_by_prdcode['NetExposure(%)']
        net_exposure_pct_in_perfect_shape = (0.99 * self.dict_strategies_allocation['EI']
                                             + 0 * self.dict_strategies_allocation['MN'])
        net_exposure_in_perfect_shape = net_exposure_pct_in_perfect_shape * self.prd_approximate_na
        dif_net_exposure2ps = net_exposure - net_exposure_in_perfect_shape
        if abs(dif_net_exposure2ps) > 1000000:
            dict_item_2b_adjusted = {
                    'DataDate': self.str_today,
                    'PrdCode': self.prdcode,
                    'NetExposure': net_exposure,
                    'NetExposure(%)': net_exposure_pct,
                    'NetExposureInPerfectShape': net_exposure_in_perfect_shape,
                    'NetExposure(%)InPerfectShape': net_exposure_pct_in_perfect_shape,
                    'NetExposureDif2PS': dif_net_exposure2ps
                }
            self.gv.list_items_2b_adjusted.append(dict_item_2b_adjusted)

    def check_exception(self):
        for acctinfo in self.iter_col_acctinfo_find:
            acctidbymxz = acctinfo['AcctIDByMXZ']
            acct = Account(self.gv, acctidbymxz)
            if acct.accttype == 'f':
                acct.check_margin_in_f_acct()
            if acct.accttype in ['c', 'm']:
                acct.check_cash_in_c_m_acct()

    def cmp_f_lots(self, strategy, tgt_exposure_from_future, ic_if_ih):
        ic_if_ih = ic_if_ih.upper()
        contract_value_spot = (self.gv.dict_index_future_windcode2close[self.gv.dict_index_future2spot[ic_if_ih]]
                               * self.gv.dict_index_future2multiplier)
        flt_lots = tgt_exposure_from_future / contract_value_spot
        if strategy == 'MN':
            int_lots = round(flt_lots)
        elif strategy == 'EI':
            int_lots = floor(flt_lots)
        else:
            raise ValueError('Unknown strategy when cmp f lots.')
        return int_lots

    def budget(self):
        """
        假设：
        1. 有target用target覆盖，无target就用现值
        2. 空头暴露分配优先级（从高到低）：融券ETF，场外收益互换，股指期货
        3. 重要： EI策略中不使用ETF来补充beta
        Note:
            1. 注意现有持仓是两个策略的合并持仓，需要按照比例分配
        思路：
            1. 先求EI的shape，剩下的都是MN的。
        todo 数据库中的仓位比例为cpslongamt的比例
        """
        # 参数部分 与 假设
        ic_if_ih = 'IC'  # todo 可进一步抽象， 与空头策略有关

        # EI 策略预算假设
        flt_ei_cash2cpslongamt = 0.0888
        flt_ei_internal_required_margin_rate = 0.2
        ei_na_oaccts_tgt = 0
        ei_net_exposure_in_oaccts = 0
        ei_cpsshortamt_tgt = 0
        ei_etflongamt_tgt = 0
        ei_etfshortamt_tgt = 0

        # MN 策略预算假设
        flt_mn_cash2cpsamt = 0.987

        # 算法部分
        tgt_na = self.prd_approximate_na
        if self.tgt_items['net_asset']:
            tgt_na = self.tgt_items['net_asset']

        # 1. EI策略budget
        ei_na_tgt = tgt_na * self.dict_strategies_allocation['EI']
        ei_cpslongamt_tgt = ei_na_tgt * self.tgt_cpspct
        ei_long_exposure_from_faccts = (ei_na_tgt
                                        - (ei_cpslongamt_tgt
                                           + ei_etflongamt_tgt
                                           - ei_cpsshortamt_tgt
                                           - ei_etfshortamt_tgt))
        ei_int_lots_index_future_tgt = self.cmp_f_lots('EI', ei_long_exposure_from_faccts, ic_if_ih)
        ei_long_exposure_from_faccts_tgt = (
                ei_int_lots_index_future_tgt
                * self.gv.dict_index_future_windcode2close[self.gv.dict_index_future2spot[ic_if_ih]]
                * self.gv.dict_index_future2multiplier[ic_if_ih]
        )
        ei_na_faccts_tgt = ei_long_exposure_from_faccts_tgt * flt_ei_internal_required_margin_rate
        ei_cpslongamt_tgt = (ei_na_tgt
                             - ei_long_exposure_from_faccts_tgt
                             + ei_cpsshortamt_tgt
                             + ei_etfshortamt_tgt
                             - ei_etflongamt_tgt)
        ei_cash_in_saccts_tgt = flt_ei_cash2cpslongamt * ei_cpslongamt_tgt
        ei_na_saccts_tgt = ei_na_tgt - ei_na_faccts_tgt - ei_na_oaccts_tgt
        ei_ce_in_saccts_tgt = (ei_na_saccts_tgt
                               - ei_cpslongamt_tgt
                               - ei_cash_in_saccts_tgt
                               - ei_etflongamt_tgt
                               + ei_etfshortamt_tgt)

        # 2. MN策略budget
        # 1. 分配MN策略涉及的账户资产
        mn_na_tgt = tgt_na * self.dict_strategies_allocation['MN']
        mn_cpsamt_tgt = mn_na_tgt * self.tgt_cpspct

        # 求信用户提供的空头暴露预算值
        # 一个基金产品只能开立一个信用账户
        dict_macct_basicinfo = self.gv.col_acctinfo.find_one(
            {'DataDate': self.str_today, 'PrdCode': self.prdcode, 'AcctType': 'm'}
        )
        mn_short_exposure_from_macct = 0
        if dict_macct_basicinfo:
            acctidbymxz_macct = dict_macct_basicinfo['AcctIDByMXZ']
            dict_bs_by_acctidbymxz = self.gv.col_exposure_analysis_by_acctidbymxz.find_one(
                {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_macct}
            )
            mn_cpsshortamt_macct = dict_bs_by_acctidbymxz['CompositeShortAmt']
            mn_etfshortamt_macct = dict_bs_by_acctidbymxz['ETFShortAmt']


        mn_short_exposure_from_macct_tgt = mn_short_exposure_from_macct
        if self.tgt_items['short_exposure_from_macct']:
            mn_short_exposure_from_macct_tgt = self.tgt_items['short_exposure_from_macct']

        # 求场外户和自定义账户提供的空头暴露预算值与多头暴露预算值
        # 求场外户和自定义账户中的存出保证金（net_asset）
        list_dicts_oacct_basicinfo = list(
            self.gv.col_acctinfo.find({'DataDate': self.str_today, 'PrdCode': self.prdcode, 'AcctType': 'o'})
        )
        short_exposure_from_oacct = 0
        long_exposure_from_oacct = 0
        approximate_na_oacct = 0
        for dict_oacct_basicinfo in list_dicts_oacct_basicinfo:
            if dict_oacct_basicinfo:
                acctidbymxz_oacct = dict_oacct_basicinfo['AcctIDByMXZ']
                dict_exposure_analysis_by_acctidbymxz = self.gv.col_acctinfo.find_one(
                    {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_oacct}
                )
                short_exposure_from_oacct_delta = dict_exposure_analysis_by_acctidbymxz['ShortExposure']
                short_exposure_from_oacct += short_exposure_from_oacct_delta
                long_exposure_from_oacct_delta = dict_exposure_analysis_by_acctidbymxz['LongExposure']
                long_exposure_from_oacct += long_exposure_from_oacct_delta
                dict_bs_by_acctidbymxz = self.gv.col_acctinfo.find_one(
                    {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_oacct}
                )
                approximate_na_oacct_delta = dict_bs_by_acctidbymxz['ApproximateNetAsset']
                approximate_na_oacct += approximate_na_oacct_delta

        short_exposure_from_oacct_tgt = short_exposure_from_oacct
        if self.tgt_items['short_exposure_from_oacct']:
            short_exposure_from_oacct_tgt = self.tgt_items['short_exposure_from_oacct']
        long_exposure_from_oacct_tgt = long_exposure_from_oacct
        if self.tgt_items['long_exposure_from_oacct']:
            long_exposure_from_oacct_tgt = self.tgt_items['long_exposure_from_oacct']

        # 求期货户提供的多空暴露预算值
        # ！！！注： 空头期指为最后算出来的项目，不可指定（指定无效）
        list_dicts_faccts_basicinfo = list(
            self.gv.col_acctinfo.find({'DataDate': self.str_today, 'PrdCode': self.prdcode, 'AcctType': 'f'})
        )
        long_exposure_from_facct = 0
        short_exposure_from_facct = 0
        for dict_facct_basicinfo in list_dicts_faccts_basicinfo:
            acctidbymxz_facct = dict_facct_basicinfo['AcctIDByMXZ']
            dict_exposure_analysis_by_acctidbymxz = self.gv.col_acctinfo.find_one(
                {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_facct}
            )
            long_exposure_from_facct_delta = dict_exposure_analysis_by_acctidbymxz['LongExposure']
            long_exposure_from_facct += long_exposure_from_facct_delta
            short_exposure_from_facct_delta = dict_exposure_analysis_by_acctidbymxz['ShortExposure']
            short_exposure_from_facct += short_exposure_from_facct_delta

        long_exposure_from_facct_tgt = long_exposure_from_facct
        if self.tgt_items['long_exposure_from_facct']:
            long_exposure_from_facct_tgt = self.tgt_items['long_exposure_from_facct']

        # long_exposure_total_tgt = (long_exposure_from_cpsamt_mn_tgt
        #                            + long_exposure_from_oacct_tgt
        #                            + long_exposure_from_facct_tgt)

        # short_exposure_from_facct_tgt = (long_exposure_total_tgt
        #                                  - short_exposure_from_macct_tgt
        #                                  - short_exposure_from_oacct_tgt)
        # int_lots_index_future_short_tgt = self.cmp_f_lots('MN', short_exposure_from_facct_tgt, ic_if_ih)
        # short_exposure_from_facct_tgt = (
        #         int_lots_index_future_short_tgt
        #         * self.gv.dict_index_future2multiplier[ic_if_ih]
        #         * self.gv.dict_index_future_windcode2close[self.gv.dict_index_future2spot[ic_if_ih]]
        # )
        # na_facct_tgt = short_exposure_from_facct_tgt * self.gv.flt_facct_internal_required_margin_rate
        #
        # na_oacct_tgt = approximate_na_oacct
        #
        # short_exposure_tgt = (short_exposure_from_facct_tgt
        #                       + short_exposure_from_macct_tgt
        #                       + short_exposure_from_oacct_tgt)
        # dict_bs_by_prdcode = self.gv.col_bs_by_prdcode.find_one({'DataDate': self.str_today, 'PrdCode': self.prdcode})
        # long_exposure_from_etf = dict_bs_by_prdcode['ETFLongAmt']
        # long_exposure_from_etf_tgt = long_exposure_from_etf
        # if self.tgt_items['long_exposure_from_etf']:
        #     long_exposure_from_etf_tgt = self.tgt_items['long_exposure_from_etf']
        #
        # long_exposure_tgt = short_exposure_tgt
        # long_exposure_from_cpsamt_mn_tgt = (long_exposure_tgt
        #                                     - long_exposure_from_oacct_tgt
        #                                     - long_exposure_from_facct_tgt
        #                                     - long_exposure_from_etf_tgt)
        # na_cmacct_tgt = na_mn_tgt - na_facct_tgt - na_oacct_tgt
        #
        # dict_tgt = {
        #     'TargetNetAsset': tgt_na,
        #     'EI': {
        #         'EINetAsset': {
        #             'EINetAssetOfSecurityAccounts': ei_na_saccts_tgt,
        #             'EINetAssetOfFutureAccounts': ei_na_faccts_tgt,
        #             'EINetAssetOfOTCAccounts': ei_na_oaccts_tgt,
        #             'EINetAsset': ei_na_tgt,
        #             'NetAssetAllocationBetweenCapitalSources': {},
        #         },
        #         'EIPosition': {
        #             'EICashOfSecurityAccount': ei_cash_in_saccts_tgt,
        #             'EICashEquivalentOfSecurityAccount': ei_ce_in_saccts_tgt,
        #             'EICompositeLongAmountOfSecurityAccounts': ei_cpslongamt_tgt,
        #             'EICompositeShortAmountOfSecurityAccounts': ei_cpsshortamt_tgt,
        #             'EIETFLongAmountOfSecurityAccounts': ei_etflongamt_tgt,
        #             'EIETFShortAmountOfSecurityAccounts': ei_etfshortamt_tgt,
        #             'EIContractsNetAmountOfFutureAccounts': ei_long_exposure_from_faccts,
        #             'EIContractsNetLotsOfFutureAccounts': ei_int_lots_index_future_tgt,
        #             'EINetExposureFromOTCAccounts': ei_net_exposure_in_oaccts,
        #             'PositionAllocationBetweenCapitalSources': {},
        #         }
        #     },
        #     'MN': {
        #         'MNNetAsset': {
        #             'MNNetAssetOfStockAccounts': mn_cpsamt_tgt,
        #             'MNNetAssetOfFutureAccounts': None,
        #             'MNNetAssetOfOTCAccounts': None,
        #             'MNNetAsset': None,
        #             'NetAssetAllocationBetweenCapitalSources': {},
        #         },
        #         'MNPosition': {
        #             'MNCashOfSecurityAccount': None,
        #             'MNCashEquivalentOfSecurityAccount': None,
        #             'MNCompositeLongAmountOfSecurityAccounts': None,
        #             'MNCompositeShortAmountOfSecurityAccounts': None,
        #             'MNETFNetAmountOfSecurityAccounts': None,
        #             'MNContractsNetAmountOfFutureAccounts': None,
        #             'MNContractsNetLotsOfFutureAccounts': None,
        #             'MNNetExposureFromOTCAccounts': None,
        #             'PositionAllocationBetweenCapitalSources': {},
        #         }
        #     },
        # }


class Account(Product):
    def __init__(self, gv, acctidbymxz):
        self.acctidbymxz = acctidbymxz
        self.prdcode = self.acctidbymxz.split('_')[0]
        super().__init__(gv, self.prdcode)
        self.dict_acctinfo = self.gv.col_acctinfo.find_one({'AcctIDByMXZ': acctidbymxz, 'RptMark': 1,
                                                            'DataDate': self.str_today})
        self.accttype = self.dict_acctinfo['AcctType']
        self.dict_bs_by_acctidbymxz = self.gv.col_bs_by_acctidbymxz.find_one(
            {'AcctIDByMXZ': self.acctidbymxz, 'DataDate': self.str_today}
        )
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
        list_dicts_future_api_holding = list(self.gv.col_future_api_holding
                                             .find({'DataDate': self.str_today, 'AcctIDByMXZ': self.acctidbymxz}))
        margin_required_in_perfect_shape = 0
        if list_dicts_future_api_holding:
            list_illegal_contract = []
            for dict_future_api_holding in list_dicts_future_api_holding:
                instrument_id = dict_future_api_holding['instrument_id']
                instrument_id_first_2 = instrument_id[:2]
                if instrument_id_first_2 not in ['IC', 'IF', 'IH']:
                    list_illegal_contract.append(instrument_id)
            if list_illegal_contract:
                dict_item_2b_adjusted = {self.acctidbymxz: {'Illegal Contract': list_illegal_contract}}
                self.gv.list_items_2b_adjusted.append(dict_item_2b_adjusted)
            df_future_api_holding = pd.DataFrame(list_dicts_future_api_holding)
            df_future_api_holding['index'] = df_future_api_holding['instrument_id'].apply(lambda x: x[:2])
            df_future_api_holding['multiplier'] = (df_future_api_holding['index']
                                                   .map(self.gv.dict_index_future2multiplier))
            df_future_api_holding['windcode'] = df_future_api_holding['instrument_id'] + '.CFE'
            df_future_api_holding['close'] = (df_future_api_holding['windcode']
                                              .map(self.gv.dict_index_future_windcode2close))
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

        dict_bs_by_acctidbymxz = (self.gv.col_bs_by_acctidbymxz
                                  .find_one({'DataDate': self.str_today, 'AcctIDByMXZ': self.acctidbymxz}))
        approximate_na = dict_bs_by_acctidbymxz['ApproximateNetAsset']
        dif_margin_required_in_perfect_shape_approximate_na = approximate_na - margin_required_in_perfect_shape
        if dif_margin_required_in_perfect_shape_approximate_na < 0:
            dict_item_2b_adjusted = {
                    'DataDate': self.str_today,
                    'PrdCode': self.prdcode,
                    'AcctIDByMXZ': self.acctidbymxz,
                    'ApproximateNetAsset': approximate_na,
                    'NetAssetInPerfectShape': margin_required_in_perfect_shape,
                    'NetAssetDif2Perfect': dif_margin_required_in_perfect_shape_approximate_na
                }
            self.gv.list_items_2b_adjusted.append(dict_item_2b_adjusted)

    def check_cash_in_c_m_acct(self):
        dict_bs_by_acctidbymxz = (self.gv.col_bs_by_acctidbymxz
                                  .find_one({'DataDate': self.str_today, 'AcctIDByMXZ': self.acctidbymxz}))
        cash = dict_bs_by_acctidbymxz['Cash']
        ce = dict_bs_by_acctidbymxz['CashEquivalent']
        composite_long_amt = dict_bs_by_acctidbymxz['CompositeLongAmt']
        cash_to_composite_long_amt_in_perfect_shape = 0.0889  # EIF perfect shape模型中的现金股票比（比MN少）
        cash_in_perfect_shape = composite_long_amt * cash_to_composite_long_amt_in_perfect_shape
        dif_cash = cash - cash_in_perfect_shape
        if abs(dif_cash) > 2000000:
            dict_item_2b_adjusted = {
                    'DataDate': self.str_today,
                    'PrdCode': self.prdcode,
                    'AcctIDByMXZ': self.acctidbymxz,
                    'Cash': cash,
                    'CashInPerfectShape': cash_in_perfect_shape,
                    'CashDif2Perfect': dif_cash,
                    'CE': ce
                }
            self.gv.list_items_2b_adjusted.append(dict_item_2b_adjusted)


class MainFrameWork:
    def __init__(self):
        self.gv = GlobalVariable()
        self.list_prdcodes = self.gv.list_prdcodes

    def run(self):
        for prdcode in self.list_prdcodes:
            prd = Product(self.gv, prdcode)
            prd.check_exception()
            prd.check_exposure()
        self.gv.db_trddata['items_2b_adjusted'].delete_many({'DataDate': self.gv.str_today})
        self.gv.db_trddata['items_2b_adjusted'].insert_many(self.gv.list_items_2b_adjusted)


if __name__ == '__main__':
    mfw = MainFrameWork()
    mfw.run()














