import arrow
import logging
import re
from bs4 import BeautifulSoup
from google.appengine.ext import ndb
from google.appengine.api import mail
from google.appengine.api import urlfetch
from series import Series
from src.main.models import Torrent, UserTorrent


class Kickass():

    RE_TID = re.compile('.*-(t[0-9]*)\.html')
    URL_BASE = 'http://kat.cr'
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
        {'code': 400, 'name': 'Games', 'categories': [
            {'code': 401, 'name': 'PC Games', 'pages': 1, 'url': 'windows-games'},
        ]},
        {'code': 200, 'name': 'Video', 'categories': [
            {'code': 209, 'name': '3D', 'pages': 1, 'url': '3d-movies'},
            {'code': 207, 'name': 'HD Movies', 'pages': 8, 'url': 'highres-movies'},
            {'code': 205, 'name': 'TV Shows', 'pages': 16, 'url': 'tv'},
        ]},
    ]

    def __init__(self):
        urlfetch.set_default_fetch_deadline(60)

    def scrape(self):
        logging.info('Kickass: scrape: started')
        for group in self.GROUPS:
            logging.info('Kickass: scrape: Group = {}'.format(len(group)))
            for category in group['categories']:
                logging.info(' -=- ' * 20)
                logging.info('Kickass: scrape: Category = {}'.format(len(category)))
                for p in range(category['pages']):
                    logging.info('Kickass: scrape: Page = {}'.format(p))
                    self.scrapePage(group, category, p)

        logging.info('Kickass: scraping complete')
        self.scrapeSeriesComplete()

    def scrapePage(self, group, category, p):
        logging.info('Kickass: scrapePage: {} {} {}'.format(group['name'], category['name'], p))

        item = {
            'group_code': group['code'],
            'group_name': group['name'],
            'category_code': category['code'],
            'category_name': category['name'],
        }

        # 3 tries to scrape page
        rows = []
        for n in xrange(3):
            try:
                url = '{}/{}/{}/'.format(self.URL_BASE, category['url'], p)
                logging.info('Kickass: scrapePage: url {}'.format(url))
                res = urlfetch.fetch(url)
                # logging.info('res {0}'.format(res.content))

                html = BeautifulSoup(res.content)
                rows = html.find('table', class_='data').find_all('tr')[2:]
            except:
                logging.error('Kickass: scrapePage: could not scrape with try {0}'.format(n))
            else:
                break
        logging.info('Kickass: scrapePage: found {} in table'.format(len(rows)))

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
        series = Series()
        logging.info('Parsing {} rows...'.format(len(rows)))
        for row in rows:
            try:
                link = row.find('a', class_='cellMainLink')
                item['title'] = link.text
                item['url'] = link['href']
                item['magnet'] = row.find('a', title=re.compile("magnet"))['href']

                # uploaded at
                value, scale = row.find_all('td')[3].text.strip().split()
                scale += 's' if scale[-1] != 's' else ''
                params = {scale: -int(value)}
                # logging.info('scale = {0}'.format(params))
                uploaded_at = arrow.utcnow().replace(**params)
                item['uploaded_at'] = uploaded_at.datetime.replace(tzinfo=None)
                item['uploaded_week'] = int(item['uploaded_at'].strftime("%U"))

                # size
                details_size_split = row.find_all('td')[1].text.replace(u"\xa0", u" ").strip().split(' ')
                details_size_mul = 9 if 'GB' in details_size_split[1] else (6 if 'MB' in details_size_split[1] else (3 if 'KB' in details_size_split[1] else 0))
                item['size'] = int((float(details_size_split[0])) * 10**details_size_mul)

                item['uploader'] = row.find('div', class_='torrentname').span.a.text

                item['seeders'] = int(row.find_all('td')[4].text)
                item['leechers'] = int(row.find_all('td')[5].text)

                # save
                match_group = re.match(self.RE_TID, item['url']).groups(0)
                item_key = ndb.Key('Torrent', match_group[0])
                torrent = item_key.get()
                if not torrent:
                    torrent = Torrent(key=item_key)
                torrent.populate(**item)
                torrent.series_complete = is_complete

                # extract series
                if torrent.category_code == 205:
                    series.parseSeries(torrent)

                torrent.put()
                logging.info('Torrent {0}'.format(torrent))
            except Exception as e:
                logging.exception(e)
