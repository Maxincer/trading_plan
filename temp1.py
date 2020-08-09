


fpath_zx = r'D:\projects\trading_plan\data\trdrec_from_trdclient\20200809holding.xls'
with open(fpath_zx, 'rb') as f:
    list_datalines = f.readlines()
    for dataline in list_datalines:
        dataline = dataline.strip().decode('gbk').replace('=', '').replace('"', '').split('\t')
        print(dataline)