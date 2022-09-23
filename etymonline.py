import re
import requests
from bs4 import BeautifulSoup
import sqlite3
from pandas import DataFrame as df


url="https://www.etymonline.com/search"
db='./words.db'

def get_item_count(q='a')->int:
    r=requests.get(url,params={'q':q})
    assert r.status_code==200
    soup=BeautifulSoup(r.text)
    tag=soup.find('div',class_='searchList__pageCount--2jQdB')
    return int(re.fullmatch(r'.*?(\d+).*?',tag.text).groups()[0])

def get_dict(q='a')->dict:
    page_count=-(-get_item_count(q)//10)
    words_dict={}
    for page in range(1,page_count+1):
        r=requests.get(url,params={'q':q,'page':page})
        assert r.status_code==200
        soup=BeautifulSoup(r.text)
        tags=soup.find_all('div',class_='word--C9UPa')
        words_dict.update({t.find(class_='word__name--TTbAA').text:t.find(class_='word__defination--2q7ZH').text for t in tags})
      
    return words_dict

def save_to_db():
    alphabet=[chr(i) for i in range(97,97+26)]
    db_con=sqlite3.Connection(db)
    for c in alphabet:
        words_dict=get_dict(c)
        words_dataframe=df.from_dict(words_dict,orient='index')
        words_dataframe.to_sql(db,db_con,if_exists='append')

save_to_db()
