#!usr/bin/env python3
# coding=utf-8

import pandas as pd
import zmq
import json
import configparser
import cx_Oracle
import telnetlib


class Trader:
    socket = None

    def __init__(self, product_id, user_id):
        """
        :param product_id: 产品ID（ORACLEDB.FUTURE1.SYSTEM_PRODUCT_DETAIL.PNAME, eg."jx4_nh")
        :param user_id: 产品ID(???)
        """
        self.user_id = str(user_id)
        self.product_id = str(product_id)

        config = configparser.ConfigParser()
        config.read("config.ini")
        username = config.get("sysconfig", "username")
        password = config.get("sysconfig", "password")
        url = config.get("sysconfig", "url")

        self.config_connect = cx_Oracle.connect('%s/%s@%s' % (username, password, url))
        self.product_name, self.product_number = self.query_product_info()

        if self.product_number is None:
            raise Exception("%s未配置后台连接端口，请确认后重试！" % self.product_name)
        self.trade_address = config.get("base", "trade_address")
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
        self.socket.send_json(json.dumps(submit_params))
        server_message = self.socket.recv_string(encoding="gb2312")
        if not server_message:
            return {"success": False, "msg": "服务器无返回内容"}
        parse_message = json.loads(server_message, encoding="gb2312")
        return parse_message

    def query_holding(self, product_id):
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
        parameter = {"product_id": self.product_id, "user_id": self.user_id}
        message = self.send_request("query_account", self.product_id, parameter=parameter)
        return message

    def query_transfer_serial(self):
        parameter = {"product_id": self.product_id, "user_id": self.user_id}
        message = self.send_request("query_transfer_serial", self.product_id, parameter=parameter)
        return message

    def query_trading(self):
        parameter = {"product_id": self.product_id, "user_id": self.user_id}
        message = self.send_request('query_trade', self.product_id, parameter=parameter)
        return message

    def query_product_info(self):
        sql = f"SELECT ID,PNAME FROM SYSTEM_PRODUCT_DETAIL WHERE PCODE='{self.product_id}'"
        query_cursor = self.config_connect.cursor()
        query_cursor.execute(sql)
        rows = query_cursor.fetchall()
        query_cursor.close()
        if len(rows) > 0:
            return rows[0][1], rows[0][0]
        else:
            return None, None


trader = Trader('3_xb', 'yangyang')
a = trader.query_account()
print(a)
print('Done.')


