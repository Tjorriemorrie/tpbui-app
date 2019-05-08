import argparse
import difflib
import re
import sqlite3
import subprocess
import sys
import time
import webbrowser
from datetime import datetime, timedelta
from operator import itemgetter

import arrow
import requests
from bs4 import BeautifulSoup
from dateutil.parser import parser as parser_
from requests.adapters import HTTPAdapter
from terminaltables import AsciiTable
from urllib3 import Retry

HOST = 'https://www.realestate.com.au'
URL_600 = '/rent/between-0-600-in-the+hills,+nsw/list-1'
# TELEVISION = 'sort-sub/41/{}/desc'
# TV_PAGES = 25
# MOVIES = 'sort-sub/42/{}/desc'
# MOVIE_PAGES = 25
# TRENDING = 'trending/w'

db = sqlite3.connect('realestate.sqlite')


TEN_DAYS_AGO = datetime.now() + timedelta(days=-10)
SEVEN_DAYS_AGO = datetime.now() + timedelta(days=-7)
MENU = {
    'q': ['category = "tv"'],
    'w': ['category = "tv"', 'uploaded_at > "{}"'.format(SEVEN_DAYS_AGO.strftime('%Y-%m-%d'))],
    'a': ['category = "movies"'],
    's': ['category = "movies"', 'uploaded_at > "{}"'.format(TEN_DAYS_AGO.strftime('%Y-%m-%d'))],
}


def main(skip_scrape=False):

    if not skip_scrape:
        scrape()

    listings = load_data()

    # removed
    removed = [l for l in listings if l['removed']]
    print_listings_table('Removed', removed)

    yesterday = datetime.now() - timedelta(days=1)
    midnight = arrow.get(yesterday.year, yesterday.month, yesterday.day)

    # known
    known = [l for l in listings if not l['open_at'] and l['added_at'] < midnight]
    print_listings_table('Known', known)

    # new
    new = [l for l in listings if not l['open_at'] and l['added_at'] >= midnight]
    print_listings_table('New', new)

    # opened
    opened = [l for l in listings if l['open_at']]
    opened.sort(key=itemgetter('open_at'))
    print_listings_table('Opened', opened)


def print_listings_table(header, data):
    if not data:
        return

    print(f'{header}:')
    rows = [['id', 'Price', 'Address', 'R - B - C', 'Open day', 'Added at', 'URL']]
    for item in data:
        rows.append([
            item['id'],
            item['price'],
            item['address'],
            f'{item["bedrooms"]} - {item["bathrooms"]} - {item["cars"]}',
            item['open_at'].strftime('%a %d %b') if item['open_at'] else '',
            item['added_at'].humanize(),
            f'{HOST}{item["url"]}',
        ])
    print(AsciiTable(rows).table)
        #
        # res = input('\n> ')
        # if res in MENU or res == 'x':
        #     v = res
        #     continue
        #
        # try:
        #     int(res)
        # except ValueError:
        #     pass
        # else:
        #     torrent = [t for t in torrents if t['id'] == int(res)][0]
        #     url = HOST + torrent['web']
        #     print(url)
        #     if sys.platform == 'darwin':  # in case of OS X
        #         subprocess.Popen(['open', url])
        #     else:
        #         webbrowser.open_new_tab(url)


def scrape():
    set_all_removed()
    scrape_page(URL_600)


def make_request(url):
    print('making request to {}'.format(url))
    s = requests.Session()
    retries = Retry(total=20, backoff_factor=2, status_forcelist=[502, 503, 504])
    s.mount('https://', HTTPAdapter(max_retries=retries))
    try:
        return s.get(url)
    except Exception:
        pass


