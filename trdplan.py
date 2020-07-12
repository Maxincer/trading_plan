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
            维持担保比例=（现金+信用证券账户内证券市值总和+其他担保物价值）/（融资买入金额+融券卖出证券数量×当前市价＋利息及费用总和）。
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

Abbr.:
    1. cps: composite
    2. MN: Market Neutral
    3. EI: Enhanced Index
    4. cpspct: composite percentage: composite amt / net asset value
todo:
    1. 期货户持仓变动时，需要试算可用保证金是否充足
        1. 期货户持仓变动触发： balance exposure
    2. 国债逆回购（核新系统）不在下载的数据文件之内，如何添加？
    3. 国债逆回购不同系统的单位价格确认。（核新为1000，有没有100的情况？）
    4. 申赎款
    5. 分渠道的资金分配
Memo:
    1. 1203 的个券融券开仓时间为20200623

Naming Convention:
    1. Security Accounts:
        1. 根据《上海证券交易所融资融券交易实施细则》，margin account 的官方翻译为：“信用证券账户”。
        2. 根据证件会《融资融券合同必备条款》，cash account 的官方翻译为：“普通证券账户”
        3. 综合上述两点，证券账户包括信用证券账户与普通证券账户，英文在本项目中约定为Security Account.
        4. Accounts 为 Account的复数形式，表示全部Account的意思。
        5. 根据《上海证券交易所融资融券交易实施细则》，“证券类资产”，是指投资者持有的客户交易结算资金、股票、债券、基金、证券公司资管计划等资产。
