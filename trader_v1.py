# coding=gbk
import zmq
import json
import configparser
import threading
import telnetlib


class Trader(threading.Thread):

    socket = None

    # ��ȡ�����ļ�
    config = configparser.ConfigParser()
    config.read("config.ini")

    # ��ʼ������
    # parameter:
    #   product_id  ��ƷID
    #   user_id    �û�ID
    def __init__(self, product_id, user_id):
        super(Trader, self).__init__()
        self.user_id = str(user_id)
        self.product_id = str(product_id)
        self.trade_address = self.config.get("base_in_if_custom_v1.0", "trade_address")
        self.trade_port = self.config.get("base_in_if_custom_v1.0", "trade_port")
        try:
            telnetlib.Telnet(self.trade_address, port=self.trade_port, timeout=10)
        except BaseException as e:
            raise Exception(u"���� %s:%s ���Ӳ�ͨ������ϵ����Ա��" % (self.trade_address, self.trade_port))

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://%s:%s" % (self.trade_address, self.trade_port))

        recv_message = self.send_message(json.dumps({"PRODUCTID": self.product_id, "USERID": self.user_id, "VERB": "check"}))
        if recv_message == "":
            raise Exception(u"���ղ�������Ϊ�գ�")
        else:
            dict_message=json.loads(recv_message, encoding="gb2312")
            if "SUCCESS" in dict_message.keys():
                if dict_message["SUCCESS"]:
                    self.product_name = dict_message["PRODUCTNAME"]
                else:
                    raise Exception(u"���� %s��Ʒʧ�ܣ�%s��" % (self.product_id, dict_message["MSG"]))
            else:
                raise Exception(u"���ղ������ݸ�ʽ����")

    def __del__(self):
        pass

    # �������������Ϣ
    # ������
    # message ��Ϣ����
    # return
    #   ���ط��������������������������Ϊ�ջ�successΪfalse���򷵻�None

    def send_message(self, message):
        self.socket.send_string(message)
        return self.socket.recv_string()

    # ��ѯ��������������
    def submit_query_order(self, orders):
        recv_message = self.send_message(
            json.dumps({"PRODUCTID": self.product_id, "USERID": self.user_id, "VERB": "order", "LIST": orders})
        )
        if len(recv_message) == 0:
            raise Exception(u"δ���յ���Ʒ�ֲ����ݣ�")
        else:
            return json.loads(recv_message, encoding="utf-8")

    # ��ѯ��������Ʒ�ֲ�
    def query_local_holding(self):
        recv_message = self.send_message(
            json.dumps({"PRODUCTID": self.product_id, "USERID": self.user_id, "VERB": "holding"})
        )
        if len(recv_message) == 0:
            raise Exception(u"δ���յ���Ʒ�ֲ����ݣ�")
        else:
            return json.loads(recv_message, encoding="utf-8")

    # ��ѯ��������Ʒ�ʽ�
    def query_local_capital(self):
        recv_message = self.send_message(
            json.dumps({"PRODUCTID": self.product_id, "USERID": self.user_id, "VERB": "capital"}))
        if len(recv_message) == 0:
            raise Exception(u"δ���յ���Ʒ�ֲ����ݣ�")
        else:
            return json.loads(recv_message, encoding="utf-8")


if __name__ == '__main__':
    a = Trader('simnow4', 'MXZ')
    ret = a.query_local_capital()
    print(ret)
