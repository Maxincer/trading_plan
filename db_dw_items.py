#!usr/bin/env python37
# coding:utf-8
# Author: Maxincer
# Create Datetime: 20200723T203000 +0800

from datetime import datetime

import pymongo


class DBDWItems:
    def __init__(self):
        self.str_today = datetime.strftime(datetime.today(), '%Y%m%d')
