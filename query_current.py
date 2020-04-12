#!usr/bin/env python3
# coding=utf8

import time
from collect_future_data import Trader
import pandas as pd
import os
import datetime
import configparser
import cx_Oracle

today = datetime.date.today()
stock_list = ['IC', 'IF', 'IH']

config = configparser.ConfigParser()
config.read("config.ini")
username = config.get("sysconfig", "username")
password = config.get("sysconfig", "password")
url = config.get("sysconfig", "url")
config_connect = cx_Oracle.connect('%s/%s@%s' % (username, password, url))

new_old_names = {'2_zc': '2', '3_xb': '3', '5_ht': '5', '6_dh': '6', '7_ya': '7', '8_ht': '8', '8_dh': '8-1', '10_xb': '10', '11_nh': '11', '12_ya': '12', '12_ht': '12-ht', '13_ht': '13', '14_ht': '14',
           '15_ht': '15', '16_ya': '16', '17_zc': '17', '18_zx': '18-zx', '18_ht': '18', '20_ht': '20', '21_sw': '21', '22_gtja': '22', '25_ya': '25', '26_zx': '26', 'ct11_fzzq': 'ct11','ct13_gf':'ct13','ct15_ht':'ct15','ct15_xb': 'ct15', 'ct16_zc': 'ct16', 'ct17_gtja': 'ct17', 'ct18_hy': 'ct18', 'ct19_zx': 'ct19', 'ct1_ht': 'ct1', 'ct26_zygj': 'ct26', 'ct3_ya': 'ct3', 'ct5_xb': 'ct5', 'ct6_jr': 'ct6', 'ct8_ht': 'ct8',
           'km10_xz': 'km10', 'km11_zx':'km11-zx', 'km11_xz': 'km11-xz', 'km11_sw': 'km11', 'km6_zc': 'km6', 'km7_nh': 'km7', 'km8_nh': 'km8',
           'mtx10_dh': 'mtx10-dh', 'mtx11_xz': 'mtx11', 'mtx13_xz': 'mtx13', 'mtx4_zx':'mtx4-zx', 'mtx4_zc': 'mtx4', 'mtx6_zc': 'mtx6', 'rczx1_xb': 'rczx1',
           'jx10_ya': 'jx10', 'jx1_gy': 'jx1', 'jx2_2_zc': 'jx2-2', 'jx2_zc': 'jx2', 'jx8_zc': 'jx8', 'jx9_zxjt': 'jx9-zxjt', 'jx9_zg': 'jx9', 'rc2_xb': 'rc2', 'rc5_ht': 'rc5', 'rc7_ya': 'rc7', 'rc8_gy':'rc8','rc9_gy':'rc9','msah2_2_yh':'msah2-2','msah2_yh':'msah2','msah3_zx':'msah3','msah5_yh':'msah5','msah7_yh':'msah7','msah8_yh':'msah8','msah9_zg':'msah9','ct20_zx':'ct20-zx','rc2_hy':'rc2-hy', 'msah7b_yh': 'msah7b-yh', 'rc3_zc': 'rc3-zc'}

