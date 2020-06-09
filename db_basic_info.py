from datetime import datetime

import pymongo
import pandas as pd


class DatabaseBasicInfo:
    def __init__(self):
        self.str_today = datetime.strftime(datetime.today(), '%Y%m%d')
        self.str_today = '20200603'
        self.fpath_basicinfo = 'data/basic_info.xlsx'
        dbclient = pymongo.MongoClient('mongodb://localhost:27017/')
        db_basicinfo = dbclient['basicinfo']
        self.col_acctinfo = db_basicinfo['acctinfo']
        self.col_acctinfo.create_index([('DataDate', pymongo.DESCENDING), ('AcctIDByMXZ', pymongo.ASCENDING)])
        self.col_myprdsinfo = db_basicinfo['myprdsinfo']

    def update_myprdsinfo(self):
        df_myprdsinfo = pd.read_excel(self.fpath_basicinfo, sheet_name='myprdsinfo', dtype={'prdcode': str})
        list_dicts_to_be_inserted = df_myprdsinfo.to_dict('records')
        for dict_to_be_inserted in list_dicts_to_be_inserted:
            dict_to_be_inserted['date'] = self.str_today
        self.col_myprdsinfo.delete_many({'date': self.str_today})
        self.col_myprdsinfo.insert_many(list_dicts_to_be_inserted)
        print('Collection "myprdsinfo" has been updated.')

    def update_acctinfo(self):
        df_acctinfo = pd.read_excel(self.fpath_basicinfo, sheet_name='acctinfo',
                                    dtype={
                                           'PrdCode': str, 'AcctID': str, 'RptMark': int, 'PatchMark': int,
                                           'AcctName': str, 'AcctIDSource': str, 'AcctStatus': str, 'AcctType': str,
                                           'BrokerAlias': str, 'DataSourceType': str
                                       },
                                    converters={'DataFilePath': lambda x: None if str(x) == 'N/A' else str(x)}
                                    )
        list_dicts_to_be_inserted = df_acctinfo.to_dict('records')
        for dict_to_be_inserted in list_dicts_to_be_inserted:
            dict_to_be_inserted['DataDate'] = self.str_today
        self.col_acctinfo.delete_many({'DataDate': self.str_today})
        self.col_acctinfo.insert_many(list_dicts_to_be_inserted)
        print('Collection "acctinfo" has been updated.')


if __name__ == '__main__':
    basicinfo = DatabaseBasicInfo()
    basicinfo.update_acctinfo()





