# coding: utf-8

from datetime import datetime
import os

import pandas as pd
import pymongo


class Product:
    def __init__(self, prdcode):
        self.str_today = datetime.strftime(datetime.today(), '%Y%m%d')
        self.dbclient = pymongo.MongoClient('mongodb://localhost:27017/')
        self.db_basicinfo = self.dbclient['basicinfo']
        self.col_myacctsinfo = self.db_basicinfo['myacctsinfo']
        cursor_find = self.col_myacctsinfo.find({'date': self.str_today, 'prdcode': prdcode})
        list_all_acctids = []
        for x in cursor_find:
            list_all_acctids.append(x['acctid'])
        self.list_all_acctids = list_all_acctids
        cursor_find = self.col_myacctsinfo.find({'date': self.str_today, 'prdcode': prdcode, 'rptmark': '1'})
        list_rpt_acctids = []
        list_rpt_cash_acctids = []
        list_rpt_margin_acctids = []
        list_rpt_future_acctids = []
        for x in cursor_find:
            list_rpt_acctids.append(x['acctid'])
            if x['accttype'] == 'c':
                list_rpt_cash_acctids.append(x['acctid'])
            elif x['accttype'] == 'm':
                list_rpt_margin_acctids.append(x['acctid'])
            elif x['accttype'] == 'f':
                list_rpt_future_acctids.append(x['acctid'])
            else:
                raise ValueError('Unknown account type in collection myacctsinfo!')
        self.prdcode = prdcode
        self.rpt_acctids = list_rpt_acctids
        self.rpt_cash_acctids = list_rpt_cash_acctids
        self.rpt_margin_acctids = list_rpt_margin_acctids
        self.rpt_future_acctids = list_rpt_future_acctids
        self.rpt_acctids_count = len(self.rpt_acctids)
        self.rpt_cash_acctids_count = len(self.rpt_cash_acctids)
        self.rpt_margin_acctids_count = len(self.rpt_margin_acctids)
        self.rpt_future_acctids_count = len(self.rpt_future_acctids)


class Account(Product):
    def __init__(self, prdcode, acctid):
        super().__init__(prdcode)
        if acctid not in self.list_all_acctids:
            raise ValueError(f'Product {prdcode} does not have Account {acctid}.')
        else:
            self.acctid = acctid
        cursor_find = self.col_myacctsinfo.find_one({'date': self.str_today, 'acctid': self.acctid})
        self.accttype = cursor_find['accttype']
        self.acct_broker_alias = cursor_find['broker_alias']
        self.acctstatus = cursor_find['acctstatus']
        self.acct_fpath_holding = cursor_find['fpath_holding']
        self.acct_rptmark = cursor_find['rptmark']
        self.col_bs = self.dbclient[self.acctid][f'{self.acctid}_balance_sheet']

    @staticmethod
    def __holding2mv_ce(df_holding):
        df_holding['证券代码'] = df_holding['证券代码'].apply(lambda x: x.zfill(6))
        df_holding[df_holding['证券代码']] =










a = Account('903', '3900155432')
a.collect_trddata('20200410')














