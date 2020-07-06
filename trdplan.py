#!usr/bin/env python37
# coding:utf-8
# Author: Maxincer
# Create Datetime: 20200626T112000 +0800
# Update Datetime: 20200626T170000 +0800

"""
思路：

重要假设:
    1. ETF: exchange traded fund: 交易所交易基金。不存在场外ETF。
    2.

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

    def budget(self):
        """
        假设：
        1. 有target用target覆盖，无target就用现值
        2. 空头暴露分配优先级（从高到低）：融券ETF，场外收益互换，股指期货
        3. 重要： EI策略中不使用ETF来补充beta
        4. 重要： 期指对冲策略中，只使用IC进行对冲
        5. 重要： 最多两个策略且由这两个策略构成： EI， MN
        6. 重要： 分配c与m的资金时，如果有融资融券负债，要尽可能少的分给m户。
        （限制： 1.最多净资产为cpslongamt的1.088 2. 维持担保比例要充足）
        7. 由于公司的策略交易模式限制，更倾向于放在m户中交易。
        Note:
            1. 注意现有持仓是两个策略的合并持仓，需要按照比例分配。
            2. 本函数未对SecurityAccounts中的 cash account 及 margin account 进行区分。
        思路：
            1. 先求EI的shape，剩下的都是MN的。
            2. 分配普通和信用时，采取信用户净资产最小原则（不低于最低维持担保比例）
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

        # 算法部分
        tgt_na = self.prd_approximate_na
        if self.dict_tgt_items:
            if self.dict_tgt_items['NetAsset']:
                tgt_na = self.dict_tgt_items['NetAsset']

        # 1. EI策略budget
        ei_na_tgt = tgt_na * self.dict_strategies_allocation['EI']
        ei_cpslongamt_tgt = ei_na_tgt * self.tgt_cpspct
        ei_long_exposure_from_faccts = (ei_na_tgt
                                        - (ei_cpslongamt_tgt
                                           + ei_etflongamt_tgt
                                           - ei_cpsshortamt_tgt
                                           - ei_etfshortamt_tgt))
        ei_int_net_lots_index_future_tgt = self.cmp_f_lots('EI', ei_long_exposure_from_faccts, ic_if_ih)
        ei_netamt_faccts_tgt = (
                ei_int_net_lots_index_future_tgt
                * self.gv.dict_index_future_windcode2close[self.gv.dict_index_future2spot[ic_if_ih]]
                * self.gv.dict_index_future2multiplier[ic_if_ih]
        )
        ei_na_faccts_tgt = ei_netamt_faccts_tgt * flt_ei_internal_required_margin_rate
        ei_cpslongamt_tgt = (ei_na_tgt
                             - ei_netamt_faccts_tgt
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
        # todo 有两种模式：1. 指定composite long amt 仓位模式 2. composite long amt 最大值模式
        # todo 先写指定仓位模式
        # todo 换仓资金比例假设：采用定值模式中，EI策略与MN策略换仓资金比例最小值，EI: 0.0888，MN：0.0987，即留出0.889的换仓资金即可。
        # todo 20200704需要分析两融户中换仓资金的准确算法， 即 保证金制度交易下的详细算法（大课题）。
        # todo 假设目前普通户与两融户无分配比例要求。

        # 指定仓位模式（根据self.tgt_cpspct确定cpsamt金额）：

        # MN 策略预算假设
        flt_mn_cash2cpslongamt = 0.0888

        # 2.1 分配MN策略涉及的账户资产
        mn_na_tgt = tgt_na * self.dict_strategies_allocation['MN']
        mn_cpslongamt_tgt = mn_na_tgt * self.tgt_cpspct
        mn_cash_2trd_in_saccts_tgt = mn_cpslongamt_tgt * flt_mn_cash2cpslongamt

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

        mn_shortamt_in_macct = mn_etfshortamt_in_macct + mn_cpsshortamt_in_macct
        # todo 假设： 若有融券负债，则将该渠道的cpslongamt均放入macct.
        # todo 若无融券负债，则不对cacct 与 macct分配，使用当前值进行分配




        # 求oacct提供的空头暴露预算值与多头暴露预算值
        # 求oacct账户中的存出保证金（net_asset）
        # 根据实际业务做出假设：1. oacct全部用于MN策略 2.oacct仅提供short exposure
        # todo oacct中出现多头暴露时需要改进
        list_dicts_oacct_basicinfo = list(
            self.gv.col_acctinfo.find({'DataDate': self.str_today, 'PrdCode': self.prdcode, 'AcctType': 'o'})
        )
        mn_short_exposure_from_oaccts = 0  # 假设oacct的账户全部且仅为MN服务
        mn_approximate_na_oaccts = 0  # 假设oacct的账户全部且仅为MN服务
        for dict_oacct_basicinfo in list_dicts_oacct_basicinfo:
            if dict_oacct_basicinfo:
                acctidbymxz_oacct = dict_oacct_basicinfo['AcctIDByMXZ']
                dict_exposure_analysis_by_acctidbymxz = self.gv.col_exposure_analysis_by_acctidbymxz.find_one(
                    {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_oacct}
                )
                mn_short_exposure_from_oacct_delta = dict_exposure_analysis_by_acctidbymxz['ShortExposure']
                mn_short_exposure_from_oaccts += mn_short_exposure_from_oacct_delta
                dict_bs_by_acctidbymxz = self.gv.col_bs_by_acctidbymxz.find_one(
                    {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_oacct}
                )
                mn_approximate_na_oacct_delta = dict_bs_by_acctidbymxz['ApproximateNetAsset']
                mn_approximate_na_oaccts += mn_approximate_na_oacct_delta

        mn_short_exposure_from_oaccts_tgt = mn_short_exposure_from_oaccts
        if self.dict_tgt_items['ShortExposureFromOTCAccounts']:
            mn_short_exposure_from_oaccts_tgt = self.dict_tgt_items['ShortExposureFromOTCAccounts']
        mn_na_oaccts_tgt = mn_approximate_na_oaccts
        if self.dict_tgt_items['NetAssetInOTCAccounts']:
            mn_na_oaccts_tgt = self.dict_tgt_items['NetAssetInOTCAccounts']

        mn_netamt_index_future_in_faccts_tgt = (mn_cpslongamt_tgt
                                                - mn_etfshortamt_in_macct_tgt
                                                - mn_cpsshortamt_in_macct_tgt
                                                - mn_short_exposure_from_oaccts_tgt)
        # todo 假设: 指定IC为唯一对冲工具
        mn_int_net_lots_index_future_tgt = self.cmp_f_lots('MN', mn_netamt_index_future_in_faccts_tgt, ic_if_ih)
        mn_na_faccts_tgt = (mn_int_net_lots_index_future_tgt
                            * self.gv.dict_index_future_windcode2close[self.gv.dict_index_future2spot[ic_if_ih]]
                            * self.gv.dict_index_future2multiplier[ic_if_ih] * 0.2)

        # 求期货户提供的多空暴露预算值
        # ！！！注： 空头期指为最后算出来的项目，不可指定（指定无效）
        # 价格为对应的现货指数价格
        list_dicts_faccts_basicinfo = list(
            self.gv.col_acctinfo.find({'DataDate': self.str_today, 'PrdCode': self.prdcode, 'AcctType': 'f'})
        )
        netamt_index_future_in_faccts = 0  # 注意 此处是faccts,（非facct）, 是所有facct的合计
        for dict_facct_basicinfo in list_dicts_faccts_basicinfo:
            acctidbymxz_facct = dict_facct_basicinfo['AcctIDByMXZ']
            # 按照exposure amount 排除ei的部分
            list_dicts_future_api_holding = self.gv.col_future_api_holding.find(
                {'DataDate': self.str_today, 'AcctIDByMXZ': acctidbymxz_facct}
            )

            longamt_index_future_in_facct = 0
            shortamt_index_future_in_facct = 0
            for dict_future_api_holding in list_dicts_future_api_holding:
                lots_position = dict_future_api_holding['position']
                direction = dict_future_api_holding['direction']
                instrument_id_first_2 = dict_future_api_holding['instrument_id'][:2]
                if instrument_id_first_2 in ['IC', 'IF', 'IH']:
                    close = self.gv.dict_index_future_windcode2close[
                        self.gv.dict_index_future2spot[instrument_id_first_2]
                    ]
                    multiplier = self.gv.dict_index_future2multiplier[instrument_id_first_2]
                    if direction == 'long':
                        longamt_index_future_in_facct_delta = lots_position * close * multiplier
                        longamt_index_future_in_facct += longamt_index_future_in_facct_delta
                    elif direction == 'short':
                        shortamt_index_future_in_facct_delta = lots_position * close * multiplier
                        shortamt_index_future_in_facct += shortamt_index_future_in_facct_delta
                    else:
                        raise ValueError('Unknown instrument_id_first_2 when computing amt in facct.')
            netamt_index_future_in_facct_delta = longamt_index_future_in_facct - shortamt_index_future_in_facct
            netamt_index_future_in_faccts += netamt_index_future_in_facct_delta

        mn_netamt_index_future_in_faccts = netamt_index_future_in_faccts - ei_netamt_faccts_tgt

        # todo 资金分配
        # 分配cacct与macct(若有负债优先分配macct，若无负债则整体达标即可)
        mn_na_saccts_tgt = mn_na_tgt - mn_na_faccts_tgt - mn_na_oaccts_tgt
        if mn_shortamt_in_macct:
            mn_cpslongamt_in_macct_tgt = mn_cpslongamt_tgt
            mn_cash_2trd_in_macct_tgt = mn_cpslongamt_in_macct_tgt * flt_mn_cash2cpslongamt
            mn_ce_in_macct_tgt = mn_cash_from_ss_in_macct_tgt
            mn_na_macct_tgt = mn_cpslongamt_in_macct_tgt + mn_cash_2trd_in_macct_tgt
            mn_na_cacct_tgt = mn_na_saccts_tgt - mn_na_macct_tgt
            mn_ce_in_cacct_tgt = mn_na_cacct_tgt - 1500000
            if mn_ce_in_cacct_tgt < 0:
                mn_ce_in_cacct_tgt = 0
        else:
            mn_cpslongamt_in_macct_tgt = 'No allocation limit between cash account and margin account.'
            mn_cash_2trd_in_macct_tgt = 'No allocation limit between cash account and margin account.'
            mn_na_macct_tgt = 'No allocation limit between cash account and margin account.'
            mn_cpslongamt_in_cacct_tgt = 'No allocation limit between cash account and margin account.'
            mn_cash_2trd_in_cacct_tgt = 'No allocation limit between cash account and margin account.'
            mn_na_cacct_tgt = 'No allocation limit between cash account and margin account.'

        # todo 算法需确认
        mn_ce_in_saccts_tgt = (mn_na_saccts_tgt
                               - mn_cpslongamt_tgt
                               - mn_cash_2trd_in_saccts_tgt
                               + mn_cash_from_ss_in_macct_tgt)

        dict_tgt = {
            'DataDate': self.str_today,
            'PrdCode': self.prdcode,
            'TargetNetAsset': tgt_na,
            'EINetAsset': ei_na_tgt,
            'EINetAssetOfSecurityAccounts': ei_na_saccts_tgt,
            'EINetAssetOfFutureAccounts': ei_na_faccts_tgt,
            'EINetAssetOfOTCAccounts': ei_na_oaccts_tgt,
            'EINetAssetAllocationBetweenCapitalSources': {},
            'EICashOfSecurityAccounts': ei_cash_in_saccts_tgt,
            'EICashEquivalentOfSecurityAccounts': ei_ce_in_saccts_tgt,
            'EICompositeLongAmountOfSecurityAccounts': ei_cpslongamt_tgt,
            'EICompositeShortAmountOfSecurityAccounts': ei_cpsshortamt_tgt,
            'EIETFLongAmountOfSecurityAccounts': ei_etflongamt_tgt,
            'EIETFShortAmountOfSecurityAccounts': ei_etfshortamt_tgt,
            'EINetAmountOfFutureAccounts': ei_netamt_faccts_tgt,
            'EIContractsNetLotsOfFutureAccounts': ei_int_net_lots_index_future_tgt,  # todo 此处仅指IC合约
            'EINetExposureFromOTCAccounts': ei_net_exposure_in_oaccts,
            'EIPositionAllocationBetweenCapitalSources': {},
            'MNNetAsset': mn_na_tgt,
            'MNNetAssetOfSecurityAccounts': mn_na_saccts_tgt,
            'MNNetAssetOfFutureAccounts': mn_na_faccts_tgt,
            'MNNetAssetOfOTCAccounts': mn_na_oaccts_tgt,
            'MNNetAssetAllocationBetweenCapitalSources': {},
            'MNCashOfSecurityAccounts': mn_cash_2trd_in_saccts_tgt,
            'MNCashEquivalentOfSecurityAccounts': mn_ce_in_saccts_tgt,
            'MNCompositeLongAmountOfSecurityAccounts': mn_cpslongamt_tgt,
            'MNCompositeShortAmountOfSecurityAccounts': mn_cpsshortamt_in_macct_tgt,
            'MNETFNetAmountOfSecurityAccounts': -mn_etfshortamt_in_macct_tgt,
            'MNNetAmountOfFutureAccounts': mn_netamt_index_future_in_faccts_tgt,
            'MNContractsNetLotsOfFutureAccounts': mn_int_net_lots_index_future_tgt,  # todo 此处仅指IC合约
            'MNNetExposureFromOTCAccounts': mn_short_exposure_from_oaccts_tgt,
            'MNPositionAllocationBetweenCapitalSources': {},
        }
        self.gv.list_items_budget.append(dict_tgt)


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


if __name__ == '__main__':
    mfw = MainFrameWork()
    mfw.run()














