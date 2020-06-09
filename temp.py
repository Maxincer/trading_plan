import os
import pandas as pd
import pymongo

client = pymongo.MongoClient('mongodb://localhost:27017/')
col = client['test']['test']
dict_ = pd.DataFrame(columns=['1', '2', '3']).to_dict('records')
print(dict_)