def scrape_page(url):
    data = []

    headers = {
        'User-agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0'
    }
    res = requests.get(f'{HOST}{url}', headers=headers)
    res.raise_for_status()

    html = BeautifulSoup(res.content, 'html.parser')
    if '403 - Permission Denied' in html:
        raise Exception('Permission denied')
    # exit(print(html))

    articles = html.find(id='searchResultsTbl').find_all('article')
    # exit(print(articles[0]))

    parser = parser_()
    for article in articles:
        listing_info = article.find('div', class_='listingInfo')

        # url
        href = listing_info.find('a', class_='name').get('href')

        # address
        address = listing_info.find('a', class_='name').text

        # price
        try:
            price_text = listing_info.find('p', class_='priceText').text
            price = re.findall(r'\$(\d+)', price_text)[0]
        except (IndexError, AttributeError):
            continue
            # exit(print(f'Price? {price_text}'))

        features = listing_info.find('dl', class_='rui-property-features').find_all('dd')
        bedrooms = int(features[0].text)
        try:
            bathrooms = int(features[1].text)
        except IndexError:
            bathrooms = 0
        try:
            cars = int(features[2].text)
        except IndexError:
            cars = 0

        badges = html.find('ul', class_='badges')
        try:
            badges.find('li', class_='newListing')
            new = True
        except AttributeError:
            new = False

        try:
            open_at_text = badges.find('li', class_='openTime').text
            open_at = parser.parse(open_at_text.lstrip('Open '))
            open_at = open_at.strftime('%Y-%m-%d')
        except AttributeError:
            open_at = ''

        item = {
            'url': href,
            'address': address,
            'price': price,
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'cars': cars,
            'new': new,
            'open_at': open_at,
            'added_at': datetime.now().strftime('%Y-%m-%d'),
        }
        data.append(item)
    # exit(print(data))
    print(f'finished scraping {url}')

    # save
    save_data(data)

    # go to next page
    try:
        next_link = html.find('li', class_='nextLink').find('a').get('href')
        scrape_page(next_link)
    except AttributeError:
        pass


def set_all_removed():
    c = db.cursor()
    c.execute('UPDATE properties SET removed=1')
    db.commit()
    print(f'Rows updated to removed')


def save_data(data):
    c = db.cursor()
    for item in data:
        rows = c.execute(f'SELECT id FROM properties WHERE url="{item["url"]}"').fetchall()
        if rows:
            c.execute(f'UPDATE properties SET new="{item["new"]}", open_at="{item["open_at"]}", '
                      f'price="{item["price"]}", removed=0 WHERE id={rows[0][0]}')
        else:
            c.execute(
                'INSERT INTO properties (url, address, price, bedrooms, bathrooms, cars, new, open_at, removed, added_at) '
                'VALUES("{url}", "{address}", "{price}", "{bedrooms}", {bathrooms}, {cars}, "{new}", "{open_at}", 0, "{added_at}")'.format(
                 **item))
    db.commit()


def load_data():
    c = db.cursor()
    selection = 'SELECT id, url, address, price, bedrooms, bathrooms, cars, new, open_at, removed, added_at FROM properties'
    rows = c.execute(selection).fetchall()
    data = [{
        'id': r[0],
        'url': r[1],
        'address': r[2],
        'price': r[3],
        'bedrooms': r[4],
        'bathrooms': r[5],
        'cars': r[6],
        'new': r[7],
        'open_at': arrow.get(r[8]) if r[8] else '',
        'removed': r[9],
        'added_at': arrow.get(r[10]),
    } for r in rows]
    data.sort(key=itemgetter('price'))
    return data


def setup():
    print('setting up...')
    cursor = db.cursor()
    cursor.execute('''
        CREATE TABLE properties(
            id INTEGER PRIMARY KEY,
            url TEXT,
            address TEXT,
            price INTEGER,
            bedrooms INTEGER,
            bathrooms INTEGER,
            cars TEXT,
            new INTEGER,
            open_at TEXT,
            removed INTEGER,
            added_at TEXT
        )
    ''')
    db.commit()
    print('done')


def get_args():
    parser = argparse.ArgumentParser(description='Scrape realestate')
    parser.add_argument('--setup', dest='setup', action='store_true',
                        help='Recreate database.')
    parser.add_argument('--skip', dest='skip_scrape', action='store_true',
                        help='Skip scraping')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = get_args()
    if args.setup:
        setup()
    else:
        main(args.skip_scrape)
