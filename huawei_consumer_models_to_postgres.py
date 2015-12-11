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
    
    with sqlite3.connect('huawei_consumer_model.sqlite3') as inconn:
        incsr = inconn.cursor()
        global ouconn
        ouconn= psycopg2.connect(GridIotConnStr)
        inRows = incsr.execute(
            "SELECT category, model FROM TFiles "
            " ORDER BY id LIMIT -1 OFFSET %d"%startInRowIdx)
        for inRowIdx, inRow in enumerate(inRows,startInRowIdx):
            category,model=inRow
            uprint('inRowIdx=%s, model="%s"'%(inRowIdx, model))

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


if __name__=='__main__':
    main()
