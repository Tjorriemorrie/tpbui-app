import argparse
import re
import sqlite3
from datetime import datetime, timedelta, date
from operator import itemgetter

import arrow
import requests
from bs4 import BeautifulSoup
from dateutil.parser import parser as parser_
from requests.adapters import HTTPAdapter
from terminaltables import AsciiTable
from urllib3 import Retry

HOST = 'https://www.realestate.com.au'
URLS = {
    # '2146 toongabbie': '/rent/property-house-between-500-625-in-nsw+2146/list-1?includeSurrounding=false',
    '2147 seven hills': '/rent/property-house-between-500-625-in-nsw+2147/list-1?includeSurrounding=false',
    # '2148 blacktown': '/rent/property-house-between-500-625-in-nsw+2148/list-1?includeSurrounding=false',
    # 2150 parramatta x
    # 2151 north rocks x
    '2152 northmead': '/rent/property-house-between-500-625-in-nsw+2152/list-1?includeSurrounding=false',
    '2153 bella vista/baulkham hills': '/rent/property-house-between-500-625-in-nsw+2153/list-1?includeSurrounding=false',
    '2154 castle hill': '/rent/property-house-between-500-625-in-nsw+2154/list-1?includeSurrounding=false',
    '2155 rouse hill': '/rent/property-house-between-500-625-in-nsw+2155/list-1?includeSurrounding=false',
    '2156 annangrove/glenhaven': '/rent/property-house-between-500-625-in-nsw+2156/list-1?includeSurrounding=false',
    '2158 dural': '/rent/property-house-between-500-625-in-nsw+2158/list-1?includeSurrounding=false',
    # '2762 schofields': '/rent/property-house-between-500-625-in-nsw+2762/list-1?includeSurrounding=false',
    '2763 acacia gardens': '/rent/property-house-between-500-625-in-nsw+2763/list-1?includeSurrounding=false',
    # 2767 woodcroft x
    '2768 glenwood (stanhope)': '/rent/property-house-between-500-625-in-nsw+2768/list-1?includeSurrounding=false',
    # '2769 the ponds': '/rent/property-house-between-500-625-in-nsw+2769/list-1?includeSurrounding=false',
}

db = sqlite3.connect('realestate.sqlite')


def main(skip_scrape=False, reload_zero=False):

    if reload_zero:
        reload_zero_rated()

    if not skip_scrape:
        scrape()

    show()


def show():
    listings = load_data()
    listings.sort(key=itemgetter('price'), reverse=True)
    listings.sort(key=itemgetter('rating'))

    # not found
    not_founds = [l for l in listings if l['not_found'] >= 3]
    single_cars = [l for l in listings if l['not_found'] < 3 and int(l['cars']) < 2]
    main = [l for l in listings if l['not_found'] < 3 and int(l['cars']) >= 2]

    print_listings_table('Not found', not_founds)
    print_listings_table('Single ports', single_cars)
    print_listings_table('Main', main)

    # yesterday = datetime.now() - timedelta(days=1)
    # midnight = arrow.get(yesterday.year, yesterday.month, yesterday.day)

    # # known
    # known = [l for l in listings if not l['open_at'] and l['added_at'] < midnight]
    # print_listings_table('Known', known)
    #
    # # new
    # new = [l for l in listings if not l['open_at'] and l['added_at'] >= midnight]
    # new.sort(key=itemgetter('price'), reverse=True)
    # new.sort(key=itemgetter('rating'))
    # print_listings_table('New', new)
    #
    # # opened
    # opened = [l for l in listings if l['open_at']]
    # opened.sort(key=itemgetter('price'), reverse=True)
    # opened.sort(key=itemgetter('rating'))
    # print_listings_table('Opened', opened)

    res = input('\n> ')
    id, rating = res.split()
    save_rating(id, rating)
    show()


def print_listings_table(header, data):
    if not data:
        return

    print(f'{header}:')
    rows = [['id', '', 'Price', 'Address', 'R - B - C', 'Open day', 'Days listed', 'URL', '404']]
    for item in data:
        rows.append([
            item['id'],
            item['rating'],
            item['price'],
            item['address'],
            f'{item["bedrooms"]} - {item["bathrooms"]} - {item["cars"]}',
            item['open_at'].strftime('%a %d %b') if item['open_at'] else '',
            (arrow.utcnow() - item['added_at']).days,
            f'{HOST}{item["url"]}',
            item['not_found'],
        ])
    print(AsciiTable(rows).table)


