#-*- coding: utf-8 -*-

# import urllib
import requests
import json
import time

import pandas as pd
import csv
import numpy as np
import pickle
from bs4 import BeautifulSoup



#  윈도우
from selenium import webdriver
def saveURLs(rcp_no_list):

    browser = webdriver.Chrome(chromedriver)
    url_list = []
    for item in rcp_no_list:
        browser.get("http://dart.fss.or.kr/dsaf001/main.do?rcpNo={}".format(item))
        time.sleep(0.2)
        elem = browser.find_element_by_id("ifrm")
        url_list.append(elem.get_attribute("src"))
    browser.close()
    return url_list

# 리눅스용
# import sys
# reload(sys)
# sys.setdefaultencoding('utf-8')
# from pyvirtualdisplay import Display
# from selenium import webdriver
#
# def saveURLs(rcp_no_list):
#     display = Display(visible=0, size=(800, 600))
#     display.start()
#     url_list = []
#     browser = webdriver.Chrome(executable_path='/usr/lib/chromium-browser/chromedriver')
#
#     for item in rcp_no_list:
#         browser.get("http://dart.fss.or.kr/dsaf001/main.do?rcpNo={}".format(item))
#         time.sleep(0.2)
#         elem = browser.find_element_by_id("ifrm")
#         url_list.append(elem.get_attribute("src"))
#     browser.quit()
#     display.stop()
#     return url_list

def readSheet(url):

    res = requests.get(url)
    time.sleep(0.2)
    # soup = BeautifulSoup(res.text, "html5lib")
    soup = BeautifulSoup(res.content, "html.parser")
    val_list = []

    # 증자방식
    try:
        tval_list2 = soup.find_all('td', attrs={"align": "CENTER"})
        val_list.append(tval_list2[8].text)
    except IndexError as e:
        # print("Title Error : ", e)
        val_list.append("Title Error")
    # 숫자데이터
    tval_list = soup.find_all('td', attrs={"align": "RIGHT"})

    try:
        for i, item in enumerate(tval_list[:14]):
            val_list.append(item.text)
        if(len(val_list) < 15):
            val_list = np.hstack((val_list, (["empty"] * (15-len(val_list)))))
        return val_list
    except IndexError as e:
        # print("Number Error : ", e)
        return ["Val Error"] * 15
        #
        # 0: 일자
        # 1: 신주 보통주 수
        # 2: 신주 우선주 수
        # 3: 신주 액면가액
        # 4: 증자 전 총 발행 보통주수
        # 5: 증자 전 총 발행 우선주수
        # 6: 조달목적 시설자금
        # 7: 조달목적 운영자금
        # 8: 조달목적 타법인 증권취득자금
        # 9: 조달목적 기타자금

        # 10: 신 보통주 발행 가액
        # 11: 신 우선주 발행 가액
        # if 10 and 11 == null 이면
        # 12: 신 보통주 예정발행 가액
        # 13: 신 우선주 예정발행 가액


def getDataFrame(crp_cd):
    DART_KEY = '620b32348a050c6b10e4d06b0ea67279ce0082f4'  # dart auth key
    bsn_tp = 'B001'  # 주요정보 공시만
    url = "http://dart.fss.or.kr/api/search.json?auth={}&crp_cd={}&bsn_tp={}&page_set={}&fin_rpt=N&start_dt=20000101".format(
        DART_KEY, crp_cd, bsn_tp, 50)
    res = requests.get(url)

    data = json.loads(res.text)
    d_list = data["list"]
    df1 = pd.DataFrame(d_list)

    if df1.size < 1:
        # 조회건수가 0이면 빈 DataFrame을 리턴함
        print("{} has 0".format(crp_cd))
        return pd.DataFrame([])

    #
    # 리스트에서 정정공시를 삭제, 최초 공시만 가져옴
    #
    rmk_list = df1.rmk.values
    num_list = [i for i in range(len(rmk_list))]
    mark = 0
    for i, item in enumerate(rmk_list):
        if item == "":
            mark = i
        else:
            num_list.remove(mark)
            mark = i
    df1 = df1.ix[num_list, :]

    # 한글 쿼리문 검색 문제
    try:
        df1 = df1[df1.rpt_nm.str.contains(u"증자")]
        rcp_no_list = df1.rcp_no.values

        url_list = saveURLs(rcp_no_list)
    except AttributeError as e:
        print("except : {}".format(crp_cd))
        return 0


    crp_report_list = []
    for url in url_list:
        crp_report_list.append(readSheet(url))
    # print(np.shape(df.values), np.shape(crp_report_list), np.shape(url_list))
    url_list = np.array(url_list)
    url_list = url_list[:, np.newaxis]
    print(crp_cd, len(df1.values), len(crp_report_list), len(url_list))
    try:
        frames = np.hstack((df1.values, crp_report_list, url_list))

        df3 = pd.DataFrame(frames, columns=['crp_cd', 'crp_cls', 'crp_nm', 'flr_nm',
                                        'rcp_dt', 'rcp_no', 'rmk', 'rpt_nm', 'kind', 'rcp_dt2',
                                        'new_stock_cnt', 'new_pref_cnt', 'par_value',
                                        'pre_stock_cnt', 'pre_pref_cnt',
                                        'infra', 'operation', 'other', 'etc',
                                        'isu_stock_price', 'isu_pref_price',
                                        'exp_stock_price', 'exp_pref_price', 'url'])
        df3.to_csv("./data/{}.csv".format(crp_cd))
        return df3
    except ValueError as e:
        print("{} : {}".format(e, crp_cd))
        return pd.DataFrame([])

def initStockList():
    kospi_list = []
    kosdak_list = []
    with open('kospi.csv', 'r') as f:
        csvReader = csv.reader(f)
        for row in csvReader:
            kospi_list.append(row)

    with open('kosdak.csv', 'r') as f:
        csvReader = csv.reader(f)
        for row in csvReader:
            kosdak_list.append(row)

    kospi = kospi_list[0]
    kosdak = kosdak_list[0]
    return (kospi, kosdak)

DART_KEY = '620b32348a050c6b10e4d06b0ea67279ce0082f4' #dart auth key
crp_cd = '000075' #종목코드
bsn_tp = 'B001' #주요정보 공시만
chromedriver = './chromedriver'


kospi_list , kosdak_list = initStockList()

crwaler = getDataFrame(crp_cd)
crwaler.to_csv("./data/{}.csv".format(crp_cd))


error_list = []
success_list = []
#
# try:
#     with open('error_list.pickle', 'rb') as f:
#         error_list = pickle.load(f)
#
#     with open('success_list.pickle', 'rb') as f:
#         success_list = pickle.load(f)
# except:
#     print("error occured while read file")
#
# result_list = []
#
# for crp_cd in kospi_list[6:8]:
#     if crp_cd in success_list:
#         continue
#     if crp_cd in error_list:
#         continue
#     else:
#         crwaler = getDataFrame(crp_cd)
#         result_list.append(crwaler)
#         if crwaler.empty:
#             error_list.append(crp_cd)
#         else:
#             success_list.append(crp_cd)
#
# result = pd.concat(result_list)
# result.to_csv("./data/result.csv", encoding="utf-8")
#
# with open('error_list.pickle', 'wb') as f:
#     pickle.dump(error_list, f)
#
# with open('success_list.pickle', 'wb') as f:
#     pickle.dump(success_list, f)


