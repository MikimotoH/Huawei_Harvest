#!/usr/bin/env python3
# coding:utf-8
import sqlite3
import psycopg2
from psycopg2 import errorcodes
import sys
from my_utils import uprint
from GridIotCredentials import GridIotConnStr
import ipdb
import traceback

ouconn=None
def ousql(query,var=None):
    global ouconn
    oucsr=ouconn.cursor()
    try:
        oucsr.execute(query,var)
        if not query.startswith('SELECT'):
            ouconn.commit()
        if query.startswith('SELECT') or 'RETURNING' in query:
            return oucsr.fetchall()
        else:
            return
    except psycopg2.Error as ex:
        oucsr.execute('ABORT')
        raise ex

def main():
    brand='Huawei'
    source='consumer.huawei.com/en'
    rev=""
    startInRowIdx=int(sys.argv[1]) if len(sys.argv)>1 else 0
    
    with sqlite3.connect('huawei_consumer_search_by_keyword.sqlite3') as inconn:
        incsr = inconn.cursor()
        global ouconn
        ouconn= psycopg2.connect(GridIotConnStr)
        inRows = incsr.execute(
            "SELECT model, fw_ver,rel_date, file_desc,file_name"
            ", file_url, file_size, file_sha1 "
            " FROM TFiles "
            " ORDER BY id LIMIT -1 OFFSET %d"%startInRowIdx)
        for inRowIdx, inRow in enumerate(inRows,startInRowIdx):
            model, fw_ver, rel_date, file_desc, file_name, \
                    file_url, file_size, file_sha1 = inRow
            if not model:
                continue
            uprint('inRowIdx=%s, model="%s","%s" '%(
                inRowIdx, model, fw_ver))

            # UPSERT new Device
            devId=ousql(
                "UPDATE TDevice SET source=%(source)s "
                "WHERE brand=%(brand)s AND model=%(model)s AND"
                " revision=%(rev)s RETURNING id" ,locals())
            if devId:
                devId=devId[0][0]
            else:
                devId=ousql(
                    "INSERT INTO TDevice (brand,model,revision,source"
                    ")VALUES(%(brand)s,%(model)s,%(rev)s,%(source)s)"
                    " RETURNING id", locals())
                devId=devId[0][0]
            uprint("UPSERT brand='%(brand)s', model=%(model)s"
                ",source=%(source)s RETURNING devId=%(devId)s"%locals())

            # UPSERT new Firmware
            if not fw_ver:
                continue
            fwId=ousql(
                "UPDATE TFirmware SET file_sha1=%(file_sha1)s,"
                " include_prev=false,file_size=%(file_size)s,"
                " file_url=%(file_url)s,"
                " description=%(file_desc)s,"
                " release_date=%(rel_date)s,"
                " file_path=%(file_name)s "
                " WHERE"
                "  device_id=%(devId)s AND version=%(fw_ver)s AND"
                "  exclude_self=false RETURNING id",locals())
            if fwId:
                fwId=fwId[0][0]
            else:
                fwId=ousql(
                    "INSERT INTO TFirmware("
                    "  device_id, version, exclude_self, "
                    "  file_sha1, file_size, "
                    "  file_url, description, release_date, file_path ) "
                    "VALUES ( %(devId)s, %(fw_ver)s, false, "
                    " %(file_sha1)s, %(file_size)s, "
                    " %(file_url)s, %(file_desc)s, %(rel_date)s, %(file_name)s)"
                    " RETURNING id", locals())
                fwId=fwId[0][0]
            uprint("UPSERT TFirmware devId='%(devId)d', fw_ver='%(fw_ver)s',"
                " sha1='%(file_sha1)s', fwId=%(fwId)d"%locals())

if __name__=='__main__':
    main()

