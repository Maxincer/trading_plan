# Trading Plan Project Research

## Outline

共4步骤

1. 追保 (maintenance requirement)
   1. 当日期指.xlsx
   2. close close of cash index
2.  敞口 (net exposure (RMB & %))
   1. 当日信息.xlsx
      1. TotalAsset = Available + fund_value + stock
         * 本项, 只抓取了股票帐户的数据
      2. 计算所得总资产 = TotalAsset + balace
         * 本项计算的是股票账户与期货账户的权益合计
      3. TODO
         * 需要加入信用账户B/S数据
   2. 敞口为净敞口，由RMB与%表示
3. 认申赎
   1. 
4. 资金管理

#### 2.3 Topics

##### 2.2.1. 认购、申购与赎回事项（认申赎事项）

1. 读取认申赎事项要素:
   1. 认申赎方向;
      2. 认申赎金额; 
      3. 认申赎净值确认日；
      4. 资金划转日；
   2. 该事项的影响：
         1. 影响敞口BM：使敞口BM发生偏移（资金未划转，但仓位已调整）
   3. 申赎事项的日期，若未分列申购和赎回的日期，则为同一天到账。



## 文件路径

1. **trading_plan**
   
   * 192.168.5.8/trading/策略汇总表/交易计划-<%Y%m%d>.xlsx
   
2. **future accounts data**

   * 192.168.5.8/accounts/future_data/summary/<%Y%m%d>.csv
   *  (Id, Balance, Holding), ("10", 31727342, "-IC2004*31;")

3. **NAV**

   * 192.168.5.8/accounts/python/YZJ/accounts/accounts-\<prdcode>/<%Y%m%d>/accounts.xlsx

4. **估值表(valuation report?)**

   * 192.168.5.8/accounts/account-\<prdcode>/估值表信息.xls

   * T-2： 当日收到T-2日估值表
   * 托管户资金
   * 净值需要向上取整

5. 当日股票普通户与期货户信息.xlsx

   * 数据组盘后在内网通中传"<%Y%m%d>汇.xlsx"
   * 由上述文件经过敞口计算，得到"当日信息.xlsx"

6. 指数现货及期货行情数据

   * 192.168.5.8\accounts\python\common_data

7. 产品交易情况监控页面

   192.168.1.125:8003/?tradetime=t1100 

8. 完整表
   
   * 5.8/accounts/barra/product_data.xlsx







## 命名规则

### 1. 日期

#### 1. 定义

1. 交易执行日，action_date, 执行交易的日期;
2. 制表日, tabulation_date, 制作该表的日期;
3. 认申赎净值确认日, confirmation_date, 按该日期确认认申赎份额的净值;

## 基础知识

### 1. 认申赎的日期(Investment & Redemption)

1. 无论是申购还是赎回都是在当天15点以前的申购按当天净值计算,在15点以后是算第二天的净值(非工作日按下一交易日计算,例星期五下午3点后买的,就是下星期一的净值),但要说的是赎回是T+4天的到账!
2. 申购日: 申购的日期
3. 认申赎净值确认日：15点之前申购，第二日开始计算收益，即第二日收盘时就有变动；15点之后申购的日期，第三日有变动。开始计算收益日期的日期计算收益期间包括该日期当天。该日在本项目中定义为**确认日**。

## Investopedia

1. margin

   2. The **initial margin** represents the percentage of the purchase price that must be covered by the investor's own money and is usually at least 50% of the needed funds.

   3. The **maintenance margin** represents the amount of equity the investor must maintain in the margin account after the purchase has been made in order to keep the position open.

      * https://www.investopedia.com/ask/answers/033015/what-difference-between-initial-margin-and-maintenance-margin.asp

2. NAV (Net Asset Value)

   1. for a company, NAV is  equal to a fund's or company's total assets less its liabilities.

   2. for a fund, NAV is equal to:

      *NAV = (Assets - Liabilities) / Total number of outstanding shares*

