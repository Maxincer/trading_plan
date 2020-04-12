# coding: utf-8
from datetime import datetime

import pymongo


class Product:
    def __init__(self, prdcode):
        str_today = datetime.strftime(datetime.today(), '%Y%m%d')
        dbclient = pymongo.MongoClient('mongodb://localhost:27017/')
        db_basicinfo = dbclient['basicinfo']
        self.col_myacctsinfo = db_basicinfo['myacctsinfo']
        cursor_find = self.col_myacctsinfo.find({'date': str_today, 'prdcode': prdcode})
        list_all_acctids = []
        for x in cursor_find:
            list_all_acctids.append(x['acctid'])
        self.all_acctids = list_all_acctids
        cursor_find = self.col_myacctsinfo.find({'date': str_today, 'prdcode': prdcode, 'rptmark': '1'})
        list_rpt_acctids = []
        list_rpt_cash_acctids = []
        list_rpt_margin_acctids = []
        list_rpt_future_acctids = []
        for x in cursor_find:
            list_rpt_acctids.append(x['acctid'])
            if x['accttype'] == 'c':
                list_rpt_cash_acctids.append(x['acctid'])
            if x['accttype'] == 'm':
                list_rpt_margin_acctids.append(x['acctid'])
            if x['accttype'] == 'f':
                list_rpt_future_acctids.append(x['acctid'])
            else:
                raise ValueError('Unknown account type in collection myacctsinfo!')
        self.rpt_acctids = list_rpt_acctids
        self.rpt_cash_acctids = list_rpt_cash_acctids
        self.rpt_margin_acctids = list_rpt_margin_acctids
        self.rpt_future_acctids = list_rpt_future_acctids
        self.rpt_acctids_count = len(self.rpt_acctids)
        self.rpt_cash_acctids_count = len(self.rpt_cash_acctids)
        self.rpt_margin_acctids_count = len(self.rpt_margin_acctids)
        self.rpt_future_acctids_count = len(self.rpt_future_acctids)








