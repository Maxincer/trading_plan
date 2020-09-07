#!usr/bin/env python37
# coding:utf-8
# Author: Maxincer
# Create Datetime: 20200626T112000 +0800
# Update Datetime: 20200626T170000 +0800

"""
思路：

重要假设:
    1. ETF: exchange traded fund: 交易所交易基金。不存在场外ETF。
    2. 换仓资金： 本项目统一为目标仓位的0.889
    3. 本项目中，所有产品的融资数据均由patchdata 传入
    4. 当指定的仓位小于max仓位（未满仓）时，在满足产品仓位达标后，还需分配渠道 todo 假设： 分配比例为渠道比例
    5. 在多渠道且有货基的条件下，产品的各渠道的货基值，受各渠道分配到的期指数量影响 todo 假设： 分配比例为渠道比例

合规假设：
    1. 融资融券业务相关：
        1. 证监会《融资融券合同必备条款》第五条第一款，甲方用于一家证券交易所上市证券交易的信用证券账户只能有一个。
            （证券公司客户信用交易担保证券账户）
        2. 证监会《融资融券合同必备条款》第五条第二款，甲方用于一家证券交易所上市证券交易的信用资金账户只能有一个。
            （证券公司客户信用交易担保资金账户）
        3. 证监会《融资融券合同必备条款》第八条第一款，融资、融券期限从甲方实际使用资金或使用证券之日起计算。
        4. 证监会《融资融券合同必备条款》第八条第二款，融资利息和融券费用按照甲方实际使用资金和证券的天数计算。
        5. 证件会《融资融券合同必备条款》第十二条第三款，甲方卖出信用证券账户中融资买入尚未了结合约的证券所得价款，应当先偿还甲方融资欠款。
        6. 证件会《融资融券合同必备条款》第十四条第三款，合同应约定：甲方融入证券后、归还证券前，证券发行人分配投资收益、向证券持有人配售或者
           无偿派发证券、发行证券持有人有优先认购权的证券的，甲方在偿还债务时，应当按照合同约定，向乙方支付与所融入证券可得利益相等的证券或资金。
           合同还应明确约定甲方对乙方进行补偿的具体方式以及数量、金额的计算方法。约定的补偿方式以及数量、金额的计算方法应公平合理。
        7. 证件会《融资融券合同必备条款》第十五条第三款，乙方向甲方提供对账服务的方式，如网站或电话交易系统查询、发送电子邮件查询、
            邮寄对账单查询等。乙方向甲方提供的对账单，应载明如下事项：
    　 　      1、甲方授信额度与剩余可用授信额度；
    　　       2、甲方信用账户资产总值、负债总额、保证金可用余额与可提取金额、担保证券市值、维持担保比例；
    　　       3、每笔融资利息与融券费用、偿还期限，融资买入和融券卖出的成交价格、数量、金额。
        8. 《上海证券交易所融资融券交易实施细则》第四十二条，维持担保比例是指客户担保物价值与其融资融券债务之间的比例，计算公式为：
            维持担保比例=（现金+信用证券账户内证券市值总和+其他担保M物价值）/（融资买入金额+融券卖出证券数量×当前市价＋利息及费用总和）。
            注：新修订的“细则”（2019年修订）取消了最低维持担保比例不得低于130%的规定。原为130% 补至160%
        9. 《上海证券交易所融资融券交易实施细则》第四十条，投资者融资买入或融券卖出时所使用的保证金不得超过其保证金可用余额。
            保证金可用余额是指投资者用于充抵保证金的现金、证券市值及融资融券交易产生的浮盈经折算后形成的保证金总额，减去投资者未了结融资融券交易
            已占用保证金和相关利息、费用的余额。其计算公式为：
            保证金可用余额 ＝ 现金
                           + ∑（可充抵保证金的证券市值×折算率）
                           + ∑［（融资买入证券市值－融资买入金额）×折算率］
                           + ∑［（融券卖出金额－融券卖出证券市值）×折算率］
                           - ∑融券卖出金额
                           - ∑融资买入证券金额×融资保证金比例
                           - ∑融券卖出证券市值×融券保证金比例
                           - 利息及费用
            公式中，
            融券卖出金额 = 融券卖出证券的数量×卖出价格，
            融券卖出证券市值=融券卖出证券数量×市价，
            融券卖出证券数量指融券卖出后尚未偿还的证券数量；
            ∑［（融资买入证券市值－融资买入金额）×折算率］、∑［（融券卖出金额－融券卖出证券市值）×折算率］中的折算率是指融资买入、
            融券卖出证券对应的折算率，当融资买入证券市值低于融资买入金额或融券卖出证券市值高于融券卖出金额时，折算率按100%计算。
        10. 《上海证券交易所融资融券交易实施细则》第三十八条，投资者融资买入证券时，融资保证金比例不得低于100%。
　　          融资保证金比例是指投资者融资买入时交付的保证金与融资交易金额的比例，计算公式为：
             融资保证金比例 = 保证金 / (融资买入证券数量 * 买入价格) * 100%
        11. 《上海证券交易所融资融券交易实施细则》第三十九条,投资者融券卖出时，融券保证金比例不得低于50%。
            融券保证金比例是指投资者融券卖出时交付的保证金与融券交易金额的比例，计算公式为：
            融券保证金比例 = 保证金 / (融券卖出证券数量 * 卖出价格) * 100%
        12. 《上海证券交易所融资融券交易实施细则》第十七条，未了结相关融券交易前，投资者融券卖出所得价款除以下用途外，不得另作他用：
            （一）买券还券；
            （二）偿还融资融券相关利息、费用和融券交易相关权益现金补偿；
            （三）买入或申购证券公司现金管理产品、货币市场基金以及本所认可的其他高流动性证券；
            （四）证监会及本所规定的其他用途。
        13. 《上海证券交易所融资融券交易实施细则》第五条，会员在本所从事融资融券交易，应按照有关规定开立
            融券专用证券账户、客户信用交易担保证券账户、 融资专用资金账户及客户信用交易担保资金账户，并在开户后3个交易日内报本所备案。
            《上海证券交易所融资融券交易实施细则》第七条，会员在向客户融资、融券前，应当按照有关规定与客户签订融资融券合同及融资融券交易风险揭示
            书，并为其开立信用证券账户和信用资金账户。
    2. 账户相关：
        1. 一个基金产品最多有3个普通证券账户，1个信用证券账户，3个期货账户。
    3. 网下申购：

Abbr.:
    1. cps: composite
    2. MN: Market Neutral
    3. EI: Enhanced Index
    4. cpspct: composite percentage: composite amt / net asset value

todo:
    2. 国债逆回购（核新系统）不在下载的数据文件之内，如何添加？
    3. 国债逆回购不同系统的单位价格确认。（核新为1000，有没有100的情况？）与债券计量单位有关，1收为10张，1张的面值为100元。交易软件中的1股债券
    6. 负债（融券与场外，利息的）的计算需要改进：
        1. 目前状态仅在patchdata 更新时考虑了利息，在源数据的读取中没有考虑利息。
        2. 源数据中提供了利息的应还与未还数据，故可以改进算法，精准计算。
        3. 目前的na=总资产-负债，负债中未计算利息的产品，na会被高估
    5. AcctType 中的c,m,f,o 统一改为大写
    8. budget算法改进： 当不满仓时，要留足期货户资金
    9. 多渠道最大值算法需要商定
    10. 申赎款项的自动化(暂时搁置)
    11. 期货满仓限定(暂时搁置)

Sympy:
    1. Sympy 中的 solveset， 不能解多元非线性方程组（带domain的），但是solve可以。
    2. Sympy中的solve, 如果解为多解时，也返回空列表。此处可用solveset区分无解与多解。

Naming Convention:
    1. Security Accounts:
        1. 根据《上海证券交易所融资融券交易实施细则》，margin account 的官方翻译为：“信用证券账户”。
        2. 根据证件会《融资融券合同必备条款》，cash account 的官方翻译为：“普通证券账户”
        3. 综合上述两点，证券账户包括信用证券账户与普通证券账户，英文在本项目中约定为Security Account.
        4. Accounts 为 Account的复数形式，表示全部Account的意思。
        5. 根据《上海证券交易所融资融券交易实施细则》，“证券类资产”，是指投资者持有的客户交易结算资金、股票、债券、基金、证券公司资管计划等资产。
    2. Cash Available: 本脚本中，将信用户可用于交易的资金，叫做Cash Available
    3. 本项目中，对于合计项目(如iclots_total)total标识一定要加上.
    4. 对于净资产字段，为避免与None值缩写’N/A,NA'产生混淆，统一使用NAV

配置相关（重要）:
    配置全量： 1. basic info 2. data_patch 3. global variable 中的初始化函数

"""
from datetime import datetime
from math import floor
from os import path
from sympy import Symbol, solve

import pandas as pd
import pymongo
from WindPy import w


class GlobalVariable:
    def __init__(self):
        self.str_today = datetime.today().strftime('%Y%m%d')
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
        self.fpath_basicinfo = 'data/basic_info.xlsx'
        df_acctinfo = pd.read_excel(self.fpath_basicinfo, sheet_name='acctinfo', dtype={'PrdCode': str})
        list_dicts_acctinfo_rpt = df_acctinfo.to_dict('records')
        self.list_prdcodes = []
        for dict_acctinfo in list_dicts_acctinfo_rpt:
            if dict_acctinfo['RptMark']:
                prdcode = dict_acctinfo['PrdCode']
                if prdcode not in self.list_prdcodes:
                    self.list_prdcodes.append(prdcode)
        self.dict_index_future2multiplier = {'IC': 200, 'IF': 300, 'IH': 300}
        self.dict_index_future2spot = {'IC': '000905.SH', 'IF': '000300.SH', 'IH': '000016.SH'}
        self.flt_facct_internal_required_margin_rate = 0.2
        self.col_formatted_holding = self.db_trddata['formatted_holding']
        self.list_items_budget_details = []
        self.list_items_budget = []
        w.start()
        self.str_last_trddate = w.tdaysoffset(-1, self.str_today, "").Data[0][0].strftime('%Y%m%d')
        self.str_next_trddate = w.tdaysoffset(1, self.str_today, '').Data[0][0].strftime('%Y%m%d')
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
        self.dict_index_future2internal_required_na_per_lot = {
            'IC': (self.dict_index_future_windcode2close['000905.SH'] * self.dict_index_future2multiplier['IC']
                   * self.flt_facct_internal_required_margin_rate),
            'IF': (self.dict_index_future_windcode2close['000300.SH'] * self.dict_index_future2multiplier['IF']
                   * self.flt_facct_internal_required_margin_rate),
            'IH': (self.dict_index_future_windcode2close['000016.SH'] * self.dict_index_future2multiplier['IH']
                   * self.flt_facct_internal_required_margin_rate),
        }
        self.dict_index_future2spot_exposure_per_lot = {
            'IC': (self.dict_index_future_windcode2close['000905.SH'] * self.dict_index_future2multiplier['IC']),
            'IF': (self.dict_index_future_windcode2close['000300.SH'] * self.dict_index_future2multiplier['IF']),
            'IH': (self.dict_index_future_windcode2close['000016.SH'] * self.dict_index_future2multiplier['IH'])
        }
        self.col_na_allocation = self.db_trddata['na_allocation']
        self.str_yesterday = w.tdaysoffset(-1, self.str_today, "").Data[0][0].strftime('%Y%m%d')
        self.col_spr = self.db_trddata['spr']
        self.fpath_datapatch = '/data/data_patch.xlsx'
        self.index_future = 'IC'
        self.flt_cash2cpslongamt = 0.0889
        self.col_bgt_by_acctidbymxz = self.db_trddata['bgt_by_acctidbymxz']
        self.col_tgtna_by_prdcode = self.db_trddata['tgtna_by_prdcode']
        self.col_broker_info = self.db_basicinfo['broker_info']
        self.list_dicts_trdplan_output = []
        self.col_facct_holding_aggr_by_prdcode = self.db_trddata['facct_holding_aggr_by_prdcode']
        self.col_facct_holding_aggr_by_acctidbymxz = self.db_trddata['facct_holding_aggr_by_acctidbymxz']
        self.list_dicts_broker_info = self.db_basicinfo['broker_info'].find({'DataDate': self.str_today})
        self.col_trdplan_output = self.db_trddata['trdplan_output']
        self.col_tgtcpsamt = self.db_trddata['tgtcpsamt']
        self.col_items_2b_adjusted = self.db_trddata['items_2b_adjusted']
        self.col_trdplan_expression = self.db_basicinfo['trdplan_expression']
        self.dict_prdcode2special_na_src1 = {'707': 5000000}  # 人工T0处理，仅处理ei策略，视为货基；mn策略无需处理，视为投下层
        self.dict_strategies2short_strategies = {
            'MN': {'index_future2adjust_exposure': 'IC'},
            'EI': {'index_future2adjust_exposure': 'IC'},
            'IPO_SH': {'index_future2adjust_exposure': 'IH'}
        }
        # todo 以下代码需要改进
        self.dict_broker_abbr2broker_alias = {}
        for dict_broker_info in self.list_dicts_broker_info:
            brokerabbr = dict_broker_info['BrokerAbbr']
            brokeralias = dict_broker_info['BrokerAlias']
            self.dict_broker_abbr2broker_alias[brokerabbr] = brokeralias


