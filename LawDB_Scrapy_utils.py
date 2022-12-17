import os
import re
import json
import math
import requests
import pytesseract
import pandas as pd
from bs4 import BeautifulSoup
from docx import Document
from PyPDF2 import PdfReader
from pandas import DataFrame as df

_headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
}

_type_law = {
    '宪法': 'xffl',
    '法律': 'flfg',
    '行政法规': 'xzfg',
    '监察法规': 'jcfg',
    '司法解释': 'sfjs',
    '地方性法规': 'dfxfg'
}

_status_code = {
    '1': '有效',
    '3': '尚未生效',
    '5': '已修改',
    '9': '已废止'
}

_dirname = '国家法律法规数据库'


def _get_laws_info(TYPE: str = 'xffl') -> list:
    """
    return json list
    """
    base_url = 'https://flk.npc.gov.cn/api/'
    laws_info = []
    params = {
        "type": TYPE,
        "sort": "true",
        "page": "1",
        "size": "10",
    }
    r = requests.get(url=base_url, headers=_headers, params=params)
    assert r.status_code == 200
    d = json.loads(r.text)
    laws_info += d['result']['data']
    if d['result']['totalSizes'] > 10:
        pages = math.ceil(d['result']['totalSizes']/10)
        for i in range(2, pages+1):
            params['page'] = str(i)
            r = requests.get(url=base_url, headers=_headers, params=params)
            assert r.status_code == 200
            laws_info += json.loads(r.text)['result']['data']
    for i in range(len(laws_info)):
        if laws_info[i]['status'] in _status_code.keys():
            laws_info[i]['status'] = _status_code[laws_info[i]['status']]
        else:
            laws_info[i]['status'] = ''
    return laws_info


def _get_law_file(law_info: dict) -> None:
    base_url = 'https://flk.npc.gov.cn/api/detail'
    _headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:107.0) Gecko/20100101 Firefox/107.0",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
    }
    data = {
        "id": law_info['id'],
    }
    r = requests.post(url=base_url, headers=_headers, data=data)
    assert r.status_code == 200
    d = json.loads(r.text)['result']['body']
    d_type = {'WORD': '.docx', 'PDF': '.pdf', 'HTML': '.html'}
    type_loc = {d[i]['type']: i for i in range(len(d))}
    """
    some law_name will be too long to store on Linux,
    so use law_id as filename
    """
    if 'WORD' in type_loc:
        dl_url = 'https://wb.flk.npc.gov.cn'+d[type_loc['WORD']]['path']
        os.system('wget '+dl_url+' -O ' +
                  law_info['id']+d_type[d[type_loc['WORD']]['type']])
    elif 'HTML' in type_loc:
        dl_url = 'https://wb.flk.npc.gov.cn'+d[type_loc['HTML']]['url']
        os.system('wget '+dl_url+' -O ' +
                  law_info['id']+d_type[d[type_loc['HTML']]['type']])
    else:
        dl_url = 'https://wb.flk.npc.gov.cn'+d[type_loc['PDF']]['path']
        os.system('wget '+dl_url+' -O ' +
                  law_info['id']+d_type[d[type_loc['PDF']]['type']])


def _download_files() -> None:
    os.mkdir(_dirname)
    os.chdir(_dirname)
    for k in _type_law.keys():
        os.mkdir(k)
        os.chdir(k)
        laws_list = _get_laws_info(_type_law[k])
        df(laws_list).to_csv(k+'目录.csv')
        for law in laws_list:
            # print(law['title'])
            _get_law_file(law)
            # time.sleep(randint(1, 3))
        os.chdir('../')
    os.chdir('../')


def _update_files() -> None:
    os.chdir(_dirname)
    for k in _type_law.keys():
        os.chdir(k)
        laws_list = _get_laws_info(_type_law[k])
        update_ids = set(df(laws_list).id)-set(pd.read_csv(k+'目录.csv').id)
        for id in update_ids:
            _get_law_file({'id': id})
        df(laws_list).to_csv(k+'目录.csv')
        os.chdir('../')
    os.chdir('../')


def _trans_to_plaintext(filename: str) -> str:
    pat = re.compile(r'\.(.*)')
    ext = pat.findall(filename)[0]
    if ext == 'html':
        with open(filename, 'r') as fp:
            txt = BeautifulSoup(fp.read(),features='lxml').text
    elif ext == 'docx':
        txt = ''
        try:
            for p in Document(filename).paragraphs:
                txt += p.text+'\n'
        except:
            print(filename)
    else:
        txt=''
        for i in PdfReader(filename).pages:
            with open('_temp_gen_from_pdf.jpg','wb+') as fp:
                fp.write(i.images[0].data)
                txt+=pytesseract.image_to_string(image='_temp_gen_from_pdf.jpg',lang='chi_sim')
        os.remove('_temp_gen_from_pdf.jpg')
    return txt

def _gen_texts(from_dir='国家法律法规数据库',to_dir='国家法律法规数据库_txt')->None:
    rootdir=os.getcwd()
    os.mkdir(to_dir)
    os.chdir(from_dir)
    for d in os.listdir():
        os.mkdir(rootdir+'/'+to_dir+'/'+d)
        os.chdir(d)
        os.system('cp '+[i for i in os.listdir() if i.find('csv')>0][0]+' '+rootdir+'/'+to_dir+'/'+d)
        for f in os.listdir():
            if f.find('csv')>0:
                continue
            pat=re.compile(r'(.*)\.')
            with open(rootdir+'/'+to_dir+'/'+d+'/'+pat.findall(f)[0],'w+') as fp:
                fp.write(_trans_to_plaintext(f))
        os.chdir('../')
    os.chdir('../')

