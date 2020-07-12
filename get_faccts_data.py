from datetime import datetime
from db_trading_data import DBTradingData

import pandas as pd
from pymongo import MongoClient


class PrintFutureFmttedInfo:
    def __init__(self):
        self.client_mongo = MongoClient('mongodb://localhost:27017/')
        self.str_today = datetime.today().strftime('%Y%m%d')
        self.str_now = datetime.now().strftime('%Y%m%dT%H%M%S')
        self.col_future_api_capital = self.client_mongo['trddata']['future_api_capital']
        self.col_future_api_holding = self.client_mongo['trddata']['future_api_holding']
        self.col_display_capital = self.client_mongo['trddata']['display_capital']
        self.col_display_holding = self.client_mongo['trddata']['display_holding']
        self.col_acctinfo = self.client_mongo['basicinfo']['acctinfo']
        self.list_acctidbymxz = list(
            self.col_acctinfo.find({'DataDate': self.str_today, 'AcctType': 'f', 'RptMark': 1})
        )
        self.list_dicts_display_capital = []
        self.list_dicts_display_holding = []
        self.list_prdcodes = ['1202']

    def get_display_col(self):
        list_dicts_future_api_capital = self.col_future_api_capital.find({'DataDate': self.str_today})
        for dict_future_api_capital in list_dicts_future_api_capital:
            flt_approximate_na = (dict_future_api_capital['pre_balance']
                                  + dict_future_api_capital['deposit']
                                  - dict_future_api_capital['withdraw']
                                  + dict_future_api_capital['close_profit']
                                  + dict_future_api_capital['position_profit']
                                  - dict_future_api_capital['commission'])
            flt_curr_margin = dict_future_api_capital['curr_margin']
            if flt_approximate_na == 0:
                curr_margin_rate = 'Net Asset Equals to 0.'
            else:
                curr_margin_rate = flt_curr_margin / flt_approximate_na
            dict_display_capital = {
                'DataDateTime': self.str_now,
                'PrdCode': dict_future_api_capital['PrdCode'],
                'AcctIDByMXZ': dict_future_api_capital['AcctIDByMXZ'],
                'PreBalance': dict_future_api_capital['pre_balance'],
                'Deposit': dict_future_api_capital['deposit'],
                'Withdraw': dict_future_api_capital['withdraw'],
                'NetAsset': flt_approximate_na,
                'CurrentMarginRate': curr_margin_rate,
            }
            self.list_dicts_display_capital.append(dict_display_capital)
        df_capital = pd.DataFrame(self.list_dicts_display_capital)
        list_dicts_future_api_holding = self.col_future_api_holding.find({'DataDate': self.str_today})
        for dict_future_api_holding in list_dicts_future_api_holding:
            secid = dict_future_api_holding['instrument_id']
            direction = dict_future_api_holding['direction']
            qty = dict_future_api_holding['position']
            dict_display_holding = {
                'DataDateTime': self.str_now,
                'PrdCode': dict_future_api_holding['PrdCode'],
                'AcctIDByMXZ': dict_future_api_holding['AcctIDByMXZ'],
                'SecurityID': secid,
                'Direction': direction,
                'Qty': qty,
            }
            self.list_dicts_display_holding.append(dict_display_holding)
        df_holding = pd.DataFrame(self.list_dicts_display_holding)
        with pd.ExcelWriter('info_faccts.xlsx') as writer:
            df_capital.to_excel(writer, sheet_name='capital', index=False)
            df_holding.to_excel(writer, sheet_name='holding', index=False)

    def run(self):
        self.get_display_col()
        for prdcode in self.list_prdcodes:
            for dict_display_capital in self.list_dicts_display_capital:
                if dict_display_capital['PrdCode'] == prdcode:
                    print(dict_display_capital)
            for dict_display_holding in self.list_dicts_display_holding:
                if dict_display_holding['PrdCode'] == prdcode:
                    print(dict_display_holding)


if __name__ == '__main__':
    db_init = DBTradingData()
    db_init.update_trddata_f()
    task = PrintFutureFmttedInfo()
    task.run()









