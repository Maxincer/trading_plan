from datetime import datetime
import json

import pymongo
import pandas as pd


class DatabaseBasicInfo:
    def __init__(self):
        self.str_today = datetime.strftime(datetime.today(), '%Y%m%d')
        # self.str_today = '20200624'
        self.fpath_basicinfo = 'data/basic_info.xlsx'
        dbclient = pymongo.MongoClient('mongodb://localhost:27017/')
        db_basicinfo = dbclient['basicinfo']
        self.col_acctinfo = db_basicinfo['acctinfo']
        self.col_acctinfo.create_index([('DataDate', pymongo.DESCENDING), ('AcctIDByMXZ', pymongo.ASCENDING)])
        self.col_prdinfo = db_basicinfo['prdinfo']

    def update_prdinfo(self):
        df_prdinfo = pd.read_excel(self.fpath_basicinfo,
                                   sheet_name='prdinfo',
                                   dtype={
                                       'PrdCode': str,
                                       'PrdName': str,
                                       'StrategiesAllocation': str,
                                       'NetAssetAllocation': str,
                                       'TargetCompositePercentage': float,
                                       'TargetItems': str,
                                   })
        df_prdinfo = df_prdinfo.where(df_prdinfo.notnull(), None)
        list_dicts_to_be_inserted = df_prdinfo.to_dict('records')
        for dict_to_be_inserted in list_dicts_to_be_inserted:
            dict_to_be_inserted['DataDate'] = self.str_today
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
                if 'ShortExposureFromOTCAccount' not in dict_tgtitems:
                    dict_tgtitems['ShortExposureFromOTCAccount'] = None
                if 'NetAsset' not in dict_tgtitems:
                    dict_tgtitems['NetAsset'] = None
                dict_to_be_inserted['TargetItems'] = dict_tgtitems
        self.col_prdinfo.delete_many({'DataDate': self.str_today})
        self.col_prdinfo.insert_many(list_dicts_to_be_inserted)
        print('Collection "prdinfo" has been updated.')

    def update_acctinfo(self):
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
                                    }
                                    )
        df_acctinfo = df_acctinfo.where(df_acctinfo.notnull(), None)
        list_dicts_to_be_inserted = df_acctinfo.to_dict('records')
        for dict_to_be_inserted in list_dicts_to_be_inserted:
            dict_to_be_inserted['DataDate'] = self.str_today
        self.col_acctinfo.delete_many({'DataDate': self.str_today})
        self.col_acctinfo.insert_many(list_dicts_to_be_inserted)
        print('Collection "acctinfo" has been updated.')

    def run(self):
        self.update_acctinfo()
        self.update_prdinfo()


if __name__ == '__main__':
    basicinfo = DatabaseBasicInfo()
    basicinfo.run()





