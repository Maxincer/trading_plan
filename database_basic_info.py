from datetime import datetime

import pymongo
import pandas as pd


class DatabaseBasicInfo:
    def __init__(self):
        self.str_today = datetime.strftime(datetime.today(), '%Y%m%d')
        self.fpath_basicinfo = 'D:/data/A_trading_data/basic_info.xlsx'
        dbclient = pymongo.MongoClient('mongodb://localhost:27017/')
        db_basicinfo = dbclient['basicinfo']
        self.col_myacctsinfo = db_basicinfo['myacctsinfo']
        self.col_myacctsinfo.create_index([('date', pymongo.DESCENDING), ('acctid', pymongo.ASCENDING)])
        self.col_myprdsinfo = db_basicinfo['myprdsinfo']

    def update_myprdsinfo(self):
        df_myprdsinfo = pd.read_excel(self.fpath_basicinfo, sheet_name='myprdsinfo', dtype={'prdcode': str})
        list_dicts_to_be_inserted = df_myprdsinfo.to_dict('records')
        for dict_to_be_inserted in list_dicts_to_be_inserted:
            dict_to_be_inserted['date'] = self.str_today
            if self.col_myprdsinfo.find_one({'date': dict_to_be_inserted['date'],
                                             'prdcode': dict_to_be_inserted['prdcode']}):
                self.col_myprdsinfo.update_one({'date': dict_to_be_inserted['date'],
                                                'prdcode': dict_to_be_inserted['prdcode']},
                                               {'$set': dict_to_be_inserted})
            else:
                self.col_myprdsinfo.insert_one(dict_to_be_inserted)
        print('Collection "myprdsinfo" has been updated.')

    def update_myacctsinfo(self):
        df_myacctsinfo = pd.read_excel(self.fpath_basicinfo, sheet_name='myacctsinfo',
                                       dtype={'prdcode': str, 'acctid': str, 'rptmark': str})
        list_dicts_to_be_inserted = df_myacctsinfo.to_dict('records')
        for dict_to_be_inserted in list_dicts_to_be_inserted:
            dict_to_be_inserted['date'] = self.str_today
            if self.col_myacctsinfo.find_one({'date': dict_to_be_inserted['date'],
                                              'acctid': dict_to_be_inserted['acctid']}):
                self.col_myacctsinfo.update_one({'date': dict_to_be_inserted['date'],
                                                 'acctid': dict_to_be_inserted['acctid']},
                                                {'$set': dict_to_be_inserted})
            else:
                self.col_myacctsinfo.insert_one(dict_to_be_inserted)
        print('Collection "myacctsinfo" has been updated.')


if __name__ == '__main__':
    basicinfo = DatabaseBasicInfo()
    basicinfo.update_myprdsinfo()
    basicinfo.update_myacctsinfo()





