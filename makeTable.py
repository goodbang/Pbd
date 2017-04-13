import time

import pandas as pd
import csv
import numpy as np
import pickle
from bs4 import BeautifulSoup

# 리스트에서 정정공시를 삭제, 최초 공시만 가져옴
def choiceFirst(df1):
    rmk_list = df1.rmk.values
    num_list = [i for i in range(len(rmk_list))]
    mark = 0
    for i, item in enumerate(rmk_list):
        if item != "정":
            mark = i
        else:
            num_list.remove(mark)
            mark = i

    df1 = df1.ix[num_list, :]
    return df1



error_list = []
success_list = []

try:
    with open('error_list.pickle', 'rb') as f:
        error_list = pickle.load(f)

    with open('success_list.pickle', 'rb') as f:
        success_list = pickle.load(f)
except:
    print("error occured while read file")


df_error = pd.DataFrame(error_list)
df_success = pd.DataFrame(success_list)
post_all_list = []
print("length of success_list : {}".format(len(success_list)))
for num in success_list[:]:
    post_df = pd.read_csv('./data/{}.csv'.format(num))
    post_all_list.append(choiceFirst(post_df))

result = pd.concat(post_all_list)
result.to_csv("result.csv", encoding="utf-8")

