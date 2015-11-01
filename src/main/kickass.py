import logging
from google.appengine.ext import ndb
from google.appengine.api import mail, urlfetch, taskqueue
from src.main.models import Torrent, UserTorrent
from bs4 import BeautifulSoup
import arrow
import re


class Kickass():

    RE_TID = re.compile('.*-(t[0-9]*)\.html')
    URL_BASE = 'http://kickasstorrent.ytsre.net'
    GROUPS = [
        {'code': 100, 'name': 'Audio', 'categories': [
            # {'code': 101, 'name': 'Music', 'pages': 2},
            {'code': 102, 'name': 'AudioBooks', 'pages': 3, 'url': 'audio-books'},
        ]},
        {'code': 600, 'name': 'Other', 'categories': [
            {'code': 601, 'name': 'eBooks', 'pages': 2, 'url': 'ebooks'},
        ]},
        {'code': 300, 'name': 'Applications', 'categories': [
            {'code': 301, 'name': 'Windows', 'pages': 2, 'url': 'windows'},
            # {'code': 302, 'name': 'Mac', 'pages': 1},
        ]},
        {'code': 400, 'name': 'Games', 'categories': [
            {'code': 401, 'name': 'PC Games', 'pages': 2, 'url': 'windows-games'},
        ]},
        {'code': 200, 'name': 'Video', 'categories': [
            {'code': 209, 'name': '3D', 'pages': 1, 'url': '3d-movies'},
            {'code': 207, 'name': 'HD Movies', 'pages': 6, 'url': 'highres-movies'},
            {'code': 205, 'name': 'TV Shows', 'pages': 12, 'url': 'tv'},
        ]},
    ]


    def __init__(self):
        urlfetch.set_default_fetch_deadline(60)


    def scrape(self):
        logging.info('Kickass: scrape: started')
        for group in self.GROUPS:
            logging.info('Kickass: scrape: Group = {}'.format(len(group)))
            for category in group['categories']:
                params = {
                    'group_code': group['code'],
                    'group_name': group['name'],
                    'category_code': category['code'],
                    'category_name': category['name'],
                    'url': category['url'],
                    'pages': category['pages'],
                    'p': 1,
                }
                taskqueue.add(url='/scrape/kickasspage', params=params)
                logging.info('Kickass: taskqueue: {}'.format(params))

        logging.info('Kickass: scraping tasks created')


    def scrapePage(self, group_code, group_name, category_code, category_name, url_section, pages, p):
        logging.info('Kickass: scrapePage: {}'.format(group_code))
        logging.info('Kickass: scrapePage: {}'.format(group_name))
        logging.info('Kickass: scrapePage: {}'.format(category_code))
        logging.info('Kickass: scrapePage: {}'.format(category_name))
        logging.info('Kickass: scrapePage: {}'.format(url_section))
        logging.info('Kickass: scrapePage: {}'.format(pages))
        logging.info('Kickass: scrapePage: {}'.format(p))

        # 3 tries to scrape page
        rows = []
        url = '{}/{}/{}/'.format(self.URL_BASE, url_section, p)
        logging.info('Kickass: scrapePage: url {}'.format(url))
        for _ in xrange(3):
            try:
                res = urlfetch.fetch(url)
                # logging.info('res {0}'.format(res.content))

                html = BeautifulSoup(res.content, 'html.parser')
                rows = html.find('table', class_='data').find_all('tr')[2:]
            except:
                logging.error('Kickass: scrapePage: could not scrape with try {}'.format(_))
            else:
                break
        logging.info('Kickass: scrapePage: found {} in table'.format(len(rows)))

        if rows:
            self.parseRows({
                'group_code': group_code,
                'group_name': group_name,
                'category_code': category_code,
                'category_name': category_name,
            }, rows)

            # scrape next page
            params = {
                'group_code': group_code,
                'group_name': group_name,
                'category_code': category_code,
                'category_name': category_name,
                'url': url_section,
                'pages': pages,
                'p': p + 1,
            }
            if params['p'] <= params['pages']:
                taskqueue.add(url='/scrape/kickasspage', params=params)
                logging.info('Kickass: taskqueue: {}'.format(params))

        else:
            mail.send_mail(
                sender='jacoj82@gmail.com',
                to='jacoj82@gmail.com',
                subject="Torrent scraping failed",
                body='Could not scrape {}'.format(url),
            )



    def parseRows(self, item, rows):
        logging.info('[Kickass] parseRows {} rows...'.format(len(rows)))
        for row in rows:
            try:
                link = row.find('a', class_='cellMainLink')
                item['title'] = link.text
                item['url'] = '{}{}'.format(self.URL_BASE, link['href'].encode('utf-8'))
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
                torrent = Torrent.get_or_insert(match_group[0], **item)
                logging.debug('Torrent {}'.format(torrent))

            except Exception as e:
                logging.exception(e)
                mail.send_mail(
                    sender='jacoj82@gmail.com',
                    to='jacoj82@gmail.com',
                    subject="Torrent saving failed",
                    body=e.message,
                )

        logging.info('{} torrents scraped in {}'.format(len(rows), item['category_name']))