class Product:
    def __init__(self, gv, prdcode):
        # 注意区分属性：产品的/子账户的
        self.gv = gv
        self.str_today = self.gv.str_today
        self.prdcode = prdcode
        self.iter_col_acctinfo_find = (
            self.gv.col_acctinfo.find({'PrdCode': self.prdcode, 'RptMark': 1, 'DataDate': self.str_today})
        )
        self.dict_bs_by_prdcode = self.gv.col_bs_by_prdcode.find_one(
            {'PrdCode': self.prdcode, 'DataDate': self.str_today}
        )
        self.dict_exposure_analysis_by_prdcode = (
            self.gv.col_exposure_analysis_by_prdcode.find_one({'PrdCode': self.prdcode, 'DataDate': self.str_today})
        )
        self.dict_prdinfo = self.gv.col_prdinfo.find_one({'DataDate': self.str_today, 'PrdCode': self.prdcode})
        self.prdname = self.dict_prdinfo['PrdName']
        self.signals_on_trdplan = self.dict_prdinfo['SignalsOnTrdPlan']
        self.str_cpsttrdstarttime = self.dict_prdinfo['CpsTrdStartTimes']
        self.dict_strategies_allocation = self.dict_prdinfo['StrategiesAllocation']
        self.dict_na_allocation = self.gv.col_na_allocation.find_one({'PrdCode': prdcode, 'DataDate': self.str_today})
        self.tgt_cpspct = self.dict_prdinfo['TargetCompositePercentage']
        self.dict_tgt_items = self.dict_prdinfo['TargetItems']
        self.prd_approximate_na = self.dict_bs_by_prdcode['ApproximateNetAsset']
        self.prd_ttasset = self.dict_bs_by_prdcode['TotalAsset']
        self.dict_upper_limit_cpspct = {'MN': 0.77, 'EI': 0.9}
        self.list_dicts_bgt_by_acctidbymxz = []
        self.dict_tgtna_by_prdcode = self.gv.col_tgtna_by_prdcode.find_one(
            {'DataDate': self.str_today, 'PrdCode': prdcode}
        )
        self.prdna_tgt = self.dict_tgtna_by_prdcode['TgtNA']
        self.ei_na_tgt = self.prdna_tgt * self.dict_strategies_allocation['EI']
        self.mn_na_tgt = self.prdna_tgt * self.dict_strategies_allocation['MN']
        recdict_unav = self.get_latest_unav()
        self.latest_rptdate_unav = recdict_unav['LatestUNAVRptDate']
        self.latest_rptunav = recdict_unav['LatestRptUNAV']

    def get_latest_unav(self):
        prdcode_in_4121_final_new = self.dict_prdinfo['PrdCodeIn4121FinalNew']
        fpath_df_unav_from_4121_final_new = (f'//192.168.4.121/data/Final_new/{self.str_today}/'
                                             f'######产品净值相关信息######.xlsx')
        # \\192.168.4.121\data\Final_new\20200724
        # fpath_df_unav_from_4121_final_new = '//192.168.4.121/data/Final_new/20200825/######产品净值相关信息######.xlsx'
        if not path.exists(fpath_df_unav_from_4121_final_new):
            fpath_df_unav_from_4121_final_new = (f'//192.168.4.121/data/Final_new/{self.gv.str_last_trddate}/'
                                                 f'######产品净值相关信息######.xlsx')
        # 注意读取的最新日期有可能会改变格式，目前为-
        df_unav_from_4121_final_new = pd.read_excel(
            fpath_df_unav_from_4121_final_new,
            dtype={
                '产品编号': str,
                '产品名称': str,
                '最新更新日期': str,
                '分红单位净值': float,
            }
        )
        latest_rptdate = None
        latest_rptunav = None
        list_dicts_unavs_from_4121_final_new = df_unav_from_4121_final_new.to_dict('records')
        for dict_unav_from_4121_final_new in list_dicts_unavs_from_4121_final_new:
            if dict_unav_from_4121_final_new['产品编号'] == prdcode_in_4121_final_new:
                latest_rptdate = dict_unav_from_4121_final_new['最新更新日期']
                latest_rptunav = dict_unav_from_4121_final_new['分红单位净值']
        recdict_unav = {
            'LatestUNAVRptDate': latest_rptdate,
            'LatestRptUNAV': latest_rptunav
        }
        return recdict_unav

    def check_exposure(self):
        dict_exposure_analysis_by_prdcode = self.gv.col_exposure_analysis_by_prdcode.find_one(
            {'DataDate': self.str_today, 'PrdCode': self.prdcode}
        )
        net_exposure = dict_exposure_analysis_by_prdcode['NetExposure']
        net_exposure_pct = dict_exposure_analysis_by_prdcode['NetExposure(%)']
        net_exposure_pct_in_perfect_shape = (
                0.99 * self.dict_strategies_allocation['EI'] + 0 * self.dict_strategies_allocation['MN']
        )
        net_exposure_in_perfect_shape = net_exposure_pct_in_perfect_shape * self.prd_approximate_na
        dif_net_exposure2ps = net_exposure - net_exposure_in_perfect_shape
        dif_pct_net_exposure = net_exposure_pct - net_exposure_pct_in_perfect_shape
        if abs(dif_net_exposure2ps) > 15000000 or abs(dif_pct_net_exposure) > 0.04:
            dict_item_2b_adjusted = {
                    'DataDate': self.str_today,
                    'PrdCode': self.prdcode,
                    'NetExposure': net_exposure,
                    'NetExposure(%)': net_exposure_pct,
                    'NetExposureInPerfectShape': net_exposure_in_perfect_shape,
                    'NetExposure(%)InPerfectShape': net_exposure_pct_in_perfect_shape,
                    'DifNetExposure2PS': dif_net_exposure2ps,
                    'DifNetExposure(%)': dif_pct_net_exposure
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
                               * self.gv.dict_index_future2multiplier[ic_if_ih])
        flt_lots = tgt_exposure_from_future / contract_value_spot
        if strategy == 'MN':
            int_lots = round(flt_lots)
        elif strategy == 'EI':
            int_lots = floor(flt_lots)
        else:
            raise ValueError('Unknown strategy when cmp f lots.')
        return int_lots

    def allocate_faccts(self, iclots_total):
        index_future = self.gv.index_future
        na_faccts = abs(iclots_total) * self.gv.dict_index_future2internal_required_na_per_lot[index_future]
        if self.dict_na_allocation:
            dict_na_allocation_faccts = self.dict_na_allocation['FutureAccountsNetAssetAllocation']
            if dict_na_allocation_faccts:
                if len(dict_na_allocation_faccts) == 2:
                    list_keys_na_allocation_faccts = list(dict_na_allocation_faccts.keys())
                    list_keys_na_allocation_faccts.sort()
                    list_values_na_allocation_faccts = [dict_na_allocation_faccts[x]
                                                        for x in list_keys_na_allocation_faccts]
                    specified_na_facct = 0  # 求定值
                    specified_na_the_other_idx = None
                    specified_na_facct_idx = None

                    for idx, value_na_allocation_faccts in enumerate(list_values_na_allocation_faccts):
                        if isinstance(value_na_allocation_faccts, str):
                            specified_na_the_other_idx = idx
                        elif value_na_allocation_faccts > 1:
                            specified_na_facct = value_na_allocation_faccts
                            specified_na_facct_idx = idx
                        else:
                            continue

                    # todo 需改进： 当定值大于开出iclots_total 所需要的na的处理(方程组需改进)
                    if specified_na_facct > 0:  # 若定值 > 0, 使用定值算法
                        specified_na_the_other_facct_src = list_keys_na_allocation_faccts[specified_na_the_other_idx]
                        acctidbymxz_facct_the_other_src = self.gv.col_acctinfo.find_one(
                            {
                                'DataDate': self.str_today,
                                'CapitalSource': specified_na_the_other_facct_src,
                                'AcctType': 'f',
                                'PrdCode': self.prdcode
                            }
                        )['AcctIDByMXZ']
                        specified_na_facct_src = list_keys_na_allocation_faccts[specified_na_facct_idx]

                        acctidbymxz_facct_specified_src = self.gv.col_acctinfo.find_one(
                            {
                                'DataDate': self.str_today,
                                'CapitalSource': specified_na_facct_src,
                                'AcctType': 'f',
                                'PrdCode': self.prdcode
                            }
                        )['AcctIDByMXZ']

                        specified_na_the_other = 0
                        if specified_na_facct > na_faccts:
                            iclots_in_specified_facct = iclots_total
                            iclots_in_the_other_facct = 0
                            print('Waring: Specified na in faccts exceeds internally required na.')
                        else:
                            iclots_in_specified_facct = int(
                                    specified_na_facct
                                    / self.gv.dict_index_future2internal_required_na_per_lot[index_future]
                            )
                            iclots_in_the_other_facct = iclots_total - iclots_in_specified_facct
                            specified_na_the_other = na_faccts - specified_na_facct

                        list_dicts_bgt_faccts = [
                            {
                                'DataDate': self.str_today,
                                'PrdCode': self.prdcode,
                                'AcctIDByMXZ': acctidbymxz_facct_specified_src,
                                'NAV': specified_na_facct,
                                'CPSLongAmt': None,
                                'ICLots': iclots_in_specified_facct,
                                'CEFromCashFromSS': None,
                                'CEFromCashAvailable': None,
                            },
                            {
                                'DataDate': self.str_today,
                                'PrdCode': self.prdcode,
                                'AcctIDByMXZ': acctidbymxz_facct_the_other_src,
                                'NAV': specified_na_the_other,
                                'CPSLongAmt': None,
                                'ICLots': iclots_in_the_other_facct,
                                'CEFromCashFromSS': None,
                                'CEFromCashAvailable': None,
                            }
                        ]
                    else:  # 若定值<=0, 使用定比算法
                        src1_faccts = list_keys_na_allocation_faccts[0]
                        acctidbymxz_facct_src1 = self.gv.col_acctinfo.find_one(
                            {
                                'DataDate': self.str_today,
                                'CapitalSource': src1_faccts,
                                'AcctType': 'f',
                                'PrdCode': self.prdcode
                            }
                        )['AcctIDByMXZ']
                        iclots_src1 = round(iclots_total * list_values_na_allocation_faccts[0])
                        na_facct_src1 = abs(iclots_src1
                                            * self.gv.dict_index_future2internal_required_na_per_lot[
                                                index_future])

                        src2_faccts = list_keys_na_allocation_faccts[1]
                        acctidbymxz_facct_src2 = self.gv.col_acctinfo.find_one(
                            {
                                'DataDate': self.str_today,
                                'CapitalSource': src2_faccts,
                                'AcctType': 'f',
                                'PrdCode': self.prdcode
                            }
                        )['AcctIDByMXZ']
                        iclots_src2 = round(iclots_total * list_values_na_allocation_faccts[1])
                        na_facct_src2 = abs(iclots_src2
                                            * self.gv.dict_index_future2internal_required_na_per_lot[
                                                index_future])

                        list_dicts_bgt_faccts = [
                            {
                                'DataDate': self.str_today,
                                'PrdCode': self.prdcode,
                                'AcctIDByMXZ': acctidbymxz_facct_src1,
                                'NAV': na_facct_src1,
                                'CPSLongAmt': None,
                                'ICLots': iclots_src1,
                                'CEFromCashFromSS': None,
                                'CEFromCashAvailable': None,
                            },
                            {
                                'DataDate': self.str_today,
                                'PrdCode': self.prdcode,
                                'AcctIDByMXZ': acctidbymxz_facct_src2,
                                'NAV': na_facct_src2,
                                'CPSLongAmt': None,
                                'ICLots': iclots_src2,
                                'CEFromCashFromSS': None,
                                'CEFromCashAvailable': None,
                            }

                        ]
                    self.list_dicts_bgt_by_acctidbymxz += list_dicts_bgt_faccts
            else:
                dict_acctidbymxz_facct_trading = self.gv.col_acctinfo.find_one(
                    {'DataDate': self.str_today, 'AcctType': 'f', 'AcctStatus': 'T',
                     'PrdCode': self.prdcode, 'RptMark': 1}
                )

                if dict_acctidbymxz_facct_trading:
                    acctidbymxz_facct_trading = dict_acctidbymxz_facct_trading['AcctIDByMXZ']
                else:
                    acctidbymxz_facct_trading = None

                dict_bgt_facct = {
                    'DataDate': self.str_today,
                    'PrdCode': self.prdcode,
                    'AcctIDByMXZ': acctidbymxz_facct_trading,
                    'NAV': na_faccts,
                    'CPSLongAmt': None,
                    'ICLots': iclots_total,
                    'CEFromCashFromSS': None,
                    'CEFromCashAvailable': None,
                }
                self.list_dicts_bgt_by_acctidbymxz.append(dict_bgt_facct)
        else:
            dict_acctidbymxz_facct_trading = self.gv.col_acctinfo.find_one(
                {'DataDate': self.str_today, 'AcctType': 'f', 'AcctStatus': 'T', 'PrdCode': self.prdcode, 'RptMark': 1}
            )

            if dict_acctidbymxz_facct_trading:
                acctidbymxz_facct_trading = dict_acctidbymxz_facct_trading['AcctIDByMXZ']
            else:
                acctidbymxz_facct_trading = None

            dict_bgt_facct = {
                'DataDate': self.str_today,
                'PrdCode': self.prdcode,
                'AcctIDByMXZ': acctidbymxz_facct_trading,
                'NAV': na_faccts,
                'CPSLongAmt': None,
                'ICLots': iclots_total,
                'CEFromCashFromSS': None,
                'CEFromCashAvailable': None,
            }
            self.list_dicts_bgt_by_acctidbymxz.append(dict_bgt_facct)

    def budget(self):
        """
        假设：
        1. 有target用target覆盖，无target就用现值
        2. 空头暴露分配优先级（从高到低）：融券ETF，场外收益互换，股指期货
        3. 重要： EI策略中不使用ETF来补充beta
        4. 重要： 期指对冲策略中，只使用IC进行对冲
        5. 重要： 最多两个策略且由这两个策略构成： EI， MN
        6. 重要： 分配c与m的资金时，如果有融资融券负债，要尽可能少的分给m户。
        7. 重要： 期货端对冲工具默认为IC合约
        （限制： 1.最多净资产为cpslongamt的1.088 2. 维持担保比例要充足）
           更正： 优先将该渠道资金的0.77的仓位加现金，全部分配至该渠道所具有的信用户进行交易
        8. 重要： 若有融券负债，则将该渠道的cpslongamt均放入macct.
        9. 重要： 渠道编程的变量命名以序列形式排列，按照字符串升序规则排列(capital source)。
        10. 信用户提供的空头暴露工具只有 etf 和 cps(个股)
        11. oacct 与 macct空头市值仅为mn策略使用
        12. ei策略无融资和融券，产品中存在的融资融券部分均分配给mn策略

        Note:
            1. 注意现有持仓是两个策略的合并持仓，需要按照比例分配。
            2. 本项目中资金的渠道分配是以营业部为主体，而非券商。（同一券商可能会有多个资金渠道）
            3. 数据库中的仓位比例为cpslongamt的比例
            4. 最后取整
            5. 若一产品出现多渠道分配情况，则该产品的caccts 与 macct 与 oaccts全部需要添加渠道标签

        思路：
            1. 先求EI的shape，剩下的都是MN的。
            2. 分配普通和信用时，采取信用户净资产最小原则（不低于最低维持担保比例）。（采用0.77 * 1.088 净资产放入信用户原则）
            3. 重要 算法顺序上，在确认了facct与oacct的NA后，再对证券户的各渠道的NA进行分配
            4. 期货手数在最后时进行整数化处理，
            5. 使用‘净值’思想处理budget
            6. 引入核心方程式求解： 1.净资产， 2. 暴露

        todo：
            1. 需要分析两融户中换仓资金的准确算法， 即 保证金制度交易下的详细算法（大课题）。
            2. 课题：策略分配环节的升级：
                1. 双策略 → 多策略
                2. 单一空头策略 → 指定空头策略
                3. 分配不同策略的目标持仓： 定比模式|最大总资产利用率模式 → 定比模式|最大总资产利用率模式|定值、定比模式
                answer:
                    1. dict_asset_allocation = {
                        src1: {'MN': 0.3, 'EI': 0.7, 'IPO': 65000000},
                        src2: {'IPO': 65000000}
                    }
                    在读取时，补充0
                    2. dict_strategy2short_strategy = {
                        'MN': {'index_future2adjust_exposure': 'IC'},
                        'EI' : {'index_future2adjust_exposure': 'IC'},
                        'IPO': {'index_future2adjust_exposure': 'IH'}
                    }
        """
        # 函数级 假设部分
        index_future = self.gv.index_future  # todo 可进一步抽象， 与空头策略有关
        dict_na_allocation = self.gv.col_na_allocation.find_one({'DataDate': self.str_today, 'PrdCode': self.prdcode})

        if dict_na_allocation:
            dict_na_allocation_saccts = dict_na_allocation['SecurityAccountsNetAssetAllocation']
            if dict_na_allocation_saccts:
                list_keys_na_allocation_saccts = list(dict_na_allocation_saccts.keys())
                list_keys_na_allocation_saccts.sort()
                list_values_na_allocation_saccts = [
                    dict_na_allocation_saccts[x] for x in list_keys_na_allocation_saccts
                ]

                # 注意，此处specified_na 是 分配到渠道对应证券户的净资产，而非渠道的净资产
                specified_na_in_saccts = 0
                idx_src = None
                for idx, value_na_allocation_saccts in enumerate(list_values_na_allocation_saccts):
                    if isinstance(value_na_allocation_saccts, str):
                        pass
                    elif value_na_allocation_saccts > 1:
                        specified_na_in_saccts = value_na_allocation_saccts
                        idx_src = idx
                    else:
                        continue

                # 讨论渠道数为2个的情况
                # # 重要课题新增： 货基分配： 满仓与非满仓；渠道1与渠道2；
                if len(dict_na_allocation_saccts) == 2:
                    src1 = list_keys_na_allocation_saccts[0]
                    src2 = list_keys_na_allocation_saccts[1]
                    # 假设：
                    ei_etflongamt_src1 = 0
                    ei_na_oaccts_src1 = 0
                    ei_capital_debt_src1 = 0
                    ei_liability_src1 = 0
                    ei_special_na_src1 = 0
                    ei_etflongamt_src2 = 0
                    ei_na_oaccts_src2 = 0
                    ei_capital_debt_src2 = 0
                    ei_liability_src2 = 0
                    ei_special_na_src2 = 0
                    ei_cpsshortamt_src1 = 0
                    ei_etfshortamt_src1 = 0
                    ei_net_exposure_from_oaccts_src1 = 0
                    ei_cpsshortamt_src2 = 0
                    ei_etfshortamt_src2 = 0
                    ei_net_exposure_from_oaccts_src2 = 0
                    ei_ce_from_ss_src1 = 0
                    ei_ce_from_ss_src2 = 0
                    mn_etflongamt_src1 = 0
                    mn_special_na_src1 = 0
                    mn_etflongamt_src2 = 0
                    mn_special_na_src2 = 0
                    # ## src1
                    dict_macct_basicinfo_src1 = self.gv.col_acctinfo.find_one(
                        {
                            'DataDate': self.str_today,
                            'PrdCode': self.prdcode,
                            'CapitalSource': src1,
                            'AcctType': 'm',
                            'RptMark': 1,
                            'SpecialAccountMark': 0,
                        }
                    )
                    mn_cash_from_ss_src1 = 0
                    mn_etfshortamt_src1 = 0
                    mn_cpsshortamt_src1 = 0
                    mn_capital_debt_in_macct_src1 = 0
                    mn_security_debt_in_macct_src1 = 0
                    if dict_macct_basicinfo_src1:
                        acctidbymxz_macct_src1 = dict_macct_basicinfo_src1['AcctIDByMXZ']

                        dict_bs_by_acctidbymxz = self.gv.col_bs_by_acctidbymxz.find_one(
                            {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_macct_src1}
                        )
                        mn_capital_debt_in_macct_src1 = dict_bs_by_acctidbymxz['CapitalDebt']
                        mn_security_debt_in_macct_src1 = (
                                dict_bs_by_acctidbymxz['CompositeShortAmt'] + dict_bs_by_acctidbymxz['ETFShortAmt']
                        )
                        list_dicts_formatted_holding = list(
                            self.gv.col_formatted_holding.find(
                                {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_macct_src1}
                            )
                        )
                        # todo 更新，在b/s中有分拆，不用重新累加， 需要在b/s表中添加卖出融券所得资金, 此处可改进
                        for dict_formatted_holding in list_dicts_formatted_holding:
                            sectype = dict_formatted_holding['SecurityType']
                            mn_cash_from_ss_delta = dict_formatted_holding['CashFromShortSelling']
                            mn_cash_from_ss_src1 += mn_cash_from_ss_delta
                            if sectype in ['ETF']:
                                mn_etfshortamt_delta = dict_formatted_holding['ShortAmt']
                                mn_etfshortamt_src1 += mn_etfshortamt_delta
                            elif sectype in ['CS']:
                                mn_cpsshortamt_delta = dict_formatted_holding['ShortAmt']
                                mn_cpsshortamt_src1 += mn_cpsshortamt_delta
                            else:
                                ValueError('Unknown security type when computing mn_etfshortamt_macct '
                                           'and mn_cpsshortamt_in_macct')
                        if self.dict_tgt_items['CashFromShortSellingInMarginAccount']:
                            mn_cash_from_ss_src1 = self.dict_tgt_items['CashFromShortSellingInMarginAccount']
                        if self.dict_tgt_items['ETFShortAmountInMarginAccount']:
                            mn_etfshortamt_src1 = self.dict_tgt_items['ETFShortAmountInMarginAccount']
                        if self.dict_tgt_items['CompositeShortAmountInMarginAccount']:
                            mn_cpsshortamt_src1 = self.dict_tgt_items['CompositeShortAmountInMarginAccount']

                    mn_ce_from_ss_src1 = mn_cash_from_ss_src1

                    # ## src2
                    dict_macct_basicinfo_src2 = self.gv.col_acctinfo.find_one(
                        {
                            'DataDate': self.str_today, 
                            'PrdCode': self.prdcode, 
                            'CapitalSource': src2,
                            'AcctType': 'm', 
                            'RptMark': 1,
                            'SpecialAccountMark': 0
                        }
                    )
                    mn_cash_from_ss_src2 = 0
                    mn_etfshortamt_src2 = 0
                    mn_cpsshortamt_src2 = 0
                    mn_capital_debt_in_macct_src2 = 0
                    mn_security_debt_in_macct_src2 = 0

                    if dict_macct_basicinfo_src2:
                        acctidbymxz_macct_src2 = dict_macct_basicinfo_src2['AcctIDByMXZ']

                        dict_bs_by_acctidbymxz = self.gv.col_bs_by_acctidbymxz.find_one(
                            {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_macct_src2}
                        )
                        mn_capital_debt_in_macct_src2 = dict_bs_by_acctidbymxz['CapitalDebt']
                        mn_security_debt_in_macct_src2 = (dict_bs_by_acctidbymxz['CompositeShortAmt']
                                                          + dict_bs_by_acctidbymxz['ETFShortAmt'])

                        list_dicts_formatted_holding = self.gv.col_formatted_holding.find(
                            {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_macct_src2}
                        )
                        for dict_formatted_holding in list_dicts_formatted_holding:
                            sectype = dict_formatted_holding['SecurityType']
                            mn_cash_from_ss_delta = dict_formatted_holding['CashFromShortSelling']
                            mn_cash_from_ss_src2 += mn_cash_from_ss_delta
                            if sectype in ['ETF']:
                                mn_etfshortamt_delta = dict_formatted_holding['ShortAmt']
                                mn_etfshortamt_src2 += mn_etfshortamt_delta
                            elif sectype in ['CS']:
                                mn_cpsshortamt_delta = dict_formatted_holding['ShortAmt']
                                mn_cpsshortamt_src2 += mn_cpsshortamt_delta
                            else:
                                ValueError('Unknown security type when computing mn_etfshortamt_macct '
                                           'and mn_cpsshortamt_in_macct')
                        if self.dict_tgt_items['CashFromShortSellingInMarginAccount']:
                            mn_cash_from_ss_src2 = self.dict_tgt_items['CashFromShortSellingInMarginAccount']
                        if self.dict_tgt_items['ETFShortAmountInMarginAccount']:
                            mn_etfshortamt_src2 = self.dict_tgt_items['ETFShortAmountInMarginAccount']
                        if self.dict_tgt_items['CompositeShortAmountInMarginAccount']:
                            mn_cpsshortamt_src2 = self.dict_tgt_items['CompositeShortAmountInMarginAccount']
                    mn_ce_from_ss_src2 = mn_cash_from_ss_src2

                    # 求oacct提供的空头暴露预算值与多头暴露预算值
                    # 求oacct账户中的存出保证金（net_asset）
                    # ## src1
                    list_dicts_oacct_basicinfo_src1 = list(
                        self.gv.col_acctinfo.find(
                            {
                                'DataDate': self.str_today,
                                'PrdCode': self.prdcode,
                                'AcctType': 'o',
                                'CapitalSource': src1
                            }
                        )
                    )
                    mn_net_exposure_from_oaccts_src1 = 0
                    mn_capital_debt_in_oaccts_src1 = 0
                    mn_ttasset_oaccts_src1 = 0
                    mn_liability_in_oaccts_src1 = 0
                    for dict_oacct_basicinfo_src1 in list_dicts_oacct_basicinfo_src1:
                        if dict_oacct_basicinfo_src1:
                            acctidbymxz_oacct = dict_oacct_basicinfo_src1['AcctIDByMXZ']
                            dict_exposure_analysis_by_acctidbymxz = self.gv.col_exposure_analysis_by_acctidbymxz.find_one(
                                {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_oacct}
                            )
                            net_exposure_from_oacct_delta = dict_exposure_analysis_by_acctidbymxz['NetExposure']
                            mn_net_exposure_from_oaccts_src1 += net_exposure_from_oacct_delta
                            dict_bs_by_acctidbymxz = self.gv.col_bs_by_acctidbymxz.find_one(
                                {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_oacct}
                            )
                            mn_ttasset_oacct_delta = dict_bs_by_acctidbymxz['TotalAsset']
                            mn_ttasset_oaccts_src1 += mn_ttasset_oacct_delta
                            mn_liability_oacct_delta = dict_bs_by_acctidbymxz['Liability']
                            mn_liability_in_oaccts_src1 += mn_liability_oacct_delta
                            mn_capital_debt_in_oaccts_delta = dict_bs_by_acctidbymxz['CapitalDebt']
                            mn_capital_debt_in_oaccts_src1 += mn_capital_debt_in_oaccts_delta

                    if self.dict_tgt_items['NetExposureFromOTCAccounts']:
                        mn_net_exposure_from_oaccts_src1 = self.dict_tgt_items['NetExposureFromOTCAccounts']

                    # ## src2
                    list_dicts_oacct_basicinfo_src2 = list(
                        self.gv.col_acctinfo.find(
                            {
                                'DataDate': self.str_today,
                                'PrdCode': self.prdcode,
                                'AcctType': 'o',
                                'CapitalSource': src2
                            }
                        )
                    )
                    mn_net_exposure_from_oaccts_src2 = 0
                    mn_capital_debt_in_oaccts_src2 = 0
                    mn_ttasset_oaccts_src2 = 0
                    mn_liability_in_oaccts_src2 = 0
                    for dict_oacct_basicinfo_src2 in list_dicts_oacct_basicinfo_src2:
                        if dict_oacct_basicinfo_src2:
                            acctidbymxz_oacct = dict_oacct_basicinfo_src2['AcctIDByMXZ']
                            dict_exposure_analysis_by_acctidbymxz = self.gv.col_exposure_analysis_by_acctidbymxz.find_one(
                                {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_oacct}
                            )
                            net_exposure_from_oacct_delta = dict_exposure_analysis_by_acctidbymxz['NetExposure']
                            mn_net_exposure_from_oaccts_src2 += net_exposure_from_oacct_delta
                            dict_bs_by_acctidbymxz = self.gv.col_bs_by_acctidbymxz.find_one(
                                {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_oacct}
                            )
                            mn_ttasset_oacct_delta = dict_bs_by_acctidbymxz['TotalAsset']
                            mn_ttasset_oaccts_src2 += mn_ttasset_oacct_delta
                            mn_liability_oacct_delta = dict_bs_by_acctidbymxz['Liability']
                            mn_liability_in_oaccts_src2 += mn_liability_oacct_delta
                            mn_capital_debt_in_oaccts_delta = dict_bs_by_acctidbymxz['CapitalDebt']
                            mn_capital_debt_in_oaccts_src2 += mn_capital_debt_in_oaccts_delta

                    if self.dict_tgt_items['NetExposureFromOTCAccounts']:
                        mn_net_exposure_from_oaccts_src2 = self.dict_tgt_items['NetExposureFromOTCAccounts']

                    # 未知量`
                    # 注：未知量iclots不分src1与src2, 而采取代数式方式替换（基于facct的分配逻辑是”再分配独立“逻辑考虑）
                    #    即： 对期指的分配跳过渠道分配的步骤（分配步骤： 渠道-策略-项目）
                    ei_cpslongamt_src1 = Symbol('ei_cpslongamt_src1', real=True, nonnegative=True)
                    ei_ce_from_cash_available_src1 = Symbol('ei_ce_from_cash_available_src1', real=True)
                    mn_cpslongamt_src1 = Symbol('mn_cpslongamt_src1', real=True, nonnegative=True)
                    mn_ce_from_cash_available_src1 = Symbol('mn_ce_from_cash_available_src1', real=True,)
                    na_src1_tgt = Symbol('na_src1_tgt', real=True, nonnegative=True)

                    ei_cpslongamt_src2 = Symbol('ei_cpslongamt_src2', real=True, nonnegative=True)
                    ei_ce_from_cash_available_src2 = Symbol('ei_ce_from_cash_available_src2', real=True)
                    mn_cpslongamt_src2 = Symbol('mn_cpslongamt_src2', real=True, nonnegative=True)
                    mn_ce_from_cash_available_src2 = Symbol('mn_ce_from_cash_available_src2', real=True)
                    na_src2_tgt = Symbol('na_src2_tgt', real=True, nonnegative=True)

                    ei_iclots = Symbol('ei_iclots', real=True)
                    mn_iclots = Symbol('mn_iclots', real=True)

                    list_eqs_2b_solved = []

                    # 代数式
                    ei_na_src1_tgt = na_src1_tgt * self.dict_strategies_allocation['EI']
                    ei_na_src2_tgt = na_src2_tgt * self.dict_strategies_allocation['EI']
                    mn_na_src1_tgt = na_src1_tgt * self.dict_strategies_allocation['MN']
                    mn_na_src2_tgt = na_src2_tgt * self.dict_strategies_allocation['MN']

                    if specified_na_in_saccts > 0:  # 定值算法
                        # 代数式
                        # 定值算法中，由于给定了单组证券账户的目标净资产，并没有给出期货户在各渠道的资产分配，以至于需要假设期货的资产分配方式
                        # 如何假设呢，该假设是随意的，没有约束条件的假设
                        # 假设：定值渠道的期货资产为0（仅保证有证券账户的即可）
                        if idx_src == 0:
                            ei_iclots_src1 = 0
                            mn_iclots_src1 = 0
                            ei_iclots_src2 = ei_iclots - ei_iclots_src1
                            mn_iclots_src2 = mn_iclots - mn_iclots_src1
                        elif idx_src == 1:
                            ei_iclots_src2 = 0
                            mn_iclots_src2 = 0
                            ei_iclots_src1 = ei_iclots - ei_iclots_src2
                            mn_iclots_src1 = mn_iclots - mn_iclots_src2
                        else:
                            raise ValueError('Unknown idx_src when get specified account index.')
                    else:  # 定比算法
                        list_tgt_na_allocation = []
                        for value_na_allocation_saccts in list_values_na_allocation_saccts:
                            tgt_na_allocation = self.prdna_tgt * value_na_allocation_saccts
                            list_tgt_na_allocation.append(tgt_na_allocation)
                        # 代数式：
                        # 货基分配/期指分配： 对货基和期指在不同渠道间分配
                        # 原则：
                        #   1. 满仓状态下，非信用户渠道中不留现金。
                        #   2. 不满仓状态下，非信用户渠道的各账户资金与满仓状态下的各账户资金相同。

                        # 在多渠道且有货基的条件下，产品的各渠道的货基值，受各渠道分配到的期指数量影响
                        # 如何假设呢，该假设是随意的，没有约束条件的假设
                        # 假设： 分配比例为渠道比例(定比模式)
                        # 需求：将全部货基放到有信用户的渠道的普通户中

                        ei_iclots_src1 = ei_iclots * list_values_na_allocation_saccts[0]
                        ei_iclots_src2 = ei_iclots * list_values_na_allocation_saccts[1]
                        mn_iclots_src1 = mn_iclots * list_values_na_allocation_saccts[0]
                        mn_iclots_src2 = mn_iclots * list_values_na_allocation_saccts[1]

                        eq_na_src1_tgt = na_src1_tgt - list_tgt_na_allocation[0]
                        eq_na_src2_tgt = na_src2_tgt - list_tgt_na_allocation[1]
                        list_eqs_2b_solved.append(eq_na_src1_tgt)
                        list_eqs_2b_solved.append(eq_na_src2_tgt)

                    # 方程-双模式计算补充
                    if self.tgt_cpspct == 'max':
                        eq_ei_ce_src1 = ei_ce_from_cash_available_src1
                        eq_ei_ce_src2 = ei_ce_from_cash_available_src2
                        eq_mn_ce_src1 = mn_ce_from_cash_available_src1
                        eq_mn_ce_src2 = mn_ce_from_cash_available_src2
                        list_eqs_2b_solved.append(eq_ei_ce_src1)
                        list_eqs_2b_solved.append(eq_ei_ce_src2)
                        list_eqs_2b_solved.append(eq_mn_ce_src1)
                        list_eqs_2b_solved.append(eq_mn_ce_src2)
                    else:
                        eq_ei_cpslongamt_tgt = (
                                ei_cpslongamt_src1 + ei_cpslongamt_src2 - self.ei_na_tgt * self.tgt_cpspct
                        )
                        eq_mn_cpslongamt_tgt = (
                                mn_cpslongamt_src1 + mn_cpslongamt_src2 - self.mn_na_tgt * self.tgt_cpspct
                        )
                        list_eqs_2b_solved.append(eq_ei_cpslongamt_tgt)
                        list_eqs_2b_solved.append(eq_mn_cpslongamt_tgt)

                        if specified_na_in_saccts > 0:  # 定值算法补充方程
                            # 由于目前对ei策略的cps与mn策略的cps不做区分，故对同一渠道下不同策略对应的cps的分配没有要求
                            # todo 故暂且假设ei_cpslongamt_src1 与 mn_cpslongamt_src1 的比例为策略比例(EI:MN)
                            # todo 即定值渠道中的ei_cpslongamt 与 mn_cpslongamt_sr1 为定值
                            # todo 注意： 当定值渠道分配，策略分配同时出现时，算法不严谨，需要改进(非定值渠道可能出现负值）
                            # todo 先填满定值渠道的权益
                            # 定值算法中，由于给定了单组证券账户的目标净资产，并没有给出货币基金的值，需要分配。再解一次方程组
                            # 如何假设呢，该假设是随意的，没有约束条件的假设
                            # 假设：若产品需要的cpslongamt*1.0889小于指定证券账户的净资产，则，闲置资金买货基。另一账户中钱全部买货基
                            # 假设：若产品需要的cpslongamt*1.0889大于指定证券账户的净资产，则，该账户中的货币资金为0，另一账户中为cps余额。
                            if idx_src == 0:
                                if self.prdna_tgt * self.tgt_cpspct > specified_na_in_saccts:
                                    eq_ei_cpslongamt_allocation_src1 = (
                                        ei_cpslongamt_src1 * (1 + self.gv.flt_cash2cpslongamt)
                                        - specified_na_in_saccts * self.dict_strategies_allocation['EI']
                                    )
                                    eq_mn_cpslongamt_allocation_src1 = (
                                        mn_cpslongamt_src1 * (1 + self.gv.flt_cash2cpslongamt)
                                        - specified_na_in_saccts * self.dict_strategies_allocation['MN']
                                    )
                                    list_eqs_2b_solved.append(eq_ei_cpslongamt_allocation_src1)
                                    list_eqs_2b_solved.append(eq_mn_cpslongamt_allocation_src1)

                                    eq_ei_ce_from_cash_available_src1 = ei_ce_from_cash_available_src1
                                    eq_mn_ce_from_cash_available_src1 = mn_ce_from_cash_available_src1
                                    list_eqs_2b_solved.append(eq_ei_ce_from_cash_available_src1)
                                    list_eqs_2b_solved.append(eq_mn_ce_from_cash_available_src1)
                                    # 约束总资产 = na_src1 + na_sr2
                                    eq_prdna_tgt = na_src1_tgt + na_src2_tgt - self.prdna_tgt
                                    list_eqs_2b_solved.append(eq_prdna_tgt)
                                else:
                                    eq_ei_cpslongamt_allocation_src1 = (
                                        self.prdna_tgt
                                        * self.gv.flt_cash2cpslongamt
                                        * self.dict_strategies_allocation['EI']
                                        - ei_cpslongamt_src1
                                    )
                                    eq_mn_cpslongamt_allocation_src1 = (
                                        self.prdna_tgt
                                        * self.gv.flt_cash2cpslongamt
                                        * self.dict_strategies_allocation['MN']
                                        - mn_cpsshortamt_src1
                                    )
                                    list_eqs_2b_solved.append(eq_ei_cpslongamt_allocation_src1)
                                    list_eqs_2b_solved.append(eq_mn_cpslongamt_allocation_src1)
                                    ce_from_cash_available_src1 = (
                                            specified_na_in_saccts - self.prdna_tgt * (1 + self.gv.flt_cash2cpslongamt)
                                    )
                                    eq_ei_ce_from_cash_available_src1 = (
                                            ce_from_cash_available_src1 * self.dict_strategies_allocation['EI']
                                            - ei_ce_from_cash_available_src1
                                    )
                                    eq_mn_ce_from_cash_available_src1 = (
                                            ce_from_cash_available_src1 * self.dict_strategies_allocation['MN']
                                            - mn_ce_from_cash_available_src1
                                    )
                                    list_eqs_2b_solved.append(eq_ei_ce_from_cash_available_src1)
                                    list_eqs_2b_solved.append(eq_mn_ce_from_cash_available_src1)

                                    # 约束总资产 = na_src1 + na_sr2
                                    eq_prdna_tgt = na_src1_tgt + na_src2_tgt - self.prdna_tgt
                                    list_eqs_2b_solved.append(eq_prdna_tgt)

                            elif idx_src == 1:
                                if self.prdna_tgt * self.tgt_cpspct > specified_na_in_saccts:
                                    eq_ei_cpslongamt_allocation_src2 = (
                                            ei_cpslongamt_src2 * (1 + self.gv.flt_cash2cpslongamt)
                                            - specified_na_in_saccts * self.dict_strategies_allocation['EI']
                                    )
                                    eq_mn_cpslongamt_allocation_src2 = (
                                            mn_cpslongamt_src2 * (1 + self.gv.flt_cash2cpslongamt)
                                            - specified_na_in_saccts * self.dict_strategies_allocation['MN']
                                    )
                                    list_eqs_2b_solved.append(eq_ei_cpslongamt_allocation_src2)
                                    list_eqs_2b_solved.append(eq_mn_cpslongamt_allocation_src2)

                                    eq_ei_ce_from_cash_available_src2 = ei_ce_from_cash_available_src2
                                    eq_mn_ce_from_cash_available_src2 = mn_ce_from_cash_available_src2
                                    list_eqs_2b_solved.append(eq_ei_ce_from_cash_available_src2)
                                    list_eqs_2b_solved.append(eq_mn_ce_from_cash_available_src2)

                                    # 约束总资产 = na_src1 + na_sr2
                                    eq_prdna_tgt = na_src1_tgt + na_src2_tgt - self.prdna_tgt
                                    list_eqs_2b_solved.append(eq_prdna_tgt)

                                else:
                                    eq_ei_cpslongamt_allocation_src2 = (
                                            self.prdna_tgt
                                            * self.gv.flt_cash2cpslongamt
                                            * self.dict_strategies_allocation['EI']
                                            - ei_cpslongamt_src2
                                    )
                                    eq_mn_cpslongamt_allocation_src2 = (
                                            self.prdna_tgt
                                            * self.gv.flt_cash2cpslongamt
                                            * self.dict_strategies_allocation['MN']
                                            - mn_cpsshortamt_src2
                                    )
                                    list_eqs_2b_solved.append(eq_ei_cpslongamt_allocation_src2)
                                    list_eqs_2b_solved.append(eq_mn_cpslongamt_allocation_src2)
                                    ce_from_cash_available_src2 = (
                                            specified_na_in_saccts - self.prdna_tgt * (1 + self.gv.flt_cash2cpslongamt)
                                    )
                                    eq_ei_ce_from_cash_available_src2 = (
                                            ce_from_cash_available_src2 * self.dict_strategies_allocation['EI']
                                            - ei_ce_from_cash_available_src2
                                    )
                                    eq_mn_ce_from_cash_available_src2 = (
                                            ce_from_cash_available_src2 * self.dict_strategies_allocation['MN']
                                            - mn_ce_from_cash_available_src2
                                    )
                                    list_eqs_2b_solved.append(eq_ei_ce_from_cash_available_src2)
                                    list_eqs_2b_solved.append(eq_mn_ce_from_cash_available_src2)
                                    # 约束总资产 = na_src1 + na_sr2
                                    eq_prdna_tgt = na_src1_tgt + na_src2_tgt - self.prdna_tgt
                                    list_eqs_2b_solved.append(eq_prdna_tgt)
                            else:
                                raise ValueError('Unknown idx_src.')

                        else:
                            # 定比方法补充方程
                            # 在定比分配渠道算法下，当指定的仓位小于max仓位（未满仓）时，在满足产品仓位达标后，还需分配渠道
                            # 假设： 分配比例为渠道比例
                            # # 找出信用户所在渠道的编号， 并将在满仓状态（0.77）下非信用户渠道的货基数量指定为0
                            # dict_acctinfo_macct = self.gv.col_acctinfo.find_one(
                            #     {
                            #         'DataDate': self.str_today,
                            #         'AcctType': 'm',
                            #         'PrdCode': self.prdcode,
                            #         'AcctStatus': 'T',
                            #         'RptMark': 1,
                            #         'SpecialAccountMark': 0,
                            #     }
                            # )
                            # capitalsrc = dict_acctinfo_macct['CapitalSource']
                            # idx_capitalsrc_in_na_allocation_saccts = list_keys_na_allocation_saccts.index(capitalsrc)
                            # if idx_capitalsrc_in_na_allocation_saccts == 0:  # 信用户在渠道1， 渠道2的ce_from_ca为0
                            #     eq_ce_allocation = ei_ce_from_cash_available_src2
                            #     list_eqs_2b_solved.append(eq_ce_allocation)
                            # elif idx_capitalsrc_in_na_allocation_saccts == 1:  # 信用户在渠道2
                            #     eq_ce_allocation = ei_ce_from_cash_available_src1
                            #     list_eqs_2b_solved.append(eq_ce_allocation)
                            # else:
                            #     raise ValueError('Unknown capital sources')

                            eq_ei_cpslongamt_allocation_src1 = (
                                list_values_na_allocation_saccts[0] * (ei_cpslongamt_src1 + ei_cpslongamt_src2)
                                - ei_cpslongamt_src1
                            )
                            eq_ei_cpslongamt_allocation_src2 = (
                                list_values_na_allocation_saccts[1] * (ei_cpslongamt_src1 + ei_cpslongamt_src2)
                                - ei_cpslongamt_src2
                            )
                            eq_mn_cpslongamt_allocation_src1 = (
                                list_values_na_allocation_saccts[0] * (mn_cpslongamt_src1 + mn_cpslongamt_src2)
                                - mn_cpslongamt_src1
                            )
                            eq_mn_cpslongamt_allocation_src2 = (
                                list_values_na_allocation_saccts[1] * (mn_cpslongamt_src1 + mn_cpslongamt_src2)
                                - mn_cpslongamt_src2
                                )
                            list_eqs_2b_solved.append(eq_ei_cpslongamt_allocation_src1)
                            list_eqs_2b_solved.append(eq_ei_cpslongamt_allocation_src2)
                            list_eqs_2b_solved.append(eq_mn_cpslongamt_allocation_src1)
                            list_eqs_2b_solved.append(eq_mn_cpslongamt_allocation_src2)

                    # 核心方程组-净资产
                    eq_ei_na_src1 = (
                            ei_cpslongamt_src1 * (1 + self.gv.flt_cash2cpslongamt)
                            + ei_ce_from_cash_available_src1
                            + ei_ce_from_ss_src1
                            + ei_etflongamt_src1
                            + ei_special_na_src1
                            + abs(ei_iclots_src1) * self.gv.dict_index_future2internal_required_na_per_lot[index_future]
                            + ei_na_oaccts_src1
                            + ei_capital_debt_src1
                            - ei_na_src1_tgt
                            - ei_liability_src1
                    )

                    eq_ei_na_src2 = (
                            ei_cpslongamt_src2 * (1 + self.gv.flt_cash2cpslongamt)
                            + ei_ce_from_cash_available_src2
                            + ei_ce_from_ss_src2
                            + ei_etflongamt_src2
                            + ei_special_na_src2
                            + abs(ei_iclots_src2) * self.gv.dict_index_future2internal_required_na_per_lot[index_future]
                            + ei_na_oaccts_src2
                            + ei_capital_debt_src2
                            - ei_na_src2_tgt
                            - ei_liability_src2
                    )
                    list_eqs_2b_solved.append(eq_ei_na_src1)
                    list_eqs_2b_solved.append(eq_ei_na_src2)

                    eq_mn_na_src1 = (
                            mn_cpslongamt_src1 * (1 + self.gv.flt_cash2cpslongamt)
                            + mn_ce_from_cash_available_src1
                            + mn_ce_from_ss_src1
                            + mn_etflongamt_src1
                            + mn_special_na_src1
                            + abs(mn_iclots_src1) * self.gv.dict_index_future2internal_required_na_per_lot[index_future]
                            + mn_ttasset_oaccts_src1
                            - mn_na_src1_tgt
                            - mn_capital_debt_in_macct_src1
                            - mn_security_debt_in_macct_src1
                            - mn_liability_in_oaccts_src1
                    )

                    eq_mn_na_src2 = (
                            mn_cpslongamt_src2 * (1 + self.gv.flt_cash2cpslongamt)
                            + mn_ce_from_cash_available_src2
                            + mn_ce_from_ss_src2
                            + mn_etflongamt_src2
                            + mn_special_na_src2
                            + abs(mn_iclots_src2) * self.gv.dict_index_future2internal_required_na_per_lot[index_future]
                            + mn_ttasset_oaccts_src2
                            - mn_na_src2_tgt
                            - mn_capital_debt_in_macct_src2
                            - mn_security_debt_in_macct_src2
                            - mn_liability_in_oaccts_src2

                    )
                    list_eqs_2b_solved.append(eq_mn_na_src1)
                    list_eqs_2b_solved.append(eq_mn_na_src2)

                    # 核心方程组-暴露
                    eq_ei_exposure = (
                            ei_cpslongamt_src1
                            + ei_etflongamt_src1
                            + ei_iclots_src1 * self.gv.dict_index_future2spot_exposure_per_lot[index_future]
                            - ei_cpsshortamt_src1
                            - ei_etfshortamt_src1
                            + ei_net_exposure_from_oaccts_src1

                            + ei_cpslongamt_src2
                            + ei_etflongamt_src2
                            + ei_iclots_src2 * self.gv.dict_index_future2spot_exposure_per_lot[index_future]
                            - ei_cpsshortamt_src2
                            - ei_etfshortamt_src2
                            + ei_net_exposure_from_oaccts_src2

                            - self.ei_na_tgt * 0.99
                                      )
                    list_eqs_2b_solved.append(eq_ei_exposure)

                    eq_mn_exposure = (
                        mn_cpslongamt_src1
                        + mn_etflongamt_src1
                        + mn_iclots_src1 * self.gv.dict_index_future2spot_exposure_per_lot[index_future]
                        - mn_cpsshortamt_src1
                        - mn_etfshortamt_src1
                        + mn_net_exposure_from_oaccts_src1

                        + mn_cpslongamt_src2
                        + mn_etflongamt_src2
                        + mn_iclots_src2 * self.gv.dict_index_future2spot_exposure_per_lot[index_future]
                        - mn_cpsshortamt_src2
                        - mn_etfshortamt_src2
                        + mn_net_exposure_from_oaccts_src2
                    )
                    list_eqs_2b_solved.append(eq_mn_exposure)

                    # 解核心方程组
                    list_tuples_eqs_solve = solve(list_eqs_2b_solved,
                                                  ei_cpslongamt_src1, ei_ce_from_cash_available_src1,
                                                  mn_cpslongamt_src1, mn_ce_from_cash_available_src1,
                                                  na_src1_tgt,
                                                  ei_cpslongamt_src2, ei_ce_from_cash_available_src2,
                                                  mn_cpslongamt_src2, mn_ce_from_cash_available_src2,
                                                  na_src2_tgt, ei_iclots, mn_iclots)
                    tuple_eqs_solve = list_tuples_eqs_solve[0]
                    ei_cpslongamt_src1 = float(tuple_eqs_solve[0])
                    ei_ce_from_cash_available_src1 = float(tuple_eqs_solve[1])
                    mn_cpslongamt_src1 = float(tuple_eqs_solve[2])
                    mn_ce_from_cash_available_src1 = float(tuple_eqs_solve[3])
                    ei_cpslongamt_src2 = float(tuple_eqs_solve[5])
                    ei_ce_from_cash_available_src2 = float(tuple_eqs_solve[6])
                    mn_cpslongamt_src2 = float(tuple_eqs_solve[7])
                    mn_ce_from_cash_available_src2 = float(tuple_eqs_solve[8])
                    ei_iclots = float(tuple_eqs_solve[10])
                    mn_iclots = float(tuple_eqs_solve[11])

                    iclots_total = int(ei_iclots) + round(mn_iclots)
                    na_faccts = abs(iclots_total) * self.gv.dict_index_future2internal_required_na_per_lot[index_future]
                    cpslongamt_src1 = ei_cpslongamt_src1 + mn_cpslongamt_src1
                    cpslongamt_src2 = ei_cpslongamt_src2 + mn_cpslongamt_src2
                    ce_from_cash_available_src1 = ei_ce_from_cash_available_src1 + mn_ce_from_cash_available_src1
                    ce_from_cash_available_src2 = ei_ce_from_cash_available_src2 + mn_ce_from_cash_available_src2

                    # 资金分配(cacct 与 macct)
                    # 公司内部分配算法：信用户如有负债则在信用户中留足够且仅够开满仓的净资产
                    acctidbymxz_cacct_src1 = self.gv.col_acctinfo.find_one(
                        {
                            'PrdCode': self.prdcode,
                            'CapitalSource': list_keys_na_allocation_saccts[0],
                            'AcctType': 'c',
                            'SpecialAccountMark': 0,
                        }
                    )['AcctIDByMXZ']
                    dict_acctidbymxz_macct_src1 = self.gv.col_acctinfo.find_one(
                        {
                            'PrdCode': self.prdcode,
                            'CapitalSource': list_keys_na_allocation_saccts[0],
                            'AcctType': 'm',
                            'SpecialAccountMark': 0,
                            'AcctStatus': 'T'
                        }
                    )
                    if dict_acctidbymxz_macct_src1:
                        acctidbymxz_macct_src1 = dict_acctidbymxz_macct_src1['AcctIDByMXZ']
                    else:
                        acctidbymxz_macct_src1 = None

                    acctidbymxz_cacct_src2 = self.gv.col_acctinfo.find_one(
                        {
                            'PrdCode': self.prdcode,
                            'CapitalSource': list_keys_na_allocation_saccts[1],
                            'AcctType': 'c',
                            'SpecialAccountMark': 0,
                        }
                    )['AcctIDByMXZ']
                    dict_acctidbymxz_macct_src2 = self.gv.col_acctinfo.find_one(
                        {
                            'PrdCode': self.prdcode,
                            'CapitalSource': list_keys_na_allocation_saccts[1],
                            'AcctType': 'm',
                            'SpecialAccountMark': 0,
                            'AcctStatus': 'T'
                        }
                    )

                    if dict_acctidbymxz_macct_src2:
                        acctidbymxz_macct_src2 = dict_acctidbymxz_macct_src2['AcctIDByMXZ']
                    else:
                        acctidbymxz_macct_src2 = None

                    cpslongamt_in_macct_src1 = None
                    na_macct_src1 = None
                    cpslongamt_in_macct_src2 = None
                    na_macct_src2 = None
                    cash_available_in_macct_src1 = None
                    cash_available_in_macct_src2 = None
                    # todo 此处假设： 若macct中不满仓，则可用于交易的现金对应的货基应全部转至cacct，故macct中ce_from_cash_available为0
                    # todo 注意，需要分情况讨论： 当担保品充足时，当担保品不足时
                    # todo 当担保品充足时，macct总资产 = (
                    #  卖出融券所得资金 + 目标持仓市值 * (1 + self.gv.flt_cash2cpslongamt) + 用于补充担保品的ce
                    #  )
                    # todo 当担保品充足时，macct净资产 = macct总资产 - macct负债
                    # todo 信用户中可用资金的锁定
                    ce_from_cash_available_in_macct_src1 = 0
                    ce_from_cash_available_in_macct_src2 = 0
                    ce_from_cash_from_ss_src1 = mn_ce_from_ss_src1
                    ce_from_cash_from_ss_src2 = mn_ce_from_ss_src2

                    # 如有信用户，则该渠道按照最少净资产原则放在信用户里交易
                    dict_macct_basicinfo = self.gv.col_acctinfo.find_one(
                        {
                            'DataDate': self.str_today,
                            'PrdCode': self.prdcode,
                            'AcctType': 'm',
                            'RptMark': 1,
                            'SpecialAccountMark': 0,
                            'AcctStatus': 'T'
                        }
                    )
                    if dict_macct_basicinfo:
                        capital_source = dict_macct_basicinfo['CapitalSource']
                        idx_capital_source = list_keys_na_allocation_saccts.index(capital_source)
                        if idx_capital_source == 0:  # 第一个渠道为信用户渠道，第二个渠道为普通户渠道
                            dict_bs_by_acctidbymxz = self.gv.col_bs_by_acctidbymxz.find_one(
                                {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_macct_src1}
                            )
                            ttasset_macct = dict_bs_by_acctidbymxz['TotalAsset']
                            liability_macct = dict_bs_by_acctidbymxz['Liability']
                            if liability_macct:
                                margin_maintenance_ratio = ttasset_macct / liability_macct
                            else:
                                margin_maintenance_ratio = 999999999
                            if margin_maintenance_ratio <= 1.5:
                                print(
                                    f'Warning, margin maintenance ratio {margin_maintenance_ratio}, '
                                    f'may be not sufficient.'
                                )

                            cpslongamt_in_macct_src1 = cpslongamt_src1
                            cash_available_in_macct_src1 = cpslongamt_src1 * self.gv.flt_cash2cpslongamt
                            na_cacct_src1 = ce_from_cash_available_src1
                            na_macct_src1 = (
                                    cpslongamt_in_macct_src1
                                    + cash_available_in_macct_src1
                                    + ce_from_cash_from_ss_src1
                                    - liability_macct
                            )
                            cpslongamt_in_cacct_src1 = 0
                            if na_cacct_src1 > 2500000:
                                ce_in_cacct_src1 = na_cacct_src1 - 2500000
                                cash_available_in_cacct_src1 = 2500000
                            else:
                                ce_in_cacct_src1 = 0
                                cash_available_in_cacct_src1 = na_cacct_src1

                            # 写第二个渠道（非信用户渠道）的数据
                            cpslongamt_in_cacct_src2 = cpslongamt_src2
                            cash_available_in_cacct_src2 = cpslongamt_in_cacct_src2 * self.gv.flt_cash2cpslongamt
                            ce_in_cacct_src2 = ce_from_cash_available_src2
                            na_cacct_src2 = cpslongamt_src2 + ce_in_cacct_src2 + cash_available_in_cacct_src2

                        elif idx_capital_source == 1:
                            dict_bs_by_acctidbymxz = self.gv.col_bs_by_acctidbymxz.find_one(
                                {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_macct_src2}
                            )
                            ttasset_macct = dict_bs_by_acctidbymxz['TotalAsset']
                            liability_macct = dict_bs_by_acctidbymxz['Liability']
                            if liability_macct:
                                margin_maintenance_ratio = ttasset_macct / liability_macct
                            else:
                                margin_maintenance_ratio = 999999999
                            if margin_maintenance_ratio <= 1.5:
                                print(
                                    f'Warning, margin maintenance ratio {margin_maintenance_ratio}, '
                                    f'may be not sufficient.'
                                )

                            cpslongamt_in_macct_src2 = cpslongamt_src2
                            cash_available_in_macct_src2 = cpslongamt_src2 * self.gv.flt_cash2cpslongamt
                            na_cacct_src2 = ce_from_cash_available_src2
                            na_macct_src2 = (
                                    cpslongamt_in_macct_src2
                                    + cash_available_in_macct_src2
                                    + ce_from_cash_from_ss_src2
                                    - liability_macct
                            )

                            cpslongamt_in_cacct_src2 = 0
                            if na_cacct_src2 > 2500000:
                                ce_in_cacct_src2 = na_cacct_src2 - 2500000
                                cash_available_in_cacct_src2 = 2500000
                            else:
                                ce_in_cacct_src2 = 0
                                cash_available_in_cacct_src2 = na_cacct_src2

                            # 写第一个渠道（非信用户渠道）的数据
                            cpslongamt_in_cacct_src1 = cpslongamt_src1
                            cash_available_in_cacct_src1 = cpslongamt_in_cacct_src1 * self.gv.flt_cash2cpslongamt
                            ce_in_cacct_src1 = ce_from_cash_available_src1
                            na_cacct_src1 = cpslongamt_src1 + ce_in_cacct_src1 + cash_available_in_cacct_src1

                        else:
                            raise ValueError('Unknown capital source when allocate sources.')

                    else:
                        cpslongamt_in_cacct_src1 = cpslongamt_src1
                        cpslongamt_in_cacct_src2 = cpslongamt_src2
                        ce_in_cacct_src1 = ce_from_cash_available_src1
                        ce_in_cacct_src2 = ce_from_cash_available_src2
                        cash_available_in_cacct_src1 = cpslongamt_in_cacct_src1 * self.gv.flt_cash2cpslongamt
                        cash_available_in_cacct_src2 = cpslongamt_in_cacct_src2 * self.gv.flt_cash2cpslongamt
                        na_cacct_src1 = cpslongamt_src1 + ce_in_cacct_src1 + cash_available_in_cacct_src1
                        na_cacct_src2 = cpslongamt_src2 + ce_in_cacct_src2 + cash_available_in_cacct_src2

                    list_dicts_bgt_secaccts = [
                        {
                            'DataDate': self.str_today,
                            'PrdCode': self.prdcode,
                            'AcctIDByMXZ': acctidbymxz_cacct_src1,
                            'NAV': na_cacct_src1,
                            'CPSLongAmt': cpslongamt_in_cacct_src1,
                            'ICLots': None,
                            'CashAvailable': cash_available_in_cacct_src1,
                            'CEFromCashFromSS': None,
                            'CEFromCashAvailable': ce_in_cacct_src1,
                        },
                        {
                            'DataDate': self.str_today,
                            'PrdCode': self.prdcode,
                            'AcctIDByMXZ': acctidbymxz_cacct_src2,
                            'NAV': na_cacct_src2,
                            'CPSLongAmt': cpslongamt_in_cacct_src2,
                            'ICLots': None,
                            'CashAvailable': cash_available_in_cacct_src2,
                            'CEFromCashFromSS': None,
                            'CEFromCashAvailable': ce_in_cacct_src2,
                        },
                        {
                            'DataDate': self.str_today,
                            'PrdCode': self.prdcode,
                            'AcctIDByMXZ': f'{self.prdcode}_faccts',
                            'NAV': na_faccts,
                            'CPSLongAmt': None,
                            'ICLots': iclots_total,
                            'CEFromCashFromSS': None,
                            'CEFromCashAvailable': None,
                        }
                    ]

                    dict_bgt_macct_src1 = {
                        'DataDate': self.str_today,
                        'PrdCode': self.prdcode,
                        'AcctIDByMXZ': acctidbymxz_macct_src1,
                        'NAV': na_macct_src1,
                        'CPSLongAmt': cpslongamt_in_macct_src1,
                        'ICLots': None,
                        'CashAvailable': cash_available_in_macct_src1,
                        'CEFromCashFromSS': ce_from_cash_from_ss_src1,
                        'CEFromCashAvailable': ce_from_cash_available_in_macct_src1,
                    }
                    dict_bgt_macct_src2 = {
                        'DataDate': self.str_today,
                        'PrdCode': self.prdcode,
                        'AcctIDByMXZ': acctidbymxz_macct_src2,
                        'NAV': na_macct_src2,
                        'CPSLongAmt': cpslongamt_in_macct_src2,
                        'ICLots': None,
                        'CashAvailable': cash_available_in_macct_src2,
                        'CEFromCashFromSS': ce_from_cash_from_ss_src2,
                        'CEFromCashAvailable': ce_from_cash_available_in_macct_src2,
                    }
                    if acctidbymxz_macct_src1:
                        list_dicts_bgt_secaccts.append(dict_bgt_macct_src1)
                    if acctidbymxz_macct_src2:
                        list_dicts_bgt_secaccts.append(dict_bgt_macct_src2)

                    self.list_dicts_bgt_by_acctidbymxz += list_dicts_bgt_secaccts
                    self.allocate_faccts(iclots_total)

                # 讨论渠道为3个的情况
                elif len(dict_na_allocation_saccts) == 3:

                    # 假设：
                    ei_etflongamt_src1 = 0
                    ei_na_oaccts_src1 = 0
                    ei_capital_debt_src1 = 0
                    ei_liability_src1 = 0
                    ei_special_na_src1 = 0
                    ei_cpsshortamt_src1 = 0
                    ei_etfshortamt_src1 = 0
                    ei_net_exposure_from_oaccts_src1 = 0
                    ei_ce_from_ss_src1 = 0
                    mn_etflongamt_src1 = 0
                    mn_special_na_src1 = 0

                    ei_etflongamt_src2 = 0
                    ei_na_oaccts_src2 = 0
                    ei_capital_debt_src2 = 0
                    ei_liability_src2 = 0
                    ei_special_na_src2 = 0
                    ei_cpsshortamt_src2 = 0
                    ei_etfshortamt_src2 = 0
                    ei_net_exposure_from_oaccts_src2 = 0
                    ei_ce_from_ss_src2 = 0
                    mn_etflongamt_src2 = 0
                    mn_special_na_src2 = 0

                    ei_etflongamt_src3 = 0
                    ei_na_oaccts_src3 = 0
                    ei_capital_debt_src3 = 0
                    ei_liability_src3 = 0
                    ei_special_na_src3 = 0
                    ei_cpsshortamt_src3 = 0
                    ei_etfshortamt_src3 = 0
                    ei_net_exposure_from_oaccts_src3 = 0
                    ei_ce_from_ss_src3 = 0
                    mn_etflongamt_src3 = 0
                    mn_special_na_src3 = 0

                    src1 = list_keys_na_allocation_saccts[0]
                    src2 = list_keys_na_allocation_saccts[1]
                    src3 = list_keys_na_allocation_saccts[2]

                    # macct - src1
                    dict_macct_basicinfo_src1 = self.gv.col_acctinfo.find_one(
                        {
                            'DataDate': self.str_today,
                            'PrdCode': self.prdcode,
                            'CapitalSource': src1,
                            'AcctType': 'm',
                            'AcctStatus': 'T',
                            'RptMark': 1,
                            'SpecialAccountMark': 0,
                        }
                    )
                    mn_cash_from_ss_src1 = 0
                    mn_etfshortamt_src1 = 0
                    mn_cpsshortamt_src1 = 0
                    mn_capital_debt_in_macct_src1 = 0
                    mn_security_debt_in_macct_src1 = 0
                    if dict_macct_basicinfo_src1:
                        acctidbymxz_macct_src1 = dict_macct_basicinfo_src1['AcctIDByMXZ']

                        dict_bs_by_acctidbymxz = self.gv.col_bs_by_acctidbymxz.find_one(
                            {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_macct_src1}
                        )
                        mn_capital_debt_in_macct_src1 = dict_bs_by_acctidbymxz['CapitalDebt']
                        mn_security_debt_in_macct_src1 = (
                                dict_bs_by_acctidbymxz['CompositeShortAmt'] + dict_bs_by_acctidbymxz['ETFShortAmt']
                        )
                        list_dicts_formatted_holding = list(
                            self.gv.col_formatted_holding.find(
                                {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_macct_src1}
                            )
                        )
                        # todo 更新，在b/s中有分拆，不用重新累加， 需要在b/s表中添加卖出融券所得资金, 此处可改进
                        for dict_formatted_holding in list_dicts_formatted_holding:
                            sectype = dict_formatted_holding['SecurityType']
                            mn_cash_from_ss_delta = dict_formatted_holding['CashFromShortSelling']
                            mn_cash_from_ss_src1 += mn_cash_from_ss_delta
                            if sectype in ['ETF']:
                                mn_etfshortamt_delta = dict_formatted_holding['ShortAmt']
                                mn_etfshortamt_src1 += mn_etfshortamt_delta
                            elif sectype in ['CS']:
                                mn_cpsshortamt_delta = dict_formatted_holding['ShortAmt']
                                mn_cpsshortamt_src1 += mn_cpsshortamt_delta
                            else:
                                ValueError('Unknown security type when computing mn_etfshortamt_macct '
                                           'and mn_cpsshortamt_in_macct')
                        if self.dict_tgt_items['CashFromShortSellingInMarginAccount']:
                            mn_cash_from_ss_src1 = self.dict_tgt_items['CashFromShortSellingInMarginAccount']
                        if self.dict_tgt_items['ETFShortAmountInMarginAccount']:
                            mn_etfshortamt_src1 = self.dict_tgt_items['ETFShortAmountInMarginAccount']
                        if self.dict_tgt_items['CompositeShortAmountInMarginAccount']:
                            mn_cpsshortamt_src1 = self.dict_tgt_items['CompositeShortAmountInMarginAccount']

                    mn_ce_from_ss_src1 = mn_cash_from_ss_src1

                    # macct - src2
                    dict_macct_basicinfo_src2 = self.gv.col_acctinfo.find_one(
                        {
                            'DataDate': self.str_today, 
                            'PrdCode': self.prdcode, 
                            'CapitalSource': src2,
                            'AcctType': 'm',
                            'AcctStatus': 'T',
                            'RptMark': 1,
                            'SpecialAccountMark': 0
                        }
                    )
                    mn_cash_from_ss_src2 = 0
                    mn_etfshortamt_src2 = 0
                    mn_cpsshortamt_src2 = 0
                    mn_capital_debt_in_macct_src2 = 0
                    mn_security_debt_in_macct_src2 = 0

                    if dict_macct_basicinfo_src2:
                        acctidbymxz_macct_src2 = dict_macct_basicinfo_src2['AcctIDByMXZ']

                        dict_bs_by_acctidbymxz = self.gv.col_bs_by_acctidbymxz.find_one(
                            {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_macct_src2}
                        )
                        mn_capital_debt_in_macct_src2 = dict_bs_by_acctidbymxz['CapitalDebt']
                        mn_security_debt_in_macct_src2 = (dict_bs_by_acctidbymxz['CompositeShortAmt']
                                                          + dict_bs_by_acctidbymxz['ETFShortAmt'])

                        list_dicts_formatted_holding = self.gv.col_formatted_holding.find(
                            {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_macct_src2}
                        )
                        for dict_formatted_holding in list_dicts_formatted_holding:
                            sectype = dict_formatted_holding['SecurityType']
                            mn_cash_from_ss_delta = dict_formatted_holding['CashFromShortSelling']
                            mn_cash_from_ss_src2 += mn_cash_from_ss_delta
                            if sectype in ['ETF']:
                                mn_etfshortamt_delta = dict_formatted_holding['ShortAmt']
                                mn_etfshortamt_src2 += mn_etfshortamt_delta
                            elif sectype in ['CS']:
                                mn_cpsshortamt_delta = dict_formatted_holding['ShortAmt']
                                mn_cpsshortamt_src2 += mn_cpsshortamt_delta
                            else:
                                ValueError('Unknown security type when computing mn_etfshortamt_macct '
                                           'and mn_cpsshortamt_in_macct')
                        if self.dict_tgt_items['CashFromShortSellingInMarginAccount']:
                            mn_cash_from_ss_src2 = self.dict_tgt_items['CashFromShortSellingInMarginAccount']
                        if self.dict_tgt_items['ETFShortAmountInMarginAccount']:
                            mn_etfshortamt_src2 = self.dict_tgt_items['ETFShortAmountInMarginAccount']
                        if self.dict_tgt_items['CompositeShortAmountInMarginAccount']:
                            mn_cpsshortamt_src2 = self.dict_tgt_items['CompositeShortAmountInMarginAccount']
                    mn_ce_from_ss_src2 = mn_cash_from_ss_src2

                    # macct - src3
                    dict_macct_basicinfo_src3 = self.gv.col_acctinfo.find_one(
                        {
                            'DataDate': self.str_today,
                            'PrdCode': self.prdcode,
                            'CapitalSource': src3,
                            'AcctType': 'm',
                            'AcctStatus': 'T',
                            'RptMark': 1,
                            'SpecialAccountMark': 0
                        }
                    )
                    mn_cash_from_ss_src3 = 0
                    mn_etfshortamt_src3 = 0
                    mn_cpsshortamt_src3 = 0
                    mn_capital_debt_in_macct_src3 = 0
                    mn_security_debt_in_macct_src3 = 0

                    if dict_macct_basicinfo_src3:
                        acctidbymxz_macct_src3 = dict_macct_basicinfo_src3['AcctIDByMXZ']

                        dict_bs_by_acctidbymxz = self.gv.col_bs_by_acctidbymxz.find_one(
                            {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_macct_src3}
                        )
                        mn_capital_debt_in_macct_src3 = dict_bs_by_acctidbymxz['CapitalDebt']
                        mn_security_debt_in_macct_src3 = (
                                dict_bs_by_acctidbymxz['CompositeShortAmt'] + dict_bs_by_acctidbymxz['ETFShortAmt']
                        )

                        list_dicts_formatted_holding = self.gv.col_formatted_holding.find(
                            {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_macct_src3}
                        )
                        for dict_formatted_holding in list_dicts_formatted_holding:
                            sectype = dict_formatted_holding['SecurityType']
                            mn_cash_from_ss_delta = dict_formatted_holding['CashFromShortSelling']
                            mn_cash_from_ss_src3 += mn_cash_from_ss_delta
                            if sectype in ['ETF']:
                                mn_etfshortamt_delta = dict_formatted_holding['ShortAmt']
                                mn_etfshortamt_src3 += mn_etfshortamt_delta
                            elif sectype in ['CS']:
                                mn_cpsshortamt_delta = dict_formatted_holding['ShortAmt']
                                mn_cpsshortamt_src3 += mn_cpsshortamt_delta
                            else:
                                ValueError('Unknown security type when computing mn_etfshortamt_macct '
                                           'and mn_cpsshortamt_in_macct')
                        if self.dict_tgt_items['CashFromShortSellingInMarginAccount']:
                            mn_cash_from_ss_src3 = self.dict_tgt_items['CashFromShortSellingInMarginAccount']
                        if self.dict_tgt_items['ETFShortAmountInMarginAccount']:
                            mn_etfshortamt_src3 = self.dict_tgt_items['ETFShortAmountInMarginAccount']
                        if self.dict_tgt_items['CompositeShortAmountInMarginAccount']:
                            mn_cpsshortamt_src3 = self.dict_tgt_items['CompositeShortAmountInMarginAccount']
                    mn_ce_from_ss_src3 = mn_cash_from_ss_src3

                    # 求oacct提供的空头暴露预算值与多头暴露预算值
                    # 求oacct账户中的存出保证金（net_asset）
                    # ## src1
                    list_dicts_oacct_basicinfo_src1 = list(
                        self.gv.col_acctinfo.find(
                            {
                                'DataDate': self.str_today,
                                'PrdCode': self.prdcode,
                                'AcctType': 'o',
                                'CapitalSource': src1
                            }
                        )
                    )
                    mn_net_exposure_from_oaccts_src1 = 0
                    mn_capital_debt_in_oaccts_src1 = 0
                    mn_ttasset_oaccts_src1 = 0
                    mn_liability_in_oaccts_src1 = 0
                    for dict_oacct_basicinfo_src1 in list_dicts_oacct_basicinfo_src1:
                        if dict_oacct_basicinfo_src1:
                            acctidbymxz_oacct = dict_oacct_basicinfo_src1['AcctIDByMXZ']
                            dict_exposure_analysis_by_acctidbymxz = self.gv.col_exposure_analysis_by_acctidbymxz.find_one(
                                {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_oacct}
                            )
                            net_exposure_from_oacct_delta = dict_exposure_analysis_by_acctidbymxz['NetExposure']
                            mn_net_exposure_from_oaccts_src1 += net_exposure_from_oacct_delta
                            dict_bs_by_acctidbymxz = self.gv.col_bs_by_acctidbymxz.find_one(
                                {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_oacct}
                            )
                            mn_ttasset_oacct_delta = dict_bs_by_acctidbymxz['TotalAsset']
                            mn_ttasset_oaccts_src1 += mn_ttasset_oacct_delta
                            mn_liability_oacct_delta = dict_bs_by_acctidbymxz['Liability']
                            mn_liability_in_oaccts_src1 += mn_liability_oacct_delta
                            mn_capital_debt_in_oaccts_delta = dict_bs_by_acctidbymxz['CapitalDebt']
                            mn_capital_debt_in_oaccts_src1 += mn_capital_debt_in_oaccts_delta

                    if self.dict_tgt_items['NetExposureFromOTCAccounts']:
                        mn_net_exposure_from_oaccts_src1 = self.dict_tgt_items['NetExposureFromOTCAccounts']

                    # ## src2
                    list_dicts_oacct_basicinfo_src2 = list(
                        self.gv.col_acctinfo.find(
                            {
                                'DataDate': self.str_today,
                                'PrdCode': self.prdcode,
                                'AcctType': 'o',
                                'CapitalSource': src2
                            }
                        )
                    )
                    mn_net_exposure_from_oaccts_src2 = 0
                    mn_capital_debt_in_oaccts_src2 = 0
                    mn_ttasset_oaccts_src2 = 0
                    mn_liability_in_oaccts_src2 = 0
                    for dict_oacct_basicinfo_src2 in list_dicts_oacct_basicinfo_src2:
                        if dict_oacct_basicinfo_src2:
                            acctidbymxz_oacct = dict_oacct_basicinfo_src2['AcctIDByMXZ']
                            dict_exposure_analysis_by_acctidbymxz = self.gv.col_exposure_analysis_by_acctidbymxz.find_one(
                                {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_oacct}
                            )
                            net_exposure_from_oacct_delta = dict_exposure_analysis_by_acctidbymxz['NetExposure']
                            mn_net_exposure_from_oaccts_src2 += net_exposure_from_oacct_delta
                            dict_bs_by_acctidbymxz = self.gv.col_bs_by_acctidbymxz.find_one(
                                {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_oacct}
                            )
                            mn_ttasset_oacct_delta = dict_bs_by_acctidbymxz['TotalAsset']
                            mn_ttasset_oaccts_src2 += mn_ttasset_oacct_delta
                            mn_liability_oacct_delta = dict_bs_by_acctidbymxz['Liability']
                            mn_liability_in_oaccts_src2 += mn_liability_oacct_delta
                            mn_capital_debt_in_oaccts_delta = dict_bs_by_acctidbymxz['CapitalDebt']
                            mn_capital_debt_in_oaccts_src2 += mn_capital_debt_in_oaccts_delta

                    if self.dict_tgt_items['NetExposureFromOTCAccounts']:
                        mn_net_exposure_from_oaccts_src2 = self.dict_tgt_items['NetExposureFromOTCAccounts']

                    # ## src3
                    list_dicts_oacct_basicinfo_src3 = list(
                        self.gv.col_acctinfo.find(
                            {
                                'DataDate': self.str_today,
                                'PrdCode': self.prdcode,
                                'AcctType': 'o',
                                'CapitalSource': src3
                            }
                        )
                    )
                    mn_net_exposure_from_oaccts_src3 = 0
                    mn_capital_debt_in_oaccts_src3 = 0
                    mn_ttasset_oaccts_src3 = 0
                    mn_liability_in_oaccts_src3 = 0
                    for dict_oacct_basicinfo_src3 in list_dicts_oacct_basicinfo_src3:
                        if dict_oacct_basicinfo_src3:
                            acctidbymxz_oacct = dict_oacct_basicinfo_src3['AcctIDByMXZ']
                            dict_exposure_analysis_by_acctidbymxz = self.gv.col_exposure_analysis_by_acctidbymxz.find_one(
                                {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_oacct}
                            )
                            net_exposure_from_oacct_delta = dict_exposure_analysis_by_acctidbymxz['NetExposure']
                            mn_net_exposure_from_oaccts_src3 += net_exposure_from_oacct_delta
                            dict_bs_by_acctidbymxz = self.gv.col_bs_by_acctidbymxz.find_one(
                                {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_oacct}
                            )
                            mn_ttasset_oacct_delta = dict_bs_by_acctidbymxz['TotalAsset']
                            mn_ttasset_oaccts_src3 += mn_ttasset_oacct_delta
                            mn_liability_oacct_delta = dict_bs_by_acctidbymxz['Liability']
                            mn_liability_in_oaccts_src3 += mn_liability_oacct_delta
                            mn_capital_debt_in_oaccts_delta = dict_bs_by_acctidbymxz['CapitalDebt']
                            mn_capital_debt_in_oaccts_src3 += mn_capital_debt_in_oaccts_delta

                    if self.dict_tgt_items['NetExposureFromOTCAccounts']:
                        mn_net_exposure_from_oaccts_src3 = self.dict_tgt_items['NetExposureFromOTCAccounts']


                    # 未知量
                    # 注：未知量iclots不分src1与src2, 而采取代数式方式替换（基于facct的分配逻辑是”再分配独立“逻辑考虑）
                    #    即： 对期指的分配跳过渠道分配的步骤（分配步骤： 渠道-策略-项目）
                    ei_cpslongamt_src1 = Symbol('ei_cpslongamt_src1', real=True, nonnegative=True)
                    ei_ce_from_cash_available_src1 = Symbol('ei_ce_from_cash_available_src1', real=True)
                    mn_cpslongamt_src1 = Symbol('mn_cpslongamt_src1', real=True, nonnegative=True)
                    mn_ce_from_cash_available_src1 = Symbol('mn_ce_from_cash_available_src1', real=True,)
                    na_src1_tgt = Symbol('na_src1_tgt', real=True, nonnegative=True)

                    ei_cpslongamt_src2 = Symbol('ei_cpslongamt_src2', real=True, nonnegative=True)
                    ei_ce_from_cash_available_src2 = Symbol('ei_ce_from_cash_available_src2', real=True)
                    mn_cpslongamt_src2 = Symbol('mn_cpslongamt_src2', real=True, nonnegative=True)
                    mn_ce_from_cash_available_src2 = Symbol('mn_ce_from_cash_available_src2', real=True)
                    na_src2_tgt = Symbol('na_src2_tgt', real=True, nonnegative=True)

                    ei_cpslongamt_src3 = Symbol('ei_cpslongamt_src3', real=True, nonnegative=True)
                    ei_ce_from_cash_available_src3 = Symbol('ei_ce_from_cash_available_src3', real=True)
                    mn_cpslongamt_src3 = Symbol('mn_cpslongamt_src3', real=True, nonnegative=True)
                    mn_ce_from_cash_available_src3 = Symbol('mn_ce_from_cash_available_src3', real=True)
                    na_src3_tgt = Symbol('na_src3_tgt', real=True, nonnegative=True)

                    ei_iclots = Symbol('ei_iclots', real=True)
                    mn_iclots = Symbol('mn_iclots', real=True)

                    list_eqs_2b_solved = []

                    # 代数式
                    ei_na_src1_tgt = na_src1_tgt * self.dict_strategies_allocation['EI']
                    ei_na_src2_tgt = na_src2_tgt * self.dict_strategies_allocation['EI']
                    ei_na_src3_tgt = na_src3_tgt * self.dict_strategies_allocation['EI']

                    mn_na_src1_tgt = na_src1_tgt * self.dict_strategies_allocation['MN']
                    mn_na_src2_tgt = na_src2_tgt * self.dict_strategies_allocation['MN']
                    mn_na_src3_tgt = na_src3_tgt * self.dict_strategies_allocation['MN']

                    if specified_na_in_saccts > 0:  # 定值算法
                        # 代数式
                        # 定值算法中，由于给定了单组证券账户的目标净资产，并没有给出期货户在各渠道的资产分配，以至于需要假设期货的资产分配方式
                        # 如何假设呢，该假设是随意的，没有约束条件的假设
                        # 假设：定值渠道的期货资产为0（仅保证有证券账户的即可）
                        # todo 当前不支持三渠道的定值算法（原因：算法未知）
                        raise ValueError('当前不支持3渠道定值分配算法')
                        # if idx_src == 0:
                        #     ei_iclots_src1 = 0
                        #     mn_iclots_src1 = 0
                        #     ei_iclots_src2 = ei_iclots - ei_iclots_src1
                        #     mn_iclots_src2 = mn_iclots - mn_iclots_src1
                        # elif idx_src == 1:
                        #     ei_iclots_src2 = 0
                        #     mn_iclots_src2 = 0
                        #     ei_iclots_src1 = ei_iclots - ei_iclots_src2
                        #     mn_iclots_src1 = mn_iclots - mn_iclots_src2
                        # else:
                        #     raise ValueError('Unknown idx_src when get specified account index.')

                    else:  # 定比算法
                        list_tgt_na_allocation = []
                        for value_na_allocation_saccts in list_values_na_allocation_saccts:
                            tgt_na_allocation = self.prdna_tgt * value_na_allocation_saccts
                            list_tgt_na_allocation.append(tgt_na_allocation)

                        # 代数式：
                        # 在多渠道且有货基的条件下，产品的各渠道的货基值，受各渠道分配到的期指数量影响
                        # 如何假设呢，该假设是随意的，没有约束条件的假设
                        # 假设： 分配比例为渠道比例(定比模式)

                        ei_iclots_src1 = ei_iclots * list_values_na_allocation_saccts[0]
                        ei_iclots_src2 = ei_iclots * list_values_na_allocation_saccts[1]
                        ei_iclots_src3 = ei_iclots * list_values_na_allocation_saccts[2]

                        mn_iclots_src1 = mn_iclots * list_values_na_allocation_saccts[0]
                        mn_iclots_src2 = mn_iclots * list_values_na_allocation_saccts[1]
                        mn_iclots_src3 = mn_iclots * list_values_na_allocation_saccts[2]

                        eq_na_src1_tgt = na_src1_tgt - list_tgt_na_allocation[0]
                        eq_na_src2_tgt = na_src2_tgt - list_tgt_na_allocation[1]
                        eq_na_src3_tgt = na_src3_tgt - list_tgt_na_allocation[2]

                        list_eqs_2b_solved.append(eq_na_src1_tgt)
                        list_eqs_2b_solved.append(eq_na_src2_tgt)
                        list_eqs_2b_solved.append(eq_na_src3_tgt)

                    # 方程-双模式计算补充
                    if self.tgt_cpspct == 'max':
                        eq_ei_ce_src1 = ei_ce_from_cash_available_src1
                        eq_ei_ce_src2 = ei_ce_from_cash_available_src2
                        eq_ei_ce_src3 = ei_ce_from_cash_available_src3

                        eq_mn_ce_src1 = mn_ce_from_cash_available_src1
                        eq_mn_ce_src2 = mn_ce_from_cash_available_src2
                        eq_mn_ce_src3 = mn_ce_from_cash_available_src3

                        list_eqs_2b_solved.append(eq_ei_ce_src1)
                        list_eqs_2b_solved.append(eq_ei_ce_src2)
                        list_eqs_2b_solved.append(eq_ei_ce_src3)
                        list_eqs_2b_solved.append(eq_mn_ce_src1)
                        list_eqs_2b_solved.append(eq_mn_ce_src2)
                        list_eqs_2b_solved.append(eq_mn_ce_src3)

                    else:
                        eq_ei_cpslongamt_tgt = (
                                ei_cpslongamt_src1
                                + ei_cpslongamt_src2
                                + ei_cpslongamt_src3
                                - self.ei_na_tgt * self.tgt_cpspct
                        )
                        eq_mn_cpslongamt_tgt = (
                                mn_cpslongamt_src1
                                + mn_cpslongamt_src2
                                + mn_cpslongamt_src3
                                - self.mn_na_tgt * self.tgt_cpspct
                        )
                        list_eqs_2b_solved.append(eq_ei_cpslongamt_tgt)
                        list_eqs_2b_solved.append(eq_mn_cpslongamt_tgt)

                        if specified_na_in_saccts > 0:  # 定值算法补充方程
                            raise ValueError('不支持三渠道定值分配')
                            # # 由于目前对ei策略的cps与mn策略的cps不做区分，故对同一渠道下不同策略对应的cps的分配没有要求
                            # # todo 故暂且假设ei_cpslongamt_src1 与 mn_cpslongamt_src1 的比例为策略比例(EI:MN)
                            # # todo 即定值渠道中的ei_cpslongamt 与 mn_cpslongamt_sr1 为定值
                            # # todo 注意： 当定值渠道分配，策略分配同时出现时，算法不严谨，需要改进(非定值渠道可能出现负值）
                            # # todo 先填满定值渠道的权益
                            # # 定值算法中，由于给定了单组证券账户的目标净资产，并没有给出货币基金的值，需要分配。再解一次方程组
                            # # 如何假设呢，该假设是随意的，没有约束条件的假设
                            # # 假设：若产品需要的cpslongamt*1.0889小于指定证券账户的净资产，则，闲置资金买货基。另一账户中钱全部买货基
                            # # 假设：若产品需要的cpslongamt*1.0889大于指定证券账户的净资产，则，该账户中的货币资金为0，另一账户中为cps余额。
                            # if idx_src == 0:
                            #     if self.prdna_tgt * self.tgt_cpspct > specified_na_in_saccts:
                            #         eq_ei_cpslongamt_allocation_src1 = (
                            #             ei_cpslongamt_src1 * (1 + self.gv.flt_cash2cpslongamt)
                            #             - specified_na_in_saccts * self.dict_strategies_allocation['EI']
                            #         )
                            #         eq_mn_cpslongamt_allocation_src1 = (
                            #             mn_cpslongamt_src1 * (1 + self.gv.flt_cash2cpslongamt)
                            #             - specified_na_in_saccts * self.dict_strategies_allocation['MN']
                            #         )
                            #         list_eqs_2b_solved.append(eq_ei_cpslongamt_allocation_src1)
                            #         list_eqs_2b_solved.append(eq_mn_cpslongamt_allocation_src1)
                            #
                            #         eq_ei_ce_from_cash_available_src1 = ei_ce_from_cash_available_src1
                            #         eq_mn_ce_from_cash_available_src1 = mn_ce_from_cash_available_src1
                            #         list_eqs_2b_solved.append(eq_ei_ce_from_cash_available_src1)
                            #         list_eqs_2b_solved.append(eq_mn_ce_from_cash_available_src1)
                            #         # 约束总资产 = na_src1 + na_sr2
                            #         eq_prdna_tgt = na_src1_tgt + na_src2_tgt - self.prdna_tgt
                            #         list_eqs_2b_solved.append(eq_prdna_tgt)
                            #     else:
                            #         eq_ei_cpslongamt_allocation_src1 = (
                            #             self.prdna_tgt
                            #             * self.gv.flt_cash2cpslongamt
                            #             * self.dict_strategies_allocation['EI']
                            #             - ei_cpslongamt_src1
                            #         )
                            #         eq_mn_cpslongamt_allocation_src1 = (
                            #             self.prdna_tgt
                            #             * self.gv.flt_cash2cpslongamt
                            #             * self.dict_strategies_allocation['MN']
                            #             - mn_cpsshortamt_src1
                            #         )
                            #         list_eqs_2b_solved.append(eq_ei_cpslongamt_allocation_src1)
                            #         list_eqs_2b_solved.append(eq_mn_cpslongamt_allocation_src1)
                            #         ce_from_cash_available_src1 = (
                            #                 specified_na_in_saccts - self.prdna_tgt * (1 + self.gv.flt_cash2cpslongamt)
                            #         )
                            #         eq_ei_ce_from_cash_available_src1 = (
                            #                 ce_from_cash_available_src1 * self.dict_strategies_allocation['EI']
                            #                 - ei_ce_from_cash_available_src1
                            #         )
                            #         eq_mn_ce_from_cash_available_src1 = (
                            #                 ce_from_cash_available_src1 * self.dict_strategies_allocation['MN']
                            #                 - mn_ce_from_cash_available_src1
                            #         )
                            #         list_eqs_2b_solved.append(eq_ei_ce_from_cash_available_src1)
                            #         list_eqs_2b_solved.append(eq_mn_ce_from_cash_available_src1)
                            #
                            #         # 约束总资产 = na_src1 + na_sr2
                            #         eq_prdna_tgt = na_src1_tgt + na_src2_tgt - self.prdna_tgt
                            #         list_eqs_2b_solved.append(eq_prdna_tgt)
                            #
                            # elif idx_src == 1:
                            #     if self.prdna_tgt * self.tgt_cpspct > specified_na_in_saccts:
                            #         eq_ei_cpslongamt_allocation_src2 = (
                            #                 ei_cpslongamt_src2 * (1 + self.gv.flt_cash2cpslongamt)
                            #                 - specified_na_in_saccts * self.dict_strategies_allocation['EI']
                            #         )
                            #         eq_mn_cpslongamt_allocation_src2 = (
                            #                 mn_cpslongamt_src2 * (1 + self.gv.flt_cash2cpslongamt)
                            #                 - specified_na_in_saccts * self.dict_strategies_allocation['MN']
                            #         )
                            #         list_eqs_2b_solved.append(eq_ei_cpslongamt_allocation_src2)
                            #         list_eqs_2b_solved.append(eq_mn_cpslongamt_allocation_src2)
                            #
                            #         eq_ei_ce_from_cash_available_src2 = ei_ce_from_cash_available_src2
                            #         eq_mn_ce_from_cash_available_src2 = mn_ce_from_cash_available_src2
                            #         list_eqs_2b_solved.append(eq_ei_ce_from_cash_available_src2)
                            #         list_eqs_2b_solved.append(eq_mn_ce_from_cash_available_src2)
                            #
                            #         # 约束总资产 = na_src1 + na_sr2
                            #         eq_prdna_tgt = na_src1_tgt + na_src2_tgt - self.prdna_tgt
                            #         list_eqs_2b_solved.append(eq_prdna_tgt)
                            #
                            #     else:
                            #         eq_ei_cpslongamt_allocation_src2 = (
                            #                 self.prdna_tgt
                            #                 * self.gv.flt_cash2cpslongamt
                            #                 * self.dict_strategies_allocation['EI']
                            #                 - ei_cpslongamt_src2
                            #         )
                            #         eq_mn_cpslongamt_allocation_src2 = (
                            #                 self.prdna_tgt
                            #                 * self.gv.flt_cash2cpslongamt
                            #                 * self.dict_strategies_allocation['MN']
                            #                 - mn_cpsshortamt_src2
                            #         )
                            #         list_eqs_2b_solved.append(eq_ei_cpslongamt_allocation_src2)
                            #         list_eqs_2b_solved.append(eq_mn_cpslongamt_allocation_src2)
                            #         ce_from_cash_available_src2 = (
                            #                 specified_na_in_saccts - self.prdna_tgt * (1 + self.gv.flt_cash2cpslongamt)
                            #         )
                            #         eq_ei_ce_from_cash_available_src2 = (
                            #                 ce_from_cash_available_src2 * self.dict_strategies_allocation['EI']
                            #                 - ei_ce_from_cash_available_src2
                            #         )
                            #         eq_mn_ce_from_cash_available_src2 = (
                            #                 ce_from_cash_available_src2 * self.dict_strategies_allocation['MN']
                            #                 - mn_ce_from_cash_available_src2
                            #         )
                            #         list_eqs_2b_solved.append(eq_ei_ce_from_cash_available_src2)
                            #         list_eqs_2b_solved.append(eq_mn_ce_from_cash_available_src2)
                            #         # 约束总资产 = na_src1 + na_sr2
                            #         eq_prdna_tgt = na_src1_tgt + na_src2_tgt - self.prdna_tgt
                            #         list_eqs_2b_solved.append(eq_prdna_tgt)
                            # else:
                            #     raise ValueError('Unknown idx_src.')

                        else:  # 定比方法补充方程
                            # 在定比分配渠道算法下，当指定的仓位小于max仓位（未满仓）时，在满足产品仓位达标后，还需分配渠道
                            # todo 假设： 分配比例为渠道比例
                            eq_ei_cpslongamt_allocation_src1 = (
                                list_values_na_allocation_saccts[0]
                                * (ei_cpslongamt_src1 + ei_cpslongamt_src2 + ei_cpslongamt_src3)
                                - ei_cpslongamt_src1
                            )
                            eq_ei_cpslongamt_allocation_src2 = (
                                list_values_na_allocation_saccts[1]
                                * (ei_cpslongamt_src1 + ei_cpslongamt_src2 + ei_cpslongamt_src3)
                                - ei_cpslongamt_src2
                            )

                            eq_ei_cpslongamt_allocation_src3 = (
                                list_values_na_allocation_saccts[2]
                                * (ei_cpslongamt_src1 + ei_cpslongamt_src2 + ei_cpslongamt_src3)
                                - ei_cpslongamt_src3
                            )

                            eq_mn_cpslongamt_allocation_src1 = (
                                list_values_na_allocation_saccts[0]
                                * (mn_cpslongamt_src1 + mn_cpslongamt_src2 + mn_cpslongamt_src3)
                                - mn_cpslongamt_src1
                            )

                            eq_mn_cpslongamt_allocation_src2 = (
                                list_values_na_allocation_saccts[1]
                                * (mn_cpslongamt_src1 + mn_cpslongamt_src2 + mn_cpslongamt_src3)
                                - mn_cpslongamt_src2
                            )
                            
                            eq_mn_cpslongamt_allocation_src3 = (
                                list_values_na_allocation_saccts[2]
                                * (mn_cpslongamt_src1 + mn_cpslongamt_src2 + mn_cpslongamt_src3)
                                - mn_cpslongamt_src3
                            )

                            list_eqs_2b_solved.append(eq_ei_cpslongamt_allocation_src1)
                            list_eqs_2b_solved.append(eq_ei_cpslongamt_allocation_src2)
                            list_eqs_2b_solved.append(eq_ei_cpslongamt_allocation_src3)

                            list_eqs_2b_solved.append(eq_mn_cpslongamt_allocation_src1)
                            list_eqs_2b_solved.append(eq_mn_cpslongamt_allocation_src2)
                            list_eqs_2b_solved.append(eq_mn_cpslongamt_allocation_src3)

                    # 核心方程组-净资产
                    eq_ei_na_src1 = (
                            ei_cpslongamt_src1 * (1 + self.gv.flt_cash2cpslongamt)
                            + ei_ce_from_cash_available_src1
                            + ei_ce_from_ss_src1
                            + ei_etflongamt_src1
                            + ei_special_na_src1
                            + abs(ei_iclots_src1) * self.gv.dict_index_future2internal_required_na_per_lot[index_future]
                            + ei_na_oaccts_src1
                            + ei_capital_debt_src1
                            - ei_na_src1_tgt
                            - ei_liability_src1
                    )

                    eq_ei_na_src2 = (
                            ei_cpslongamt_src2 * (1 + self.gv.flt_cash2cpslongamt)
                            + ei_ce_from_cash_available_src2
                            + ei_ce_from_ss_src2
                            + ei_etflongamt_src2
                            + ei_special_na_src2
                            + abs(ei_iclots_src2) * self.gv.dict_index_future2internal_required_na_per_lot[index_future]
                            + ei_na_oaccts_src2
                            + ei_capital_debt_src2
                            - ei_na_src2_tgt
                            - ei_liability_src2
                    )

                    eq_ei_na_src3 = (
                            ei_cpslongamt_src3 * (1 + self.gv.flt_cash2cpslongamt)
                            + ei_ce_from_cash_available_src3
                            + ei_ce_from_ss_src3
                            + ei_etflongamt_src3
                            + ei_special_na_src3
                            + abs(ei_iclots_src3) * self.gv.dict_index_future2internal_required_na_per_lot[index_future]
                            + ei_na_oaccts_src3
                            + ei_capital_debt_src3
                            - ei_na_src3_tgt
                            - ei_liability_src3
                    )

                    list_eqs_2b_solved.append(eq_ei_na_src1)
                    list_eqs_2b_solved.append(eq_ei_na_src2)
                    list_eqs_2b_solved.append(eq_ei_na_src3)

                    eq_mn_na_src1 = (
                            mn_cpslongamt_src1 * (1 + self.gv.flt_cash2cpslongamt)
                            + mn_ce_from_cash_available_src1
                            + mn_ce_from_ss_src1
                            + mn_etflongamt_src1
                            + mn_special_na_src1
                            + abs(mn_iclots_src1) * self.gv.dict_index_future2internal_required_na_per_lot[index_future]
                            + mn_ttasset_oaccts_src1
                            - mn_na_src1_tgt
                            - mn_capital_debt_in_macct_src1
                            - mn_security_debt_in_macct_src1
                            - mn_liability_in_oaccts_src1
                    )

                    eq_mn_na_src2 = (
                            mn_cpslongamt_src2 * (1 + self.gv.flt_cash2cpslongamt)
                            + mn_ce_from_cash_available_src2
                            + mn_ce_from_ss_src2
                            + mn_etflongamt_src2
                            + mn_special_na_src2
                            + abs(mn_iclots_src2) * self.gv.dict_index_future2internal_required_na_per_lot[index_future]
                            + mn_ttasset_oaccts_src2
                            - mn_na_src2_tgt
                            - mn_capital_debt_in_macct_src2
                            - mn_security_debt_in_macct_src2
                            - mn_liability_in_oaccts_src2

                    )

                    eq_mn_na_src3 = (
                            mn_cpslongamt_src3 * (1 + self.gv.flt_cash2cpslongamt)
                            + mn_ce_from_cash_available_src3
                            + mn_ce_from_ss_src3
                            + mn_etflongamt_src3
                            + mn_special_na_src3
                            + abs(mn_iclots_src3) * self.gv.dict_index_future2internal_required_na_per_lot[index_future]
                            + mn_ttasset_oaccts_src3
                            - mn_na_src3_tgt
                            - mn_capital_debt_in_macct_src3
                            - mn_security_debt_in_macct_src3
                            - mn_liability_in_oaccts_src3
                    )

                    list_eqs_2b_solved.append(eq_mn_na_src1)
                    list_eqs_2b_solved.append(eq_mn_na_src2)
                    list_eqs_2b_solved.append(eq_mn_na_src3)

                    # 核心方程组-暴露
                    eq_ei_exposure = (
                            ei_cpslongamt_src1
                            + ei_etflongamt_src1
                            + ei_iclots_src1 * self.gv.dict_index_future2spot_exposure_per_lot[index_future]
                            - ei_cpsshortamt_src1
                            - ei_etfshortamt_src1
                            + ei_net_exposure_from_oaccts_src1

                            + ei_cpslongamt_src2
                            + ei_etflongamt_src2
                            + ei_iclots_src2 * self.gv.dict_index_future2spot_exposure_per_lot[index_future]
                            - ei_cpsshortamt_src2
                            - ei_etfshortamt_src2
                            + ei_net_exposure_from_oaccts_src2

                            + ei_cpslongamt_src3
                            + ei_etflongamt_src3
                            + ei_iclots_src3 * self.gv.dict_index_future2spot_exposure_per_lot[index_future]
                            - ei_cpsshortamt_src3
                            - ei_etfshortamt_src3
                            + ei_net_exposure_from_oaccts_src3

                            - self.ei_na_tgt * 0.99
                                      )

                    list_eqs_2b_solved.append(eq_ei_exposure)

                    eq_mn_exposure = (
                        mn_cpslongamt_src1
                        + mn_etflongamt_src1
                        + mn_iclots_src1 * self.gv.dict_index_future2spot_exposure_per_lot[index_future]
                        - mn_cpsshortamt_src1
                        - mn_etfshortamt_src1
                        + mn_net_exposure_from_oaccts_src1

                        + mn_cpslongamt_src2
                        + mn_etflongamt_src2
                        + mn_iclots_src2 * self.gv.dict_index_future2spot_exposure_per_lot[index_future]
                        - mn_cpsshortamt_src2
                        - mn_etfshortamt_src2
                        + mn_net_exposure_from_oaccts_src2

                        + mn_cpslongamt_src3
                        + mn_etflongamt_src3
                        + mn_iclots_src3 * self.gv.dict_index_future2spot_exposure_per_lot[index_future]
                        - mn_cpsshortamt_src3
                        - mn_etfshortamt_src3
                        + mn_net_exposure_from_oaccts_src3
                    )
                    list_eqs_2b_solved.append(eq_mn_exposure)

                    # 解核心方程组
                    list_tuples_eqs_solve = solve(list_eqs_2b_solved,
                                                  ei_cpslongamt_src1, ei_ce_from_cash_available_src1,
                                                  mn_cpslongamt_src1, mn_ce_from_cash_available_src1,
                                                  na_src1_tgt,
                                                  ei_cpslongamt_src2, ei_ce_from_cash_available_src2,
                                                  mn_cpslongamt_src2, mn_ce_from_cash_available_src2,
                                                  na_src2_tgt,
                                                  ei_cpslongamt_src3, ei_ce_from_cash_available_src3,
                                                  mn_cpslongamt_src3, mn_ce_from_cash_available_src3,
                                                  na_src3_tgt,
                                                  ei_iclots, mn_iclots)

                    tuple_eqs_solve = list_tuples_eqs_solve[0]

                    ei_cpslongamt_src1 = float(tuple_eqs_solve[0])
                    ei_ce_from_cash_available_src1 = float(tuple_eqs_solve[1])
                    mn_cpslongamt_src1 = float(tuple_eqs_solve[2])
                    mn_ce_from_cash_available_src1 = float(tuple_eqs_solve[3])

                    ei_cpslongamt_src2 = float(tuple_eqs_solve[5])
                    ei_ce_from_cash_available_src2 = float(tuple_eqs_solve[6])
                    mn_cpslongamt_src2 = float(tuple_eqs_solve[7])
                    mn_ce_from_cash_available_src2 = float(tuple_eqs_solve[8])

                    ei_cpslongamt_src3 = float(tuple_eqs_solve[10])
                    ei_ce_from_cash_available_src3 = float(tuple_eqs_solve[11])
                    mn_cpslongamt_src3 = float(tuple_eqs_solve[12])
                    mn_ce_from_cash_available_src3 = float(tuple_eqs_solve[13])

                    ei_iclots = float(tuple_eqs_solve[15])
                    mn_iclots = float(tuple_eqs_solve[16])

                    iclots_total = int(ei_iclots) + round(mn_iclots)
                    na_faccts = abs(iclots_total) * self.gv.dict_index_future2internal_required_na_per_lot[index_future]
                    cpslongamt_src1 = ei_cpslongamt_src1 + mn_cpslongamt_src1
                    cpslongamt_src2 = ei_cpslongamt_src2 + mn_cpslongamt_src2
                    cpslongamt_src3 = ei_cpslongamt_src3 + mn_cpslongamt_src3
                    ce_from_cash_available_src1 = ei_ce_from_cash_available_src1 + mn_ce_from_cash_available_src1
                    ce_from_cash_available_src2 = ei_ce_from_cash_available_src2 + mn_ce_from_cash_available_src2
                    ce_from_cash_available_src3 = ei_ce_from_cash_available_src3 + mn_ce_from_cash_available_src3

                    # 资金分配(cacct 与 macct)
                    # 公司内部分配算法：信用户如有负债则在信用户中留足够且仅够开满仓的净资产
                    acctidbymxz_cacct_src1 = self.gv.col_acctinfo.find_one(
                        {
                            'PrdCode': self.prdcode,
                            'CapitalSource': list_keys_na_allocation_saccts[0],
                            'AcctType': 'c',
                            'SpecialAccountMark': 0,
                        }
                    )['AcctIDByMXZ']
                    dict_acctidbymxz_macct_src1 = self.gv.col_acctinfo.find_one(
                        {
                            'PrdCode': self.prdcode,
                            'CapitalSource': list_keys_na_allocation_saccts[0],
                            'AcctType': 'm',
                            'SpecialAccountMark': 0,
                            'AcctStatus': 'T'
                        }
                    )
                    if dict_acctidbymxz_macct_src1:
                        acctidbymxz_macct_src1 = dict_acctidbymxz_macct_src1['AcctIDByMXZ']
                    else:
                        acctidbymxz_macct_src1 = None

                    acctidbymxz_cacct_src2 = self.gv.col_acctinfo.find_one(
                        {
                            'PrdCode': self.prdcode,
                            'CapitalSource': list_keys_na_allocation_saccts[1],
                            'AcctType': 'c',
                            'SpecialAccountMark': 0,
                        }
                    )['AcctIDByMXZ']
                    dict_acctidbymxz_macct_src2 = self.gv.col_acctinfo.find_one(
                        {
                            'PrdCode': self.prdcode,
                            'CapitalSource': list_keys_na_allocation_saccts[1],
                            'AcctType': 'm',
                            'SpecialAccountMark': 0,
                            'AcctStatus': 'T'
                        }
                    )

                    if dict_acctidbymxz_macct_src2:
                        acctidbymxz_macct_src2 = dict_acctidbymxz_macct_src2['AcctIDByMXZ']
                    else:
                        acctidbymxz_macct_src2 = None

                    acctidbymxz_cacct_src3 = self.gv.col_acctinfo.find_one(
                        {
                            'PrdCode': self.prdcode,
                            'CapitalSource': list_keys_na_allocation_saccts[2],
                            'AcctType': 'c',
                            'SpecialAccountMark': 0,
                        }
                    )['AcctIDByMXZ']
                    dict_acctidbymxz_macct_src3 = self.gv.col_acctinfo.find_one(
                        {
                            'PrdCode': self.prdcode,
                            'CapitalSource': list_keys_na_allocation_saccts[2],
                            'AcctType': 'm',
                            'SpecialAccountMark': 0,
                            'AcctStatus': 'T'
                        }
                    )

                    if dict_acctidbymxz_macct_src3:
                        acctidbymxz_macct_src3 = dict_acctidbymxz_macct_src2['AcctIDByMXZ']
                    else:
                        acctidbymxz_macct_src3 = None

                    na_cacct_src1 = 0
                    na_cacct_src2 = 0
                    na_cacct_src3 = 0

                    cpslongamt_in_macct_src1 = None
                    na_macct_src1 = None
                    cash_available_in_macct_src1 = None

                    cpslongamt_in_macct_src2 = None
                    na_macct_src2 = None
                    cash_available_in_macct_src2 = None

                    cpslongamt_in_macct_src3 = None
                    na_macct_src3 = None
                    cash_available_in_macct_src3 = None
                    # todo 此处假设： 若macct中不满仓，则可用于交易的现金对应的货基应全部转至cacct，故macct中ce_from_cash_available为0
                    # todo 注意，需要分情况讨论： 当担保品充足时，当担保品不足时
                    # todo 当担保品充足时，macct总资产 = (
                    #  卖出融券所得资金 + 目标持仓市值 * (1 + self.gv.flt_cash2cpslongamt) + 用于补充担保品的ce
                    #  )
                    # todo 当担保品充足时，macct净资产 = macct总资产 - macct负债
                    # todo 信用户中可用资金的锁定
                    ce_from_cash_available_in_macct_src1 = 0
                    ce_from_cash_from_ss_src1 = mn_ce_from_ss_src1

                    ce_from_cash_from_ss_src2 = mn_ce_from_ss_src2
                    ce_from_cash_available_in_macct_src2 = 0

                    ce_from_cash_from_ss_src3 = mn_ce_from_ss_src3
                    ce_from_cash_available_in_macct_src3 = 0

                    # 如有信用户，则该渠道按照最少净资产原则放在信用户里交易（实际中由于受担保比例3的影响，转账受到限制）
                    dict_macct_basicinfo = self.gv.col_acctinfo.find_one(
                        {
                            'PrdCode': self.prdcode,
                            'AcctType': 'm',
                            'RptMark': 1,
                            'SpecialAccountMark': 0,
                            'AcctStatus': 'T'
                        }
                    )
                    if dict_macct_basicinfo:
                        capital_source = dict_macct_basicinfo['CapitalSource']
                        idx_capital_source = list_keys_na_allocation_saccts.index(capital_source)
                        if idx_capital_source == 0:  # 第一个渠道为信用户渠道，第二、三个渠道为普通户渠道
                            dict_bs_by_acctidbymxz = self.gv.col_bs_by_acctidbymxz.find_one(
                                {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_macct_src1}
                            )
                            ttasset_macct = dict_bs_by_acctidbymxz['TotalAsset']
                            liability_macct = dict_bs_by_acctidbymxz['Liability']
                            if liability_macct:
                                margin_maintenance_ratio = ttasset_macct / liability_macct
                            else:
                                margin_maintenance_ratio = 999999999
                            if margin_maintenance_ratio <= 1.5:
                                print(
                                    f'Warning, margin maintenance ratio {margin_maintenance_ratio}, '
                                    f'may be not sufficient.'
                                )

                            cpslongamt_in_macct_src1 = cpslongamt_src1
                            cash_available_in_macct_src1 = cpslongamt_src1 * self.gv.flt_cash2cpslongamt
                            na_cacct_src1 = ce_from_cash_available_src1
                            na_macct_src1 = (
                                    cpslongamt_in_macct_src1
                                    + cash_available_in_macct_src1
                                    + ce_from_cash_from_ss_src1
                                    - liability_macct
                            )
                            cpslongamt_in_cacct_src1 = 0
                            if na_cacct_src1 > 2500000:
                                ce_in_cacct_src1 = na_cacct_src1 - 2500000
                                cash_available_in_cacct_src1 = 2500000
                            else:
                                ce_in_cacct_src1 = 0
                                cash_available_in_cacct_src1 = na_cacct_src1

                            # 第二个渠道（非信用户渠道）的数据
                            cpslongamt_in_cacct_src2 = cpslongamt_src2
                            cash_available_in_cacct_src2 = cpslongamt_in_cacct_src2 * self.gv.flt_cash2cpslongamt
                            ce_in_cacct_src2 = ce_from_cash_available_src2
                            na_cacct_src2 = cpslongamt_in_cacct_src2 + cash_available_in_cacct_src2 + ce_in_cacct_src2

                            # 第三个渠道（非信用户渠道）的数据
                            cpslongamt_in_cacct_src3 = cpslongamt_src3
                            cash_available_in_cacct_src3 = cpslongamt_in_cacct_src3 * self.gv.flt_cash2cpslongamt
                            ce_in_cacct_src3 = ce_from_cash_available_src3
                            na_cacct_src3 = cpslongamt_in_cacct_src3 + cash_available_in_cacct_src3 + ce_in_cacct_src3

                        elif idx_capital_source == 1:  # 第二个渠道为信用户渠道
                            dict_bs_by_acctidbymxz = self.gv.col_bs_by_acctidbymxz.find_one(
                                {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_macct_src2}
                            )
                            ttasset_macct = dict_bs_by_acctidbymxz['TotalAsset']
                            liability_macct = dict_bs_by_acctidbymxz['Liability']
                            if liability_macct:
                                margin_maintenance_ratio = ttasset_macct / liability_macct
                            else:
                                margin_maintenance_ratio = 999999999
                            if margin_maintenance_ratio <= 1.5:
                                print(
                                    f'Warning, margin maintenance ratio {margin_maintenance_ratio}, '
                                    f'may be not sufficient.'
                                )

                            cpslongamt_in_macct_src2 = cpslongamt_src2
                            cash_available_in_macct_src2 = cpslongamt_src2 * self.gv.flt_cash2cpslongamt
                            na_cacct_src2 = ce_from_cash_available_src2
                            na_macct_src2 = (
                                    cpslongamt_in_macct_src2
                                    + cash_available_in_macct_src2
                                    + ce_from_cash_from_ss_src2
                                    - liability_macct
                            )

                            cpslongamt_in_cacct_src2 = 0
                            if na_cacct_src2 > 2500000:
                                ce_in_cacct_src2 = na_cacct_src2 - 2500000
                                cash_available_in_cacct_src2 = 2500000
                            else:
                                ce_in_cacct_src2 = 0
                                cash_available_in_cacct_src2 = na_cacct_src2

                            # 写第一个渠道（非信用户渠道）的数据
                            cpslongamt_in_cacct_src1 = cpslongamt_src1
                            cash_available_in_cacct_src1 = cpslongamt_in_cacct_src1 * self.gv.flt_cash2cpslongamt
                            ce_in_cacct_src1 = ce_from_cash_available_src1
                            na_cacct_src1 = cpslongamt_in_cacct_src1 + cash_available_in_cacct_src1 + ce_in_cacct_src1
                            # 写第三个渠道（非信用户渠道）的数据
                            cpslongamt_in_cacct_src3 = cpslongamt_src3
                            cash_available_in_cacct_src3 = cpslongamt_in_cacct_src3 * self.gv.flt_cash2cpslongamt
                            ce_in_cacct_src3 = ce_from_cash_available_src3
                            na_cacct_src3 = cpslongamt_in_cacct_src3 + cash_available_in_cacct_src3 + ce_in_cacct_src3

                        elif idx_capital_source == 2:  # 第三个渠道为信用户渠道
                            dict_bs_by_acctidbymxz = self.gv.col_bs_by_acctidbymxz.find_one(
                                {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_macct_src3}
                            )
                            ttasset_macct = dict_bs_by_acctidbymxz['TotalAsset']
                            liability_macct = dict_bs_by_acctidbymxz['Liability']
                            if liability_macct:
                                margin_maintenance_ratio = ttasset_macct / liability_macct
                            else:
                                margin_maintenance_ratio = 999999999
                            if margin_maintenance_ratio <= 1.5:
                                print(
                                    f'Warning, margin maintenance ratio {margin_maintenance_ratio}, '
                                    f'may be not sufficient.'
                                )

                            cpslongamt_in_macct_src3 = cpslongamt_src3
                            cash_available_in_macct_src3 = cpslongamt_src3 * self.gv.flt_cash2cpslongamt
                            na_cacct_src3 = ce_from_cash_available_src3
                            na_macct_src3 = (
                                    cpslongamt_in_macct_src3
                                    + cash_available_in_macct_src3
                                    + ce_from_cash_from_ss_src3
                                    - liability_macct
                            )

                            cpslongamt_in_cacct_src3 = 0
                            if na_cacct_src3 > 2500000:
                                ce_in_cacct_src3 = na_cacct_src3 - 2500000
                                cash_available_in_cacct_src3 = 2500000
                            else:
                                ce_in_cacct_src3 = 0
                                cash_available_in_cacct_src3 = na_cacct_src3
                            # 写第一个渠道（非信用户渠道）的数据
                            cpslongamt_in_cacct_src1 = cpslongamt_src1
                            cash_available_in_cacct_src1 = cpslongamt_in_cacct_src1 * self.gv.flt_cash2cpslongamt
                            ce_in_cacct_src1 = ce_from_cash_available_src1
                            na_cacct_src1 = cpslongamt_in_cacct_src1 + cash_available_in_cacct_src1 + ce_in_cacct_src1
                            # 写第二个渠道（非信用户渠道）的数据
                            cpslongamt_in_cacct_src2 = cpslongamt_src2
                            cash_available_in_cacct_src2 = cpslongamt_in_cacct_src2 * self.gv.flt_cash2cpslongamt
                            ce_in_cacct_src2 = ce_from_cash_available_src2
                            na_cacct_src2 = cpslongamt_in_cacct_src2 + cash_available_in_cacct_src2 + ce_in_cacct_src2

                        else:
                            raise ValueError('Unknown capital source when allocate sources.')

                    else:
                        cpslongamt_in_cacct_src1 = cpslongamt_src1
                        ce_in_cacct_src1 = ce_from_cash_available_src1
                        cash_available_in_cacct_src1 = cpslongamt_in_cacct_src1 * self.gv.flt_cash2cpslongamt
                        na_cacct_src1 = cpslongamt_src1 + ce_in_cacct_src1 + cash_available_in_cacct_src1

                        cpslongamt_in_cacct_src2 = cpslongamt_src2
                        ce_in_cacct_src2 = ce_from_cash_available_src2
                        cash_available_in_cacct_src2 = cpslongamt_in_cacct_src2 * self.gv.flt_cash2cpslongamt
                        na_cacct_src2 = cpslongamt_src2 + ce_in_cacct_src2 + cash_available_in_cacct_src2

                        cpslongamt_in_cacct_src3 = cpslongamt_src3
                        ce_in_cacct_src3 = ce_from_cash_available_src3
                        cash_available_in_cacct_src3 = cpslongamt_in_cacct_src3 * self.gv.flt_cash2cpslongamt
                        na_cacct_src3 = cpslongamt_src3 + ce_in_cacct_src3 + cash_available_in_cacct_src3

                    list_dicts_bgt_secaccts = [
                        {
                            'DataDate': self.str_today,
                            'PrdCode': self.prdcode,
                            'AcctIDByMXZ': acctidbymxz_cacct_src1,
                            'NAV': na_cacct_src1,
                            'CPSLongAmt': cpslongamt_in_cacct_src1,
                            'ICLots': None,
                            'CashAvailable': cash_available_in_cacct_src1,
                            'CEFromCashFromSS': None,
                            'CEFromCashAvailable': ce_in_cacct_src1,
                        },
                        {
                            'DataDate': self.str_today,
                            'PrdCode': self.prdcode,
                            'AcctIDByMXZ': acctidbymxz_cacct_src2,
                            'NAV': na_cacct_src2,
                            'CPSLongAmt': cpslongamt_in_cacct_src2,
                            'ICLots': None,
                            'CashAvailable': cash_available_in_cacct_src2,
                            'CEFromCashFromSS': None,
                            'CEFromCashAvailable': ce_in_cacct_src2,
                        },
                        {
                            'DataDate': self.str_today,
                            'PrdCode': self.prdcode,
                            'AcctIDByMXZ': acctidbymxz_cacct_src3,
                            'NAV': na_cacct_src3,
                            'CPSLongAmt': cpslongamt_in_cacct_src3,
                            'ICLots': None,
                            'CashAvailable': cash_available_in_cacct_src3,
                            'CEFromCashFromSS': None,
                            'CEFromCashAvailable': ce_in_cacct_src3,
                        },
                        {
                            'DataDate': self.str_today,
                            'PrdCode': self.prdcode,
                            'AcctIDByMXZ': f'{self.prdcode}_faccts',
                            'NAV': na_faccts,
                            'CPSLongAmt': None,
                            'ICLots': iclots_total,
                            'CEFromCashFromSS': None,
                            'CEFromCashAvailable': None,
                        }
                    ]

                    dict_bgt_macct_src1 = {
                        'DataDate': self.str_today,
                        'PrdCode': self.prdcode,
                        'AcctIDByMXZ': acctidbymxz_macct_src1,
                        'NAV': na_macct_src1,
                        'CPSLongAmt': cpslongamt_in_macct_src1,
                        'ICLots': None,
                        'CashAvailable': cash_available_in_macct_src1,
                        'CEFromCashFromSS': ce_from_cash_from_ss_src1,
                        'CEFromCashAvailable': ce_from_cash_available_in_macct_src1,
                    }
                    dict_bgt_macct_src2 = {
                        'DataDate': self.str_today,
                        'PrdCode': self.prdcode,
                        'AcctIDByMXZ': acctidbymxz_macct_src2,
                        'NAV': na_macct_src2,
                        'CPSLongAmt': cpslongamt_in_macct_src2,
                        'ICLots': None,
                        'CashAvailable': cash_available_in_macct_src2,
                        'CEFromCashFromSS': ce_from_cash_from_ss_src2,
                        'CEFromCashAvailable': ce_from_cash_available_in_macct_src2,
                    }
                    dict_bgt_macct_src3 = {
                        'DataDate': self.str_today,
                        'PrdCode': self.prdcode,
                        'AcctIDByMXZ': acctidbymxz_macct_src3,
                        'NAV': na_macct_src3,
                        'CPSLongAmt': cpslongamt_in_macct_src3,
                        'ICLots': None,
                        'CashAvailable': cash_available_in_macct_src3,
                        'CEFromCashFromSS': ce_from_cash_from_ss_src3,
                        'CEFromCashAvailable': ce_from_cash_available_in_macct_src3,
                    }
                    if acctidbymxz_macct_src1:
                        list_dicts_bgt_secaccts.append(dict_bgt_macct_src1)
                    if acctidbymxz_macct_src2:
                        list_dicts_bgt_secaccts.append(dict_bgt_macct_src2)
                    if acctidbymxz_macct_src3:
                        list_dicts_bgt_secaccts.append(dict_bgt_macct_src3)

                    self.list_dicts_bgt_by_acctidbymxz += list_dicts_bgt_secaccts
                    self.allocate_faccts(iclots_total)
                else:
                    raise ValueError('CapitalSrcs Number over 3.')
            else:
                self.get_bgt_without_na_allocation()
        else:
            self.get_bgt_without_na_allocation()

        self.gv.col_bgt_by_acctidbymxz.delete_many(
            {'PrdCode': self.prdcode, 'DataDate': self.gv.str_today, }
        )
        if self.list_dicts_bgt_by_acctidbymxz:
            self.gv.col_bgt_by_acctidbymxz.insert_many(self.list_dicts_bgt_by_acctidbymxz)

    def get_bgt_without_na_allocation(self):
        """
        todo 增加沪市打新策略
        """
        # 假设：
        ei_etflongamt_src1 = 0
        ei_na_oaccts_src1 = 0
        ei_capital_debt_src1 = 0
        ei_liability_src1 = 0
        # special na
        ei_special_na_src1 = 0
        if self.prdcode in self.gv.dict_prdcode2special_na_src1:
            ei_special_na_src1 = self.gv.dict_prdcode2special_na_src1[self.prdcode]
        ei_cpsshortamt_src1 = 0
        ei_etfshortamt_src1 = 0
        ei_net_exposure_from_oaccts_src1 = 0
        ei_ce_from_ss_src1 = 0
        mn_etflongamt_src1 = 0
        mn_special_na_src1 = 0

        # ## src1
        na_src1_tgt = self.prdna_tgt
        # ipo_sh_src1_tgt = self.dict_strategies_allocation['IPO_SH']
        # # 根据当前业务假设，一般情况下不调整为IPO准备的市值，目前的做法是单列出一个账户作为该策略的全部持仓
        # if ipo_sh_src1_tgt in ['current_amt']:
        ei_na_src1_tgt = na_src1_tgt * self.dict_strategies_allocation['EI']
        mn_na_src1_tgt = na_src1_tgt * self.dict_strategies_allocation['MN']

        dict_macct_basicinfo_src1 = self.gv.col_acctinfo.find_one(
            {
                'DataDate': self.str_today,
                'PrdCode': self.prdcode,
                'AcctType': 'm',
                'RptMark': 1,
                'AcctStatus': 'T',
                'SpecialAccountMark': 0
            }
        )
        mn_cash_from_ss_src1 = 0
        mn_etfshortamt_src1 = 0
        mn_cpsshortamt_src1 = 0
        mn_capital_debt_in_macct_src1 = 0
        mn_security_debt_in_macct_src1 = 0
        if dict_macct_basicinfo_src1:
            acctidbymxz_macct_src1 = dict_macct_basicinfo_src1['AcctIDByMXZ']
            dict_bs_by_acctidbymxz = self.gv.col_bs_by_acctidbymxz.find_one(
                {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_macct_src1}
            )
            mn_capital_debt_in_macct_src1 = dict_bs_by_acctidbymxz['CapitalDebt']
            mn_security_debt_in_macct_src1 = (
                    dict_bs_by_acctidbymxz['CompositeShortAmt'] + dict_bs_by_acctidbymxz['ETFShortAmt']
            )
            iter_dicts_formatted_holding = self.gv.col_formatted_holding.find(
                {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_macct_src1}
            )

            # todo 更新，在b/s中有分拆，不用重新累加， 需要在b/s表中添加卖出融券所得资金, 此处可改进
            for dict_formatted_holding in iter_dicts_formatted_holding:
                sectype = dict_formatted_holding['SecurityType']
                mn_cash_from_ss_delta = dict_formatted_holding['CashFromShortSelling']
                mn_cash_from_ss_src1 += mn_cash_from_ss_delta
                if sectype in ['ETF']:
                    mn_etfshortamt_delta = dict_formatted_holding['ShortAmt']
                    mn_etfshortamt_src1 += mn_etfshortamt_delta
                elif sectype in ['CS']:
                    mn_cpsshortamt_delta = dict_formatted_holding['ShortAmt']
                    mn_cpsshortamt_src1 += mn_cpsshortamt_delta
                else:
                    ValueError('Unknown security type when computing mn_etfshortamt_macct '
                               'and mn_cpsshortamt_in_macct')
            if self.dict_tgt_items['CashFromShortSellingInMarginAccount']:
                mn_cash_from_ss_src1 = self.dict_tgt_items['CashFromShortSellingInMarginAccount']
            if self.dict_tgt_items['ETFShortAmountInMarginAccount']:
                mn_etfshortamt_src1 = self.dict_tgt_items['ETFShortAmountInMarginAccount']
            if self.dict_tgt_items['CompositeShortAmountInMarginAccount']:
                mn_cpsshortamt_src1 = self.dict_tgt_items['CompositeShortAmountInMarginAccount']

        mn_ce_from_ss_src1 = mn_cash_from_ss_src1

        # 求oacct提供的空头暴露预算值与多头暴露预算值
        # 求oacct账户中的存出保证金（net_asset）

        # ## src1
        list_dicts_oacct_basicinfo_src1 = list(
            self.gv.col_acctinfo.find({'DataDate': self.str_today, 'PrdCode': self.prdcode, 'AcctType': 'o'})
        )
        mn_net_exposure_from_oaccts_src1 = 0
        mn_capital_debt_in_oaccts_src1 = 0
        mn_ttasset_oacct = 0
        mn_liability_in_oacct_src1 = 0
        for dict_oacct_basicinfo_src1 in list_dicts_oacct_basicinfo_src1:
            if dict_oacct_basicinfo_src1:
                acctidbymxz_oacct = dict_oacct_basicinfo_src1['AcctIDByMXZ']
                dict_exposure_analysis_by_acctidbymxz = self.gv.col_exposure_analysis_by_acctidbymxz.find_one(
                    {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_oacct}
                )
                net_exposure_from_oacct_delta = dict_exposure_analysis_by_acctidbymxz['NetExposure']
                mn_net_exposure_from_oaccts_src1 += net_exposure_from_oacct_delta
                dict_bs_by_acctidbymxz = self.gv.col_bs_by_acctidbymxz.find_one(
                    {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_oacct}
                )
                mn_ttasset_oacct_delta = dict_bs_by_acctidbymxz['TotalAsset']
                mn_ttasset_oacct += mn_ttasset_oacct_delta
                mn_liability_oacct_delta = dict_bs_by_acctidbymxz['Liability']
                mn_liability_in_oacct_src1 += mn_liability_oacct_delta
                mn_capital_debt_in_oaccts_delta = dict_bs_by_acctidbymxz['CapitalDebt']
                mn_capital_debt_in_oaccts_src1 += mn_capital_debt_in_oaccts_delta

        if self.dict_tgt_items['NetExposureFromOTCAccounts']:
            mn_net_exposure_from_oaccts_src1 = self.dict_tgt_items['NetExposureFromOTCAccounts']

        # todo max模式补充： 单渠道，双渠道
        # todo 期货户满仓资金？ 如果有融券，满仓是怎么计算？假设： 按照资金利用率最大计算
        # todo 对于EI与MN来说，满仓-空仓状态下期货户所留的资金的变动趋势是相反的
        # 不管是什么模式，都要解满仓状态下的核心方程组，来求出满仓状态下期货户应留的资金。即：对于定仓位的产品，需要解2次方程组。
        # max_asset 模式：最大化资金利用率，用float 格式 9 表示

        # 解满仓方程组
        # 未知量
        ei_cpslongamt_src1 = Symbol('ei_cpslongamt_src1', real=True, nonnegative=True)
        ei_ce_from_cash_available_src1 = Symbol('ei_ce_from_cash_available_src1', real=True)
        mn_cpslongamt_src1 = Symbol('mn_cpslongamt_src1', real=True, nonnegative=True)
        mn_ce_from_cash_available_src1 = Symbol('mn_ce_from_cash_available_src1', real=True, )
        ei_iclots_src1 = Symbol('ei_iclots_src1', real=True)
        mn_iclots_src1 = Symbol('mn_iclots_src1', real=True)
        list_eqs_2b_solved = []

        if self.tgt_cpspct == 9:
            eq_ei_ce_src1 = ei_ce_from_cash_available_src1
            eq_mn_ce_src1 = mn_ce_from_cash_available_src1
            list_eqs_2b_solved.append(eq_ei_ce_src1)
            list_eqs_2b_solved.append(eq_mn_ce_src1)
        else:
            eq_ei_cpslongamt_tgt = ei_cpslongamt_src1 - self.ei_na_tgt * self.tgt_cpspct
            eq_mn_cpslongamt_tgt = mn_cpslongamt_src1 - self.mn_na_tgt * self.tgt_cpspct
            list_eqs_2b_solved.append(eq_ei_cpslongamt_tgt)
            list_eqs_2b_solved.append(eq_mn_cpslongamt_tgt)

        # 核心方程组-总资产等式
        # todo 检查ei方程 要不要合一起？ 多策略产品的期指会出现节省金额
        eq_ei_na_src1 = (
                ei_cpslongamt_src1 * (1 + self.gv.flt_cash2cpslongamt)
                + ei_ce_from_cash_available_src1
                + ei_ce_from_ss_src1
                + ei_etflongamt_src1
                + ei_special_na_src1
                + abs(ei_iclots_src1) * self.gv.dict_index_future2internal_required_na_per_lot[self.gv.index_future]
                - ei_na_src1_tgt
                - ei_liability_src1
        )

        eq_mn_na_src1 = (
                mn_cpslongamt_src1 * (1 + self.gv.flt_cash2cpslongamt)
                + mn_ce_from_cash_available_src1
                + mn_ce_from_ss_src1
                + mn_etflongamt_src1
                + mn_special_na_src1
                + abs(mn_iclots_src1) * self.gv.dict_index_future2internal_required_na_per_lot[self.gv.index_future]
                + mn_ttasset_oacct
                - mn_na_src1_tgt
                - mn_capital_debt_in_macct_src1
                - mn_security_debt_in_macct_src1
                - mn_liability_in_oacct_src1
        )
        list_eqs_2b_solved.append(eq_mn_na_src1)
        list_eqs_2b_solved.append(eq_ei_na_src1)

        # # 核心方程组-净资产
        # eq_na_src1 = (
        #         ei_cpslongamt_src1 * (1 + self.gv.flt_cash2cpslongamt)
        #         + ei_ce_from_cash_available_src1
        #         + ei_ce_from_ss_src1
        #         + ei_etflongamt_src1
        #         + ei_special_na_src1
        #         + abs(ei_iclots_src1 + mn_iclots_src1)
        #         * self.gv.dict_index_future2internal_required_na_per_lot[self.gv.index_future]
        #         - ei_na_src1_tgt
        #         - ei_liability_src1
        #         + mn_cpslongamt_src1 * (1 + self.gv.flt_cash2cpslongamt)
        #         + mn_ce_from_cash_available_src1
        #         + mn_ce_from_ss_src1
        #         + mn_etflongamt_src1
        #         + mn_special_na_src1
        #         + mn_ttasset_oacct
        #         - mn_na_src1_tgt
        #         - mn_capital_debt_in_macct_src1
        #         - mn_security_debt_in_macct_src1
        #         - mn_liability_in_oacct_src1
        # )
        #
        # list_eqs_2b_solved.append(eq_na_src1)

        # 核心方程组-暴露
        eq_ei_exposure = (
                ei_cpslongamt_src1
                + ei_etflongamt_src1
                + ei_iclots_src1 * self.gv.dict_index_future2spot_exposure_per_lot[self.gv.index_future]
                - ei_cpsshortamt_src1
                - ei_etfshortamt_src1
                + ei_net_exposure_from_oaccts_src1
                - self.ei_na_tgt * 0.99
        )

        eq_mn_exposure = (
                mn_cpslongamt_src1
                + mn_etflongamt_src1
                + mn_iclots_src1 * self.gv.dict_index_future2spot_exposure_per_lot[self.gv.index_future]
                - mn_cpsshortamt_src1
                - mn_etfshortamt_src1
                + mn_net_exposure_from_oaccts_src1
        )
        list_eqs_2b_solved.append(eq_ei_exposure)
        list_eqs_2b_solved.append(eq_mn_exposure)

        # eq_exposure = (
        #         ei_cpslongamt_src1
        #         + ei_etflongamt_src1
        #         + (ei_iclots_src1 + mn_iclots_src1) * self.gv.dict_index_future2spot_exposure_per_lot[self.gv.index_future]
        #         - ei_cpsshortamt_src1
        #         - ei_etfshortamt_src1
        #         + ei_net_exposure_from_oaccts_src1
        #         - self.ei_na_tgt * 0.99
        #         + mn_cpslongamt_src1
        #         + mn_etflongamt_src1
        #         - mn_cpsshortamt_src1
        #         - mn_etfshortamt_src1
        #         + mn_net_exposure_from_oaccts_src1
        # )
        # list_eqs_2b_solved.append(eq_exposure)
        # 解核心方程组（满仓状态）
        list_tuples_eqs_solve_under_max_cpspct = solve(list_eqs_2b_solved,
                                                       ei_cpslongamt_src1, ei_ce_from_cash_available_src1,
                                                       mn_cpslongamt_src1, mn_ce_from_cash_available_src1,
                                                       ei_iclots_src1, mn_iclots_src1)
        tuple_eqs_solve = list_tuples_eqs_solve_under_max_cpspct[0]
        ei_cpslongamt_src1 = float(tuple_eqs_solve[0])
        ei_ce_from_cash_available_src1 = float(tuple_eqs_solve[1])
        mn_cpslongamt_src1 = float(tuple_eqs_solve[2])
        mn_ce_from_cash_available_src1 = float(tuple_eqs_solve[3])
        ei_iclots_src1 = float(tuple_eqs_solve[4])
        mn_iclots_src1 = float(tuple_eqs_solve[5])
        iclots_total = int(ei_iclots_src1) + round(mn_iclots_src1)
        na_faccts = (
                abs(iclots_total) * self.gv.dict_index_future2internal_required_na_per_lot[self.gv.index_future]
        )
        cpslongamt_src1 = ei_cpslongamt_src1 + mn_cpslongamt_src1
        ce_from_cash_available_src1 = ei_ce_from_cash_available_src1 + mn_ce_from_cash_available_src1

        # 资金分配(cacct 与 macct)
        # 原则上，信用户如有负债则在信用户中留足够且仅够开满仓的净资产，但事实上一半无法保证实时达到。
        acctidbymxz_cacct_src1 = self.gv.col_acctinfo.find_one(
            {
                'PrdCode': self.prdcode,
                'AcctType': 'c',
                'DataDate': self.str_today,
                'RptMark': 1,
                'SpecialAccountMark': 0
            }
        )['AcctIDByMXZ']
        dict_macct_basicinfo = self.gv.col_acctinfo.find_one(
            {
                'PrdCode': self.prdcode,
                'AcctType': 'm',
                'DataDate': self.str_today,
                'RptMark': 1,
                'SpecialAccountMark': 0,
                'AcctStatus': 'T',
            }
        )
        if dict_macct_basicinfo:
            acctidbymxz_macct_src1 = dict_macct_basicinfo['AcctIDByMXZ']
        else:
            acctidbymxz_macct_src1 = None

        cpslongamt_in_macct_src1 = None
        na_macct_src1 = None
        cash_available_in_macct_src1 = None
        # todo 此处假设： 若macct中不满仓，则可用于交易的现金对应的货基应全部转至cacct，故macct中ce_from_cash_available为0
        # todo 注意，需要分情况讨论： 当担保品充足时，当担保品不足时
        # todo 当担保品充足时，macct总资产 = 卖出融券所得资金 + 目标持仓市值 * (1 + self.gv.flt_cash2cpslongamt) + 用于补充担保品的ce
        # todo 当担保品充足时，macct净资产 = macct总资产 - macct负债
        # todo 信用户中可用资金的锁定

        ce_from_cash_available_in_macct_src1 = 0
        ce_from_cash_from_ss_src1 = mn_ce_from_ss_src1

        if dict_macct_basicinfo:
            dict_bs_by_acctidbymxz = self.gv.col_bs_by_acctidbymxz.find_one(
                {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_macct_src1}
            )
            ttasset_macct = dict_bs_by_acctidbymxz['TotalAsset']
            liability_macct = dict_bs_by_acctidbymxz['Liability']
            if liability_macct:
                margin_maintenance_ratio = ttasset_macct / liability_macct
            else:
                margin_maintenance_ratio = 999999999
            if margin_maintenance_ratio <= 1.5:
                print(f'Warning: {dict_macct_basicinfo["AcctIDByMXZ"]} margin maintenance ratio {margin_maintenance_ratio}, may be not sufficient.')

            cpslongamt_in_macct_src1 = cpslongamt_src1
            cash_available_in_macct_src1 = cpslongamt_src1 * self.gv.flt_cash2cpslongamt
            na_cacct_src1 = ce_from_cash_available_src1
            na_macct_src1 = (
                    cpslongamt_in_macct_src1
                    + cash_available_in_macct_src1
                    + ce_from_cash_from_ss_src1
                    - liability_macct
            )
            cpslongamt_in_cacct_src1 = 0
            if na_cacct_src1 > 2500000:
                ce_in_cacct_src1 = na_cacct_src1 - 2500000
                cash_available_in_cacct_src1 = 2500000
            else:
                ce_in_cacct_src1 = 0
                cash_available_in_cacct_src1 = na_cacct_src1
        else:
            cpslongamt_in_cacct_src1 = cpslongamt_src1
            ce_in_cacct_src1 = ce_from_cash_available_src1
            cash_available_in_cacct_src1 = cpslongamt_in_cacct_src1 * self.gv.flt_cash2cpslongamt
            na_cacct_src1 = cpslongamt_src1 + ce_in_cacct_src1 + cash_available_in_cacct_src1

        list_dicts_bgt_secaccts = [
            {
                'DataDate': self.str_today,
                'PrdCode': self.prdcode,
                'AcctIDByMXZ': acctidbymxz_cacct_src1,
                'NAV': na_cacct_src1,
                'CPSLongAmt': cpslongamt_in_cacct_src1,
                'ICLots': None,
                'CashAvailable': cash_available_in_cacct_src1,
                'CEFromCashFromSS': None,
                'CEFromCashAvailable': ce_in_cacct_src1,
            },
            {
                'DataDate': self.str_today,
                'PrdCode': self.prdcode,
                'AcctIDByMXZ': f'{self.prdcode}_faccts',
                'NAV': na_faccts,
                'CPSLongAmt': None,
                'ICLots': iclots_total,
                'CEFromCashFromSS': None,
                'CEFromCashAvailable': None,
            }
        ]

        dict_bgt_macct_src1 = {
            'DataDate': self.str_today,
            'PrdCode': self.prdcode,
            'AcctIDByMXZ': acctidbymxz_macct_src1,
            'NAV': na_macct_src1,
            'CPSLongAmt': cpslongamt_in_macct_src1,
            'ICLots': None,
            'CashAvailable': cash_available_in_macct_src1,
            'CEFromCashFromSS': ce_from_cash_from_ss_src1,
            'CEFromCashAvailable': ce_from_cash_available_in_macct_src1,
        }
        if acctidbymxz_macct_src1:
            list_dicts_bgt_secaccts.append(dict_bgt_macct_src1)

        self.list_dicts_bgt_by_acctidbymxz += list_dicts_bgt_secaccts
        self.allocate_faccts(iclots_total)

    def output_trdplan_order(self):
        # todo 添加过滤器
        # 今资金划转计划
        list_dicts_bgt_by_acctidbymxz = list(
            self.gv.col_bgt_by_acctidbymxz
                .find({'DataDate': self.str_today, 'PrdCode': self.prdcode})
        )
        list_str_orders_capital_outflow = []
        list_str_orders_capital_inflow = []

        for dict_bgt_by_acctidbymxz in list_dicts_bgt_by_acctidbymxz:
            acctidbymxz = dict_bgt_by_acctidbymxz['AcctIDByMXZ']
            if acctidbymxz.split('_')[1] == 'faccts':
                continue

            special_acct_mark = self.gv.col_acctinfo.find_one(
                {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz}
            )['SpecialAccountMark']
            if special_acct_mark:
                continue

            nav_bgt = dict_bgt_by_acctidbymxz['NAV']
            dict_bs_by_acctidbymxz = self.gv.col_bs_by_acctidbymxz.find_one(
                {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz}
            )
            approximate_na = dict_bs_by_acctidbymxz['ApproximateNetAsset']
            capital_dif = approximate_na - nav_bgt
            # 精度调整
            capital_dif_round = round(capital_dif / 50000) * 5
            prdcode = acctidbymxz.split('_')[0]
            accttype = acctidbymxz.split('_')[1]
            broker_abbr = acctidbymxz.split('_')[2]
            dict_accttype2natual_language = {'c': '证', 'm': '证', 'f': '期'}
            dict_accttype2cmname = {'c': '（普通）', 'm': '（信用）'}
            dict_accttype2natual_language_with_secsrc_and_cmname = {
                'c': f'（{self.gv.dict_broker_abbr2broker_alias[broker_abbr]}普通）',
                'm': f'（{self.gv.dict_broker_abbr2broker_alias[broker_abbr]}信用）',
                'f': f'（{self.gv.dict_broker_abbr2broker_alias[broker_abbr]}）'
            }
            dict_accttype2natual_language_with_secsrc = {
                'c': f'（{self.gv.dict_broker_abbr2broker_alias[broker_abbr]}）',
                'm': f'（{self.gv.dict_broker_abbr2broker_alias[broker_abbr]}）',
                'f': f'（{self.gv.dict_broker_abbr2broker_alias[broker_abbr]}）'
            }
            dict_acctinfo_for_m_mark = self.gv.col_acctinfo.find_one(
                {'DataDate': self.str_today, 'AcctType': 'm', 'PrdCode': prdcode, 'BrokerAbbr': broker_abbr}
            )

            if self.dict_na_allocation:
                if self.dict_na_allocation['SecurityAccountsNetAssetAllocation']:
                    if self.dict_na_allocation['FutureAccountsNetAssetAllocation']:
                        if dict_acctinfo_for_m_mark:
                            if capital_dif_round > 0:
                                str_order_capital = (
                                    f'{dict_accttype2natual_language[accttype]}'
                                    f'{dict_accttype2natual_language_with_secsrc_and_cmname[accttype]}转银'
                                    f'{abs(capital_dif_round)}万'
                                )
                            elif capital_dif_round < 0:
                                str_order_capital = (
                                    f'银转{dict_accttype2natual_language[accttype]}'
                                    f'{dict_accttype2natual_language_with_secsrc_and_cmname[accttype]}'
                                    f'{abs(capital_dif_round)}万'
                                )
                            else:
                                str_order_capital = ''
                        else:
                            str_order_capital = (
                                f'{dict_accttype2natual_language[accttype]}'
                                f'{dict_accttype2natual_language_with_secsrc_and_cmname[accttype]}转银'
                                f'{abs(capital_dif_round)}万'
                            )
                    else:
                        if accttype == 'f':
                            if capital_dif_round > 0:
                                str_order_capital = f'期转银{abs(capital_dif_round)}万'
                            elif capital_dif_round < 0:
                                str_order_capital = f'银转期{abs(capital_dif_round)}万'
                            else:
                                str_order_capital = ''
                        else:
                            if dict_acctinfo_for_m_mark:
                                if capital_dif_round > 0:
                                    str_order_capital = (
                                        f'{dict_accttype2natual_language[accttype]}'
                                        f'{dict_accttype2natual_language_with_secsrc_and_cmname[accttype]}转银'
                                        f'{abs(capital_dif_round)}万'
                                    )
                                elif capital_dif_round < 0:
                                    str_order_capital = (
                                        f'银转{dict_accttype2natual_language[accttype]}'
                                        f'{dict_accttype2natual_language_with_secsrc_and_cmname[accttype]}'
                                        f'{abs(capital_dif_round)}万'
                                    )
                                else:
                                    str_order_capital = ''
                            else:
                                if capital_dif_round > 0:
                                    str_order_capital = (
                                        f'{dict_accttype2natual_language[accttype]}'
                                        f'{dict_accttype2natual_language_with_secsrc[accttype]}转银'
                                        f'{abs(capital_dif_round)}万'
                                    )
                                elif capital_dif_round < 0:
                                    str_order_capital = (
                                        f'银转{dict_accttype2natual_language[accttype]}'
                                        f'{dict_accttype2natual_language_with_secsrc[accttype]}'
                                        f'{abs(capital_dif_round)}万'
                                    )
                                else:
                                    str_order_capital = ''
                else:
                    if accttype in ['c', 'm']:
                        if dict_acctinfo_for_m_mark:
                            if capital_dif_round > 0:
                                str_order_capital = f'证{dict_accttype2cmname[accttype]}转银{abs(capital_dif_round)}万'
                            elif capital_dif_round < 0:
                                str_order_capital = f'银转证{dict_accttype2cmname[accttype]}{abs(capital_dif_round)}万'
                            else:
                                str_order_capital = ''
                        else:
                            if capital_dif_round > 0:
                                str_order_capital = f'证转银{abs(capital_dif_round)}万'
                            elif capital_dif_round < 0:
                                str_order_capital = f'银转证{abs(capital_dif_round)}万'
                            else:
                                str_order_capital = ''
                    elif accttype in ['f']:
                        if self.dict_na_allocation['FutureAccountsNetAssetAllocation']:
                            if capital_dif_round > 0:
                                str_order_capital = (f'期{dict_accttype2natual_language_with_secsrc[accttype]}转银'
                                                     f'{abs(capital_dif_round)}万')
                            elif capital_dif_round < 0:
                                str_order_capital = (f'银转期{dict_accttype2natual_language_with_secsrc[accttype]}'
                                                     f'{abs(capital_dif_round)}万')
                            else:
                                str_order_capital = ''
                        else:
                            if capital_dif_round > 0:
                                str_order_capital = f'期转银{abs(capital_dif_round)}万'
                            elif capital_dif_round < 0:
                                str_order_capital = f'银转期{abs(capital_dif_round)}万'
                            else:
                                str_order_capital = ''
                    else:
                        raise ValueError('Unknown accttype')
            else:
                if accttype in ['c', 'm']:
                    if dict_acctinfo_for_m_mark:
                        if capital_dif_round > 0:
                            str_order_capital = f'证{dict_accttype2cmname[accttype]}转银{abs(capital_dif_round)}万'
                        elif capital_dif_round < 0:
                            str_order_capital = f'银转证{dict_accttype2cmname[accttype]}{abs(capital_dif_round)}万'
                        else:
                            str_order_capital = ''
                    else:
                        if capital_dif_round > 0:
                            str_order_capital = f'证转银{abs(capital_dif_round)}万'
                        elif capital_dif_round < 0:
                            str_order_capital = f'银转证{abs(capital_dif_round)}万'
                        else:
                            str_order_capital = ''
                elif accttype in ['f']:
                    if capital_dif_round > 0:
                        str_order_capital = f'期转银{abs(capital_dif_round)}万'
                    elif capital_dif_round < 0:
                        str_order_capital = f'银转期{abs(capital_dif_round)}万'
                    else:
                        str_order_capital = ''
                else:
                    raise ValueError('Unknown accttype')

            if capital_dif_round > 0:
                list_str_orders_capital_outflow.append(str_order_capital)
            elif capital_dif_round < 0:
                list_str_orders_capital_inflow.append(str_order_capital)
            else:
                pass

        list_dicts_bs_by_acctidbymxz = list(
            self.gv.col_bs_by_acctidbymxz.find({'DataDate': self.str_today, 'PrdCode': self.prdcode})
        )
        for dict_bs_by_acctidbymxz in list_dicts_bs_by_acctidbymxz:
            acctidbymxz_in_bs = dict_bs_by_acctidbymxz['AcctIDByMXZ']
            approximate_na = dict_bs_by_acctidbymxz['ApproximateNetAsset']
            dict_bgt_by_acctidbymxz = self.gv.col_bgt_by_acctidbymxz.find_one(
                {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_in_bs}
            )

            if dict_bgt_by_acctidbymxz is None:
                if approximate_na > 0:
                    accttype = acctidbymxz_in_bs.split('_')[1]
                    if accttype in ['o']:
                        continue
                    broker_abbr = acctidbymxz_in_bs.split('_')[2]
                    dict_accttype2natual_language = {'c': '证', 'm': '证', 'f': '期'}
                    dict_accttype2natual_language_with_secsrc_and_cmname = {
                        'c': f'（{self.gv.dict_broker_abbr2broker_alias[broker_abbr]}普通）',
                        'm': f'（{self.gv.dict_broker_abbr2broker_alias[broker_abbr]}信用）',
                        'f': f'（{self.gv.dict_broker_abbr2broker_alias[broker_abbr]}）'
                    }
                    str_order_capital = (
                        f'{dict_accttype2natual_language[accttype]}'
                        f'{dict_accttype2natual_language_with_secsrc_and_cmname[accttype]}转银全部'
                    )
                    list_str_orders_capital_outflow.append(str_order_capital)
        list_str_orders_capital_outflow.sort()
        list_str_orders_capital_inflow.sort()
        list_str_orders_capital = list_str_orders_capital_outflow + list_str_orders_capital_inflow
        str_orders_capital = '\n'.join(list_str_orders_capital)
        # 今交易组合计划开始
        # 在内存建立数据表类型条目，记录调整敞口后的各期货账户holding
        list_dicts_facct_holding_aggr_after_exposure_adjustment_by_acctidbymxz = []
        list_order_exposure_adjustment = []
        net_exposure_dif = self.dict_exposure_analysis_by_prdcode['NetExposureDif']
        iclots_rounded2adjust_exposure_by_prdcode = round(
            net_exposure_dif / self.gv.dict_index_future2spot_exposure_per_lot[self.gv.index_future]
        )
        # 开盘即平掉敞口
        # todo 在多期货户的条件下，会出现操作冗余
        if iclots_rounded2adjust_exposure_by_prdcode:
            if self.dict_na_allocation:
                if self.dict_na_allocation['FutureAccountsNetAssetAllocation']:
                    for key, value in self.dict_na_allocation['FutureAccountsNetAssetAllocation'].items():
                        dict_trdplan_expression = self.gv.col_trdplan_expression.find_one(
                            {'DataDate': self.str_today, 'CapitalSrc': key}
                        )
                        str_trdplan_expression = dict_trdplan_expression['TrdPlanExpression']
                        iclots_rounded2adjust_exposure_after_allocation = round(
                            iclots_rounded2adjust_exposure_by_prdcode * value
                        )
                        list_dicts_acctinfo_facct = list(
                            self.gv.col_acctinfo.find(
                                {
                                    'DataDate': self.str_today,
                                    'PrdCode': self.prdcode,
                                    'AcctType': 'f',
                                    'CapitalSource': key,
                                    'AcctStatus': 'T',
                                    'RptMark': 1
                                }
                            )
                        )
                        i_accts_f_t = len(list_dicts_acctinfo_facct)
                        if i_accts_f_t != 1:
                            raise ValueError('Wrong facct number, please check col_acctinfo.')

                        dict_acctinfo_facct = list_dicts_acctinfo_facct[0]
                        acctidbymxz = dict_acctinfo_facct['AcctIDByMXZ']

                        dict_holding_aggr_by_acctidbymxz = self.gv.col_facct_holding_aggr_by_acctidbymxz.find_one(
                            {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz}
                        )['holding_aggr_by_secid_first_part']

                        if 'IC' in dict_holding_aggr_by_acctidbymxz:
                            iclots_in_facct_holding_aggr_by_acctidbymxz = dict_holding_aggr_by_acctidbymxz['IC']
                        else:
                            iclots_in_facct_holding_aggr_by_acctidbymxz = 0

                        iclots_after_exposure_adjustment = (
                                iclots_in_facct_holding_aggr_by_acctidbymxz
                                - iclots_rounded2adjust_exposure_after_allocation
                        )

                        dict_facct_holding_aggr_after_exposure_adjustment_by_acctidbymxz = {
                            'DataDate': self.str_today,
                            'AcctIDByMXZ': acctidbymxz,
                            'PrdCode': self.prdcode,
                            'ICLotsAfterExposureAdjustment': iclots_after_exposure_adjustment
                        }

                        list_dicts_facct_holding_aggr_after_exposure_adjustment_by_acctidbymxz.append(
                            dict_facct_holding_aggr_after_exposure_adjustment_by_acctidbymxz
                        )

                        if iclots_in_facct_holding_aggr_by_acctidbymxz * iclots_after_exposure_adjustment >= 0:
                            if iclots_rounded2adjust_exposure_after_allocation < 0:  # Buy
                                if iclots_after_exposure_adjustment > 0:
                                    str_order_exposure_adjustment_delta = (
                                        f'{str_trdplan_expression}开'
                                        f'{abs(iclots_rounded2adjust_exposure_after_allocation)}手IC多头'
                                    )
                                else:
                                    str_order_exposure_adjustment_delta = (
                                        f'{str_trdplan_expression}'
                                        f'平{abs(iclots_rounded2adjust_exposure_after_allocation)}手IC空头'
                                    )
                            elif iclots_rounded2adjust_exposure_after_allocation > 0:  # Sell
                                if iclots_after_exposure_adjustment >= 0:
                                    str_order_exposure_adjustment_delta = (
                                        f'{str_trdplan_expression}'
                                        f'平{abs(iclots_rounded2adjust_exposure_after_allocation)}手IC多头'
                                    )
                                else:
                                    str_order_exposure_adjustment_delta = (
                                        f'{str_trdplan_expression}'
                                        f'开{abs(iclots_rounded2adjust_exposure_after_allocation)}手IC空头'
                                    )
                            else:
                                str_order_exposure_adjustment_delta = ''
                        else:
                            if iclots_rounded2adjust_exposure_after_allocation < 0:  # Buy
                                str_order_exposure_adjustment_delta = (
                                    f'{str_trdplan_expression}'
                                    f'平{abs(iclots_in_facct_holding_aggr_by_acctidbymxz)}手IC空头，'
                                    f'开{abs(iclots_after_exposure_adjustment)}手IC多头')
                            elif iclots_rounded2adjust_exposure_after_allocation > 0:  # Sell
                                str_order_exposure_adjustment_delta = (
                                    f'{str_trdplan_expression}'
                                    f'平{abs(iclots_in_facct_holding_aggr_by_acctidbymxz)}手IC多头，'
                                    f'开{abs(iclots_after_exposure_adjustment)}手IC空头')
                            else:
                                str_order_exposure_adjustment_delta = ''
                        list_order_exposure_adjustment.append(str_order_exposure_adjustment_delta)
                    str_order_exposure_adjustment = '，'.join(list_order_exposure_adjustment)

                else:
                    list_dicts_acctinfo_facct = list(
                        self.gv.col_acctinfo.find(
                            {
                                'DataDate': self.str_today,
                                'PrdCode': self.prdcode,
                                'AcctType': 'f',
                                'AcctStatus': 'T',
                                'RptMark': 1
                            }
                        )
                    )
                    i_accts_f_t = len(list_dicts_acctinfo_facct)
                    if i_accts_f_t != 1:
                        raise ValueError('Wrong facct number, please check col_acctinfo.')

                    # todo 重要假设：期货空头只使用IC
                    dict_acctinfo_facct = list_dicts_acctinfo_facct[0]
                    acctidbymxz = dict_acctinfo_facct['AcctIDByMXZ']

                    dict_holding_aggr_by_acctidbymxz = self.gv.col_facct_holding_aggr_by_acctidbymxz.find_one(
                        {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz}
                    )['holding_aggr_by_secid_first_part']

                    if 'IC' in dict_holding_aggr_by_acctidbymxz:
                        iclots_in_facct_holding_aggr_by_acctidbymxz = dict_holding_aggr_by_acctidbymxz['IC']
                    else:
                        iclots_in_facct_holding_aggr_by_acctidbymxz = 0

                    iclots_after_exposure_adjustment = (
                            iclots_in_facct_holding_aggr_by_acctidbymxz - iclots_rounded2adjust_exposure_by_prdcode
                    )

                    dict_facct_holding_aggr_after_exposure_adjustment_by_acctidbymxz = {
                        'DataDate': self.str_today,
                        'AcctIDByMXZ': acctidbymxz,
                        'PrdCode': self.prdcode,
                        'ICLotsAfterExposureAdjustment': iclots_after_exposure_adjustment
                    }
                    list_dicts_facct_holding_aggr_after_exposure_adjustment_by_acctidbymxz.append(
                        dict_facct_holding_aggr_after_exposure_adjustment_by_acctidbymxz
                    )

                    if iclots_in_facct_holding_aggr_by_acctidbymxz * iclots_after_exposure_adjustment >= 0:
                        if iclots_rounded2adjust_exposure_by_prdcode < 0:  # Buy
                            if iclots_after_exposure_adjustment > 0:
                                str_order_exposure_adjustment = (
                                    f'开{abs(iclots_rounded2adjust_exposure_by_prdcode)}手IC多头'
                                )
                            else:
                                str_order_exposure_adjustment = (
                                    f'平{abs(iclots_rounded2adjust_exposure_by_prdcode)}手IC空头'
                                )
                        elif iclots_rounded2adjust_exposure_by_prdcode > 0:  # Sell
                            if iclots_after_exposure_adjustment >= 0:
                                str_order_exposure_adjustment = (
                                    f'平{abs(iclots_rounded2adjust_exposure_by_prdcode)}手IC多头'
                                )
                            else:
                                str_order_exposure_adjustment = (
                                    f'开{abs(iclots_rounded2adjust_exposure_by_prdcode)}手IC空头'
                                )
                        else:
                            str_order_exposure_adjustment = ''
                    else:
                        if iclots_rounded2adjust_exposure_by_prdcode < 0:  # Buy
                            str_order_exposure_adjustment = (
                                f'平{abs(iclots_in_facct_holding_aggr_by_acctidbymxz)}手IC空头，'
                                f'开{abs(iclots_after_exposure_adjustment)}手IC多头'
                            )
                        elif iclots_rounded2adjust_exposure_by_prdcode > 0:  # Sell
                            str_order_exposure_adjustment = (
                                f'平{abs(iclots_in_facct_holding_aggr_by_acctidbymxz)}手IC多头，'
                                f'开{abs(iclots_after_exposure_adjustment)}手IC空头'
                            )
                        else:
                            str_order_exposure_adjustment = ''
            else:
                list_dicts_acctinfo_facct = list(
                    self.gv.col_acctinfo.find(
                        {
                            'DataDate': self.str_today,
                            'PrdCode': self.prdcode,
                            'AcctType': 'f',
                            'AcctStatus': 'T',
                            'RptMark': 1
                        }
                    )
                )
                i_accts_f_t = len(list_dicts_acctinfo_facct)
                if i_accts_f_t != 1:
                    raise ValueError('Wrong facct number, please check col_acctinfo.')

                # todo 重要假设：期货空头只使用IC
                dict_acctinfo_facct = list_dicts_acctinfo_facct[0]
                acctidbymxz = dict_acctinfo_facct['AcctIDByMXZ']

                dict_facct_holding_aggr_by_acctidbymxz = self.gv.col_facct_holding_aggr_by_acctidbymxz.find_one(
                    {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz}
                )
                dict_holding_aggr_by_acctidbymxz = (
                    dict_facct_holding_aggr_by_acctidbymxz['holding_aggr_by_secid_first_part']
                )
                if 'IC' in dict_holding_aggr_by_acctidbymxz:
                    iclots_in_facct_holding_aggr_by_acctidbymxz = dict_holding_aggr_by_acctidbymxz['IC']
                else:
                    iclots_in_facct_holding_aggr_by_acctidbymxz = 0

                iclots_after_exposure_adjustment = (
                        iclots_in_facct_holding_aggr_by_acctidbymxz - iclots_rounded2adjust_exposure_by_prdcode
                )

                dict_facct_holding_aggr_after_exposure_adjustment_by_acctidbymxz = {
                    'DataDate': self.str_today,
                    'AcctIDByMXZ': acctidbymxz,
                    'PrdCode': self.prdcode,
                    'ICLotsAfterExposureAdjustment': iclots_after_exposure_adjustment
                }
                list_dicts_facct_holding_aggr_after_exposure_adjustment_by_acctidbymxz.append(
                    dict_facct_holding_aggr_after_exposure_adjustment_by_acctidbymxz
                )

                if iclots_in_facct_holding_aggr_by_acctidbymxz * iclots_after_exposure_adjustment >= 0:
                    if iclots_rounded2adjust_exposure_by_prdcode < 0:  # Buy
                        if iclots_after_exposure_adjustment > 0:
                            str_order_exposure_adjustment = (
                                f'开{abs(iclots_rounded2adjust_exposure_by_prdcode)}手IC多头'
                            )
                        else:
                            str_order_exposure_adjustment = (
                                f'平{abs(iclots_rounded2adjust_exposure_by_prdcode)}手IC空头'
                            )
                    elif iclots_rounded2adjust_exposure_by_prdcode > 0:  # Sell
                        if iclots_after_exposure_adjustment >= 0:
                            str_order_exposure_adjustment = (
                                f'平{abs(iclots_rounded2adjust_exposure_by_prdcode)}手IC多头'
                            )
                        else:
                            str_order_exposure_adjustment = (
                                f'开{abs(iclots_rounded2adjust_exposure_by_prdcode)}手IC空头'
                            )
                    else:
                        str_order_exposure_adjustment = ''
                else:
                    if iclots_rounded2adjust_exposure_by_prdcode < 0:  # Buy
                        str_order_exposure_adjustment = (
                            f'平{abs(iclots_in_facct_holding_aggr_by_acctidbymxz)}手IC空头，'
                            f'开{abs(iclots_after_exposure_adjustment)}手IC多头'
                        )
                    elif iclots_rounded2adjust_exposure_by_prdcode > 0:  # Sell
                        str_order_exposure_adjustment = (
                            f'平{abs(iclots_in_facct_holding_aggr_by_acctidbymxz)}手IC多头，'
                            f'开{abs(iclots_after_exposure_adjustment)}手IC空头'
                        )
                    else:
                        str_order_exposure_adjustment = ''
        else:  # 若无敞口调整事项，则list_dicts_facct_holding_aggr_after_exposure_adjustment_by_acctidbymxz不变
            list_dicts_facct_holding_aggr_by_acctidbymxz = self.gv.col_facct_holding_aggr_by_acctidbymxz.find(
                {'DataDate': self.str_today, 'PrdCode': self.prdcode}
            )
            for dict_facct_holding_aggr_by_acctidbymxz in list_dicts_facct_holding_aggr_by_acctidbymxz:
                acctidbymxz = dict_facct_holding_aggr_by_acctidbymxz['AcctIDByMXZ']
                datadate = dict_facct_holding_aggr_by_acctidbymxz['DataDate']
                prdcode = dict_facct_holding_aggr_by_acctidbymxz['PrdCode']
                dict_holding_aggr_by_secid_first_part = (
                    dict_facct_holding_aggr_by_acctidbymxz['holding_aggr_by_secid_first_part']
                )
                if 'IC' in dict_holding_aggr_by_secid_first_part:
                    iclots_after_exposure_adjustment = dict_holding_aggr_by_secid_first_part['IC']
                else:
                    iclots_after_exposure_adjustment = 0
                dict_facct_holding_aggr_after_exposure_adjustment_by_acctidbymxz = {
                    'DataDate': datadate,
                    'AcctIDByMXZ': acctidbymxz,
                    'PrdCode': prdcode,
                    'ICLotsAfterExposureAdjustment': iclots_after_exposure_adjustment
                }
                list_dicts_facct_holding_aggr_after_exposure_adjustment_by_acctidbymxz.append(
                    dict_facct_holding_aggr_after_exposure_adjustment_by_acctidbymxz
                )
            str_order_exposure_adjustment = ''

        # 今组合交易计划 - 货基、目标持仓、期指
        list_str_orders_position_saccts = []
        list_str_orders_position_faccts_sum_part = []
        list_str_orders_position_faccts_bracket_part = []
        str_warning_from_exposure_adjustment = ''
        for dict_bgt_by_acctidbymxz in list_dicts_bgt_by_acctidbymxz:
            acctidbymxz = dict_bgt_by_acctidbymxz['AcctIDByMXZ']
            prdcode = acctidbymxz.split('_')[0]
            accttype = acctidbymxz.split('_')[1]
            dict_accttype2broker_type = {'c': 's', 'm': 's', 'f': 'f'}
            dict_acctinfo_for_t_mark = self.gv.col_acctinfo.find_one(
                {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz, 'AcctStatus': 'T'}
            )
            if accttype in ['c', 'm']:
                broker_abbr = acctidbymxz.split('_')[2]
                dict_acctinfo_for_m_mark = self.gv.col_acctinfo.find_one(
                    {'DataDate': self.str_today, 'AcctType': 'm', 'PrdCode': prdcode, 'BrokerAbbr': broker_abbr}
                )
                broker_type = dict_accttype2broker_type[accttype]
                dict_broker_info = self.gv.col_broker_info.find_one(
                    {'DataDate': self.str_today, 'BrokerAbbr': broker_abbr, 'BrokerType': broker_type}
                )
                broker_alias_in_trdplan = dict_broker_info['BrokerAliasInTrdPlan']
                # 特殊账户不做处理
                special_acct_mark = self.gv.col_acctinfo.find_one(
                    {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz}
                )['SpecialAccountMark']
                if special_acct_mark:
                    continue
                tgtpst = dict_bgt_by_acctidbymxz['CPSLongAmt']
                ce_from_cash_available_in_bgt_by_acctidbymxz = dict_bgt_by_acctidbymxz['CEFromCashAvailable']
                ce_from_cash_from_ss_in_bgt_by_acctidbymxz = dict_bgt_by_acctidbymxz['CEFromCashFromSS']
                if ce_from_cash_from_ss_in_bgt_by_acctidbymxz is None:
                    ce_from_cash_from_ss_in_bgt_by_acctidbymxz = 0

                ce_in_bgt_by_acctidbymxz = (
                        ce_from_cash_available_in_bgt_by_acctidbymxz + ce_from_cash_from_ss_in_bgt_by_acctidbymxz
                )
                ce_in_bs = self.gv.col_bs_by_acctidbymxz.find_one(
                    {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz}
                )['CashEquivalent']
                ce_delta = ce_in_bs - ce_in_bgt_by_acctidbymxz
                if ce_delta < -3000000:
                    str_order_ce = f'买货基{round(abs(ce_delta) / 500000) * 50}万，'
                elif ce_delta > 500000:
                    str_order_ce = f'卖货基{round(ce_delta / 500000) * 50}万，'
                else:
                    str_order_ce = ''

                # 假设每天都重新计算目标持仓
                if self.dict_na_allocation:
                    if self.dict_na_allocation['SecurityAccountsNetAssetAllocation']:
                        if dict_acctinfo_for_m_mark:
                            if dict_acctinfo_for_t_mark:
                                if accttype == 'c':
                                    str_order_position = (
                                        f'{broker_alias_in_trdplan}普通户{str_order_ce}目标持仓{round(tgtpst/500000)*50}万'
                                    )
                                elif accttype == 'm':
                                    str_order_position = (
                                        f'{broker_alias_in_trdplan}信用户{str_order_ce}目标持仓{round(tgtpst/500000)*50}万'
                                    )
                                else:
                                    raise ValueError('Unknown accttype')
                            else:
                                str_order_position = ''
                        else:
                            str_order_position = (
                                f'{broker_alias_in_trdplan}{str_order_ce}目标持仓{round(tgtpst/500000)*50}万'
                            )
                    else:
                        if dict_acctinfo_for_m_mark:
                            if dict_acctinfo_for_t_mark:
                                if accttype == 'c':
                                    str_order_position = f'普通户{str_order_ce}目标持仓{round(tgtpst / 500000) * 50}万'
                                elif accttype == 'm':
                                    str_order_position = f'信用户{str_order_ce}目标持仓{round(tgtpst / 500000) * 50}万'
                                else:
                                    raise ValueError('Unknown accttype')
                            else:
                                str_order_position = ''
                        else:
                            str_order_position = f'{str_order_ce}目标持仓{round(tgtpst / 500000) * 50}万'
                else:
                    if dict_acctinfo_for_m_mark:
                        if dict_acctinfo_for_t_mark:
                            if accttype == 'c':
                                str_order_position = f'普通户{str_order_ce}目标持仓{round(tgtpst / 500000) * 50}万'
                            elif accttype == 'm':
                                str_order_position = f'信用户{str_order_ce}目标持仓{round(tgtpst / 500000) * 50}万'
                            else:
                                raise ValueError('Unknown accttype')
                        else:
                            str_order_position = ''
                    else:
                        str_order_position = f'{str_order_ce}目标持仓{round(tgtpst / 500000) * 50}万'
                if str_order_position:
                    list_str_orders_position_saccts.append(str_order_position)

            # 期指总数部分
            elif accttype in ['faccts']:
                dict_facct_holding_aggr_by_prdcode = self.gv.col_facct_holding_aggr_by_prdcode.find_one(
                    {'DataDate': self.str_today, 'PrdCode': prdcode}
                )
                dict_holding_aggr_by_prdcode = dict_facct_holding_aggr_by_prdcode['holding_aggr_by_prdcode']
                if 'IC' in dict_holding_aggr_by_prdcode:
                    iclots_in_facct_holding_aggr_by_prdcode = dict_holding_aggr_by_prdcode['IC']
                else:
                    iclots_in_facct_holding_aggr_by_prdcode = 0

                iclots_in_bgt_by_acctidbymxz = dict_bgt_by_acctidbymxz['ICLots']
                if iclots_in_bgt_by_acctidbymxz > 0:
                    if iclots_in_bgt_by_acctidbymxz != iclots_in_facct_holding_aggr_by_prdcode:
                        str_order_position = f'{abs(iclots_in_bgt_by_acctidbymxz)}手IC多头'
                    else:
                        str_order_position = f'equal-{abs(iclots_in_bgt_by_acctidbymxz)}手IC多头'

                elif iclots_in_bgt_by_acctidbymxz < 0:
                    if iclots_in_bgt_by_acctidbymxz != iclots_in_facct_holding_aggr_by_prdcode:
                        str_order_position = f'{abs(iclots_in_bgt_by_acctidbymxz)}手IC空头'
                    else:
                        str_order_position = f'equal-{abs(iclots_in_bgt_by_acctidbymxz)}手IC空头'
                else:
                    # todo 商议表述形式
                    if iclots_in_facct_holding_aggr_by_prdcode > 0:
                        str_order_position = '清仓期指'
                    elif iclots_in_facct_holding_aggr_by_prdcode < 0:
                        str_order_position = '清仓期指'
                    else:
                        str_order_position = 'equal-清仓期指'
                list_str_orders_position_faccts_sum_part.append(str_order_position)

            # 期指括号内部分
            elif accttype in ['f']:
                broker_type = dict_accttype2broker_type[accttype]
                broker_abbr = acctidbymxz.split('_')[2]
                dict_broker_info = self.gv.col_broker_info.find_one(
                    {'DataDate': self.str_today, 'BrokerAbbr': broker_abbr, 'BrokerType': broker_type}
                )
                broker_alias_in_trdplan = dict_broker_info['BrokerAliasInTrdPlan']
                iclots_after_exposure_adjustment = None
                for dict_facct_holding_aggr_after_exposure_adjustment_by_acctidbymxz in (
                        list_dicts_facct_holding_aggr_after_exposure_adjustment_by_acctidbymxz
                ):
                    if acctidbymxz == dict_facct_holding_aggr_after_exposure_adjustment_by_acctidbymxz['AcctIDByMXZ']:
                        iclots_after_exposure_adjustment = (
                            dict_facct_holding_aggr_after_exposure_adjustment_by_acctidbymxz
                            ['ICLotsAfterExposureAdjustment']
                        )
                        # 0.16追保线报警
                        iclots_warning_margin_from_exposure_adjustment = (
                                iclots_after_exposure_adjustment
                                * self.gv.dict_index_future2internal_required_na_per_lot['IC']
                                * 0.8
                        )
                        dict_bs_by_acctidbymxz = self.gv.col_bs_by_acctidbymxz.find_one(
                            {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz}
                        )
                        approximate_na = dict_bs_by_acctidbymxz['ApproximateNetAsset']
                        # todo 敞口调整导致触发追保线的警告
                        if iclots_warning_margin_from_exposure_adjustment > approximate_na:
                            str_warning_from_exposure_adjustment = '（Waring: 调敞口导致期货户触发0.16）'

                iclots_in_bgt_by_acctidbymxz = dict_bgt_by_acctidbymxz['ICLots']
                iclots_delta = iclots_after_exposure_adjustment - iclots_in_bgt_by_acctidbymxz

                if self.dict_na_allocation:
                    if self.dict_na_allocation['FutureAccountsNetAssetAllocation']:
                        if iclots_after_exposure_adjustment * iclots_in_bgt_by_acctidbymxz >= 0:
                            if iclots_delta < 0:  # Buy
                                if iclots_in_bgt_by_acctidbymxz > 0:
                                    str_order_position = f'{broker_alias_in_trdplan}开{abs(iclots_delta)}手IC多头'
                                else:
                                    str_order_position = f'{broker_alias_in_trdplan}平{abs(iclots_delta)}手IC空头'
                            elif iclots_delta > 0:  # Sell
                                if iclots_in_bgt_by_acctidbymxz >= 0:
                                    str_order_position = f'{broker_alias_in_trdplan}平{abs(iclots_delta)}手IC多头'
                                else:
                                    str_order_position = f'{broker_alias_in_trdplan}开{abs(iclots_delta)}手IC空头'
                            else:
                                str_order_position = ''
                        else:
                            if iclots_delta < 0:  # Buy
                                str_order_position = (
                                    f'{broker_alias_in_trdplan}'
                                    f'平{abs(iclots_after_exposure_adjustment)}手IC空头，'
                                    f'开{abs(iclots_in_bgt_by_acctidbymxz)}手IC多头')
                            elif iclots_delta > 0:  # Sell
                                str_order_position = (
                                    f'{broker_alias_in_trdplan}'
                                    f'平{abs(iclots_after_exposure_adjustment)}手IC多头，'
                                    f'开{abs(iclots_in_bgt_by_acctidbymxz)}手IC空头')
                            else:
                                str_order_position = ''
                    else:
                        if iclots_after_exposure_adjustment * iclots_in_bgt_by_acctidbymxz >= 0:
                            if iclots_delta < 0:  # Buy
                                if iclots_in_bgt_by_acctidbymxz > 0:
                                    str_order_position = f'开{abs(iclots_delta)}手IC多头'
                                else:
                                    str_order_position = f'平{abs(iclots_delta)}手IC空头'
                            elif iclots_delta > 0:  # Sell
                                if iclots_in_bgt_by_acctidbymxz >= 0:
                                    str_order_position = f'平{abs(iclots_delta)}手IC多头'
                                else:
                                    str_order_position = f'开{abs(iclots_delta)}手IC空头'
                            else:
                                str_order_position = ''
                        else:
                            if iclots_delta < 0:  # Buy
                                str_order_position = (f'平{abs(iclots_after_exposure_adjustment)}手IC空头，'
                                                      f'开{abs(iclots_in_bgt_by_acctidbymxz)}手IC多头')
                            elif iclots_delta > 0:  # Sell
                                str_order_position = (f'平{abs(iclots_after_exposure_adjustment)}手IC多头，'
                                                      f'开{abs(iclots_in_bgt_by_acctidbymxz)}手IC空头')
                            else:
                                str_order_position = ''
                else:
                    if iclots_after_exposure_adjustment * iclots_in_bgt_by_acctidbymxz >= 0:
                        if iclots_delta < 0:  # Buy
                            if iclots_in_bgt_by_acctidbymxz > 0:
                                str_order_position = f'开{abs(iclots_delta)}手IC多头'
                            else:
                                str_order_position = f'平{abs(iclots_delta)}手IC空头'
                        elif iclots_delta > 0:  # Sell
                            if iclots_in_bgt_by_acctidbymxz >= 0:
                                str_order_position = f'平{abs(iclots_delta)}手IC多头'
                            else:
                                str_order_position = f'开{abs(iclots_delta)}手IC空头'
                        else:
                            str_order_position = ''
                    else:
                        if iclots_delta < 0:  # Buy
                            str_order_position = (f'平{abs(iclots_after_exposure_adjustment)}手IC空头，'
                                                  f'开{abs(iclots_in_bgt_by_acctidbymxz)}手IC多头')
                        elif iclots_delta > 0:  # Sell
                            str_order_position = (f'平{abs(iclots_after_exposure_adjustment)}手IC多头，'
                                                  f'开{abs(iclots_in_bgt_by_acctidbymxz)}手IC空头')
                        else:
                            str_order_position = ''
                if str_order_position:
                    list_str_orders_position_faccts_bracket_part.append(str_order_position)
            elif accttype in ['o']:
                continue
            else:
                raise ValueError('Unknown accttype.')

        if list_str_orders_position_saccts:
            str_orders_position_saccts = '，\n'.join(list_str_orders_position_saccts)
        else:
            str_orders_position_saccts = ''

        if list_str_orders_position_faccts_bracket_part:
            str_orders_position_faccts_bracket_part = f"（{'，'.join(list_str_orders_position_faccts_bracket_part)}）"
        else:
            str_orders_position_faccts_bracket_part = ''

        if str_orders_position_faccts_bracket_part:
            str_orders_position_faccts_sum_part = list_str_orders_position_faccts_sum_part[0].replace('equal-', '')
        else:
            str_orders_position_faccts_sum_part = ''

        str_orders_position_faccts = str_orders_position_faccts_sum_part + str_orders_position_faccts_bracket_part
        if str_orders_position_faccts:
            str_orders_position = f'{str_orders_position_saccts}，{str_orders_position_faccts}'
        else:
            str_orders_position = str_orders_position_saccts

        if str_order_exposure_adjustment:
            str_orders_exposure_adjustment_and_position = f"{str_order_exposure_adjustment}，\n{str_orders_position}"
        else:
            str_orders_exposure_adjustment_and_position = str_orders_position

        if str_warning_from_exposure_adjustment:
            str_orders_exposure_adjustment_and_position_and_warning = (
                f"{str_orders_exposure_adjustment_and_position}\n，{str_warning_from_exposure_adjustment}"
            )
        else:
            str_orders_exposure_adjustment_and_position_and_warning = f"{str_orders_exposure_adjustment_and_position}"

        signals_on_trdplan = self.dict_prdinfo['SignalsOnTrdPlan']

        # 凡是在今日仍保留的划款事项，均会体现到trdplan中。但只有状态为2与3的事项，才会影响tgtna 的计算。
        list_dicts_dwitems = list(
            self.gv.db_trddata['manually_patchdata_dwitems'].find(
                {'DataDate': self.str_today, 'PrdCode': self.prdcode}
            )
        )
        str_dwitems = ''
        for dict_dwitems in list_dicts_dwitems:
            dwbgt_netamt_estimated = round(dict_dwitems['DWBGTNetAmtEstimated'] / 10000)
            str_confirmation_date = dict_dwitems['UNAVConfirmationDate']
            str_expected_dwdate = dict_dwitems['ExpectedDWDate']
            dwtype = dict_dwitems['DWItem']
            if dwtype == 'P':
                str_dwitems_delta = (
                    f'申购{abs(dwbgt_netamt_estimated)}万 '
                    f'按照{str_confirmation_date}净值 {str_expected_dwdate}划款.\n'
                )
            elif dwtype == 'R':
                redemption_shares = dict_dwitems['Shares']
                str_dwitems_delta = (
                    f'赎回{abs(redemption_shares)}份（约计{abs(dwbgt_netamt_estimated)}万） '
                    f'按照{str_confirmation_date}净值 {str_expected_dwdate}划款.\n'
                )
            else:
                str_dwtype_display = dwtype
                str_dwitems_delta = (
                    f'{str_dwtype_display}{abs(dwbgt_netamt_estimated)}万 '
                    f'按照{str_confirmation_date}净值 {str_expected_dwdate}划款.\n'
                )
            str_dwitems += str_dwitems_delta

        accrued_performance_compensation_according_to_alpha_mark = self.dict_prdinfo['超额计提']
        if accrued_performance_compensation_according_to_alpha_mark:
            str_apcata_mark = 'y'
        else:
            str_apcata_mark = ''

        dict_holding_aggr = self.gv.col_facct_holding_aggr_by_prdcode.find_one(
            {'DataDate': self.str_today, 'PrdCode': self.prdcode}
        )['holding_aggr_by_prdcode']

        # 当前期指持仓
        list_str_future_index = []
        for key, value in dict_holding_aggr.items():
            if value > 0:
                str_future_index_delta = f'{abs(value)}手{key}多头'
            elif value < 0:
                str_future_index_delta = f'{abs(value)}手{key}空头'
            else:
                str_future_index_delta = ''
            if str_future_index_delta:
                list_str_future_index.append(str_future_index_delta)
        str_future_index = '\n'.join(list_str_future_index)

        # 当前股票持仓
        list_dicts_bs_by_acctidbymxz = self.gv.col_bs_by_acctidbymxz.find(
            {'DataDate': self.str_today, 'PrdCode': self.prdcode}
        )
        list_str_cpslongamt = []
        for dict_bs_by_acctidbymxz in list_dicts_bs_by_acctidbymxz:
            acctidbymxz = dict_bs_by_acctidbymxz['AcctIDByMXZ']
            accttype = acctidbymxz.split('_')[1]
            broker_abbr = acctidbymxz.split('_')[2]
            if accttype == 'c':
                cpslongamt_rounded = round(dict_bs_by_acctidbymxz['CompositeLongAmt'] / 500000) * 50
                if cpslongamt_rounded == 0:
                    continue
                str_cpslongamt_delta = (f'{self.gv.dict_broker_abbr2broker_alias[broker_abbr]}'
                                        f'普通户{cpslongamt_rounded}万')
            elif accttype == 'm':
                cpslongamt_rounded = round(dict_bs_by_acctidbymxz['CompositeLongAmt'] / 500000) * 50
                if cpslongamt_rounded == 0:
                    continue
                str_cpslongamt_delta = (f'{self.gv.dict_broker_abbr2broker_alias[broker_abbr]}'
                                        f'信用户{cpslongamt_rounded}万')
            else:
                str_cpslongamt_delta = ''
            if str_cpslongamt_delta:
                list_str_cpslongamt.append(str_cpslongamt_delta)
        str_cpslongamt = '\n'.join(list_str_cpslongamt)

        dict_trdplan_orders2gv = {
            '产品代码': self.prdcode,
            '证券自动交易': ' ',
            '期货自动交易': ' ',
            '产品名称': self.prdname,
            '总规模': f'{round(self.prd_approximate_na/10000)}',
            '最新净值': f'{round(self.latest_rptunav, 4)}',
            '信号': signals_on_trdplan,
            '今资金划转计划': str_orders_capital,
            '今资金划转执行': '',
            '明资金划转计划': '',
            '今日组合交易计划': str_orders_exposure_adjustment_and_position_and_warning,
            '今日组合交易执行': '',
            '明日组合交易计划': str_dwitems,
            '注意事项': '',
            '超额计提': str_apcata_mark,
            '当前股票持仓': str_cpslongamt,
            '当前期指持仓': str_future_index,
            '备注': '',
        }
        self.gv.list_dicts_trdplan_output.append(dict_trdplan_orders2gv)

        dict_trdplan_orders2mongodb = {
            'DataDate': self.str_today,
            '产品代码': self.prdcode,
            '证券自动交易': ' ',
            '期货自动交易': ' ',
            '产品名称': self.prdname,
            '总规模': f'{round(self.prd_approximate_na / 10000)}',
            '最新净值': f'{round(self.latest_rptunav, 4)}',
            '信号': signals_on_trdplan,
            '今资金划转计划': str_orders_capital,
            '今资金划转执行': '',
            '明资金划转计划': '',
            '今日组合交易计划': str_orders_exposure_adjustment_and_position_and_warning,
            '今日组合交易执行': '',
            '明日组合交易计划': str_dwitems,
            '注意事项': '',
            '超额计提': str_apcata_mark,
            '当前股票持仓': str_cpslongamt,
            '当前期指持仓': str_future_index,
            '备注': '',
        }

        self.gv.col_trdplan_output.delete_many({'DataDate': self.str_today, 'PrdCode': self.prdcode})
        if dict_trdplan_orders2gv:
            self.gv.col_trdplan_output.insert_one(dict_trdplan_orders2mongodb)

    def output_tgtcpsamt(self):
        list_dicts_acctinfo = self.gv.col_acctinfo.find(
            {
                'DataDate': self.str_today,
                'PrdCode': self.prdcode,
                'SpecialAccountMark': 0,
                'AcctStatus': 'T',
                'RptMark': 1,
            }
        )
        list_dicts_tgtcpsamt = []
        for dict_acctinfo in list_dicts_acctinfo:
            acctidbymxz = dict_acctinfo['AcctIDByMXZ']
            accttype = dict_acctinfo['AcctType']
            if accttype in ['c', 'm']:
                dict_cpsamt_in_bgt = self.gv.col_bgt_by_acctidbymxz.find_one(
                    {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz}
                )
                dict_cpsamt_in_bs = self.gv.col_bs_by_acctidbymxz.find_one(
                    {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz}
                )
                if dict_cpsamt_in_bgt:
                    tgtcpsamt = dict_cpsamt_in_bgt['CPSLongAmt']
                    dict_bs_by_acctidbymxz = self.gv.col_bs_by_acctidbymxz.find_one(
                        {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz}
                    )
                    if dict_bs_by_acctidbymxz:
                        real_cpsamt_pre_date = dict_cpsamt_in_bs['CompositeLongAmt']
                    else:
                        real_cpsamt_pre_date = 0
                    dict_acctinfo = self.gv.col_acctinfo.find_one(
                        {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz}
                    )
                    acctidbyxj4trd = dict_acctinfo['AcctIDByXuJie4Trd']
                    acctidbyxxq4trd = dict_acctinfo['AcctIDByXuXiaoQiang4Trd']
                    dict_tgtcpsamt = {
                        'DataDate': self.str_today,
                        'AcctIDByMXZ': acctidbymxz,
                        'PrdCode': self.prdcode,
                        'AcctIDByXuJie4Trd': acctidbyxj4trd,
                        'AcctIDByXuXiaoQiang4Trd': acctidbyxxq4trd,
                        'TgtCpsAmt': tgtcpsamt,
                        'RealCpsAmtPreDate': real_cpsamt_pre_date,
                    }
                    list_dicts_tgtcpsamt.append(dict_tgtcpsamt)
        self.gv.col_tgtcpsamt.delete_many({'DataDate': self.str_today, 'PrdCode': self.prdcode, })
        if list_dicts_tgtcpsamt:
            self.gv.col_tgtcpsamt.insert_many(list_dicts_tgtcpsamt)


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

    def check_margin_in_f_acct(self):
        # todo 假设持仓均为股指
        # 参考： 中金所 “跨品种” 单向大边保证金制度，上期所，单向大边保证金制度
        # 资料来源：上海期货交易所结算细则
        # 同一客户在同一会员处的同品种期货合约双向持仓（期货合约进入最后交易日前第五个交易日闭市后除外）
        # 对IC、IH、IF跨品种双向持仓，按照交易保证金单边较大者收取交易保证金
        margin_rate_in_perfect_shape = 0.2
        margin_rate_warning = 0.16
        list_dicts_future_api_holding = list(
            self.gv.col_future_api_holding.find({'DataDate': self.str_today, 'AcctIDByMXZ': self.acctidbymxz})
        )
        margin_required_in_perfect_shape = 0
        margin_warning = 0
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
            df_future_api_holding['multiplier'] = (
                df_future_api_holding['index'].map(self.gv.dict_index_future2multiplier)
            )
            df_future_api_holding['windcode'] = df_future_api_holding['instrument_id'] + '.CFE'
            df_future_api_holding['close'] = (
                df_future_api_holding['windcode'].map(self.gv.dict_index_future_windcode2close)
            )
            df_future_api_holding['spot_of_index'] = (
                df_future_api_holding['index'].map(self.gv.dict_index_future2spot)
            )
            df_future_api_holding['close_of_spot'] = (
                df_future_api_holding['spot_of_index'].map(self.gv.dict_index_future_windcode2close)
            )
            df_future_api_holding['margin_required_in_perfect_shape'] = (
                    df_future_api_holding['position']
                    * df_future_api_holding['multiplier']
                    * df_future_api_holding['close_of_spot']
                    * margin_rate_in_perfect_shape
            )
            df_future_api_holding['margin_warning'] = (
                    df_future_api_holding['position']
                    * df_future_api_holding['multiplier']
                    * df_future_api_holding['close_of_spot']
                    * margin_rate_warning
            )

            # 跨品种单向大边保证金制度
            dicts_future_api_holding_sum_by_direction = (
                df_future_api_holding
                .loc[:, ['direction', 'margin_required_in_perfect_shape', 'margin_warning']]
                .groupby(by='direction')
                .sum()
                .to_dict()
            )
            dict_direction2margin_required_in_perfect_shape = (
                dicts_future_api_holding_sum_by_direction['margin_required_in_perfect_shape']
            )
            dict_direction2margin_warning = dicts_future_api_holding_sum_by_direction['margin_warning']
            if 'buy' not in dict_direction2margin_required_in_perfect_shape:
                dict_direction2margin_required_in_perfect_shape['buy'] = 0
                dict_direction2margin_warning['buy'] = 0
            if 'sell' not in dict_direction2margin_required_in_perfect_shape:
                dict_direction2margin_required_in_perfect_shape['sell'] = 0
                dict_direction2margin_warning['sell'] = 0

            margin_required_by_long = dict_direction2margin_required_in_perfect_shape['buy']
            margin_required_by_short = dict_direction2margin_required_in_perfect_shape['sell']
            margin_required_in_perfect_shape = max(margin_required_by_long, margin_required_by_short)

            margin_warning_by_long = dict_direction2margin_warning['buy']
            margin_warning_by_short = dict_direction2margin_warning['sell']
            margin_warning = max(margin_warning_by_long, margin_warning_by_short)

        dict_bs_by_acctidbymxz = (
            self.gv.col_bs_by_acctidbymxz.find_one({'DataDate': self.str_today, 'AcctIDByMXZ': self.acctidbymxz})
        )
        approximate_na = dict_bs_by_acctidbymxz['ApproximateNetAsset']
        dif_margin_warning = approximate_na - margin_warning
        dif_margin_required_in_perfect_shape_approximate_na = approximate_na - margin_required_in_perfect_shape
        if dif_margin_warning < 0:
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
        dict_bs_by_acctidbymxz = (
            self.gv.col_bs_by_acctidbymxz.find_one({'DataDate': self.str_today, 'AcctIDByMXZ': self.acctidbymxz})
        )
        acctidbymxz = dict_bs_by_acctidbymxz['AcctIDByMXZ']
        accttype = acctidbymxz.split('_')[1]
        ce = dict_bs_by_acctidbymxz['CashEquivalent']
        cash = dict_bs_by_acctidbymxz['Cash']
        cash_from_ss = dict_bs_by_acctidbymxz['CashFromShortSelling']
        # todo 待验证假设： 交易资金 = cash - cash_from_ss
        if accttype in ['c']:
            cash2trd = cash
        elif accttype in ['m']:
            cash2trd = cash + ce - cash_from_ss
        else:
            raise ValueError('Unknown accttype.')

        composite_long_amt = dict_bs_by_acctidbymxz['CompositeLongAmt']
        cash_to_composite_long_amt_in_perfect_shape = 0.0889
        cash_in_perfect_shape = composite_long_amt * cash_to_composite_long_amt_in_perfect_shape
        dif_cash = cash - cash_in_perfect_shape
        if composite_long_amt:
            pct_cash2trd_by_cpslongamt = round(cash2trd / composite_long_amt, 3)
        else:
            pct_cash2trd_by_cpslongamt = 999999999

        if dif_cash > 5000000 and pct_cash2trd_by_cpslongamt > 0.12 or pct_cash2trd_by_cpslongamt < 0.05:
            dict_item_2b_adjusted = {
                    'DataDate': self.str_today,
                    'PrdCode': self.prdcode,
                    'AcctIDByMXZ': self.acctidbymxz,
                    'Cash': cash,
                    'Cash2Trd': cash2trd,
                    'PctCash2TrdByCpsLongAmt': pct_cash2trd_by_cpslongamt,
                    'CashInPerfectShape': cash_in_perfect_shape,
                    'CashDif2Perfect': dif_cash,
                    'CE': ce
                }
            self.gv.list_items_2b_adjusted.append(dict_item_2b_adjusted)