def scrape():
    set_all_not_found()
    for loc, url in URLS.items():
        print(f'scraping {loc}')
        scrape_page(url)
    remove_marked()


def make_request(url):
    print('making request to {}'.format(url))
    s = requests.Session()
    retries = Retry(total=20, backoff_factor=2, status_forcelist=[502, 503, 504])
    s.mount('https://', HTTPAdapter(max_retries=retries))
    return s.get(url)


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

    articles = html.find(id='wrapper').find_all('article', class_='results-card')
    # exit(print(articles[0]))

    parser = parser_()
    for article in articles:
        # url
        href = article.find('a', class_='residential-card__details-link').get('href')

        # address
        address = article.find('a', class_='residential-card__details-link').text.title()

        # price
        try:
            price_text = article.find('div', class_='residential-card__price').text
            price = re.findall(r'\$(\d+)', price_text)[0]
        except (IndexError, AttributeError):
            continue
            # exit(print(f'Price? {price_text}'))

        features = article.find('ul', class_='general-features')
        try:
            bedrooms = int(features.find('span', class_='general-features__beds').text)
        except AttributeError:
            bedrooms = 0
        try:
            bathrooms = int(features.find('span', class_='general-features__baths').text)
        except AttributeError:
            bathrooms = 0
        try:
            cars = int(features.find('span', class_='general-features__cars').text)
        except AttributeError:
            cars = 0

        try:
            open_at_text = article.find('span', class_='inspection__long-label').text
            open_at = open_at_text.lstrip('Open ')
            if open_at.startswith('today'):
                time_day = datetime.now()
                open_at = open_at.replace('today', time_day.strftime("%Y-%m-%d"))
            if open_at.startswith('tomorrow'):
                time_day = datetime.now() + timedelta(days=1)
                open_at = open_at.replace('tomorrow', time_day.strftime("%Y-%m-%d"))
            open_at = parser.parse(open_at)
            open_at = open_at.strftime('%Y-%m-%d %H:%M')
        except AttributeError:
            open_at = ''

        item = {
            'url': href,
            'address': address,
            'price': price,
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'cars': cars,
            'new': False,
            'open_at': open_at,
            'added_at': datetime.now().strftime('%Y-%m-%d'),
            'rating': 100,
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


def set_all_not_found():
    c = db.cursor()
    c.execute('UPDATE properties SET not_found=not_found + 1')
    db.commit()
    print(f'Rows not found incremented')


def remove_marked():
    c = db.cursor()
    c.execute('DELETE FROM properties WHERE not_found > 28')
    print(f'Removed properties!')
    db.commit()


def save_rating(id_, rating):
    c = db.cursor()
    c.execute(f'UPDATE properties SET rating={int(rating)} WHERE id={int(id_)}')
    print(f'Set property {id_} to rating {rating}')
    db.commit()


def save_data(data):
    c = db.cursor()
    for item in data:
        rows = c.execute(f'SELECT id FROM properties WHERE address="{item["address"]}"').fetchall()
        if rows:
            c.execute(f'UPDATE properties SET new="{item["new"]}", open_at="{item["open_at"]}", '
                      f'price="{item["price"]}", not_found=0 WHERE id={rows[0][0]}')
        else:
            c.execute(
                'INSERT INTO properties (url, address, price, bedrooms, bathrooms, cars, new, open_at, added_at, rating, not_found) '
                'VALUES("{url}", "{address}", "{price}", "{bedrooms}", {bathrooms}, {cars}, "{new}", "{open_at}", "{added_at}", "{rating}", 0)'.format(
                 **item))
    db.commit()


def load_data():
    c = db.cursor()
    selection = 'SELECT id, url, address, price, bedrooms, bathrooms, cars, new, open_at, added_at, rating, not_found' \
                ' FROM properties'
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
        'added_at': arrow.get(r[9]),
        'rating': r[10],
        'not_found': r[11],
    } for r in rows]
    data.sort(key=itemgetter('rating'))
    return data


def reload_zero_rated():
    c = db.cursor()
    c.execute('UPDATE properties SET rating = 10 WHERE rating = 0')
    db.commit()
    print(f'Zero rated rows reset')


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
            added_at TEXT,
            rating INTEGER,
            not_found INTEGER
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
    parser.add_argument('--reload', dest='reload', action='store_true',
                        help='Reload 0 rated')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = get_args()
    if args.setup:
        setup()
    else:
        main(args.skip_scrape, args.reload)
