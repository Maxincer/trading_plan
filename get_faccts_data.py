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
        self.col_future_api_trdrec = self.client_mongo['trddata']['future_api_trdrec']
        self.col_display_capital = self.client_mongo['trddata']['display_capital']
        self.col_display_holding = self.client_mongo['trddata']['display_holding']
        self.col_acctinfo = self.client_mongo['basicinfo']['acctinfo']
        self.list_acctidbymxz = list(
            self.col_acctinfo.find({'DataDate': self.str_today, 'AcctType': 'f', 'RptMark': 1})
        )
        self.list_dicts_display_capital = []
        self.list_dicts_display_holding = []
        self.list_dicts_display_trdrec_aggr = []
        self.list_dicts_display_trdrec_details = []

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
                'AcctIDByMXZ': dict_future_api_capital['AcctIDByMXZ'],
                'PrdCode': dict_future_api_capital['PrdCode'],
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
                'AcctIDByMXZ': dict_future_api_holding['AcctIDByMXZ'],
                'PrdCode': dict_future_api_holding['PrdCode'],
                'SecurityID': secid,
                'Direction': direction,
                'Qty': qty,
            }
            self.list_dicts_display_holding.append(dict_display_holding)
        df_holding = pd.DataFrame(self.list_dicts_display_holding)

        list_dicts_future_api_trdrec = list(self.col_future_api_trdrec.find({'DataDate': self.str_today}))
        if list_dicts_future_api_trdrec:

            for dict_future_api_trdrec in list_dicts_future_api_trdrec:
                secid = dict_future_api_trdrec['instrument_id']
                direction = dict_future_api_trdrec['direction']
                time = dict_future_api_trdrec['time']
                volume = dict_future_api_trdrec['volume']
                price = dict_future_api_trdrec['price']
                offset = dict_future_api_trdrec['offset']

                dict_display_trdrec_details = {
                    'DataDateTime': self.str_now,
                    'AcctIDByMXZ': dict_future_api_trdrec['AcctIDByMXZ'],
                    'PrdCode': dict_future_api_trdrec['PrdCode'],
                    'TradeTime': time,
                    'SecurityID': secid,
                    'Direction': direction,
                    'Offset': offset,
                    'Qty': volume,
                    'Price': price,
                }
                self.list_dicts_display_trdrec_details.append(dict_display_trdrec_details)
            df_trdrec_details = pd.DataFrame(self.list_dicts_display_trdrec_details)
        else:
            df_trdrec_details = pd.DataFrame(
                columns=['DataDateTime', 'AcctIDByMXZ', 'PrdCode', 'TradeTime',
                         'SecurityID', 'Direction', 'Offset', 'Qty', 'Price']
            )

        df_trdrec_aggr_draft = (df_trdrec_details
                                .loc[:, ['AcctIDByMXZ', 'SecurityID', 'Direction', 'Qty']]
                                .copy())
        df_trdrec_aggr_draft['DirectionMark'] = df_trdrec_aggr_draft['Direction'].map({'buy': 1, 'sell': -1})
        df_trdrec_aggr_draft['NetQty'] = df_trdrec_aggr_draft['Qty'] * df_trdrec_aggr_draft['DirectionMark']
        df_trdrec_aggr = df_trdrec_aggr_draft.groupby(by=['AcctIDByMXZ', 'SecurityID', 'Direction']).sum().reset_index()
        if df_trdrec_aggr.empty:
            df_trdrec_aggr = pd.DataFrame(columns=['AcctIDByMXZ', 'SecurityID', 'Direction', 'NetQty'])
        df_trdrec_aggr['DataDateTime'] = self.str_now
        df_trdrec_aggr['PrdCode'] = df_trdrec_aggr['AcctIDByMXZ'].apply(lambda x: x.split('_')[0])
        df_trdrec_aggr = (df_trdrec_aggr
                          .loc[:, ['DataDateTime', 'AcctIDByMXZ', 'PrdCode', 'SecurityID', 'NetQty']]
                          .copy())

        with pd.ExcelWriter('info_faccts.xlsx') as writer:
            df_capital.to_excel(writer, sheet_name='capital', index=False)
            df_holding.to_excel(writer, sheet_name='holding', index=False)
            df_trdrec_aggr.to_excel(writer, sheet_name='trdrec_aggr', index=False)
            df_trdrec_details.to_excel(writer, sheet_name='trdrec_details', index=False)
            worksheet_capital = writer.sheets['capital']
            worksheet_capital.set_column('A:B', 17.75)
            worksheet_capital.set_column('C:C', 9)
            worksheet_capital.set_column('D:D', 12.63)
            worksheet_capital.set_column('E:E', 9)
            worksheet_capital.set_column('F:F', 10.13)
            worksheet_capital.set_column('G:G', 12.13)
            worksheet_capital.set_column('H:H', 24.38)
            worksheet_holding = writer.sheets['holding']
            worksheet_holding.set_column('A:B', 17.75)
            worksheet_holding.set_column('C:C', 9)
            worksheet_holding.set_column('D:E', 12.63)
            worksheet_holding.set_column('F:F', 5)
            worksheet_trdrec_aggr = writer.sheets['trdrec_aggr']
            worksheet_trdrec_aggr.set_column('A:B', 17.75)
            worksheet_trdrec_aggr.set_column('C:C', 9)
            worksheet_trdrec_aggr.set_column('D:D', 12.63)
            worksheet_trdrec_aggr.set_column('E:E', 5)
            worksheet_trdrec_details = writer.sheets['trdrec_details']
            worksheet_trdrec_details.set_column('A:B', 17.75)
            worksheet_trdrec_details.set_column('C:C', 9)
            worksheet_trdrec_details.set_column('D:D', 11.38)
            worksheet_trdrec_details.set_column('E:E', 12.63)
            worksheet_trdrec_details.set_column('F:F', 11.38)
            worksheet_trdrec_details.set_column('G:G', 8)
            worksheet_trdrec_details.set_column('H:H', 4.5)
            worksheet_trdrec_details.set_column('I:I', 6.88)
            writer.save()
            print('Generate Future TrdRec Finished')

    def run(self):
        self.get_display_col()


if __name__ == '__main__':
    db_init = DBTradingData()
    db_init.update_trddata_f()
    task = PrintFutureFmttedInfo()
    task.run()









