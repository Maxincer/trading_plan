#!usr/bin/env/python38
# coding: utf-8
# author: Maxincer
# CreateDateTime: 20201009T110000

"""
本脚本从银河证券Apama量化交易平台通过sftp传输获取资金、持仓及交易数据
采用的策略为apama的扫单策略， 传输方式为, 账号及密码:  (//sftp: 139.196.103.39:22, root, llys3,ysykR)

Steps:
    1. 在以资金账户名命名的各自的文件夹中，生成文件单: query_YYYYMMDD.dat, file_server_list_YYYYMMDD.dat
    2. 将1中两个文件先后传入对应目录
    3. 取回源数据(stock_YYYYMMDD.dat, fund_YYYYMMD.dat)
    4. 将源数据清洗为通用格式数据(fund, position, trdrec)

Note:
    1. strftime行为中的%f为microsecond, 是微秒, 是0.000001秒；millisecond是毫秒, 是0.001秒
    2. 查询类可发起重复查询，资金股份查询类业务流速控制，每分钟最多查询一笔。

"""

from datetime import datetime
from time import sleep
import os
import pymongo

import paramiko


class yh_apama_api:
    def __init__(self):
        self.dt_now = datetime.now()
        self.str_now = datetime.strftime(self.dt_now, '%Y%m%d%H%M%S%f')
        self.str_today = datetime.strftime(self.dt_now, '%Y%m%d')
        self.dirpath_output = 'data/yh_apama_api'
        self.fn_dat_query = f'query_{self.str_today}.dat'
        self.fn_dat_file_server_list = f'file_server_list_{self.str_today}.dat'
        self.fn_dat_fund = f'fund_{self.str_today}.dat'
        self.fn_dat_stock = f'stock_{self.str_today}.dat'
        self.client_mongo = pymongo.MongoClient('mongodb://localhost:27017/')
        self.db_basicinfo = self.client_mongo['basicinfo']
        self.col_acctinfo = self.db_basicinfo['acctinfo']
        self.host_sftp_yh_apama = '139.196.103.39'
        self.port_sftp_yh_apama = 22
        self.username_103_39 = 'root'
        self.password_103_39 = 'llys3,ysykR'
        list_dicts_acctinfo_cacct = list(
            self.col_acctinfo.find(
                {'DataDate': self.str_today, 'DataDownloadMark': 1, 'BrokerAbbr': 'yh', 'AcctType': 'c'}
            )
        )
        list_dicts_acctinfo_macct = list(
            self.col_acctinfo.find(
                {'DataDate': self.str_today, 'DataDownloadMark': 1, 'BrokerAbbr': 'yh', 'AcctType': 'm'}
            )
        )
        self.list_dicts_acctinfo_sacct = list_dicts_acctinfo_cacct + list_dicts_acctinfo_macct

    def generate_and_put_dat_query_and_dat_file_server_list(self):
        trans = paramiko.Transport((self.host_sftp_yh_apama, self.port_sftp_yh_apama))
        trans.connect(username=self.username_103_39, password=self.password_103_39)
        sftp = paramiko.SFTPClient.from_transport(trans)

        for dict_acctinfo_sacct in self.list_dicts_acctinfo_sacct:
            acctidbybroker = dict_acctinfo_sacct['AcctIDByBroker']
            dlddata_filter = dict_acctinfo_sacct['DownloadDataFilter']
            dirpath_acctidbybroker_for_dat = os.path.join(self.dirpath_output, acctidbybroker)
            if not os.path.exists(dirpath_acctidbybroker_for_dat):
                os.mkdir(dirpath_acctidbybroker_for_dat)

            fpath_dat_query = os.path.join(dirpath_acctidbybroker_for_dat, self.fn_dat_query)
            str_datalines_query = f'{int(self.str_now)}|{acctidbybroker}|1|\n{int(self.str_now)+1}|{acctidbybroker}|2|'

            with open(fpath_dat_query, 'w') as f:
                f.write(str_datalines_query)
            fpath_dat_query_remote = f'/home/{dlddata_filter}/{self.fn_dat_query}'
            sftp.put(fpath_dat_query, fpath_dat_query_remote)

            fpath_dat_file_server_list = os.path.join(dirpath_acctidbybroker_for_dat, self.fn_dat_file_server_list)
            str_datalines_query = f'{self.fn_dat_query}|{self.str_now[8:17]}'
            with open(fpath_dat_file_server_list, 'w') as f:
                f.write(str_datalines_query)
            fpath_dat_file_server_list_remote = f'/home/{dlddata_filter}/{self.fn_dat_file_server_list}'
            sleep(0.001)
            sftp.put(fpath_dat_file_server_list, fpath_dat_file_server_list_remote)
            print(f'query and file_server_list files of {acctidbybroker} uploaded!')
            sleep(0.001)
            fpath_dat_fund_remote = f'/home/{dlddata_filter}/{self.fn_dat_fund}'
            fpath_dat_stock_remote = f'/home/{dlddata_filter}/{self.fn_dat_stock}'
            fpath_dat_fund_local = f'data/yh_apama_api/{acctidbybroker}/{self.fn_dat_fund}'
            fpath_dat_stock_local = f'data/yh_apama_api/{acctidbybroker}/{self.fn_dat_stock}'
            sftp.get(fpath_dat_fund_remote, fpath_dat_fund_local)
            sftp.get(fpath_dat_stock_remote, fpath_dat_stock_local)
        trans.close()

    def fmt2custom_style(self):
        list_dicts_fund = []
        list_dicts_position = []
        list_dicts_deal = []
        for dict_acctinfo_sacct in self.list_dicts_acctinfo_sacct:
            acctidbybroker = dict_acctinfo_sacct['AcctIDByBroker']
            dlddata_filter = dict_acctinfo_sacct['DownloadDataFilter']
            dirpath_acctidbybroker_for_dat = os.path.join(self.dirpath_output, acctidbybroker)




    def run(self):
        self.generate_and_put_dat_query_and_dat_file_server_list()


if __name__ == '__main__':
    task = yh_apama_api()
    task.run()