3. Capital Buffer

   1. A capital buffer is mandatory capital that financial institutions are required to hold in addition to other minimum [capital requirements](https://www.investopedia.com/terms/c/capitalrequirement.asp). Regulations targeting the creation of adequate capital buffers are designed to reduce the procyclical nature of [lending](https://www.investopedia.com/articles/wealth-management/040216/using-hard-money-loans-real-estate-investments.asp) by promoting the creation of countercyclical buffers as set forth in the [Basel III](https://www.investopedia.com/terms/b/basell-iii.asp) regulatory reforms created by the [Basel Committee on Banking Supervision](https://www.investopedia.com/terms/b/baselcommittee.asp).
   2. A capital buffer is mandatory capital that financial institutions are required to hold.
   3. Capital buffers were mandated under the Basel III regulatory reforms, which were implemented following the 2007-2008 financial crisis.
   4. Capital buffers help to ensure a more resilient global banking system.

4. Cash Account

   * A cash account is a brokerage account in which a customer is required to pay the full amount for securities purchased, and [buying on margin](https://www.investopedia.com/terms/b/buying-on-margin.asp) is prohibited. The Federal Reserve's [Regulation T](https://www.investopedia.com/terms/r/regulationt.asp) governs cash accounts and the purchase of securities on margin. This regulation gives investors two business days to pay for security.
   * 为国内的"普通账户"

5. Margin Account

   * A **margin account** allows an investor to purchase stocks with a percentage of the price covered by a loan from the brokerage firm.

   * 为国内的"信用账户".

6. Long Market Value

   * The long market value is the aggregate worth, in dollars, of a group of securities held in a cash or margin brokerage account. Long market value is calculated using the prior trading day's closing prices of each security in the account. Although, in a liquid market, current market values on individual securities are available real time. However, most financial applications use the prior days ending balance as the current long market value of a portfolio.
   
7. Short Position

   1. A [naked short](https://www.investopedia.com/terms/n/nakedshorting.asp) is when a trader sells a security without having possession of it. 
   2. However, that practice is illegal in the U.S. for equities. 
   3. A covered short is when a trader borrows the shares from a stock loan department; in return, the trader pays a borrow-rate during the time the short position is in place.
   
8. Liquidate

   * [Liquidate means to convert assets into cash or cash equivalents by selling them on the open market.](https://www.investopedia.com/terms/l/liquidate.asp)
   
9. Cash Equivalents

   * Cash equivalents are investments securities that are meant for short-term investing; they have high [credit quality](https://www.investopedia.com/terms/c/creditquality.asp) and are highly liquid.

## Markdown Shortcuts

1. C + shift + m, 添加数学公式模块



# trading_period

| trade_time |   开始   |   结束   |
| :--------: | :------: | :------: |
|   t0930    | 9:31:30  | 9:45:00  |
|   t0935    | 9:32:30  | 10:30:00 |
|  t093502   | 9:35:00  | 9:50:00  |
|   t0945    | 9:45:00  | 10:15:00 |
|   t1000    | 10:00:00 | 10:25:00 |
|   t1030    | 10:30:30 | 11:10:00 |
|   t1100    | 11:00:00 | 11:25:30 |
|   t1300    | 13:00:00 | 13:27:01 |
|   t1330    | 13:30:00 | 13:55:59 |
|   t1400    | 14:03:00 | 14:45:50 |
|   t1430    | 14:25:00 | 14:56:50 |

# 20200402

## 0. 总原则

1. 先考虑期货户资金， 再考虑其他账户

   1. 足够的保证金
   2. 没有多余的保证金

   

## 1. 追保

1. 数据载入

   1. 192.168.5.8/accounts/future_data/summary/<%Y%m%d>.csv 载入
   2. 本地文件"当日期指1.xlsx"载入
   3. 行情数据：shiming\accouts\python\common_data\ETF000905.csv

2. 以"当日期指1.xlsx"为底稿，进行计算

   1. 行情更新，价格为收盘价

   2. Ratio, 单手合约合约价值之比, IH/IC.

      1. IC, 200, 8%;
      2. IF, 300, 8%;
      3. IH, 300, 8%.

   3. 计算账户维持保证金(MM, maintenance margin)

      * maintenance margin = max(short_side MM, long_side MM)

   4. 12%: 0%buffer; 17%: 5%buffer; 20%: 8%buffer

      * 期货公司要求保证金比率: 12%

   5. 关注:[目前buffer, 8%buffer保证金_required, 权益-8%buffer保证金]

      * 目前buffer: 

        * = balance/ 空头合约价值 - 0.12
        * 平时要求在3%以上, 节假日要求5%以上
        * 升序排列观察产品追保必要性

      * 8%buffer保证金_required 

        = "期指数量" * 20%保证金

   6. TODO

      * 确认期指数量算法

## 2. 敞口

1. 数据载入
   1. 交易计划表
      * 192.168.5.8/trading/策略汇总表/交易计划-<%Y%m%d>.xlsx
   2. 当日股票普通户与期货户信息表
      * 数据组盘后在内网通中传"<%Y%m%d>汇.xlsx"
2. 计算"<%Y%m%d>汇.xlsx"，得到"当日信息.xlsx"

   * 计算敞口RMB及%
3. 敞口分析
   1. 919 敞口金额近-100万， 可平空1手

   2. 913敞口金额377w

* 有信用户（空）, 需要通过华泰一户通登陆

* 开空3手
      * 需查询实际交易情况
      

3. 922 → No action

   1. 922共有4个账户: 国君普通, 国君信用, 中信普通, 国君期货
      1. 国君普通, asset = 752w, stock_value = 0w, mmf_value = 602w, available = 150w, equity = 752w
      2. 国君信用, asset = 4047w, stock_value = 1844w, equity = 2209w, available = 251w, liability = 1837w, mmf_value = 1952w
      3. 中信普通, asset = 2600w, mmf_value = 2600w
      4. 国君期货, liquidated, balance = 435w
      5. total_stock_value = 1844, liability = 1837, total equity = 5561
      6. net exposure = 7w(0%)
      7. No action

## 3. 申赎

1. 数据载入

   1. 微信群通知消息
   2. 由杨老师整理至"交易计划-<%Y%s%d>.xlsx"中的"明日资金划转计划"列。
   3. 净值文件，向上调整
      * 192.168.5.8/accounts/python/YZJ/accounts/accounts-\<prdcode>/<%Y%m%d>/accounts.xlsx
      * sheet:accounts, U208
   4. 192.168.5.8/accounts/account-\<prdcode>/估值表信息.xls

2. 数据处理

   1. 903, 赎回1100万

      1. 原则：划出1100万现金后，产品组合符合要求

      2. 903有4个账户，4类账户(cash/margin/future/option)各有一个

         * 1C, 1M, 1F, 1O

         * cash_account
           * A: 6w

         * margin_account
           * A: 4415w, L: 0, E: 4415w, Cash: 0, MMF:  3300w, Stock: 900w
         * future_account
           * E: 963w, A: 800w, CapitalMaintenance: 160w, AvailableFund: 800w
         * ProductEquity = 6+4415+963 = 5384w

      3. 期货账户要求要留足现金，以hedge掉多头满仓（0.77tot_asset）

         1. 多头市值满仓估算原则

            1. 对冲型(0.77)
               $$
               ExpectedLongMarketValue = 0.77*ProductEquity
               $$

               $$
               ExpectedCashInStockAccount = 0.1*LongMarketValue
               $$

            2. 指数增强型(0.9)
               $$
               ExpectedLongMarketValue = 0.9*ProductEquity
               $$

         2. 903划款分配

         $$
            ExpectedLMV = (5384-1100) * 0.77*0.3 = 989w
         $$

         $$
            FutureAccountEquity = (5384-1100)*0.77*0.20=660w
         $$

            即，期货户可转出963-660=300w 

            则，信用户转出1100-300=800w。

3. 数据输出

   1. 903赎回1100w
      1. 903, 信用户\<id>, 转银300w;
      2. 903, 期货户\<id>, 转银800w。卖出货基800w, 多卖一些，以防止交易不达预期占用

   2. 

## 4. 资金管理（补充意义）

1. 数据载入

2. 数据处理

   0. 原则
      * 保证股票在换仓时有市值的8%~10%的换仓资金为可用状态

   1. 903, 扣除赎回款后
      1. margin account: stock_value = 900w, cash_required_by_

3. 数据输出

## 5. 临时事件影响

行情大幅波动

申赎

仓位

账户间分配

合同限制

账户更换

##  6. 输出格式

1. 目标持仓7800万，77手IC空头（平29手IC空头）/3c
2. 买货基2800万
3. 交易时段开2手IC多头
4. 海通证券目标持仓3900万，华泰目标持仓2500万，64手IC空头



## 6. TODO

1. 建立两个数据库

   1. 需要掌握产品所有的账户信息，需建立映射
      * 产品账户数据库
        * 据此实现函数，产品状况概览
   2. 账户密码数据库

   

2. 申赎计算中，产品规模的起算时间





"""
acctstatus:

	* T, trading: trading, not liquidated, equity != 0.
	* N, null: equity = 0（或可忽略不计） and liquidated.
	* L, liquidated and equity !=0
	* C: closed or to be closed.
	* abnormal: 账户异常
	* unknown: 账户状态未知

"""



