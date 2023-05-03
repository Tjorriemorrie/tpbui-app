import argparse
import re
import sqlite3
from datetime import datetime, timedelta, date
from operator import itemgetter
from random import choice, shuffle

import arrow
import requests
from bs4 import BeautifulSoup
from dateutil.parser import parser as parser_
from requests.adapters import HTTPAdapter
from terminaltables import AsciiTable
from urllib3 import Retry

HOST = 'https://www.privateproperty.co.za'
URLS = {
    # 'harties land': '/for-sale/north-west/hartbeespoort-dam/74?tp=1000000&pt=7'
    'harties farm': '/for-sale/north-west/hartbeespoort-dam/74?tp=2500000&pt=1&si=1706,2314,585,587',
    'krug farm': '/for-sale/gauteng/west-rand/krugersdorp/840?tp=2500000&pt=1&si=1704,291,2659,295,823',
}

db = sqlite3.connect('privateproperty.sqlite')


def main(skip_scrape=False, reload_zero=False):

    if reload_zero:
        reload_zero_rated()

    if not skip_scrape:
        unzero_random()
        scrape()

    show()


def show():
    listings = load_data()
    listings.sort(key=itemgetter('location'))
    listings.sort(key=itemgetter('ppu'), reverse=True)
    listings.sort(key=itemgetter('rating'))

    main = [l for l in listings
            if l['not_found'] < 3
            # and l['structure'] == 'Farm'
    ]

    # exit(dump(main))

    not_founds = [l for l in listings if l['not_found'] >= 3]
    # print_listings_table('Not found', not_founds)

    print_listings_table('Main', main)

    res = input('\n> ')
    id, rating = res.split()
    save_rating(id, rating)
    show()


def dump(listings):
    for l in listings:
        print(f'{l["rating"]} {l["size"] // 1000 / 10}ha R{l["price"]} (R/m2: {l["ppu"]})' )
        print(f'{HOST}{l["url"]}')
        print('')


def print_listings_table(header, data):
    if not data:
        return

    print(f'{header}:')
    rows = [['id', '', 'R/m2', 'Price', 'Size', 'Address', 'Days listed', 'URL', '404']]
    for item in data:
        rows.append([
            item['id'],
            item['rating'],
            item['ppu'],
            item['price'],
            item['size'],
            item['address'] + ', ' + item['location'],
            (arrow.utcnow() - item['added_at']).days,
            f'{HOST}{item["url"]}',
            item['not_found'],
        ])
    print(AsciiTable(rows).table)


def scrape():
    set_all_not_found()
    for loc, url in URLS.items():
        print(f'scraping {loc}: {url}')
        scrape_page(url)
    remove_marked()


def make_request(url):
    print('making request to {}'.format(url))
    s = requests.Session()
    retries = Retry(total=20, backoff_factor=2, status_forcelist=[502, 503, 504])
    s.mount('https://', HTTPAdapter(max_retries=retries))
    return s.get(url)


