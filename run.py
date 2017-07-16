import re
import shelve
import subprocess
from datetime import datetime, timedelta
from operator import itemgetter
from time import sleep

import arrow
import requests
from bs4 import BeautifulSoup
from terminaltables import AsciiTable

host = 'https://thepiratebay.org'
url_browse = '{host}/browse/{code}/{p}/7/0'

CATEGORIES = [
    {'code': '205', 'name': 'TV Shows', 'pages': 10},
    {'code': '207', 'name': 'HD Movies', 'pages': 4},
]

PIRATES = [
    'SVA', 'BATSHIT', 'DEFLATE', 'BATV', 'Ebi', 'FLEET', 'FS', 'PLUTONiUM', 'AFG', 'KILLERS', 'ZLY', 'FUM', 'LOL', 'HEEL', 'PROPER', 'RARBG', 'RiddlerA', 'ORGANiC',
    'MkvCage', 'JYK', 'YIFY', 'ShAaNiG', 'M2Tv', 'Hon3y', 'EVO', 'OHE', 'FGT', 'ETRG', 'Ozlem',
]


def scrape(db):
    """Scrape categories"""
    hours_ago = datetime.now() + timedelta(hours=-4)
    for cat in CATEGORIES:
        db_cat = db.get(cat['code'], {'torrents': {}, 'scraped_at': datetime(2000, 1, 1)})
        if db_cat['scraped_at'] < hours_ago:
            for p in range(cat['pages']):
                scrape_page(db_cat['torrents'], cat, p)
                # break
            db_cat['scraped_at'] = datetime.now()
            db[cat['code']] = db_cat


def scrape_page(db_cat, cat, p):
    print('scraping {} page {}'.format(cat['name'], p))

    # 3 tries to scrape page
    rows = None
    for n in range(3):
        try:
            url = url_browse.format(host=host, code=cat['code'], p=p)
            res = requests.get(url)
            # logging.info('res {0}'.format(res.content))

            html = BeautifulSoup(res.content, 'html.parser')
            rows = html.find('table', id='searchResult').find_all('tr')[1:-1]
        except:
            print('Could not scrape with try {}'.format(n))
            sleep(n)
        else:
            break

    if not rows:
        raise ValueError('Expected rows to parse')

    for row in rows:
        # parse
        item = parse(cat, row)

        # extract series
        if item['category'] == '205':
            parse_series(item)

        # save
        db_cat[item['guid']] = item
        # logging.info('Torrent: {}'.format(torrent.title.encode('utf-8')))


def parse(cat, row):
    item = {'category': cat['code']}

    # logging.debug('row html {0}'.format(row))
    row_top = row.find('div', class_='detName')

    # guid
    grps = re.search('/(\d+)/', row_top.find('a')['href'])
    item['guid'] = grps.groups(0)[0]

    # title
    item['title'] = row_top.find('a').text

    # pirate
    pirate = ''
    for pirate_name in PIRATES:
        if pirate_name in item['title']:
            pirate = pirate_name
            break
    else:
        print('Pirate? {}'.format(item['title']))
    item['pirate'] = pirate

    # url
    item['url'] = row_top.find('a')['href']

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


def parse_series(torrent):
    # logging.info('parsing {0}...'.format(torrent.title.encode('utf-8')))

    # plain and simple e.g. xxx S##E##
    title_groups = re.match(r'(.*)\s(s\d{1,2})(e\d{1,2})\s', torrent['title'].replace('.', ' ').strip(), re.I)
    if title_groups is not None:
        # print('series and episode found {0}'.format(title_groups.groups()))
        torrent['series_title'] = title_groups.group(1)
        torrent['series_season'] = int(title_groups.group(2)[1:])
        torrent['series_episode'] = int(title_groups.group(3)[1:])
        # msg = '[200] {0} S{1} E{2}'.format(torrent['series_title'].encode('utf-8'), torrent['series_season'], torrent['series_episode'])
    else:
        # logging.info('series and episode not found')

        # only episode given e.g. xxx E###
        title_groups = re.match(r'(.*)\s(e\d{1,3})\s', torrent['title'].replace('.', ' ').strip(), re.I)
        if title_groups is not None:
            # logging.info('only episode found')
            torrent['series_title'] = title_groups.group(1).replace('.', ' ').strip()
            torrent['series_season'] = None
            torrent['series_episode'] = int(title_groups.group(2)[1:])
            # msg = '[200] {0} E{1}'.format(torrent['series_title'].encode('utf-8'), torrent['series_episode'])
        else:
            # logging.info('only episode not found')

            # simple version e.g. ##x##_
            title_groups = re.match(r'(.*)(\d{1,2})x(\d{1,2})\s', torrent['title'].replace('.', ' ').strip(), re.I)
            if title_groups is not None:
                # logging.info('series x episode found')
                torrent['series_title'] = title_groups.group(1).replace('.', ' ').strip()
                torrent['series_season'] = int(title_groups.group(2))
                torrent['series_episode'] = int(title_groups.group(3))
                # msg = '[200] <= {0} S{1} E{2}'.format(torrent['series_title'].encode('utf-8'), torrent['series_season'], torrent['series_episode'])
            else:
                # logging.info('simple version not found')

                # pilot?
                title_groups = re.match(r'(.*)(-pilot)', torrent['title'].replace('.', ' ').strip(), re.I)
                if title_groups is not None:
                    # logging.info('pilot episode found')
                    torrent['series_title'] = title_groups.group(1).replace('.', ' ').strip()
                    torrent['series_season'] = 1
                    torrent['series_episode'] = 1
                    # msg = '[200] <= {0} S{1} E{2}'.format(torrent['series_title'].encode('utf-8'), torrent['series_season'], torrent['series_episode'])
                else:
                    # logging.info('absolutely not found')
                    print('series? {}'.format(torrent['title']))


