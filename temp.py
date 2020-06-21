# À„∑®£∫ perfect shape
from math import floor

net_asset = 13650
strategy = 'n' # n for neutral, eif for enhanced index fund
alpha_position_percent = 0.77

spot500 = 5787.15

def get_perfect_shape(net_asset, strategy, alpha_position_percent):
    margin_required_by_ms = spot500 * 200 * 0.2
    future_contract_value = spot500 * 200
    stock_amt = net_asset * alpha_position_percent
    if strategy == 'n':
        future_contract_lots = floor(stock_amt / future_contract_value)
        short_amt_provided_by_future = future_contract_lots * future_contract_value
        stock_amt_final = short_amt_provided_by_future




