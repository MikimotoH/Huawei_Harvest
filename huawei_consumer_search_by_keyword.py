#!/usr/bin/env python3
# coding: utf-8
import harvest_utils
from harvest_utils import waitVisible, waitText, getElems, getFirefox,driver,waitTextChanged, getElemText, elemWithText, waitClickable, waitUntilStable, isReadyState,waitUntil,retryStable,getNumElem,goToUrl
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException, WebDriverException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys
import sys
import sqlite3
import re
import time
import ipdb
import traceback
from my_utils import uprint,ulog
from urllib import parse
from os import path
import itertools


driver,conn=None,None
prevTrail=[]
startTrail=[]
conn,driver=None,None
keyword=''

def glocals()->dict:
    """ globals() + locals()
    """
    import inspect
    ret = dict(inspect.stack()[1][0].f_locals)
    ret.update(globals())
    return ret

def retryUntilTrue(statement, timeOut:float=6.2, pollFreq:float=0.3):
    timeElap=0
    while timeElap<timeOut:
        timeBegin=time.time()
        try:
            r = statement()
            if r==True:
                return r
        except (StaleElementReferenceException,NoSuchElementException, StopIteration):
            pass
        except Exception as ex:
            ulog('raise %s %s'%(type(ex),str(ex)))
            raise ex
        #ulog('sleep %f secs'%pollFreq)
        time.sleep(pollFreq)
        timeElap+=(time.time()-timeBegin)
    raise TimeoutException(getFuncName()+': timeOut=%f'%timeOut)

def getStartIdx():
    global startTrail
    if startTrail:
        return startTrail.pop(0)
    else:
        return 0

def sql(query:str, var=None):
    global conn
    csr=conn.cursor()
    try:
        if var:
            rows = csr.execute(query,var)
        else:
            rows = csr.execute(query)
        if not query.startswith('SELECT'):
            conn.commit()
        if query.startswith('SELECT'):
            return rows.fetchall()
        else:
            return
    except sqlite3.Error as ex:
        print(ex)
        raise ex

def guessDate(txt:str):
    """ txt = '2015-05-30' """
    try:
        from datetime import datetime
        m = re.search(r'\d{4}-\d{2}-\d{2}', txt)
        return datetime.strptime(m.group(0), '%Y-%m-%d')
    except Exception as ex:
        ipdb.set_trace()
        traceback.print_exc()
def guessFileSize(txt:str)->int:
    """ txt='6.56 MB'
    """
    try:
        m = re.search(r'(\d+\.?\d+)\s*(GB|MB|KB)', txt, re.I)
        if not m:
            ulog('error txt="%s"'%txt)
            return 0
        unitDic=dict(MB=1024**2,KB=1024,GB=1024**3)
        unitTxt = m.group(2).upper()
        return int(float(m.group(1)) * unitDic[unitTxt] )
    except Exception as ex:
        ipdb.set_trace()
        print('txt=',txt)


def rowWalker():
    global prevTrail, driver,keyword
    try:
        rows = getElems('#product-support-downloads-ul > li')
        numRows =len(rows)
        ulog('numRows=%s'%numRows)
        startIdx = getStartIdx()
        for idx in range(startIdx, numRows):
            ulog('idx=%s'%idx)
            file_name = rows[idx].find_element_by_css_selector('h2').text
            file_desc = rows[idx].find_element_by_css_selector('p.p-1').text
            date_size = rows[idx].find_element_by_css_selector('p.p-2').text
            rel_date = guessDate(date_size)
            file_size = guessFileSize(date_size)
            down = rows[idx].find_element_by_css_selector('a.download-bnt')
            file_url = down.get_attribute('href')
            tree_trail = str(prevTrail+[idx])
            sql("INSERT OR REPLACE INTO TFiles (keyword,file_name, file_desc, rel_date, file_size, file_url,tree_trail) VALUES (:keyword,:file_name,:file_desc,:rel_date,:file_size,:file_url,:tree_trail) ", glocals())
            uprint('UPSERT "%(file_name)s", %(file_url)s, %(tree_trail)s'%locals())
    except Exception as ex:
        ipdb.set_trace()
        traceback.print_exc()

def pageWalker():
    global prevTrail, driver
    try:
        startIdx = getStartIdx()
        for idx in range(0, startIdx):
            ulog('idx=%d,page=%d'%(idx, (idx+1)))
            waitClickable('.x-next-on').click()

        for idx in itertools.count(startIdx):
            ulog('idx=%d,page=%d'%(idx, (idx+1)))
            prevTrail+=[idx]
            rowWalker()
            prevTrail.pop()
            try:
                nextPage = waitClickable('.x-next-on')
            except (NoSuchElementException, TimeoutException):
                ulog('last page')
                break
            nextPage.click()
    except Exception as ex:
        ipdb.set_trace()
        traceback.print_exc()

rootUrl='http://consumer.huawei.com/en/support/downloads/index.htm'
def main():
    global startTrail, prevTrail,driver,conn,keyword
    try:
        keyword = sys.argv[1]
        startTrail = [int(re.search(r'\d+', _).group(0)) for _ in sys.argv[2:]]
        ulog('startTrail=%s'%startTrail)
        conn=sqlite3.connect('huawei_consumer_search_by_keyword.sqlite3')
        sql("CREATE TABLE IF NOT EXISTS TFiles("
            "id INTEGER NOT NULL,"
            "file_name TEXT," # 'Ascend Mate (MT1-U06,Android 4.1,Emotion UI,V100R001C00B221,General Version)'
            "file_desc TEXT," # NBG5715
            "rel_date DATE," # 2015-05-30
            "file_size INTEGER," # '1.26 GB' '352.32 MB'
            "file_url TEXT," # "http://download-c.huawei.com/download/downloadCenter?downloadId=44602&version=92646&siteCode=worldwide"
            "tree_trail TEXT," # [1, 2]
            "file_sha1 TEXT," # 
            "PRIMARY KEY (id),"
            "UNIQUE(file_name)"
            ")")
        driver=harvest_utils.getFirefox()
        harvest_utils.driver=driver
        prevTrail=[]
        goToUrl(rootUrl)
        inp = waitClickable('#savekeyword')
        inp.click()
        inp.send_keys(keyword)
        waitClickable('#search_by_kw > img').click()
        CSS=driver.find_elements_by_css_selector
        retryUntilTrue(lambda:len(CSS('x.waite'))==1, 4, 0.4 )
        uprint('waitCursor shows')
        retryUntilTrue(lambda:len(CSS('x.waite'))==0, 30, 1 )
        uprint('waitCursor disappears')
        pageWalker()
        driver.quit()
        conn.close()
    except Exception as ex:
        ipdb.set_trace()
        traceback.print_exc()
        driver.save_screenshot('main_excep.png')

def main():


if __name__=='__main__':
    try:
        main()
    except Exception as ex:
        ipdb.set_trace()
        traceback.print_exc()
        try:
            driver.save_screenshot(getScriptName()+'_excep.png')
            driver.quit()
        except Exception:
            pass
