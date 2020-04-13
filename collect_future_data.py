#!usr/bin/env python3
# coding=utf-8

"""
Trader对象，为访问期货交易接口
需具备config.ini
"""

import pandas as pd
import zmq
import json
import configparser
import cx_Oracle
import telnetlib

pd.set_option('display.max_columns', None)
pd.set_option('max_colwidth', 9999)


class Trader:
    socket = None

    def __init__(self, product_id, user_id='INDEXFUTURE'):
        """
        :param product_id: 产品ID（ORACLEDB.FUTURE1.SYSTEM_PRODUCT_DETAIL.PNAME, eg."jx4_nh")
        :param user_id: 'INDEXFUTURE'
        """
        self.product_id = str(product_id)
        self.user_id = str(user_id)

        __config = configparser.ConfigParser()
        __config.read("config.ini")
        __username = __config.get("sysconfig", "username")
        __password = __config.get("sysconfig", "password")
        __url = __config.get("sysconfig", "url")

        self.config_connect = cx_Oracle.connect('%s/%s@%s' % (__username, __password, __url))
        self.product_name, self.product_number = self.query_product_info()

        if self.product_number is None:
            raise Exception("%s未配置后台连接端口，请确认后重试！" % self.product_name)
        self.trade_address = __config.get("base", "trade_address")
        try:
            telnetlib.Telnet(self.trade_address, port=7000+self.product_number, timeout=10)
        except BaseException as e:
            raise Exception("测连【%s】地址【7%03d】端口不通，%s未开启交易程序。"
                            % (self.trade_address, self.product_number, self.product_name))

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://%s:7%03d" % (self.trade_address, self.product_number))

    def __del__(self):
        if self.config_connect:
            self.config_connect.close()
            del self.config_connect
        if self.socket:
            self.socket.disconnect("tcp://%s:7%03d" % (self.trade_address, self.product_number))
            del self.socket
            self.context.term()
            del self.context
        del self.product_name, self.product_id, self.user_id, self.trade_address, self.product_number

    def send_request(self, verb, product_id, parameter={}):
        """
        向服务器发送操作请求
        :param verb: 操作类型
        :param product_id: 产品ID
        :param parameter: 提交参数
        :return: 返回服务器处理结果，如果服务器返回为空或success为false，则返回None
        """
        if len(parameter) > 0:
            submit_params = {"product_id": product_id, "user_id": self.user_id, "verb": verb, "parameter": parameter}
        else:
            submit_params = {"product_id": product_id, "user_id": self.user_id, "verb": verb}
        self.socket.send_string(json.dumps(submit_params))
        server_message = self.socket.recv_string(encoding="gb2312")
        if not server_message:
            return {"success": False, "msg": "服务器无返回内容"}
        parse_message = json.loads(server_message, encoding="gb2312")
        return parse_message

    def query_holding(self, product_id):
        """
        Query the holding information
        :param product_id:
        :return:
        """
        message = self.send_request("query_holding", product_id)
        if message["success"] and "list" in message:
            columns = {"instrument_id": str, "direction": str, "hedge": str, "position": int, "position_td": int,
                       "position_pre": int, "open_volume": int, "close_volume": int, "use_margin": float,
                       "position_cost": float}
            df_ret_draft = pd.DataFrame(message['list'], columns=columns)
            df_ret = df_ret_draft.fillna(0).groupby(['instrument_id', "direction", "hedge"]).sum().reset_index()
            return df_ret
        else:
            if 'msg' in message:
                print("%s持仓明细查询失败，错误信息：%s" % (self.product_name, message["msg"]))
            else:
                print("%s持仓明细查询失败！" % self.product_name)

            return pd.DataFrame(columns=["instrument_id", "direction", "hedge",
                                         "position", "position_td", "position_pre"])

    def query_account(self):
        """
        Query the capital info of the account.
        :return:
        DataFrame
            columns = ['instrument_id', 'direction', 'hedge', 'position', 'position_td', 'position_pre', 'open_volume',
            'close_volume', 'use_margin', 'position_cost']
        dict
            example:
            {'success':1, 'list':[{'pre_balance': 6175894.4399999995, 'pre_credit': 0.0, 'pre_mortgage': 0.0,
            'mortgage': 0.0, 'withdraw': 0.0, 'deposit': 0.0, 'close_profit': 0.0, 'position_profit': 56000.0,
            'commission': 0.0, 'curr_margin': 1052854.4000000001, 'frozen_margin': 0.0, 'frozen_commission': 0.0,
            'delivery_margin': 0.0, 'credit': 0.0, 'account_id': '666073675'}]}

        :Note:
            动态权益 = 静态权益 + 平仓盈亏 + 持仓盈亏
            + 权利金 - 手续费 - 上次货币质入金额 + 上次货币质出金额 + 货币质入金额 - 货币质出金额
        """
        parameter = {"product_id": self.product_id, "user_id": self.user_id}
        message = self.send_request("query_account", self.product_id, parameter=parameter)
        return message

    def query_transfer_serial(self):
        """
        Query the transfer serial.
        :return:
        dict
            example
            {'success': 1, 'list': []}
        """
        parameter = {"product_id": self.product_id, "user_id": self.user_id}
        message = self.send_request("query_transfer_serial", self.product_id, parameter=parameter)
        return message

    def query_trading(self):
        parameter = {"product_id": self.product_id, "user_id": self.user_id}
        message = self.send_request('query_trade', self.product_id, parameter=parameter)
        return message

    def query_product_info(self):
        __sql = f"SELECT ID,PNAME FROM SYSTEM_PRODUCT_DETAIL WHERE PCODE='{self.product_id}'"
        __query_cursor = self.config_connect.cursor()
        __query_cursor.execute(__sql)
        __rows = __query_cursor.fetchall()
        __query_cursor.close()
        if len(__rows) > 0:
            return __rows[0][1], __rows[0][0]
        else:
            return None, None

    def acctid2product_id(self, acctid):
        """
        注：在trader类中，product_id形如3_xb, 由产品代码和经济上缩写联合表示，映射一个期货账户
        :acctid:
        str
            期货交易账号

        :return:
        str
            trader项目中使用的product_id
        """
        __sql = f"SELECT PCODE FROM SYSTEM_PRODUCT_DETAIL WHERE ACCOUNTID='{acctid}'"
        __query_cursor = self.config_connect.cursor()
        __query_cursor.execute(__sql)
        __rows = __query_cursor.fetchall()
        __query_cursor.close()
        product_id = __rows[0][0]
        return product_id


a = Trader('3_xb')
print(a.acctid2product_id('666073675'))
















print('Done.')


