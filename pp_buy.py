import argparse
import re
import sqlite3
from datetime import datetime, timedelta, date
from operator import itemgetter
from time import sleep

import arrow
import requests
from bs4 import BeautifulSoup
from dateutil.parser import parser as parser_
from requests.adapters import HTTPAdapter
from terminaltables import AsciiTable
from urllib3 import Retry

MIN_SIZE = 100_000
TOP_PRICE = 2_500_000
BEDROOMS = 0
BATHROOMS = 0
GARAGES = 0
HOST = 'https://www.privateproperty.co.za'
URLS = {
    'buy farm hartbeespoortdam': f'/for-sale/north-west/hartbeespoort-dam/74?tp={TOP_PRICE}&bd={BEDROOMS}&ba={BATHROOMS}&ga={GARAGES}&pt=1&si=1706,585,587&page=',
    'buy farm magaliesburg': f'/for-sale/gauteng/west-rand/krugersdorp/840?tp={TOP_PRICE}&bd={BEDROOMS}&ba={BATHROOMS}&ga={GARAGES}&pt=1&si=1704,291,295&page=',
}

db = sqlite3.connect('privateproperty.sqlite')


def main(skip_scrape=False):

    if not skip_scrape:
        scrape()
        remove_unfound()

    show()


def show():
    listings = load_data()
    listings.sort(key=itemgetter('ppu'), reverse=True)
    listings.sort(key=itemgetter('rating'))

    junk = []
    main = []
    for l in listings:
        if l['rating'] < 2:
            junk.append(l)
        else:
            main.append(l)

    print_listings_table('Junk', junk)
    print_listings_table('Main', main)

    res = input('\n> ')
    id, rating = res.split()
    save_rating(id, rating)
    show()


def print_listings_table(header, data):
    if not data:
        return

    print(f'{header}:')
    rows = [['id', '', 'Price', 'PPU', 'Size', 'Address', 'R - B - C', 'Age', 'Website']]
    for item in data:
        rows.append([
            item['id'],
            item['rating'],
            f'R{round(item["price"] / 1_000_000, 2)} mil',
            int(item['ppu']),
            f'{item["size"] // 10000} ha',
            f'[{item["area"]}] {item["address"]}',
            f'{item["bedrooms"]} - {item["bathrooms"]} - {item["cars"]}',
            item['added_at'].humanize(arrow.utcnow()),
            f'{HOST}{item["url"]}',
        ])
    print(AsciiTable(rows).table)


def scrape():
    for loc, url in URLS.items():
        print(f'scraping {loc}')
        scrape_page(url)


def make_request(url):
    print('making request to {}'.format(url))
    s = requests.Session()
    retries = Retry(total=20, backoff_factor=2, status_forcelist=[502, 503, 504])
    s.mount('https://', HTTPAdapter(max_retries=retries))
    return s.get(url)


def handle_number(num):
    try:
        v = int(num)
    except ValueError:
        v = float(num)
    return v


def scrape_page(url, page=1):
    print(f'page {page}...', end='')
    data = []

    headers = {
        'User-agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0'
    }
    res = requests.get(f'{HOST}{url}{page}', headers=headers)
    res.raise_for_status()

    html = BeautifulSoup(res.content, 'html.parser')
    if 'There were no listings' in html.text:
        print('not found')
        return

    listings = html.find_all('a', class_='listingResult')
    # parser = parser_()
    for listing in listings:
        # url
        href = listing.get('href')

        # title
        try:
            title = listing.find('div', class_='title').text
            title_bits = title.split()
            size = float(title_bits.pop(0))
            mul = title_bits.pop(0)
            if mul == 'ha':
                size *= 10000
            category = title_bits.pop(0)
            area = title_bits[1:]
        except ValueError:
            size = 5555
            category = 'Farm'
            area = ''

        # address
        try:
            address = listing.find('div', class_='address').text.title()
        except AttributeError:
            address = ''

        # price
        try:
            price_text = listing.find('div', class_='priceDescription').text
            price = re.findall(r'(\d+)', price_text.replace(' ', ''))[0]
        except (IndexError, AttributeError):
            exit(print(f'Price? {price_text}'))
            continue

        try:
            bedrooms = listing.find('div', class_='bedroom').previous_sibling.previous_sibling.text
        except AttributeError:
            bedrooms = 0
        try:
            bathrooms = listing.find('div', class_='bathroom').previous_sibling.previous_sibling.text
        except AttributeError:
            bathrooms = 0
        try:
            cars = listing.find('div', class_='garage').previous_sibling.previous_sibling.text
        except AttributeError:
            cars = 0

        item = {
            'url': href,
            'size': size,
            'category': category,
            'area': ' '.join(area),
            'address': address,
            'price': price,
            'bedrooms': handle_number(bedrooms),
            'bathrooms': handle_number(bathrooms),
            'cars': handle_number(cars),
            'added_at': datetime.now().strftime('%Y-%m-%d'),
            'updated_at': datetime.now().strftime('%Y-%m-%d'),
            'unfound_at': '',
            'rating': 10,
        }
        data.append(item)

    save_data(data)
    print('saved')
    scrape_page(url, page + 1)