"""
from datetime import datetime
from math import ceil, floor
from sympy import solve, Symbol

import pandas as pd
import pymongo
from WindPy import w


class GlobalVariable:
    def __init__(self):
        self.str_today = datetime.today().strftime('%Y%m%d')
        self.str_today = '20200710'
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
        self.col_formatted_holding = self.db_trddata['formatted_holding']
        self.list_items_budget_details = []
        self.list_items_budget = []
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
        self.dict_tgt_items = self.dict_prdinfo['TargetItems']
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
                               * self.gv.dict_index_future2multiplier[ic_if_ih])
        flt_lots = tgt_exposure_from_future / contract_value_spot
        if strategy == 'MN':
            int_lots = round(flt_lots)
        elif strategy == 'EI':
            int_lots = floor(flt_lots)
        else:
            raise ValueError('Unknown strategy when cmp f lots.')
        return int_lots

    def update_col_na_allocation(self):
        """
        1. 从col_na_allocation数据库读取上一交易日na_allocation数据，
        2. 从SP&R数据表中读取今日生效的申赎数据， 从b/s_by_prdcode中读取产品净值数据
        3. 计算
        4. 若prdinfo中指定na_allocation比例，则使用prdinfo中的当前值
        4. 更新col_na_allocation今日的数据。

        col structure:
        fields = ['DataDate', 'PrdCode', 'NetAssetAllocationOfSecurityAccounts', 'NetAssetAllocationOfFutureAccounts']
        dict_na_allocation_saccts = {}
        dict_na_allocation_faccts = {}

        Note:
            1. Future Accounts 的分配比例不随申赎款的变化而变化， 故facct的比例只可以手动更改

        业务约定：
            1. 申购款，申购生效后款项到账后改变比例
            2. 赎回款，赎回生效日当天改变比例
        todo 移到db_trading_data.py中
        """

        dict_na_allocation_yesterday = self.gv.col_na_allocation.find_one(
            {'DataDate': self.gv.str_yesterday, 'PrdCode': self.prdcode}
        )
        dict_na_allocation_saccts_yesterday = dict_na_allocation_yesterday['NetAssetAllocationOfSecurityAccounts']
        dict_bs_by_prdcode = self.gv.col_bs_by_prdcode.find_one(
            {'DataDate': self.str_today, 'PrdCode': self.prdcode}
        )
        approximate_na = dict_bs_by_prdcode['ApproximateNetAsset']
        # todo 对该表的通知时间字段建立降序索引，取最新值。
        dict_spr = self.gv.col_spr.find_one({'EffectiveDate': self.str_today, 'PrdCode': self.prdcode})

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

        Note:
            1. 注意现有持仓是两个策略的合并持仓，需要按照比例分配。
            2. 本项目中资金的渠道分配是以营业部为主体，而非券商。（同一券商可能会有多个资金渠道）
            3. 数据库中的仓位比例为cpslongamt的比例
            4. 最后取整

        思路：
            1. 先求EI的shape，剩下的都是MN的。
            2. 分配普通和信用时，采取信用户净资产最小原则（不低于最低维持担保比例）。（采用0.77 * 1.088 净资产放入信用户原则）
            3. 重要 算法顺序上，在确认了facct与oacct的NA后，再对证券户的各渠道的NA进行分配
            4. 期货手数在最后时进行整数化处理，
            5. 使用‘净值’思想处理budget
            6. 引入核心方程式求解： 1.净资产， 2. 暴露
        """
        flt_cash2cpslongamt = 0.0889
        dict_na_allocation = self.gv.col_na_allocation.find_one({'DataDate': self.str_today, 'PrdCode': self.prdcode})
        prdna = self.prd_approximate_na
        if self.dict_tgt_items:
            if self.dict_tgt_items['NetAsset']:
                prdna = self.dict_tgt_items['NetAsset']
        if dict_na_allocation:
            dict_na_allocation_saccts = dict_na_allocation['SecurityAccountsNetAssetAllocation']
            if dict_na_allocation_saccts:
                tool_v = None
                for capital_src, value in dict_na_allocation_saccts.items():
                    if not isinstance(value, str):
                        if value > 1:
                            tool_v = value

                for capital_src, value in dict_na_allocation_saccts.items():
                    if isinstance(value, str):
                        tgt_na = prdna - tool_v
                    else:
                        if value <= 1:
                            tgt_na = prdna * value
                        else:
                            tgt_na = value

                    index_future = 'IC'  # todo 可进一步抽象， 与空头策略有关
                    # todo 需要分期货

                    # EI 策略预算假设
                    ei_na_oaccts_tgt = 0
                    ei_etflongamt_tgt = 0
                    ei_cpsshortamt_tgt = 0
                    ei_etfshortamt_tgt = 0
                    ei_net_exposure_in_oaccts = 0

                    # special na, 用于如人工T0/外部团队特殊情况的处理。
                    ei_special_na = 0
                    ei_na_tgt = tgt_na * self.dict_strategies_allocation['EI']
                    if self.tgt_cpspct == 'max':
                        ei_ce_in_saccts_tgt = 0
                        ei_cpslongamt_tgt = Symbol('ei_cpslongamt_tgt')
                    else:
                        ei_ce_in_saccts_tgt = Symbol('ei_ce_in_saccts_tgt')
                        ei_cpslongamt_tgt = ei_na_tgt * self.tgt_cpspct

                    # 方程部分
                    ei_iclots_tgt = Symbol('ei_iclots_tgt')
                    eq_ei_na = (ei_cpslongamt_tgt * (1 + flt_cash2cpslongamt)
                                + ei_ce_in_saccts_tgt
                                + ei_etflongamt_tgt
                                + ei_special_na
                                + ei_iclots_tgt * self.gv.dict_index_future2internal_required_na_per_lot[index_future]
                                + ei_na_oaccts_tgt
                                - ei_na_tgt
                                )
                    eq_ei_exposure = (ei_cpslongamt_tgt
                                      + ei_etflongamt_tgt
                                      + ei_iclots_tgt * self.gv.dict_index_future2spot_exposure_per_lot[index_future]
                                      - ei_cpsshortamt_tgt
                                      - ei_etfshortamt_tgt
                                      + ei_net_exposure_in_oaccts
                                      - ei_na_tgt * 0.99
                                      )
                    # 2. MN策略
                    # todo 20200704需要分析两融户中换仓资金的准确算法， 即 保证金制度交易下的详细算法（大课题）。

                    # MN 假设：
                    mn_etflongamt_tgt = 0
                    mn_special_na = 0

                    # 方程部分
                    # 未知
                    mn_iclots_tgt = Symbol('mn_iclots_tgt')

                    # 已知
                    mn_na_tgt = tgt_na * self.dict_strategies_allocation['MN']
                    if self.tgt_cpspct == 'max':
                        mn_ce_from_cash_available = 0
                        mn_cpslongamt_tgt = Symbol('mn_cpslongamt_tgt')
                    else:
                        mn_cpslongamt_tgt = mn_na_tgt * self.tgt_cpspct
                        mn_ce_from_cash_available = Symbol('mn_ce_from_cash_available')

                    # 求信用户提供的空头暴露预算值
                    # 求信用户中的卖出融券所得资金
                    # 假设：信用户提供的空头暴露工具只有 etf 和 cps(个股)
                    dict_macct_basicinfo = self.gv.col_acctinfo.find_one(
                        {'DataDate': self.str_today, 'PrdCode': self.prdcode, 'AcctType': 'm', 'RptMark': 1}
                    )
                    mn_etfshortamt_in_macct = 0
                    mn_cpsshortamt_in_macct = 0
                    mn_cash_from_ss_in_macct = 0
                    if dict_macct_basicinfo:
                        acctidbymxz_macct = dict_macct_basicinfo['AcctIDByMXZ']
                        list_dicts_formatted_holding = self.gv.col_formatted_holding.find(
                            {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_macct}
                        )
                        for dict_formatted_holding in list_dicts_formatted_holding:
                            sectype = dict_formatted_holding['SecurityType']
                            mn_cash_from_ss_delta = dict_formatted_holding['CashFromShortSelling']
                            mn_cash_from_ss_in_macct += mn_cash_from_ss_delta
                            if sectype in ['ETF']:
                                mn_etfshortamt_in_macct_delta = dict_formatted_holding['ShortAmt']
                                mn_etfshortamt_in_macct += mn_etfshortamt_in_macct_delta
                            elif sectype in ['CS']:
                                mn_cpsshortamt_in_macct_delta = dict_formatted_holding['ShortAmt']
                                mn_cpsshortamt_in_macct += mn_cpsshortamt_in_macct_delta
                            else:
                                ValueError('Unknown security type when computing mn_etfshortamt_macct '
                                           'and mn_cpsshortamt_in_macct')
                    mn_cash_from_ss_in_macct_tgt = mn_cash_from_ss_in_macct
                    mn_etfshortamt_in_macct_tgt = mn_etfshortamt_in_macct
                    mn_cpsshortamt_in_macct_tgt = mn_cpsshortamt_in_macct

                    if self.dict_tgt_items['ETFShortAmountInMarginAccount']:
                        mn_etfshortamt_in_macct_tgt = self.dict_tgt_items['ETFShortAmountInMarginAccount']
                    if self.dict_tgt_items['CompositeShortAmountInMarginAccount']:
                        mn_cpsshortamt_in_macct_tgt = self.dict_tgt_items['CompositeShortAmountInMarginAccount']
                    if self.dict_tgt_items['CashFromShortSellingInMarginAccount']:
                        mn_cash_from_ss_in_macct_tgt = self.dict_tgt_items['CashFromShortSellingInMarginAccount']

                    # 求oacct提供的空头暴露预算值与多头暴露预算值
                    # 求oacct账户中的存出保证金（net_asset）
                    # 根据实际业务做出假设：1. oacct全部用于MN策略 2.oacct仅提供short exposure，todo oacct中出现多头暴露时需要改进
                    list_dicts_oacct_basicinfo = list(
                        self.gv.col_acctinfo.find({'DataDate': self.str_today, 'PrdCode': self.prdcode, 'AcctType': 'o'})
                    )
                    net_exposure_from_oaccts = 0  # 假设oacct的账户全部且仅为MN服务
                    approximate_na_oaccts = 0  # 假设oacct的账户全部且仅为MN服务
                    for dict_oacct_basicinfo in list_dicts_oacct_basicinfo:
                        if dict_oacct_basicinfo:
                            acctidbymxz_oacct = dict_oacct_basicinfo['AcctIDByMXZ']
                            dict_exposure_analysis_by_acctidbymxz = self.gv.col_exposure_analysis_by_acctidbymxz.find_one(
                                {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_oacct}
                            )
                            net_exposure_from_oacct_delta = dict_exposure_analysis_by_acctidbymxz['NetExposure']
                            net_exposure_from_oaccts += net_exposure_from_oacct_delta
                            dict_bs_by_acctidbymxz = self.gv.col_bs_by_acctidbymxz.find_one(
                                {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_oacct}
                            )
                            approximate_na_oacct_delta = dict_bs_by_acctidbymxz['ApproximateNetAsset']
                            approximate_na_oaccts += approximate_na_oacct_delta
                    net_exposure_from_oaccts_tgt = net_exposure_from_oaccts
                    if self.dict_tgt_items['NetExposureFromOTCAccounts']:
                        net_exposure_from_oaccts_tgt = self.dict_tgt_items['NetExposureFromOTCAccounts']
                    na_oaccts_tgt = approximate_na_oaccts
                    if self.dict_tgt_items['NetAssetInOTCAccounts']:
                        na_oaccts_tgt = self.dict_tgt_items['NetAssetInOTCAccounts']

                    mn_ce_from_cash_from_ss_tgt = mn_cash_from_ss_in_macct_tgt
                    eq_mn_na = (mn_cpslongamt_tgt * (1 + flt_cash2cpslongamt)
                                + mn_etflongamt_tgt
                                + mn_ce_from_cash_from_ss_tgt
                                + mn_ce_from_cash_available
                                + mn_special_na
                                - mn_iclots_tgt * self.gv.dict_index_future2internal_required_na_per_lot[index_future]
                                + na_oaccts_tgt
                                - mn_na_tgt
                                )

                    eq_mn_exposure = (mn_cpslongamt_tgt
                                      + mn_etflongamt_tgt
                                      - mn_etfshortamt_in_macct_tgt
                                      - mn_cpsshortamt_in_macct_tgt
                                      + mn_iclots_tgt * self.gv.dict_index_future2spot_exposure_per_lot[index_future]
                                      + net_exposure_from_oaccts_tgt
                                      )

                    if self.tgt_cpspct == 'max':
                        dict_solve = solve(
                            [eq_ei_na, eq_mn_na, eq_ei_exposure, eq_mn_exposure],
                            ei_cpslongamt_tgt, ei_iclots_tgt, mn_cpslongamt_tgt, mn_iclots_tgt
                        )
                    else:
                        dict_solve = solve(
                            [eq_ei_na, eq_mn_na, eq_ei_exposure, eq_mn_exposure],
                            ei_iclots_tgt, mn_iclots_tgt, ei_ce_in_saccts_tgt, mn_ce_from_cash_available
                        )
                    if ei_cpslongamt_tgt in dict_solve:
                        ei_cpslongamt_tgt = float(dict_solve[ei_cpslongamt_tgt])
                    if ei_iclots_tgt in dict_solve:
                        ei_iclots_tgt = float(dict_solve[ei_iclots_tgt])
                    if ei_ce_in_saccts_tgt in dict_solve:
                        ei_ce_in_saccts_tgt = float(dict_solve[ei_ce_in_saccts_tgt])
                    if mn_cpslongamt_tgt in dict_solve:
                        mn_cpslongamt_tgt = float(dict_solve[mn_cpslongamt_tgt])
                    if mn_iclots_tgt in dict_solve:
                        mn_iclots_tgt = float(dict_solve[mn_iclots_tgt])
                    if mn_ce_from_cash_available in dict_solve:
                        mn_ce_from_cash_available = float(dict_solve[mn_ce_from_cash_available])

                    # 资金分配(cacct 与 macct)
                    # 公司内部分配算法：信用户如有负债则在信用户中留足够开满仓的资金（0.77 * mn_na_tgt）
                    mn_na_faccts_tgt = mn_iclots_tgt * self.gv.dict_index_future2internal_required_na_per_lot[index_future]
                    mn_cash_2trd_in_saccts_tgt = mn_cpslongamt_tgt * flt_cash2cpslongamt
                    mn_shortamt_in_macct = mn_etfshortamt_in_macct + mn_cpsshortamt_in_macct
                    mn_na_saccts_tgt = mn_na_tgt - mn_na_faccts_tgt - na_oaccts_tgt
                    if mn_shortamt_in_macct:
                        mn_na_macct_tgt = mn_na_tgt * 0.77 * (1 + flt_cash2cpslongamt)  # 按分配到该渠道的满仓资金计算，分配给macct
                        mn_cpslongamt_in_macct_tgt = mn_cpslongamt_tgt  # 注意 此处可能不是满仓(0.77)
                        mn_cash_2trd_in_macct_tgt = mn_cpslongamt_in_macct_tgt * flt_cash2cpslongamt
                        mn_ce_in_macct_tgt = mn_na_macct_tgt - mn_cpslongamt_in_macct_tgt - mn_cash_2trd_in_macct_tgt
                        mn_na_cacct_tgt = mn_na_saccts_tgt - mn_na_macct_tgt
                        mn_ce_in_cacct_tgt = mn_na_cacct_tgt - 1500000
                        if mn_ce_in_cacct_tgt < 0:
                            mn_ce_in_cacct_tgt = 0
                        mn_cash_in_cacct_tgt = mn_na_cacct_tgt - mn_ce_in_cacct_tgt
                        mn_ce_in_saccts_tgt = mn_ce_in_cacct_tgt + mn_ce_in_macct_tgt
                        mn_cash_in_saccts_tgt = mn_cash_in_cacct_tgt + mn_cash_2trd_in_macct_tgt
                        mn_cpslongamt_in_cacct_tgt = 0
                        mn_cash_in_macct_tgt = mn_cash_2trd_in_macct_tgt
                    else:
                        mn_cpslongamt_in_macct_tgt = 'No allocation limit between cash account and margin account.'
                        mn_cash_2trd_in_macct_tgt = 'No allocation limit between cash account and margin account.'
                        mn_cash_in_macct_tgt = mn_cash_2trd_in_macct_tgt
                        mn_na_macct_tgt = 'No allocation limit between cash account and margin account.'
                        mn_cpslongamt_in_cacct_tgt = 'No allocation limit between cash account and margin account.'
                        mn_cash_in_cacct_tgt = 'No allocation limit between cash account and margin account.'
                        mn_na_cacct_tgt = 'No allocation limit between cash account and margin account.'
                        mn_ce_in_cacct_tgt = 'No allocation limit between cash account and margin account.'
                        mn_ce_in_macct_tgt = 'No allocation limit between cash account and margin account.'
                        mn_cash_in_saccts_tgt = mn_cash_2trd_in_saccts_tgt
                        mn_ce_in_saccts_tgt = mn_na_saccts_tgt - mn_cpslongamt_tgt - mn_cash_in_saccts_tgt

                    ei_na_faccts_tgt = abs(ei_iclots_tgt) * self.gv.dict_index_future2internal_required_na_per_lot[
                        index_future]
                    ei_na_saccts_tgt = ei_na_tgt - ei_na_faccts_tgt - ei_na_oaccts_tgt
                    ei_cash_in_saccts_tgt = ei_cpslongamt_tgt * flt_cash2cpslongamt
                    ei_netamt_faccts_tgt = floor(ei_iclots_tgt) * self.gv.dict_index_future2spot_exposure_per_lot[
                        index_future]
                    ei_int_net_lots_index_future_tgt = floor(ei_iclots_tgt)

                    mn_int_net_lots_index_future_tgt = round(mn_iclots_tgt)
                    mn_netamt_index_future_in_faccts_tgt = (round(mn_iclots_tgt)
                                                            * self.gv.dict_index_future2spot_exposure_per_lot[index_future])

                    dict_bgt_details = {
                        'DataDate': self.str_today,
                        'PrdCode': self.prdcode,
                        'CapitalSource': capital_src,
                        'TargetNetAsset': tgt_na,
                        'EINetAsset': ei_na_tgt,
                        'EINetAssetOfSecurityAccounts': ei_na_saccts_tgt,
                        'EINetAssetOfFutureAccounts': ei_na_faccts_tgt,
                        'EINetAssetOfOTCAccounts': ei_na_oaccts_tgt,
                        'EINetAssetAllocationBetweenCapitalSources': {},
                        'EICashInSecurityAccounts': ei_cash_in_saccts_tgt,
                        'EICashEquivalentInSecurityAccounts': ei_ce_in_saccts_tgt,
                        'EICompositeLongAmountInSecurityAccounts': ei_cpslongamt_tgt,
                        'EICompositeShortAmountInSecurityAccounts': ei_cpsshortamt_tgt,
                        'EIETFLongAmountInSecurityAccounts': ei_etflongamt_tgt,
                        'EIETFShortAmountInSecurityAccounts': ei_etfshortamt_tgt,
                        'EINetAmountInFutureAccounts': ei_netamt_faccts_tgt,
                        'EIContractsNetLotsInFutureAccounts': ei_int_net_lots_index_future_tgt,
                        'EINetExposureFromOTCAccounts': ei_net_exposure_in_oaccts,
                        'EIPositionAllocationBetweenCapitalSources': {},
                        'MNNetAsset': mn_na_tgt,
                        'MNNetAssetOfSecurityAccounts': mn_na_saccts_tgt,
                        'MNNetAssetOfCashAccount': mn_na_cacct_tgt,
                        'MNNetAssetOfMarginAccount': mn_na_macct_tgt,
                        'MNNetAssetOfFutureAccounts': mn_na_faccts_tgt,
                        'MNNetAssetOfOTCAccounts': na_oaccts_tgt,
                        'MNNetAssetAllocationBetweenCapitalSources': {},
                        'MNCashInSecurityAccounts': mn_cash_in_saccts_tgt,
                        'MNCashInCashAccount': mn_cash_in_cacct_tgt,
                        'MNCashInMarginAccount': mn_cash_in_macct_tgt,
                        'MNCashEquivalentInSecurityAccounts': mn_ce_in_saccts_tgt,
                        'MNCashEquivalentInCashAccount': mn_ce_in_cacct_tgt,
                        'MNCashEquivalentInMarginAccount': mn_ce_in_macct_tgt,
                        'MNCashEquivalentFromCashAvailable': mn_ce_from_cash_available,
                        'MNCompositeLongAmountInSecurityAccounts': mn_cpslongamt_tgt,
                        'MNCompositeLongAmountInCashAccount': mn_cpslongamt_in_cacct_tgt,
                        'MNCompositeLongAmountInMarginAccount': mn_cpslongamt_in_macct_tgt,
                        'MNCompositeShortAmountInSecurityAccounts': mn_cpsshortamt_in_macct_tgt,
                        'MNCompositeShortAmountInMarginAccount': mn_cpsshortamt_in_macct_tgt,
                        'MNETFNetAmountInSecurityAccounts': -mn_etfshortamt_in_macct_tgt,
                        'MNETFShortAmountInMarginAccount': mn_etfshortamt_in_macct_tgt,
                        'MNNetAmountOfFutureAccounts': mn_netamt_index_future_in_faccts_tgt,
                        'MNContractsNetLotsOfFutureAccounts': mn_int_net_lots_index_future_tgt,
                        'MNNetExposureFromOTCAccounts': net_exposure_from_oaccts_tgt,
                        'MNPositionAllocationBetweenCapitalSources': {},
                    }
                    dict_bgt = {
                        'DataDate': self.str_today,
                        'PrdCode': self.prdcode,
                        'CapitalSource': capital_src,
                        'CPSLongAmt': float(ei_cpslongamt_tgt + mn_cpslongamt_tgt),
                        'ICLots': ceil(ei_iclots_tgt) + round(mn_iclots_tgt),
                        'CE': float(ei_ce_in_saccts_tgt + mn_ce_from_cash_available + mn_ce_from_cash_from_ss_tgt)
                    }

                    self.gv.list_items_budget_details.append(dict_bgt_details)
                    self.gv.list_items_budget.append(dict_bgt)

        else:
            # 参数部分 与 假设
            index_future = 'IC'  # todo 可进一步抽象， 与空头策略有关

            # EI 策略预算假设
            ei_na_oaccts_tgt = 0
            ei_etflongamt_tgt = 0
            ei_cpsshortamt_tgt = 0
            ei_etfshortamt_tgt = 0
            ei_net_exposure_in_oaccts = 0

            # special na, 用于如人工T0/外部团队特殊情况的处理。
            ei_special_na = 0
            tgt_na = self.prd_approximate_na
            if self.dict_tgt_items:
                if self.dict_tgt_items['NetAsset']:
                    tgt_na = self.dict_tgt_items['NetAsset']

            ei_na_tgt = tgt_na * self.dict_strategies_allocation['EI']
            if self.tgt_cpspct == 'max':
                ei_ce_in_saccts_tgt = 0
                ei_cpslongamt_tgt = Symbol('ei_cpslongamt_tgt')
            else:
                ei_ce_in_saccts_tgt = Symbol('ei_ce_in_saccts_tgt')
                ei_cpslongamt_tgt = ei_na_tgt * self.tgt_cpspct

            # 方程部分
            ei_iclots_tgt = Symbol('ei_iclots_tgt')
            eq_ei_na = (ei_cpslongamt_tgt * (1 + flt_cash2cpslongamt)
                        + ei_ce_in_saccts_tgt
                        + ei_etflongamt_tgt
                        + ei_special_na
                        + ei_iclots_tgt * self.gv.dict_index_future2internal_required_na_per_lot[index_future]
                        + ei_na_oaccts_tgt
                        - ei_na_tgt
                        )
            eq_ei_exposure = (ei_cpslongamt_tgt
                              + ei_etflongamt_tgt
                              + ei_iclots_tgt * self.gv.dict_index_future2spot_exposure_per_lot[index_future]
                              - ei_cpsshortamt_tgt
                              - ei_etfshortamt_tgt
                              + ei_net_exposure_in_oaccts
                              - ei_na_tgt * 0.99
            )
            # 2. MN策略
            # todo 20200704需要分析两融户中换仓资金的准确算法， 即 保证金制度交易下的详细算法（大课题）。

            # MN 假设：
            mn_etflongamt_tgt = 0
            mn_special_na = 0

            # 方程部分
            # 未知
            mn_iclots_tgt = Symbol('mn_iclots_tgt')

            # 已知
            mn_na_tgt = tgt_na * self.dict_strategies_allocation['MN']
            if self.tgt_cpspct == 'max':
                mn_ce_from_cash_available = 0
                mn_cpslongamt_tgt = Symbol('mn_cpslongamt_tgt')
            else:
                mn_cpslongamt_tgt = mn_na_tgt * self.tgt_cpspct
                mn_ce_from_cash_available = Symbol('mn_ce_from_cash_available')

            # 求信用户提供的空头暴露预算值
            # 求信用户中的卖出融券所得资金
            # 假设：信用户提供的空头暴露工具只有 etf 和 cps(个股)
            dict_macct_basicinfo = self.gv.col_acctinfo.find_one(
                {'DataDate': self.str_today, 'PrdCode': self.prdcode, 'AcctType': 'm', 'RptMark': 1}
            )
            mn_etfshortamt_in_macct = 0
            mn_cpsshortamt_in_macct = 0
            mn_cash_from_ss_in_macct = 0
            if dict_macct_basicinfo:
                acctidbymxz_macct = dict_macct_basicinfo['AcctIDByMXZ']
                list_dicts_formatted_holding = self.gv.col_formatted_holding.find(
                    {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_macct}
                )
                for dict_formatted_holding in list_dicts_formatted_holding:
                    sectype = dict_formatted_holding['SecurityType']
                    mn_cash_from_ss_delta = dict_formatted_holding['CashFromShortSelling']
                    mn_cash_from_ss_in_macct += mn_cash_from_ss_delta
                    if sectype in ['ETF']:
                        mn_etfshortamt_in_macct_delta = dict_formatted_holding['ShortAmt']
                        mn_etfshortamt_in_macct += mn_etfshortamt_in_macct_delta
                    elif sectype in ['CS']:
                        mn_cpsshortamt_in_macct_delta = dict_formatted_holding['ShortAmt']
                        mn_cpsshortamt_in_macct += mn_cpsshortamt_in_macct_delta
                    else:
                        ValueError('Unknown security type when computing mn_etfshortamt_macct '
                                   'and mn_cpsshortamt_in_macct')
            mn_cash_from_ss_in_macct_tgt = mn_cash_from_ss_in_macct
            mn_etfshortamt_in_macct_tgt = mn_etfshortamt_in_macct
            mn_cpsshortamt_in_macct_tgt = mn_cpsshortamt_in_macct

            if self.dict_tgt_items['ETFShortAmountInMarginAccount']:
                mn_etfshortamt_in_macct_tgt = self.dict_tgt_items['ETFShortAmountInMarginAccount']
            if self.dict_tgt_items['CompositeShortAmountInMarginAccount']:
                mn_cpsshortamt_in_macct_tgt = self.dict_tgt_items['CompositeShortAmountInMarginAccount']
            if self.dict_tgt_items['CashFromShortSellingInMarginAccount']:
                mn_cash_from_ss_in_macct_tgt = self.dict_tgt_items['CashFromShortSellingInMarginAccount']

            # 求oacct提供的空头暴露预算值与多头暴露预算值
            # 求oacct账户中的存出保证金（net_asset）
            # 根据实际业务做出假设：1. oacct全部用于MN策略 2.oacct仅提供short exposure，todo oacct中出现多头暴露时需要改进
            list_dicts_oacct_basicinfo = list(
                self.gv.col_acctinfo.find({'DataDate': self.str_today, 'PrdCode': self.prdcode, 'AcctType': 'o'})
            )
            net_exposure_from_oaccts = 0  # 假设oacct的账户全部且仅为MN服务
            approximate_na_oaccts = 0  # 假设oacct的账户全部且仅为MN服务
            for dict_oacct_basicinfo in list_dicts_oacct_basicinfo:
                if dict_oacct_basicinfo:
                    acctidbymxz_oacct = dict_oacct_basicinfo['AcctIDByMXZ']
                    dict_exposure_analysis_by_acctidbymxz = self.gv.col_exposure_analysis_by_acctidbymxz.find_one(
                        {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_oacct}
                    )
                    net_exposure_from_oacct_delta = dict_exposure_analysis_by_acctidbymxz['NetExposure']
                    net_exposure_from_oaccts += net_exposure_from_oacct_delta
                    dict_bs_by_acctidbymxz = self.gv.col_bs_by_acctidbymxz.find_one(
                        {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_oacct}
                    )
                    approximate_na_oacct_delta = dict_bs_by_acctidbymxz['ApproximateNetAsset']
                    approximate_na_oaccts += approximate_na_oacct_delta
            net_exposure_from_oaccts_tgt = net_exposure_from_oaccts
            if self.dict_tgt_items['NetExposureFromOTCAccounts']:
                net_exposure_from_oaccts_tgt = self.dict_tgt_items['NetExposureFromOTCAccounts']
            na_oaccts_tgt = approximate_na_oaccts
            if self.dict_tgt_items['NetAssetInOTCAccounts']:
                na_oaccts_tgt = self.dict_tgt_items['NetAssetInOTCAccounts']

            mn_ce_from_cash_from_ss_tgt = mn_cash_from_ss_in_macct_tgt
            eq_mn_na = (mn_cpslongamt_tgt * (1 + flt_cash2cpslongamt)
                        + mn_etflongamt_tgt
                        + mn_ce_from_cash_from_ss_tgt
                        + mn_ce_from_cash_available
                        + mn_special_na
                        - mn_iclots_tgt * self.gv.dict_index_future2internal_required_na_per_lot[index_future]
                        + na_oaccts_tgt
                        - mn_na_tgt
                        )

            eq_mn_exposure = (mn_cpslongamt_tgt
                              + mn_etflongamt_tgt
                              - mn_etfshortamt_in_macct_tgt
                              - mn_cpsshortamt_in_macct_tgt
                              + mn_iclots_tgt * self.gv.dict_index_future2spot_exposure_per_lot[index_future]
                              + net_exposure_from_oaccts_tgt
                              )

            if self.tgt_cpspct == 'max':
                dict_solve = solve(
                    [eq_ei_na, eq_mn_na, eq_ei_exposure, eq_mn_exposure],
                    ei_cpslongamt_tgt, ei_iclots_tgt, mn_cpslongamt_tgt, mn_iclots_tgt
                )
            else:
                dict_solve = solve(
                    [eq_ei_na, eq_mn_na, eq_ei_exposure, eq_mn_exposure],
                    ei_iclots_tgt, mn_iclots_tgt, ei_ce_in_saccts_tgt, mn_ce_from_cash_available
                )
            if ei_cpslongamt_tgt in dict_solve:
                ei_cpslongamt_tgt = float(dict_solve[ei_cpslongamt_tgt])
            if ei_iclots_tgt in dict_solve:
                ei_iclots_tgt = float(dict_solve[ei_iclots_tgt])
            if ei_ce_in_saccts_tgt in dict_solve:
                ei_ce_in_saccts_tgt = float(dict_solve[ei_ce_in_saccts_tgt])
            if mn_cpslongamt_tgt in dict_solve:
                mn_cpslongamt_tgt = float(dict_solve[mn_cpslongamt_tgt])
            if mn_iclots_tgt in dict_solve:
                mn_iclots_tgt = float(dict_solve[mn_iclots_tgt])
            if mn_ce_from_cash_available in dict_solve:
                mn_ce_from_cash_available = float(dict_solve[mn_ce_from_cash_available])

            # 资金分配(cacct 与 macct)
            # 公司内部分配算法：信用户如有负债则在信用户中留足够开满仓的资金（0.77 * mn_na_tgt）
            mn_na_faccts_tgt = mn_iclots_tgt * self.gv.dict_index_future2internal_required_na_per_lot[index_future]
            mn_cash_2trd_in_saccts_tgt = mn_cpslongamt_tgt * flt_cash2cpslongamt
            mn_shortamt_in_macct = mn_etfshortamt_in_macct + mn_cpsshortamt_in_macct
            mn_na_saccts_tgt = mn_na_tgt - mn_na_faccts_tgt - na_oaccts_tgt
            if mn_shortamt_in_macct:
                mn_na_macct_tgt = mn_na_tgt * 0.77 * (1 + flt_cash2cpslongamt)  # 按分配到该渠道的满仓资金计算，分配给macct
                mn_cpslongamt_in_macct_tgt = mn_cpslongamt_tgt  # 注意 此处可能不是满仓(0.77)
                mn_cash_2trd_in_macct_tgt = mn_cpslongamt_in_macct_tgt * flt_cash2cpslongamt
                mn_ce_in_macct_tgt = mn_na_macct_tgt - mn_cpslongamt_in_macct_tgt - mn_cash_2trd_in_macct_tgt
                mn_na_cacct_tgt = mn_na_saccts_tgt - mn_na_macct_tgt
                mn_ce_in_cacct_tgt = mn_na_cacct_tgt - 1500000
                if mn_ce_in_cacct_tgt < 0:
                    mn_ce_in_cacct_tgt = 0
                mn_cash_in_cacct_tgt = mn_na_cacct_tgt - mn_ce_in_cacct_tgt
                mn_ce_in_saccts_tgt = mn_ce_in_cacct_tgt + mn_ce_in_macct_tgt
                mn_cash_in_saccts_tgt = mn_cash_in_cacct_tgt + mn_cash_2trd_in_macct_tgt
                mn_cpslongamt_in_cacct_tgt = 0
                mn_cash_in_macct_tgt = mn_cash_2trd_in_macct_tgt
            else:
                mn_cpslongamt_in_macct_tgt = 'No allocation limit between cash account and margin account.'
                mn_cash_2trd_in_macct_tgt = 'No allocation limit between cash account and margin account.'
                mn_cash_in_macct_tgt = mn_cash_2trd_in_macct_tgt
                mn_na_macct_tgt = 'No allocation limit between cash account and margin account.'
                mn_cpslongamt_in_cacct_tgt = 'No allocation limit between cash account and margin account.'
                mn_cash_in_cacct_tgt = 'No allocation limit between cash account and margin account.'
                mn_na_cacct_tgt = 'No allocation limit between cash account and margin account.'
                mn_ce_in_cacct_tgt = 'No allocation limit between cash account and margin account.'
                mn_ce_in_macct_tgt = 'No allocation limit between cash account and margin account.'
                mn_cash_in_saccts_tgt = mn_cash_2trd_in_saccts_tgt
                mn_ce_in_saccts_tgt = mn_na_saccts_tgt - mn_cpslongamt_tgt - mn_cash_in_saccts_tgt

            ei_na_faccts_tgt = abs(ei_iclots_tgt) * self.gv.dict_index_future2internal_required_na_per_lot[index_future]
            ei_na_saccts_tgt = ei_na_tgt - ei_na_faccts_tgt - ei_na_oaccts_tgt
            ei_cash_in_saccts_tgt = ei_cpslongamt_tgt * flt_cash2cpslongamt
            ei_netamt_faccts_tgt = floor(ei_iclots_tgt) * self.gv.dict_index_future2spot_exposure_per_lot[index_future]
            ei_int_net_lots_index_future_tgt = floor(ei_iclots_tgt)

            mn_int_net_lots_index_future_tgt = round(mn_iclots_tgt)
            mn_netamt_index_future_in_faccts_tgt = (round(mn_iclots_tgt)
                                                    * self.gv.dict_index_future2spot_exposure_per_lot[index_future])

            dict_bgt_details = {
                'DataDate': self.str_today,
                'PrdCode': self.prdcode,
                'TargetNetAsset': tgt_na,
                'EINetAsset': ei_na_tgt,
                'EINetAssetOfSecurityAccounts': ei_na_saccts_tgt,
                'EINetAssetOfFutureAccounts': ei_na_faccts_tgt,
                'EINetAssetOfOTCAccounts': ei_na_oaccts_tgt,
                'EINetAssetAllocationBetweenCapitalSources': {},
                'EICashInSecurityAccounts': ei_cash_in_saccts_tgt,
                'EICashEquivalentInSecurityAccounts': ei_ce_in_saccts_tgt,
                'EICompositeLongAmountInSecurityAccounts': ei_cpslongamt_tgt,
                'EICompositeShortAmountInSecurityAccounts': ei_cpsshortamt_tgt,
                'EIETFLongAmountInSecurityAccounts': ei_etflongamt_tgt,
                'EIETFShortAmountInSecurityAccounts': ei_etfshortamt_tgt,
                'EINetAmountInFutureAccounts': ei_netamt_faccts_tgt,
                'EIContractsNetLotsInFutureAccounts': ei_int_net_lots_index_future_tgt,
                'EINetExposureFromOTCAccounts': ei_net_exposure_in_oaccts,
                'EIPositionAllocationBetweenCapitalSources': {},
                'MNNetAsset': mn_na_tgt,
                'MNNetAssetOfSecurityAccounts': mn_na_saccts_tgt,
                'MNNetAssetOfCashAccount': mn_na_cacct_tgt,
                'MNNetAssetOfMarginAccount': mn_na_macct_tgt,
                'MNNetAssetOfFutureAccounts': mn_na_faccts_tgt,
                'MNNetAssetOfOTCAccounts': na_oaccts_tgt,
                'MNNetAssetAllocationBetweenCapitalSources': {},
                'MNCashInSecurityAccounts': mn_cash_in_saccts_tgt,
                'MNCashInCashAccount': mn_cash_in_cacct_tgt,
                'MNCashInMarginAccount': mn_cash_in_macct_tgt,
                'MNCashEquivalentInSecurityAccounts': mn_ce_in_saccts_tgt,
                'MNCashEquivalentInCashAccount': mn_ce_in_cacct_tgt,
                'MNCashEquivalentInMarginAccount': mn_ce_in_macct_tgt,
                'MNCashEquivalentFromCashAvailable': mn_ce_from_cash_available,
                'MNCompositeLongAmountInSecurityAccounts': mn_cpslongamt_tgt,
                'MNCompositeLongAmountInCashAccount': mn_cpslongamt_in_cacct_tgt,
                'MNCompositeLongAmountInMarginAccount': mn_cpslongamt_in_macct_tgt,
                'MNCompositeShortAmountInSecurityAccounts': mn_cpsshortamt_in_macct_tgt,
                'MNCompositeShortAmountInMarginAccount': mn_cpsshortamt_in_macct_tgt,
                'MNETFNetAmountInSecurityAccounts': -mn_etfshortamt_in_macct_tgt,
                'MNETFShortAmountInMarginAccount': mn_etfshortamt_in_macct_tgt,
                'MNNetAmountOfFutureAccounts': mn_netamt_index_future_in_faccts_tgt,
                'MNContractsNetLotsOfFutureAccounts': mn_int_net_lots_index_future_tgt,
                'MNNetExposureFromOTCAccounts': net_exposure_from_oaccts_tgt,
                'MNPositionAllocationBetweenCapitalSources': {},
            }
            dict_bgt = {
                'DataDate': self.str_today,
                'PrdCode': self.prdcode,
                'CPSLongAmt': float(ei_cpslongamt_tgt + mn_cpslongamt_tgt),
                'ICLots': ceil(ei_iclots_tgt) + round(mn_iclots_tgt),
                'CE': float(ei_ce_in_saccts_tgt + mn_ce_from_cash_available + mn_ce_from_cash_from_ss_tgt)
            }

            self.gv.list_items_budget_details.append(dict_bgt_details)
            self.gv.list_items_budget.append(dict_bgt)


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
        list_dicts_future_api_holding = list(self.gv.col_future_api_holding
                                             .find({'DataDate': self.str_today, 'AcctIDByMXZ': self.acctidbymxz}))
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
            df_future_api_holding['multiplier'] = (df_future_api_holding['index']
                                                   .map(self.gv.dict_index_future2multiplier))
            df_future_api_holding['windcode'] = df_future_api_holding['instrument_id'] + '.CFE'
            df_future_api_holding['close'] = (df_future_api_holding['windcode']
                                              .map(self.gv.dict_index_future_windcode2close))
            df_future_api_holding['margin_required_in_perfect_shape'] = (df_future_api_holding['position']
                                                                         * df_future_api_holding['multiplier']
                                                                         * df_future_api_holding['close']
                                                                         * margin_rate_in_perfect_shape)
            df_future_api_holding['margin_warning'] = (df_future_api_holding['position']
                                                       * df_future_api_holding['multiplier']
                                                       * df_future_api_holding['close']
                                                       * margin_rate_warning)
            # 跨品种单向大边保证金制度
            dicts_future_api_holding_sum_by_direction = (df_future_api_holding
                                                         .loc[:, ['direction',
                                                                  'margin_required_in_perfect_shape',
                                                                  'margin_warning']]
                                                         .groupby(by='direction')
                                                         .sum()
                                                         .to_dict())
            dict_direction2margin_required_in_perfect_shape = \
                dicts_future_api_holding_sum_by_direction['margin_required_in_perfect_shape']
            dict_direction2margin_warning = dicts_future_api_holding_sum_by_direction['margin_warning']
            if 'long' not in dict_direction2margin_required_in_perfect_shape:
                dict_direction2margin_required_in_perfect_shape['long'] = 0
                dict_direction2margin_warning['long'] = 0
            if 'short' not in dict_direction2margin_required_in_perfect_shape:
                dict_direction2margin_required_in_perfect_shape['short'] = 0
                dict_direction2margin_warning['short'] = 0

            margin_required_by_long = dict_direction2margin_required_in_perfect_shape['long']
            margin_required_by_short = dict_direction2margin_required_in_perfect_shape['short']
            margin_required_in_perfect_shape = max(margin_required_by_long, margin_required_by_short)

            margin_warning_by_long = dict_direction2margin_warning['long']
            margin_warning_by_short = dict_direction2margin_warning['short']
            margin_warning = max(margin_warning_by_long, margin_warning_by_short)

        dict_bs_by_acctidbymxz = (self.gv.col_bs_by_acctidbymxz
                                  .find_one({'DataDate': self.str_today, 'AcctIDByMXZ': self.acctidbymxz}))
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
            prd.budget()
            prd.check_exception()
            prd.check_exposure()
        self.gv.db_trddata['items_2b_adjusted'].delete_many({'DataDate': self.gv.str_today})
        self.gv.db_trddata['items_2b_adjusted'].insert_many(self.gv.list_items_2b_adjusted)
        self.gv.db_trddata['items_budget'].delete_many({'DataDate': self.gv.str_today})
        self.gv.db_trddata['items_budget'].insert_many(self.gv.list_items_budget)
        self.gv.db_trddata['items_budget_details'].delete_many({'DataDate': self.gv.str_today})
        self.gv.db_trddata['items_budget_details'].insert_many(self.gv.list_items_budget_details)


if __name__ == '__main__':
    mfw = MainFrameWork()
    mfw.run()














