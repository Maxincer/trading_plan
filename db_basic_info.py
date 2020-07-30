#!usr/bin/env python37
# coding:utf-8
# Author: Maxincer

from datetime import datetime
import json
from os import path

import pymongo
import pandas as pd


class DatabaseBasicInfo:
    def __init__(self):
        self.str_today = datetime.strftime(datetime.today(), '%Y%m%d')
        self.fpath_basicinfo = 'data/basic_info.xlsx'
        dbclient = pymongo.MongoClient('mongodb://localhost:27017/')
        db_basicinfo = dbclient['basicinfo']
        self.col_acctinfo = db_basicinfo['acctinfo']
        self.col_acctinfo.create_index([('DataDate', pymongo.DESCENDING), ('AcctIDByMXZ', pymongo.ASCENDING)])
        self.col_prdinfo = db_basicinfo['prdinfo']
        self.col_broker_info = db_basicinfo['broker_info']

    def update_acctinfo(self):
        """
        重要： 在self.update_prdinfo之前运行
        """
        df_acctinfo = pd.read_excel(self.fpath_basicinfo,
                                    sheet_name='acctinfo',
                                    dtype={
                                        'AcctIDByBroker': str,
                                        'AcctIDByMXZ': str,
                                        'AcctStatus': str,
                                        'AcctType': str,
                                        'BrokerAlias': str,
                                        'DataDate': str,
                                        'DataFilePath': str,
                                        'DataSourceType': str,
                                        'PatchMark': int,
                                        'PrdCode': str,
                                        'RptMark': int,
                                        'CapitalSource': str,
                                    }
                                    )
        df_acctinfo = df_acctinfo.where(df_acctinfo.notnull(), None)
        list_dicts_to_be_inserted = df_acctinfo.to_dict('records')
        for dict_to_be_inserted in list_dicts_to_be_inserted:
            dict_to_be_inserted['DataDate'] = self.str_today
        self.col_acctinfo.delete_many({'DataDate': self.str_today})
        self.col_acctinfo.insert_many(list_dicts_to_be_inserted)
        print('Collection "acctinfo" has been updated.')

    def update_prdinfo(self):
        iter_dicts_prdcodes_rptmark = self.col_acctinfo.find(
            {'DataDate': self.str_today, 'RptMark': 1}, {'PrdCode': 1, '_id': 0}
        )
        set_prdcodes_rptmark = set()
        for dict_prdcode_rptmark in iter_dicts_prdcodes_rptmark:
            prdcode = dict_prdcode_rptmark['PrdCode']
            set_prdcodes_rptmark.add(prdcode)

        df_prdinfo = pd.read_excel(self.fpath_basicinfo,
                                   sheet_name='prdinfo',
                                   dtype={
                                       'PrdCode': str,
                                       'PrdName': str,
                                       'SignalsOnTrdPlan': str,
                                       'CptTrdStartTime': str,
                                       'PrdCodeIn4121FinalNew': str,
                                       'StrategiesAllocation': str,
                                       'NetAssetAllocation': str,
                                       'TargetCompositePercentage': float,
                                       '超额计提': int,
                                       'TargetItems': str,
                                   })
        df_prdinfo = df_prdinfo.where(df_prdinfo.notnull(), None)
        list_dicts_to_be_inserted = df_prdinfo.to_dict('records')
        for dict_to_be_inserted in list_dicts_to_be_inserted:
            prdcode = dict_to_be_inserted['PrdCode']
            if prdcode in set_prdcodes_rptmark:
                dict_to_be_inserted['RptMark'] = 1
            else:
                dict_to_be_inserted['RptMark'] = 0
            dict_to_be_inserted['DataDate'] = self.str_today
            dict_to_be_inserted['UNAVFromLiquidationRpt'] = None

            if dict_to_be_inserted['StrategiesAllocation']:
                dict_strategy_allocation = json.loads(dict_to_be_inserted['StrategiesAllocation'].replace("'", '"'))
                if 'MN' not in dict_strategy_allocation:
                    dict_strategy_allocation['MN'] = 0
                if 'EI' not in dict_strategy_allocation:
                    dict_strategy_allocation['EI'] = 0
                dict_to_be_inserted['StrategiesAllocation'] = dict_strategy_allocation
            if dict_to_be_inserted['NetAssetAllocation']:
                dict_na_allocation = json.loads(dict_to_be_inserted['NetAssetAllocation'].replace("'", '"'))
                dict_to_be_inserted['NetAssetAllocation'] = dict_na_allocation
            if dict_to_be_inserted['TargetItems']:
                dict_tgtitems = json.loads(dict_to_be_inserted['TargetItems'].replace("'", '"'))
                if 'ETFShortAmountInMarginAccount' not in dict_tgtitems:
                    dict_tgtitems['ETFShortAmountInMarginAccount'] = None
                if 'CompositeShortAmountInMarginAccount' not in dict_tgtitems:
                    dict_tgtitems['CompositeShortAmountInMarginAccount'] = None
                if 'ShortExposureFromOTCAccounts' not in dict_tgtitems:
                    dict_tgtitems['ShortExposureFromOTCAccounts'] = None
                if 'NetExposureFromOTCAccounts' not in dict_tgtitems:
                    dict_tgtitems['NetExposureFromOTCAccounts'] = None
                if 'CashFromShortSellingInMarginAccount' not in dict_tgtitems:
                    dict_tgtitems['CashFromShortSellingInMarginAccount'] = None
                if 'NetAssetInOTCAccounts' not in dict_tgtitems:
                    dict_tgtitems['NetAssetInOTCAccounts'] = None
                if 'NetAsset' not in dict_tgtitems:
                    dict_tgtitems['NetAsset'] = None
                dict_to_be_inserted['TargetItems'] = dict_tgtitems
            else:
                dict_to_be_inserted['TargetItems'] = {
                    'ETFShortAmountInMarginAccount': None,
                    'CompositeShortAmountInMarginAccount': None,
                    'ShortExposureFromOTCAccounts': None,
                    'NetExposureFromOTCAccounts': None,
                    'CashFromShortSellingInMarginAccount': None,
                    'NetAssetInOTCAccounts': None,
                    'NetAsset': None,
                }
        self.col_prdinfo.delete_many({'DataDate': self.str_today})
        self.col_prdinfo.insert_many(list_dicts_to_be_inserted)

        fpath_df_unav_from_4121_final_new = (f'//192.168.4.121/data/Final_new/{self.str_today}/'
                                             f'######产品净值相关信息######.xlsx')
        if path.exists(fpath_df_unav_from_4121_final_new):
            # 注意读取的最新日期有可能会改变格式，目前为-
            df_unav_from_4121_final_new = pd.read_excel(
                fpath_df_unav_from_4121_final_new,
                dtype={
                    '产品编号': str,
                    '产品名称': str,
                    '最新更新日期': str,
                    '最新净值': float,
                }
            )
            list_dicts_unavs_from_4121_final_new = df_unav_from_4121_final_new.to_dict('records')
            for dict_unav_from_4121_final_new in list_dicts_unavs_from_4121_final_new:
                prdcode_in_4122_final_new = dict_unav_from_4121_final_new['产品编号']
                latest_unav_date_in_final_new = dict_unav_from_4121_final_new['最新更新日期'].replace('-', '')
                latest_unav_in_final_new = dict_unav_from_4121_final_new['最新净值']

                dict_prdinfo = self.col_prdinfo.find_one(
                    {'DataDate': self.str_today, 'PrdCodeIn4121FinalNew': prdcode_in_4122_final_new}
                )
                if dict_prdinfo:
                    self.col_prdinfo.update_one(
                        {
                            'DataDate': latest_unav_date_in_final_new,
                            'PrdCodeIn4121FinalNew': prdcode_in_4122_final_new,
                        },
                        {
                            '$set': {'UNAVFromLiquidationRpt': latest_unav_in_final_new}
                        }
                    )
        print('Collection "prdinfo" has been updated.')

    def update_broker_info(self):
        """
        无运行顺序要求
        """
        df_broker_info = pd.read_excel(self.fpath_basicinfo,
                                       sheet_name='broker_info',
                                       dtype={
                                           'BrokerAlias': str,
                                           'BrokerAbbr': str,
                                           'BrokerType': str,
                                           'BrokerAliasInTrdPlan': str
                                       })
        df_broker_info = df_broker_info.where(df_broker_info.notnull(), None)
        list_dicts_to_be_inserted = df_broker_info.to_dict('records')
        for dict_to_be_inserted in list_dicts_to_be_inserted:
            dict_to_be_inserted['DataDate'] = self.str_today
        self.col_broker_info.delete_many({'DataDate': self.str_today})
        self.col_broker_info.insert_many(list_dicts_to_be_inserted)
        print('Collection "broker_info" has been updated.')

    def run(self):
        self.update_acctinfo()
        self.update_prdinfo()
        self.update_broker_info()


if __name__ == '__main__':
    basicinfo = DatabaseBasicInfo()
    basicinfo.run()