def remove_unfound():
    c = db.cursor()
    unfound_cutoff = datetime.now() - timedelta(days=7)
    result_set = list(c.execute(f'SELECT unfound_at FROM properties WHERE unfound_at < "{unfound_cutoff.strftime("%Y-%m-%d")}" AND unfound_at != ""'))
    if result_set:
        c.execute(f'DELETE FROM properties WHERE unfound_at < "{unfound_cutoff.strftime("%Y-%m-%d")}"')
        db.commit()
        print(f'Removed {result_set[0][0]} properties!')


def save_rating(id_, rating):
    c = db.cursor()
    rating = int(rating)
    if rating not in range(1, 6):
        print(f'Rating not correct', end='')
        for i in range(3):
            print('.')
            sleep(1)
        return
    c.execute(f'UPDATE properties SET rating={int(rating)} WHERE id={int(id_)}')
    print(f'Set property {id_} to rating {rating}')
    db.commit()


def save_data(data):
    c = db.cursor()
    for item in data:
        rows = c.execute(f'SELECT id FROM properties WHERE url="{item["url"]}"').fetchall()
        if rows:
            c.execute(f'UPDATE properties SET '
                      f'price="{item["price"]}", '
                      f'size="{item["size"]}", '
                      f'bedrooms="{item["bedrooms"]}", '
                      f'bathrooms="{item["bathrooms"]}", '
                      f'cars="{item["cars"]}", '
                      f'unfound_at="", '
                      f'updated_at="{item["updated_at"]}" '
                      f'WHERE url="{item["url"]}"')
        else:
            c.execute(
                'INSERT INTO properties (url, size, category, area, address, price, bedrooms, bathrooms, cars, added_at, updated_at, unfound_at, rating) '
                'VALUES("{url}", "{size}", "{category}", "{area}", "{address}", "{price}", "{bedrooms}", {bathrooms}, {cars}, "{added_at}", "{updated_at}", "", "{rating}")'.format(
                 **item))
    db.commit()


def load_data():
    c = db.cursor()
    selection = f'SELECT id, url, size, category, area, address, price, bedrooms, bathrooms, cars, added_at, updated_at, unfound_at, rating' \
                f' FROM properties WHERE size > {MIN_SIZE}'
    rows = c.execute(selection).fetchall()
    data = [{
        'id': r[0],
        'url': r[1],
        'size': r[2],
        'category': r[3],
        'area': r[4],
        'address': r[5],
        'price': r[6],
        'bedrooms': r[7],
        'bathrooms': r[8],
        'cars': r[9],
        'added_at': arrow.get(r[10]),
        'updated_at': arrow.get(r[11]),
        'unfound_at': arrow.get(r[12]) if r[12] else r[12],
        'rating': r[13],
    } for r in rows]

    # add dynamic ratio
    for item in data:
        item['ppu'] = item['price'] / item['size']

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
            size INTEGER,
            category TEXT,
            area TEXT,
            address TEXT,
            price INTEGER,
            bedrooms INTEGER,
            bathrooms INTEGER,
            cars TEXT,
            added_at TEXT,
            updated_at TEXT,
            unfound_at TEXT,
            rating INTEGER
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
