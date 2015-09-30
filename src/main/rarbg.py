import logging
from google.appengine.ext import ndb
from google.appengine.api import mail
from google.appengine.api import urlfetch
import urllib2
from src.main.models import Torrent, UserTorrent
from bs4 import BeautifulSoup
import arrow
import re


class Rarbg():

    URL_BASE = 'http://rarbg.to'
    # HEADERS = {
    #     'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:40.0) Gecko/20100101 Firefox/40.0',
    #     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    #     'Accept-Encoding': 'gzip, deflate',
    #     'Accept-Language': 'en-US,en;q=0.5',
    #     'Connection': 'keep-alive',
    #     'DNT': 1,
    #     'Origin': 'http://rarbg.to',
    #     'Referrer': 'http://rarbg.to',
    # }
    GROUPS = [
        # {'code': 100, 'name': 'Audio', 'categories': [
            # {'code': 101, 'name': 'Music', 'pages': 2},
            # {'code': 102, 'name': 'AudioBooks', 'pages': 3, 'url': 'audio-books'},
        # ]},
        # {'code': 600, 'name': 'Other', 'categories': [
        #     {'code': 601, 'name': 'eBooks', 'pages': 2, 'url': 'ebooks'},
        # ]},
        # {'code': 300, 'name': 'Applications', 'categories': [
        #     {'code': 301, 'name': 'Windows', 'pages': 2, 'url': 'windows'},
            # {'code': 302, 'name': 'Mac', 'pages': 1},
        # ]},
        # {'code': 400, 'name': 'Games', 'categories': [
        #     {'code': 401, 'name': 'PC Games', 'pages': 2, 'url': 'pc-games'},
        # ]},
        {'code': 200, 'name': 'Video', 'categories': [
            # {'code': 209, 'name': '3D', 'pages': 1, 'url': '3d-movies'},
            {'code': 207, 'name': 'HD Movies', 'pages': 1, 'url': 'torrents.php?category=14;17;42;44;45;46;47;48&search=&order=seeders&by=DESC'},
            # {'code': 205, 'name': 'TV Shows', 'pages': 12, 'url': 'tv'},
        ]},
    ]


    def __init__(self):
        urlfetch.set_default_fetch_deadline(60)


    def scrape(self):
        for group in self.GROUPS:
            logging.info('Rarbg: scrape: Group = {}'.format(group['name']))

            for category in group['categories']:
                logging.info(' -=- ' * 20)
                logging.info('Rarbg: scrape: Category = {}'.format(category['name']))

                for p in range(1, category['pages']+1):
                    logging.info('Rarbg: scrape: Page = {}'.format(p))

                    self.scrapePage(group, category, p)

        # logging.info('Kickass: scraping complete series')
        # self.scrapeSeriesComplete()


    def scrapePage(self, group, category, p):
        logging.info('Rarbg: scrapePage')

        item = {
            'group_code': group['code'],
            'group_name': group['name'],
            'category_code': category['code'],
            'category_name': category['name'],
        }
        logging.debug(item)

        # 3 tries to scrape page
        rows = []
        for _ in xrange(1):
            try:
                url = '{}/{}&page={}'.format(self.URL_BASE, category['url'], p)
                url = 'http://rarbg.to/torrents.php?category=14;17;42;44;45;46;47;48&order=seeders&by=DESC&page=1'
                logging.info('Rarbg: scrapePage: url {}'.format(url))
                req = urllib2.Request(url, headers={'User-Agent': 'Magic Browser'})
                res = urllib2.urlopen(req, timeout=60)
                # res = urlfetch.fetch(url, headers=self.HEADERS)
                # logging.info(res.headers)
                if res.getcode() != 200:
                    logging.warn('Rarbg: getcode: {}'.format(res.getcode()))
                    logging.warn('Rarbg: read: {}'.format(res.read()))
                    continue
                # if res.status_code != 200:
                #     logging.warn('Rarbg: status_code: {}'.format(res.status_code))
                #     logging.warn('Rarbg: content: {}'.format(res.content))
                #     logging.warn('Rarbg: headers: {}'.format(res.headers))
                #     continue

                logging.info('res {}'.format(res.content))

                html = BeautifulSoup(res.content)
                html_table = html.find('table', class_='lista2t')
                logging.info('Rarbg: Table found? {}'.format(type(html_table)))
                rows = html_table.find_all('tr', class_='lista2')
                logging.info('Rarbg: {} rows found in table'.format(len(rows)))
                break
            except Exception, e:
                logging.critical('Rarbg: scrapePage: could not scrape with try {0}'.format(_))
                logging.exception(e)

        if rows:
            self.parseRows(item, rows)


    def scrapeSeriesComplete(self):
        logging.info('Kickass: scraping complete series')

        item = {
            'group_code': 200,
            'group_name': 'Video',
            'category_code': 205,
            'category_name': 'TV Shows',
        }

        # 3 tries to scrape page
        rows = []
        for n in xrange(3):
            try:
                url = '{}/usearch/complete%20category:tv'.format(self.URL_BASE)
                logging.info('Kickass: scrapePage: url {0}'.format(url))
                res = urlfetch.fetch(url)
                # logging.info('res {0}'.format(res.content))

                html = BeautifulSoup(res.content)
                rows = html.find('table', class_='data').find_all('tr')[2:]
                break
            except:
                logging.error('Kickass: scrapePage: could not scrape with try {0}'.format(n))
        logging.info('Kickass: scrapePage: found {0} in table'.format(len(rows)))

        if rows:
            self.parseRows(item, rows, True)


    def parseRows(self, item, rows, is_complete=False):
        logging.info('Rarbg: Parsing {} rows...'.format(len(rows)))
        for row in rows:
            item = {}
            try:
                td_file = row.find_all('td')[1]
                td_added = row.find_all('td')[2]
                td_size = row.find_all('td')[3]
                td_seeders = row.find_all('td')[4]
                td_leechers = row.find_all('td')[5]
                td_uploader = row.find_all('td')[7]

                # title
                item['title'] = td_file.find_all('a')[0].text

                # url
                item['url'] = '{}{}'.format(self.URL_BASE, td_file.find_all('a')[0]['href'])

                # uploaded at and week
                uploaded_at = arrow.get(td_added.text)
                item['uploaded_at'] = uploaded_at.datetime.replace(tzinfo=None)
                item['uploaded_week'] = uploaded_at.strftime("%U")

                # size
                details_size_split = td_size.text.strip().split(' ')
                details_size_mul = 9 if 'GB' in details_size_split[1] else (6 if 'MB' in details_size_split[1] else (3 if 'KB' in details_size_split[1] else 0))
                item['size'] = int((float(details_size_split[0])) * 10**details_size_mul)

                # seeders and leechers
                item['seeders'] = int(td_seeders.text)
                item['leechers'] = int(td_leechers.text)

                # uploader
                item['uploader'] = td_uploader.text

                break
                # item['magnet'] = row.find('a', title=re.compile("magnet"))['href']

                # save
                match_group = re.match(self.RE_TID, item['url']).groups(0)
                item_key = ndb.Key('Torrent', match_group[0])
                torrent = item_key.get()
                if not torrent:
                    torrent = Torrent(key=item_key)
                torrent.populate(**item)
                torrent.series_complete = is_complete
                torrent.put()
                logging.info('Torrent {0}'.format(torrent))
            except Exception as e:
                logging.exception(e)
