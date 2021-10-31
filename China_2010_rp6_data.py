#!/usr/local/anaconda3/bin/python
# encoding:utf-8

import re
import os
import requests
from bs4 import BeautifulSoup

root_url = 'http://www.stats.gov.cn/tjsj/pcsj/rkpc/6rp/'

r = requests.get(root_url+'lefte.htm')
assert r.status_code == 200
r.encoding = 'gbk'

soup = BeautifulSoup(r.text)
tags = soup.find('ul').find_all('li')[:-15]

folder_pat = re.compile(r'id="foldheader">(.*?)<')
excel_pat = re.compile(r'ref="(?P<link>.*?)">(?P<title>.*?)<')

root_dir = '中国 2010 年第六次人口普查资料'
os.mkdir(root_dir)
os.chdir(root_dir)
absolute_root_path = os.getcwd()

for tag in tags:
    t = str(tag)
    is_folder = folder_pat.search(t)
    if is_folder:
        folder_name = is_folder.group(1)
        if folder_name.find('部分') > 0 or len(folder_name) == 2:
            os.chdir(absolute_root_path)
        else:
            if os.listdir():
                os.chdir('../')
        os.mkdir(folder_name)
        os.chdir(folder_name)
    else:
        excel_info_dict = excel_pat.search(t).groupdict()
        r = requests.get(root_url+excel_info_dict['link'])
        r.encoding = 'gbk'
        with open(excel_info_dict['title']+'.xls', 'wb+') as fp:
            fp.write(r.content)
