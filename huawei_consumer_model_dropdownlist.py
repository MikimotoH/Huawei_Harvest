#!/usr/bin/env python3
#coding: utf-8
import harvest_utils
from harvest_utils import waitVisible, waitText, getElems, getFirefox,driver,waitTextChanged, getElemText, elemWithText, waitClickable, waitUntilStable, isReadyState,waitUntil,retryStable,getNumElem,goToUrl
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException, WebDriverException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait,Select
import sys
import sqlite3
import re
import time
import ipdb
import traceback
from my_utils import uprint,ulog,getFuncName
from urllib import parse
from os import path
import itertools

driver,conn=None,None

rootUrl = 'http://consumer.huawei.com/en/support/index.htm'

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

def modelWalker(category):
    global driver
    CSS = driver.find_elements_by_css_selector
    try:
        waitClickable('#Combo_support-select-2 div input').click()
        models = getElems('#Combo_support-select-2 ul a')
        numModels = len(models)
        ulog('numModels=%d'%numModels)
        for idx in range(numModels):
            model = models[idx].text
            ulog('idx=%d, model=%s'%(idx, model))
            sql("INSERT OR REPLACE INTO TFiles(category,model)"
                "VALUES(:category,:model)",locals())
            uprint('UPSERT "%(category)s," "%(model)s"'%locals())
    except Exception as ex:
        ipdb.set_trace()
        traceback.print_exc()
        driver.save_screenshot('huawei_excep.png')


def categoryWalker():
    global driver
    try:
        # Select a Type (Category)
        waitClickable('#Combo_support-select-1 > div > input').click()
        cats = getElems('#Combo_support-select-1 ul a')
        numCats = len(cats)
        ulog('numCats=%d'%numCats)
        for idx in range(numCats):
            category=cats[idx].text
            ulog('idx=%d, select category=%s'% (idx,category))
            cats[idx].click()
            modelWalker(category)
            waitClickable('#Combo_support-select-1 > div > input').click()
            cats = getElems('#Combo_support-select-1 ul a')
    except Exception as ex:
        ipdb.set_trace()
        traceback.print_exc()
        driver.save_screenshot('huawei_excep.png')


def main():
    global driver,conn
    try:
        conn=sqlite3.connect('huawei_consumer_model.sqlite3')
        sql("CREATE TABLE IF NOT EXISTS TFiles("
            "id INTEGER NOT NULL,"
            "category TEXT,"
            "model TEXT," 
            "tree_trail TEXT," # [1, 2]
            "PRIMARY KEY (id),"
            "UNIQUE(model)"
            ")")
        driver=harvest_utils.getFirefox()
        harvest_utils.driver=driver
        prevTrail=[]
        goToUrl(rootUrl)
        categoryWalker()
        driver.quit()
        conn.close()
    except Exception as ex:
        ipdb.set_trace()
        traceback.print_exc()
        driver.save_screenshot('huawei_excep.png')

if __name__=='__main__':
    try:
        main()
    except Exception as ex:
        ipdb.set_trace()
        traceback.print_exc()
        try:
            driver.save_screenshot('huawei_excep.png')
            driver.quit()
        except Exception:
            pass

