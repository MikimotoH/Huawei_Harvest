#!/usr/bin/env python3
# coding: utf-8
import sqlite3
import ipdb
import traceback
import sys
from ftp_credentials import ftpHostName,ftpUserName,ftpPassword
import ftputil
from os import path
from urllib import parse
import os
from my_utils import uprint
from web_utils import getFileSha1
from web_utils import downloadFile
import re

conn=None
        
def guessModel(txt):
    txt = txt.replace('_', ' ')
    m = re.search(r'[A-Z]{1,2}\d{2,4}[A-Za-z]{0,1}', txt)
    return m.group(0)

def guessVersion(txt):
    txt = txt.replace('_',' ')
    m = re.search(r'(V[A-Z0-9\.]+)\b', txt)
    return m.group(1)


def main():
    global startTrail,prevTrail,conn
    try:
        startIdx = int(sys.argv[1]) if len(sys.argv)>1 else 0
        conn= sqlite3.connect('huawei_consumer_search_by_keyword.sqlite3')
        csr=conn.cursor()
        rows = csr.execute(
            "SELECT id,file_name,file_url,file_sha1,file_size FROM TFiles"
            " ORDER BY id LIMIT -1 OFFSET %d"%startIdx
            ).fetchall()
        for idx, row in enumerate(rows,startIdx):
            devId,file_name,file_url,file_sha1,file_size = row
            if not file_url:
                continue
            if file_sha1:
                continue
            if 'Android' in file_name:
                continue
            if 'Ascend' in file_name:
                continue
            if 'Honor' in file_name:
                continue
            if 'Open Source' in file_name:
                continue
            if 'opensource' in file_name.lower():
                continue

            uprint('idx=%d, file_name="%s",file_size=%d'%(idx,file_name,file_size))
            model = guessModel(file_name)
            uprint('model="%s"'%model)
            fw_ver = guessVersion(file_name)
            uprint('fw_ver="%s"'%fw_ver)
            try:
                local_file  = downloadFile(file_url, "Content-Disposition")
            except TypeError:
                continue
            file_sha1 = getFileSha1(local_file)
            file_size = path.getsize(local_file)
            csr.execute(
                "UPDATE TFiles SET file_sha1=:file_sha1"
                ",file_size=:file_size"
                ",model=:model "
                ",fw_ver=:fw_ver "
                " WHERE id = :devId", locals())
            conn.commit()
            ftp = ftputil.FTPHost(ftpHostName,ftpUserName,ftpPassword)
            uprint('upload to GRID')
            ftp.upload(local_file, path.basename(local_file))
            ftp.close()
            os.remove(local_file)
    except Exception as ex:
        ipdb.set_trace()
        traceback.print_exc()

if __name__=='__main__':
    main()

