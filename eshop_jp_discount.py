import requests
from bs4 import BeautifulSoup
import re
import json

url = 'https://search.nintendo.jp/nintendo_soft/search.json'

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15'
}

params = {'opt_sshow': '1',
          'xopt_ssitu[]': 'not_found',
          'limit': '24',
          'page': 0,
          'c': '81326513548567025',
          'opt_sale_flg': '1',
          'sort': 'ssdate%20desc%2Cscore',
          'opt_search': '1',
          'opt_hard[]': '1_HAC'
          }

games = []
for page in range(1, 29):
    params['page'] = page
    r = requests.get(url=url, params=params, headers=headers)
    jsondata = json.loads(r.text)
    items = jsondata['result']['items']
    games += [item['title'] for item in items]
