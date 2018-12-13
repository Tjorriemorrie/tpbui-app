from gevent import monkey
monkey.patch_all()

import sys
import webbrowser
import argparse
import difflib
import gevent
import sqlite3
import subprocess
from datetime import datetime, timedelta

import arrow
import requests
from bs4 import BeautifulSoup
from dateutil.parser import parser as parser_
from requests.adapters import HTTPAdapter
from terminaltables import AsciiTable
from urllib3 import Retry


HOST = 'https://1337x.to'
TELEVISION = 'sort-cat/TV/{}/desc'
TV_PAGES = 50
MOVIES = 'sort-cat/Movies/{}/desc'
MOVIE_PAGES = 50

db = sqlite3.connect('1337x.sqlite')


TEN_DAYS_AGO = datetime.now() + timedelta(days=-10)
MENU = {
    'q': ['category = "tv"'],
    'w': ['category = "tv"', 'uploaded_at > "{}"'.format(TEN_DAYS_AGO.strftime('%Y-%m-%d'))],
    'a': ['category = "movies"'],
    's': ['category = "movies"', 'uploaded_at > "{}"'.format(TEN_DAYS_AGO.strftime('%Y-%m-%d'))],
}


def main(skip_scrape=False):

    if not skip_scrape:
        scrape()

    v = None
    while v != 'x':
        print('Menu:')
        menu = [
            ['Key', 'Choice'],
            ['q', 'all series'],
            ['w', 'new series'],
            ['a', 'all movies'],
            ['s', 'new movies'],
            ['x', 'Exit'],
        ]
        print(AsciiTable(menu).table)

        if v:
            filters = MENU[v]
            torrents = load_data(filters)
            # torrents = make_it_seem_right(torrents)

            data = [['id', 'Title', 'Quality', 'Size', 'Seeders', 'Date', 'Uploader']] + [
                [
                    t['id'], t['title'], t['quality'], t['size'],
                    t['seeders'], arrow.get(t['uploaded_at']).humanize(),
                    t['uploader']
                ] for t in torrents
            ]
            print(AsciiTable(data).table)

        res = input('\n> ')
        if res in MENU or res == 'x':
            v = res
            continue

        try:
            int(res)
        except ValueError:
            pass
        else:
            torrent = [t for t in torrents if t['id'] == int(res)][0]
            url = HOST + torrent['web']
            if sys.platform == 'darwin':  # in case of OS X
                subprocess.Popen(['open', url])
            else:
                webbrowser.open_new_tab(url)


def make_it_seem_right(torrents):
    original_len = len(torrents)
    current = torrents.pop(0)
    by_kind = [current]
    while len(torrents):
        closest = difflib.get_close_matches(current['title'], [t['title'] for t in torrents], n=1)
        if closest:
            current = [t for t in torrents if t['title'] == closest[0]][0]
            torrents = [t for t in torrents if t['title'] != closest[0]]
        else:
            current = torrents.pop(0)
        by_kind.append(current)
    assert len(by_kind) == original_len
    return by_kind


def scrape():
    scrape_television()
    scrape_movies()


def scrape_television():
    jobs = []
    data = []
    for ordering in ['leechers', 'seeders']:
        for page in range(1, TV_PAGES + 1):
            url = '{}/{}/{}/'.format(HOST, TELEVISION.format(ordering), page)
            jobs.append(gevent.spawn(scrape_page, url, data))
    gevent.joinall(jobs)
    save_data('tv', data)


def scrape_movies():
    jobs = []
    data = []
    for ordering in ['leechers', 'seeders']:
        for page in range(1, MOVIE_PAGES + 1):
            url = '{}/{}/{}/'.format(HOST, MOVIES.format(ordering), page)
            jobs.append(gevent.spawn(scrape_page, url, data))
    gevent.joinall(jobs)
    save_data('movies', data)


def make_request(url):
    print('making request to {}'.format(url))
    s = requests.Session()
    retries = Retry(total=20, backoff_factor=2, status_forcelist=[502, 503, 504])
    s.mount('https://', HTTPAdapter(max_retries=retries))
    try:
        return s.get(url)
    except Exception:
        pass


def scrape_page(url, data):
    res = requests.get(url)
    res.raise_for_status()

    html = BeautifulSoup(res.content, 'html.parser')
    rows = html.find('table', class_='table-list').find_all('tr')
    parser = parser_()

    for row in rows[1:]:
        cols = row.find_all('td')

        # quality
        quality = cols[0].find_all('a')[0]
        quality = quality.find('i')['class']
        quality = quality[0].replace('flaticon-', '')

        # title
        title = cols[0].find_all('a')[1]
        title = title.text

        # web
        web = cols[0].find_all('a')[1]
        web = web['href']

        # seeders
        seeders = int(cols[1].text)

        # leechers
        leechers = int(cols[2].text)

        # upload date
        uploaded_at = parser.parse(cols[3].text)
        uploaded_at = uploaded_at.strftime('%Y-%m-%d')

        # size
        size = cols[4].find(text=True)

        # uploader
        uploader = cols[5].text

        item = {
            'quality': quality,
            'title': title,
            'web': web,
            'seeders': seeders,
            'leechers': leechers,
            'uploaded_at': uploaded_at,
            'size': size,
            'uploader': uploader,
        }
        data.append(item)
    print('finished scraping {}'.format(url))


def save_data(cat, data):
    c = db.cursor()
    for item in data:
        rows = c.execute('SELECT * FROM torrents WHERE web="{}"'.format(item['web'])).fetchall()
        if not rows:
            c.execute('INSERT INTO torrents (category, quality, title, web, seeders, leechers, uploaded_at, size, uploader) '
                      'VALUES("{category}", "{quality}", "{title}", "{web}", {seeders}, {leechers}, "{uploaded_at}", "{size}", "{uploader}")'.format(
                category=cat, **item))
    db.commit()


def load_data(filters):
    c = db.cursor()
    filters = ' and '.join(filters)
    query = ' WHERE '.join(['SELECT * FROM torrents', filters])
    query += ' ORDER BY title'
    rows = c.execute(query).fetchall()
    data = [{
        'id': r[0],
        'category': r[1],
        'quality': r[2],
        'title': r[3],
        'web': r[4],
        'seeders': r[5],
        'leechers': r[6],
        'uploaded_at': r[7],
        'size': r[8],
        'uploader': r[9],
    } for r in rows]
    return data


def setup():
    cursor = db.cursor()
    cursor.execute('''
        CREATE TABLE torrents(
            id INTEGER PRIMARY KEY, 
            category TEXT,
            quality TEXT,
            title TEXT,
            web TEXT unique,
            seeders INTEGER,
            leechers INTEGER,
            uploaded_at TEXT,
            size TEXT,
            uploader TEXT
        )
    ''')
    db.commit()


def get_args():
    parser = argparse.ArgumentParser(description='Scrape 1337x')
    parser.add_argument('--setup', dest='setup', action='store_true',
                        help='Recreate database.')
    parser.add_argument('--skip', dest='skip_scrape', action='store_true',
                        help='Skip scraping 1337x')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = get_args()
    if args.setup:
        setup()
    else:
        main(args.skip_scrape)