if config_connect:
    query_cursor = None
    try:
        query_cursor = config_connect.cursor()
        query_cursor.execute("SELECT ID,PNAME,PCODE FROM SYSTEM_PRODUCT_DETAIL WHERE ID>=0 ORDER BY ID")
        rows = query_cursor.fetchall()
    finally:
        if query_cursor:
            query_cursor.close()

    for row in rows:
        product_code = row[2]
        product_code_old = (lambda product_code:new_old_names[product_code] if product_code in new_old_names else product_code)(product_code)
        product_code_old = product_code_old.replace("_", "-")
        product_name = row[1]
        print(product_name)
        product_id = row[0]
        print(product_id)
        try:
            asset_data = {}
            trade_data = {}
            transfer_serial = {}
            a = Trader(product_code, "yangyang")
            asset_inf = a.query_account()
            time.sleep(1.1)
            holding_inf = a.query_holding(product_code)
            time.sleep(1.1)
            trade_inf = a.query_trading()
            time.sleep(1.1)
            transfer_serial = a.query_transfer_serial()
            log.info(u"%s查询账户、持仓明细、交易明细、资金流水等内容完成。" % product_name)

            print(product_code_old)
            if not os.path.exists(path+'\{}'.format(product_code_old)):
                os.mkdir(path+'\{}'.format(product_code_old))

            if asset_inf['success'] ==1:
                print(asset_inf['list'][0])
                asset_data[row[2]] = asset_inf['list'][0]
                df = pd.DataFrame(asset_data).T
                df['static_balance']=df['pre_balance']+df['deposit']-df['withdraw']-df['pre_credit']-df['pre_mortgage']
                df['dynamic_balance']=df['static_balance']+df['close_profit']+df['position_profit']-df['commission']
                df['usable_current']=df['dynamic_balance']-df['curr_margin']-df['frozen_margin']-df['frozen_commission']-df['delivery_margin']+df['credit']#-df['position_profit']
                df['CurrMargin'] = df['curr_margin']
                df['Avaliable'] = df['usable_current']
                df['Balance'] = df['dynamic_balance']
                df['Long_MarketCap'] = 0.0
                df['Short_MarketCap'] = 0.0
                asset_col = ['Balance','CurrMargin','Avaliable','commission','withdraw','deposit','pre_balance','static_balance','Long_MarketCap','Short_MarketCap']
                for index in df.columns.tolist():
                    if index not in asset_col:
                        df.drop(index,axis = 1,inplace =True)
                df.to_csv(path+r'\{}\asset_fut.csv'.format(product_code_old),index = None,columns=['Balance', 'CurrMargin', 'Avaliable', 'Long_MarketCap', 'Short_MarketCap','commission','withdraw','deposit','pre_balance','static_balance'])

                if len(holding_inf) > 0:
                    holding_inf['Holding'] = holding_inf['position']
                    holding_inf['Id'] = holding_inf['instrument_id']
                    # holding_inf['Direction'] = holding_inf['direction']
                    holding_inf['Direction'] = holding_inf['direction'].apply(lambda x: 'sell' if x == 'short' else 'buy')
                    holding_inf['type'] = holding_inf['Id'].map(lambda x: x[0:2])
                    holding_inf['stock'] = holding_inf['type'].map(lambda x: int(x in stock_list))
                    holding_col = ['Id','Direction','Holding','stock']
                    for c in holding_inf.columns.tolist():
                        if c not in holding_col:
                           holding_inf.drop(c,axis =1,inplace =True)
                else:
                    log.warning(u"%s持仓为空！" % product_name)
                    holding_inf = pd.DataFrame(columns=['Id', 'Direction', 'Holding', 'stock'])
                holding_inf.to_csv(path+'\{}\holding_fut.csv'.format(product_code_old),index = None,columns = ['Id','Direction','Holding','stock'])
            else:
                log.error(u"获取%s资金内容异常！" % product_name)

            if trade_inf['success'] == False or ("list" in trade_inf and len(trade_inf['list']) == 0):
                log.warning(u'%s至当前时间未发生交易！' % product_name)
                df = pd.DataFrame(columns = ['Id','Direction','Price','Volume'])
            else:
                trade_data[row[2]] = trade_inf['list']
                df = pd.DataFrame(trade_data[row[2]])
                df.rename(columns = {'instrument_id':'Id','direction':'Direction','volume':'Volume','Price':'price'},inplace =True)
                df['Commission'] = 0
                df['stock']= df['Id'].apply(lambda x: 1 if (x[:2] == 'IF') or (x[:2] == 'IH') or (x[:2] == 'IC')else 0)
                df['Price'] = df['price']
                cols = ['Id','Direction','Commission','Price','Volume','stock']
                df = df[cols]
            df.to_csv(path + r'\{}\trade_fut.csv'.format(product_code_old), index=None,columns =['Id','Direction','Commission','Price','Volume','stock'])

            #输出资金流水到文件
            if transfer_serial['success'] == False or (list in transfer_serial and len(transfer_serial['list']) == 0):
                log.warning(u'%s至当前时间未发生资金流水！' % product_name)
                df = pd.DataFrame(columns=['Time', 'Amount'])
            else:
                trade_data[row[2]] = trade_inf['list']
                df = pd.DataFrame(trade_data[row[2]])
                #'availability_flag', 'currency_id', 'broker_id', 'bank_branch_id', 'idetified_card_no', 'future_acc_type', 'investor_id', 'cust_fee', 'bank_serial', 'trade_date', 'trade_time', 'broker_fee', 'id_card_type', 'account_id', 'operator_code', 'broker_branch_id', 'future_serial', 'bank_acc_type', 'trading_day', 'bank_account', 'trade_amount', 'plate_serial', 'bank_id', 'session_id', 'trade_code', 'bank_new_account'
                df.rename(columns={'trade_time': 'Time', 'trade_amount': 'Amount'},inplace =True)
                cols = ['Time', 'Amount']
                df = df[cols]
            df.to_csv(path + r'\{}\transfer_serial.csv'.format(product_code_old), index=None,columns =['Time', 'Amount'])
            del a
        except BaseException as e:
            print("************************************")
            print(u"%s" % e)
            print("************************************")
            print(e)


# for prod in prod_list:
#
#
#
# for prod in prod_list:
#     for file in ['asset_fut.csv','holding_fut.csv','trade_fut.csv']:
#         if not os.path.exists(path+ r'\{}\{}'.format(prod,file)):
#             print prod,file,' is none ***************************************'
# print u'已检查是否下全'