class MainFrameWork:
    def __init__(self):
        self.gv = GlobalVariable()
        self.list_prdcodes = self.gv.list_prdcodes

    def output_future_basis_analysis(self):
        """输出df, 期指基差分析表"""
        pass

    def generate_excel(self):
        # 生成交易计划页
        fn_trdplan = f'data/trdplan_auto/trdplan_mxz-{self.gv.str_next_trddate}.xlsx'

        df_trdplan = pd.DataFrame(self.gv.list_dicts_trdplan_output).T.reset_index().T
        with pd.ExcelWriter(fn_trdplan) as writer:
            # 格式化 trdplan 页
            df_trdplan.to_excel(writer, sheet_name='交易计划', index=False, header=False)
            worksheet_trdplan = writer.sheets['交易计划']
            fmt_header = writer.book.add_format(
                {
                    'font_name': '宋体',
                    'font_size': 11,
                    'bold': False,
                    'border': 1,
                    'align': 'center',
                    'valign': 'vcenter',
                    'text_wrap': True,
                }
            )
            fmt1 = writer.book.add_format(
                {
                    'valign': 'vcenter',
                    'bold': False,
                    'text_wrap': True,
                    'bg_color': '#00B0F0',
                    'border': 1,
                    'align': 'left',
                }
            )

            fmt2 = writer.book.add_format(
                {
                    'valign': 'vcenter',
                    'text_wrap': True,
                    'bg_color': '#A6A6A6',
                    'border': 1,
                    'align': 'left',
                }
            )
            fmt_first_col = writer.book.add_format(
                {
                    'valign': 'vcenter',
                    'bold': True,
                    'italic': True,
                    'text_wrap': True,
                    'bg_color': '#00B0F0',
                    'border': 1,
                    'align': 'right',
                }
            )
            worksheet_trdplan.set_column('B:C', 7, fmt1)
            worksheet_trdplan.set_column('D:D', 14.25, fmt1)
            worksheet_trdplan.set_column('E:F', 8.5, fmt1)
            worksheet_trdplan.set_column('G:G', 12, fmt1)
            worksheet_trdplan.set_column('H:J', 28.25, fmt2)
            worksheet_trdplan.set_column('K:M', 46.63, fmt1)
            worksheet_trdplan.set_column('N:N', 20.88, fmt2)
            worksheet_trdplan.set_column('O:O', 5, fmt1)
            worksheet_trdplan.set_column('P:P', 22.13, fmt2)
            worksheet_trdplan.set_column('Q:Q', 12.38, fmt2)
            worksheet_trdplan.set_column('R:R', 35.88, fmt1)
            worksheet_trdplan.set_column('A:A', 8.38, fmt_first_col)
            worksheet_trdplan.set_row(0, 31.5, fmt_header)
            worksheet_trdplan.autofilter(0, 0, 0, 17)
            for idx in range(1, 40):
                worksheet_trdplan.set_row(idx, 80)

            # 生成目标持仓页
            list_dicts_tgtcpsamt = list(
                self.gv.col_tgtcpsamt.find({'DataDate': self.gv.str_today}, {'_id': 0})
            )
            df_tgtcpsamt = pd.DataFrame(list_dicts_tgtcpsamt).T.reset_index().T
            df_tgtcpsamt.to_excel(writer, sheet_name='目标持仓', index=False, header=False)

            worksheet_tgtcpsamt = writer.sheets['目标持仓']
            worksheet_tgtcpsamt.set_column('A:A', 8.88)
            worksheet_tgtcpsamt.set_column('B:B', 18.75)
            worksheet_tgtcpsamt.set_column('C:C', 7.88)
            worksheet_tgtcpsamt.set_column('D:D', 18.75)
            worksheet_tgtcpsamt.set_column('E:E', 25.5)
            worksheet_tgtcpsamt.set_column('F:F', 12.13)
            worksheet_tgtcpsamt.set_column('F:F', 18.75)
            worksheet_tgtcpsamt.set_column('G:G', 18.75)
            writer.save()

    def run(self):
        for prdcode in self.list_prdcodes:
            if prdcode in ['1202']:
                prd = Product(self.gv, prdcode)
                prd.budget()
                prd.output_trdplan_order()
                prd.output_tgtcpsamt()
                prd.check_exception()
                prd.check_exposure()
                print(f'{prdcode} trdplan finished.')

        self.gv.db_trddata['items_2b_adjusted'].delete_many({'DataDate': self.gv.str_today})
        if self.gv.list_items_2b_adjusted:
            self.gv.db_trddata['items_2b_adjusted'].insert_many(self.gv.list_items_2b_adjusted)
        self.generate_excel()


if __name__ == '__main__':
    mfw = MainFrameWork()
    mfw.run()














