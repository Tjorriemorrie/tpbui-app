import logging
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from google.appengine.api import mail, urlfetch
from google.appengine.ext import ndb
from series import extract
from src.main.models import Torrent
from time import sleep


class PirateBay():

    HOST = 'http://thepiratebay.org'

    GROUPS = [
        # {'code': 100, 'name': 'Audio', 'categories': [
            # {'code': 101, 'name': 'Music', 'pages': 2},
            # {'code': 102, 'name': 'AudioBooks', 'pages': 2},
        # ]},
        # {'code': 600, 'name': 'Other', 'categories': [
        #     {'code': 601, 'name': 'eBooks', 'pages': 2},
        # ]},
        # {'code': 300, 'name': 'Applications', 'categories': [
        #     {'code': 301, 'name': 'Windows', 'pages': 2},
        #     {'code': 302, 'name': 'Mac', 'pages': 1},
        # ]},
        {'code': 400, 'name': 'Games', 'categories': [
            {'code': 401, 'name': 'PC Games', 'pages': 1},
        ]},
        {'code': 200, 'name': 'Video', 'categories': [
            {'code': 209, 'name': '3D', 'pages': 1},
            {'code': 207, 'name': 'HD Movies', 'pages': 5},
            {'code': 205, 'name': 'TV Shows', 'pages': 10},
        ]},
    ]

    def __init__(self):
        urlfetch.set_default_fetch_deadline(60)

    def scrape(self):
        # scrape site
        body = ''
        for group in self.GROUPS:
            for category in group['categories']:
                n = 0
                for p in range(category['pages']):
                    try:
                        n += self.scrapePage(group, category, p)
                    except Exception as e:
                        logging.exception(e)
                        n = e.message
                        break
                body += '{} - {}: {} from {} pages\n'.format(
                    group['name'], category['name'], n, category['pages']
                )

        # notify scrape results
        logging.info('{}'.format(body))
        mail.send_mail(
            sender='jacoj82@gmail.com',
            to='jacoj82@gmail.com',
            subject="TPB scraping",
            body=body,
        )

    def scrapePage(self, group, category, p):
        logging.info('PirateBay: scrapePage: {} {} {}'.format(
            group['name'], category['name'], p)
        )

        # 3 tries to scrape page
        rows = None
        for n in xrange(3):
            try:
                url = '{2}/browse/{0}/{1}/7/0'.format(category['code'], p, self.HOST)
                logging.info('PirateBay: scrapePage: url {0}'.format(url))
                res = urlfetch.fetch(url)
                # logging.info('res {0}'.format(res.content))

                html = BeautifulSoup(res.content, 'html.parser')
                rows = html.find('table', id='searchResult').find_all('tr')[1:-1]
            except:
                logging.error('Could not scrape with try {0}'.format(n))
                sleep(1)
            else:
                break

        if not rows:
            raise ValueError('Expected rows to parse')

        for row in rows:
            # parse
            item = self.parse(group, category, row)

            # save
            item_key = ndb.Key('Torrent', item['guid'])
            torrent = item_key.get()
            if not torrent:
                torrent = Torrent(key=item_key)
            torrent.populate(**item)

            # extract series
            if torrent.category_code == 205:
                extract(torrent)

            torrent.put()
            logging.info('Torrent: {}'.format(torrent.title.encode('utf-8')))

        return len(rows)

    def parse(self, group, category, row):
        item = {
            'group_code': group['code'],
            'group_name': group['name'],
            'category_code': category['code'],
            'category_name': category['name'],
        }

        # logging.debug('row html {0}'.format(row))
        row_top = row.find('div', class_='detName')

        # guid
        grps = re.search('/(\d+)/', row_top.find('a')['href'])
        item['guid'] = grps.groups(0)[0]

        # title
        item['title'] = row_top.find('a').text

        # url
        item['url'] = '{}{}'.format(self.HOST, row_top.find('a')['href'])

        # magnet
        item['magnet'] = row.find('a', title='Download this torrent using magnet')['href']

        details = row.find('font', class_='detDesc').text
        details_date, details_size, details_uploader = details.split(',')

        # date
        details_date_val = details_date.split(' ', 1)[1].replace(u"\xa0", u" ")
        # logging.info('{}'.format(details_date_val))
        if 'Y-day' in details_date_val:
            details_datetime = datetime.utcnow().replace(hour=int(details_date_val[-5:-3]), minute=int(details_date_val[-2:])) + timedelta(days=-1)
        elif 'Today' in details_date_val:
            details_datetime = datetime.utcnow().replace(hour=int(details_date_val[-5:-3]), minute=int(details_date_val[-2:]))
        elif 'mins ago' in details_date_val:
            details_datetime = datetime.utcnow().replace(minute=int(details_date_val.split(' ')[0]))
        elif ':' in details_date:
            details_datetime = datetime.strptime('{}-{}'.format(datetime.now().year, details_date_val), '%Y-%m-%d %H:%M')
        else:
            details_datetime = datetime.strptime(details_date_val, '%m-%d %Y')
        item['uploaded_at'] = details_datetime.replace(tzinfo=None)
        # logging.info('Date extracted {0} from {1}'.format(item['uploaded_at'], details_date.encode('utf-8')))

        # size
        details_size_split = details_size.replace(u"\xa0", u" ").strip().split(' ')
        details_size_mul = 9 if 'GiB' in details_size_split[2] else (6 if 'MiB' in details_size_split[2] else 3)
        item['size'] = int((float(details_size_split[1])) * 10**details_size_mul)

        # uploader
        item['uploader'] = details_uploader.split(' ')[-1]

        # seeders
        item['seeders'] = int(row.find_all('td')[2].text)

        # leechers
        item['leechers'] = int(row.find_all('td')[3].text)

        # logging.info('item {0}'.format(item))
        return item

    def parseSeries(self, torrent):
        logging.info('parsing {0}...'.format(torrent.title.encode('utf-8')))

        # plain and simple e.g. xxx S##E##
        title_groups = re.match(r'(.*)\s(s\d{1,2})(e\d{1,2})\s', torrent.title.replace('.', ' ').strip(), re.I)
        if title_groups is not None:
            logging.info('series and episode found {0}'.format(title_groups.groups()))
            torrent.series_title = title_groups.group(1)
            torrent.series_season = int(title_groups.group(2)[1:])
            torrent.series_episode = int(title_groups.group(3)[1:])
            torrent.put()
            # pprint(torrent)
            msg = '[200] {0} S{1} E{2}'.format(torrent.series_title.encode('utf-8'), torrent.series_season, torrent.series_episode)
        else:
            logging.info('series and episode not found')

            # only episode given e.g. xxx E###
            title_groups = re.match(r'(.*)\s(e\d{1,3})\s', torrent.title.replace('.', ' ').strip(), re.I)
            if title_groups is not None:
                logging.info('only episode found')
                torrent.series_title = title_groups.group(1).replace('.', ' ').strip()
                torrent.series_season = None
                torrent.series_episode = int(title_groups.group(2)[1:])
                torrent.put()
                # pprint(torrent)
                msg = '[200] {0} E{1}'.format(torrent.series_title.encode('utf-8'), torrent.series_episode)
            else:
                logging.info('only episode not found')

                # simple version e.g. ##x##_
                title_groups = re.match(r'(.*)(\d{1,2})x(\d{1,2})\s', torrent.title.replace('.', ' ').strip(), re.I)
                if title_groups is not None:
                    logging.info('series x episode found')
                    torrent.series_title = title_groups.group(1).replace('.', ' ').strip()
                    torrent.series_season = int(title_groups.group(2))
                    torrent.series_episode = int(title_groups.group(3))
                    torrent.put()
                    # pprint(torrent)
                    msg = '[200] <= {0} S{1} E{2}'.format(torrent.series_title.encode('utf-8'), torrent.series_season, torrent.series_episode)
                else:
                    logging.info('simple version not found')

                    # pilot?
                    title_groups = re.match(r'(.*)(-pilot)', torrent.title.replace('.', ' ').strip(), re.I)
                    if title_groups is not None:
                        logging.info('pilot episode found')
                        torrent.series_title = title_groups.group(1).replace('.', ' ').strip()
                        torrent.series_season = 1
                        torrent.series_episode = 1
                        torrent.put()
                        # pprint(torrent)
                        msg = '[200] <= {0} S{1} E{2}'.format(torrent.series_title.encode('utf-8'), torrent.series_season, torrent.series_episode)
                    else:
                        logging.info('absolutely not found')
                        msg = '[404] <= {0}'.format(torrent.title.encode('utf-8'))
        return msg

    def notify(self, results):
        mail.send_mail(
            sender='jacoj82@gmail.com',
            to='jacoj82@gmail.com',
            subject="Series extracted",
            body='\n'.join(results),
        )
