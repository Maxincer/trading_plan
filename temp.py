import os
import pandas as pd
import pymongo

client = pymongo.MongoClient('mongodb://localhost:27017/')
col = client['basicinfo']['myacctsinfo']
for _ in col.find():
    print(_)


