fpath_zx = r'D:\projects\trading_plan\data\trdrec_from_trdclient\922_c_zx_0322.txt'
with open(fpath_zx, 'rb') as f:
    lines = f.readlines()
    for line in lines:
        print(line)