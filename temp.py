import os
import pandas as pd
import pymongo

client = pymongo.MongoClient('mongodb://localhost:27017/')
col = client['test']['test']
a = list(col.find())
print('a')