def scrape_page(url, page=1):
    print(f'page {page}...', end='')
    data = []

    headers = {
        'User-agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0'
    }
    res = requests.get(f'{HOST}{url}&page={page}', headers=headers)
    res.raise_for_status()

    html = BeautifulSoup(res.content, 'html.parser')
    # exit(print(html))

    # no more pages
    if html.find('div', class_='noResultsInnerBox'):
        print('done')
        return

    articles = html.find_all(class_='listingResult row')
    # exit(print(articles[0]))

    parser = parser_()
    for article in articles:
        # url
        href = article.get('href')

        info_holder = article.find('div', class_='infoHolder')
        title = info_holder.find('div', class_='title').text.title().split()

        # address
        try:
            address = info_holder.find('div', class_='address').text.title()
        except AttributeError:
            # print(f'No address for {href}')
            address = 'unknown'

        # structure
        structure = info_holder.find('div', class_='propertyType').text.title()

        # location
        location = title[-1]

        # price
        try:
            price_text = article.find('div', class_='priceDescription').text.replace(' ', '')
            price = re.findall(r'(\d+)', price_text)[0]
        except (IndexError, AttributeError):
            if price_text == 'OnAuction':
                price = '10000'
            else:
                if price_text in ['Sold', 'Price on Application', 'PriceonApplication']:
                    continue
                exit(print(f'Price? {price_text}'))

        # size
        size = title[0]
        if title[1].lower() != 'm²':
            if title[1] == 'Ha':
                size = float(size) * 10000
            else:
                if size in ['Farm']:
                    continue
                exit(print(f'size? {size} {title[1]}'))

        try:
            bedrooms = float(info_holder.find('div', class_='icon bedroom').previous_sibling.previous_sibling.text)
        except AttributeError:
            bedrooms = 0
        try:
            bathrooms = float(info_holder.find('div', class_='icon bathroom').previous_sibling.previous_sibling.text)
        except AttributeError:
            bathrooms = 0
        try:
            cars = float(info_holder.find('div', class_='icon garage').previous_sibling.previous_sibling.text)
        except AttributeError:
            cars = 0

        item = {
            'url': href,
            'structure': structure,
            'address': address,
            'location': location,
            'price': price,
            'size': size,
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'cars': cars,
            'added_at': datetime.now().strftime('%Y-%m-%d'),
            'rating': 100,
        }
        data.append(item)
    # exit(print(data))

    # save
    save_data(data)

    # go to next page
    scrape_page(url, page + 1)


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


def unzero_random():
    c = db.cursor()
    selection = 'SELECT id FROM properties'
    raw = c.execute(selection).fetchall()
    rows = [r[0] for r in raw]
    shuffle(rows)
    sel = rows[:len(rows) // 50]
    ids = ",".join(map(str, sel))
    c.execute(f'UPDATE properties SET rating=100 WHERE id IN ({ids})')
    print(f'Resetted {ids}')


def save_rating(id_, rating):
    c = db.cursor()
    c.execute(f'UPDATE properties SET rating={int(rating)} WHERE id={int(id_)}')
    print(f'Set property {id_} to rating {rating}')
    db.commit()


def save_data(data):
    c = db.cursor()
    for item in data:
        rows = c.execute(f'SELECT id FROM properties WHERE url="{item["url"]}"').fetchall()
        if rows:
            c.execute(f'UPDATE properties SET size="{item["size"]}", price="{item["price"]}", not_found=0 WHERE id={rows[0][0]}')
        else:
            c.execute(
                'INSERT INTO properties (url, structure, address, location, price, size, bedrooms, bathrooms, cars, added_at, rating, not_found) '
                'VALUES("{url}", "{structure}", "{address}", "{location}", "{price}", "{size}", "{bedrooms}", {bathrooms}, {cars}, "{added_at}", "{rating}", 0)'.format(**item))
    db.commit()
    print('saved')


def load_data():
    c = db.cursor()
    selection = 'SELECT id, url, structure, address, location, price, ' \
                'size, bedrooms, bathrooms, cars, added_at, rating, not_found ' \
                'FROM properties'
    rows = c.execute(selection).fetchall()
    data = [{
        'id': r[0],
        'url': r[1],
        'structure': r[2],
        'address': r[3],
        'location': r[4],
        'price': r[5],
        'size': r[6],
        'bedrooms': r[7],
        'bathrooms': r[8],
        'cars': r[9],
        'added_at': arrow.get(r[10]),
        'rating': r[11],
        'not_found': r[12],
    } for r in rows]
    # add price per m2
    for l in data:
        l['ppu'] = l['price'] // l['size']
    # drop zeros
    data = [l for l in data if l['rating']]
    # min size
    data = [l for l in data if l['size'] >= 90000]
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
            structure TEXT,
            address TEXT,
            location TEXT,
            price INTEGER,

            size INTEGER,

            bedrooms TEXT,
            bathrooms TEXT,
            cars TEXT,

            added_at TEXT,
            rating INTEGER,
            not_found INTEGER
        )
    ''')
    db.commit()
    print('done')


def get_args():
    parser = argparse.ArgumentParser(description='Scrape privateproperty')
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
