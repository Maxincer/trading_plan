# coding=gbk
import zmq
import json
import configparser
import threading
import telnetlib


class Trader(threading.Thread):

    socket = None

    # 读取配置文件
    config = configparser.ConfigParser()
    config.read("config.ini")

    # 初始化方法
    # parameter:
    #   product_id  产品ID
    #   user_id    用户ID
    def __init__(self, product_id, user_id):
        super(Trader, self).__init__()
        self.user_id = str(user_id)
        self.product_id = str(product_id)
        self.trade_address = self.config.get("base_in_if_custom_v1.0", "trade_address")
        self.trade_port = self.config.get("base_in_if_custom_v1.0", "trade_port")
        try:
            telnetlib.Telnet(self.trade_address, port=self.trade_port, timeout=10)
        except BaseException as e:
            raise Exception(u"测连 %s:%s 连接不通，请联系管理员。" % (self.trade_address, self.trade_port))

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://%s:%s" % (self.trade_address, self.trade_port))

        recv_message = self.send_message(json.dumps({"PRODUCTID": self.product_id, "USERID": self.user_id, "VERB": "check"}))
        if recv_message == "":
            raise Exception(u"接收测连数据为空！")
        else:
            dict_message=json.loads(recv_message, encoding="gb2312")
            if "SUCCESS" in dict_message.keys():
                if dict_message["SUCCESS"]:
                    self.product_name = dict_message["PRODUCTNAME"]
                else:
                    raise Exception(u"测连 %s产品失败：%s！" % (self.product_id, dict_message["MSG"]))
            else:
                raise Exception(u"接收测连数据格式错误！")

    def __del__(self):
        pass

    # 向服务器发送消息
    # 参数：
    # message 消息内容
    # return
    #   返回服务器处理结果，如果服务器返回为空或success为false，则返回None

    def send_message(self, message):
        self.socket.send_string(message)
        return self.socket.recv_string()

    # 查询服务器订单交易
    def submit_query_order(self, orders):
        recv_message = self.send_message(
            json.dumps({"PRODUCTID": self.product_id, "USERID": self.user_id, "VERB": "order", "LIST": orders})
        )
        if len(recv_message) == 0:
            raise Exception(u"未接收到产品持仓数据！")
        else:
            return json.loads(recv_message, encoding="utf-8")

    # 查询服务器产品持仓
    def query_local_holding(self):
        recv_message = self.send_message(
            json.dumps({"PRODUCTID": self.product_id, "USERID": self.user_id, "VERB": "holding"})
        )
        if len(recv_message) == 0:
            raise Exception(u"未接收到产品持仓数据！")
        else:
            return json.loads(recv_message, encoding="utf-8")

    # 查询服务器产品资金
    def query_local_capital(self):
        recv_message = self.send_message(
            json.dumps({"PRODUCTID": self.product_id, "USERID": self.user_id, "VERB": "capital"}))
        if len(recv_message) == 0:
            raise Exception(u"未接收到产品持仓数据！")
        else:
            return json.loads(recv_message, encoding="utf-8")


if __name__ == '__main__':
    a = Trader('simnow4', 'MXZ')
    ret = a.query_local_capital()
    print(ret)
