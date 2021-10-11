#!/usr/local/anaconda3/bin/python
# encoding:utf-8

import re
import os
import json
import time
import requests
from multiprocessing import Pool
from bs4 import BeautifulSoup


user_agent = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15'
}


def get_bookinfolist_by_page(page: int = 1):  # page range:1~5
    url = 'https://www.qidian.com/all/action1-vip0-sign1-page'+str(page)
    r = requests.get(url, headers=user_agent)
    if r.status_code != 200:
        return None
    soup = BeautifulSoup(r.text, 'lxml')
    tags = soup.find_all('div', class_='book-mid-info')
    pat = re.compile(
        r'data-bid="(?P<id>\d+)".*?href="(?P<link>.*?)".*?>(?P<name>.*?)<')
    bookinfo = [pat.search(str(tag)).groupdict() for tag in tags]
    return bookinfo  # list of dict:id,link,name


def get_chapters_by_bookid(id: str):
    url = 'https://book.qidian.com/info/'+id+'/#Catalog'
    r = requests.get(url, headers=user_agent)
    if r.status_code != 200:
        return None
    soup = BeautifulSoup(r.text, 'lxml')
    # 第三方的书籍此处 soup.find_all返回 empty list
    if soup.find_all('div', class_='volume'):
        tags = soup.find_all('div', class_='volume')[-1].find_all('li')
        pat = re.compile(r'href="(?P<link>.*?)".*>(?P<name>.*?)<')
        chapterinfo = [pat.search(str(tag)).groupdict() for tag in tags]
    else:
        json_url = 'https://book.qidian.com/ajax/book/category?bookId='+id
        json_r = requests.get(json_url, headers=user_agent)
        json_r.encoding = 'u8'
        cs = json.loads(json_r.text)['data']['vs'][0]['cs']
        chapterinfo = [
            {'link': "//vipreader.qidian.com/chapter/"+id+'/'+str(c['id']), 'name':c['cN']} for c in cs]
    return chapterinfo  # list of dict:link,chapter name


def get_content_by_chapterlink(link: str):
    url = 'https:'+link
    r = requests.get(url, headers=user_agent)
    if r.status_code != 200:
        return None
    soup = BeautifulSoup(r.text, 'lxml')
    tags = soup.find('div', class_='read-content j_readContent').find_all('p')
    pat = re.compile(r'<p>(.*?)</p>')
    content = [pat.search(str(tag))[1]+'\n' for tag in tags[:-1]]
    return ''.join(content)  # str: chapter content


def save_book_by_bookinfo(bookinfo: dict):
    fp = open(bookinfo['name']+'.txt', 'a+')
    print(bookinfo['name']+'\tstart...\n')
    st = time.time()
    chapters = get_chapters_by_bookid(bookinfo['id'])
    for chapter in chapters:
        chaptername = chapter['name']
        content = get_content_by_chapterlink(chapter['link'])
        fp.write('\n'+chaptername+'\n')
        fp.write(content+'\n\n\n')
    ft = time.time()
    fp.close()
    os.system('mv '+bookinfo['name']+'.txt '+bookinfo['name']+'\(完本\).txt')
    print(bookinfo['name']+'\tend in '+str(ft-st)+' seconds.\n')


def save_books():
    bookinfo = []
    for page in range(1, 6):
        bookinfo.extend(get_bookinfolist_by_page(page))
    p = Pool(os.cpu_count())
    for b in bookinfo:
        p.apply_async(save_book_by_bookinfo, args=(b,))
    p.close()
    p.join()


books_dir = './Qidian_com'
os.mkdir(books_dir)
os.chdir(books_dir)
save_books()
os.chdir('../')
print('Complete!\n')
