#!usr/bin/env python3
# coding: utf-8

from ftplib import FTP


def ftpconnect(host, username, password):
    ftp = FTP()
    ftp.connect(host, 21)
    ftp.login(username, password)
    ftp.encoding = 'UTF-8'
    ftp.set_pasv(0)
    ftp.passiveserver = 0
    return ftp


def uploadfile(ftp, remotepath, localpath):
    bufsize = 1024
    fp = open(localpath, 'rb')
    ftp.storbinary('STOR' + remotepath, fp, bufsize)
    ftp.set_debuglevel(0)
    fp.close()


if __name__ == '__name__':
    ftp = ftpconnect('172.16.1.10', 'wjp', 'Wjp123456')
    print(ftp.dir())
    ftppath_from = f'D:/ftp/{mxz}'