def main(db):

    scrape(db)

    v = None
    while v != 'x':
        print('Menu:')
        menu = [
            ['Key', 'Choice'],
            ['q', 'all series'],
            ['w', 'new series'],
            ['a', 'all movies'],
            ['s', 'new movies'],
            ['z', 'all downloaded'],
            ['x', 'Exit'],
        ]
        print(AsciiTable(menu).table)

        if v == 'q':
            db_cat = db['205']
            cat_torrents = db_cat['torrents']
            torrents = list(cat_torrents.values())
            torrents.sort(key=itemgetter('title'))
            print('\nAll {} shows'.format(len(torrents)))
            data = [['guid', '', 'Series', 'S', 'E', 'Seeders', 'Age', 'Uploader']] + [
                [t['guid'], 'Y' if t.get('downloaded_at') else '',
                 t.get('series_title', t['title']), t.get('series_season', ''), t.get('series_episode', ''),
                 t['seeders'], arrow.get(t['uploaded_at']).humanize(), t['uploader']]
                for t in torrents]
            print(AsciiTable(data).table)

        if v == 'w':
            db_cat = db['205']
            cat_torrents = db_cat['torrents']
            torrents = list(cat_torrents.values())
            weeks_ago = datetime.now() + timedelta(days=-16)
            torrents = [t for t in torrents if t['uploaded_at'] > weeks_ago]
            torrents.sort(key=itemgetter('uploaded_at'), reverse=True)
            torrents.sort(key=itemgetter('title'), reverse=True)
            # torrents.sort(key=itemgetter('series_season'), reverse=True)
            # torrents.sort(key=itemgetter('series_title'), reverse=True)
            print('\nNew {} episodes'.format(len(torrents)))
            data = [['guid', '', 'Series', 'S', 'E', 'Seeders', 'Age', 'Uploader']] + [
                [t['guid'], 'Y' if t.get('downloaded_at') else '',
                 t.get('series_title', t['title']), t.get('series_season', ''), t.get('series_episode', ''),
                 t['seeders'], arrow.get(t['uploaded_at']).humanize(), t['uploader']]
                for t in torrents]
            print(AsciiTable(data).table)

        if v == 'a':
            db_cat = db['207']
            cat_torrents = db_cat['torrents']
            torrents = list(cat_torrents.values())
            torrents.sort(key=itemgetter('title'))
            print('\nAll {} movies'.format(len(torrents)))
            data = [['guid', '', 'Title', 'Pirate', 'Seeders', 'Age', 'Uploader']] + [
                [t['guid'], 'Y' if t.get('downloaded_at') else '', t['title'], t['pirate'], t['seeders'],
                 arrow.get(t['uploaded_at']).humanize(), t['uploader']]
                for t in torrents]
            print(AsciiTable(data).table)

        if v == 's':
            db_cat = db['207']
            cat_torrents = db_cat['torrents']
            torrents = list(cat_torrents.values())
            weeks_ago = datetime.now() + timedelta(days=-16)
            torrents = [t for t in torrents if t['uploaded_at'] > weeks_ago]
            torrents.sort(key=itemgetter('seeders'), reverse=True)
            print('\nNew {} movies'.format(len(torrents)))
            data = [['guid', '', 'Title', 'Pirate', 'Seeders', 'Age', 'Uploader']] + [
                [t['guid'], 'Y' if t.get('downloaded_at') else '',
                 t['title'], t['pirate'], t['seeders'],
                 arrow.get(t['uploaded_at']).humanize(), t['uploader']]
                for t in torrents]
            print(AsciiTable(data).table)

        if v == 'z':
            torrents = list(db['205']['torrents'].values()) + list(db['207']['torrents'].values())
            torrents = [t for t in torrents if t.get('downloaded_at')]
            torrents.sort(key=itemgetter('downloaded_at'), reverse=True)
            print('\nAll {} downloaded'.format(len(torrents)))
            print(AsciiTable([[t['guid'], t['title']] for t in torrents]).table)


        res = input('\n> ')
        if res in ['x', 'q', 'w', 'e', 'a', 's', 'z']:
            v = res
        else:
            try:
                int(res)
            except ValueError:
                pass
            else:
                torrent = cat_torrents[res]
                if torrent.get('downloaded_at'):
                    del torrent['downloaded_at']
                else:
                    subprocess.Popen(['open', torrent['magnet']])
                    torrent['downloaded_at'] = datetime.now()


if __name__ == '__main__':
    with shelve.open('data.shlv', writeback=True) as db:
        main(db)
