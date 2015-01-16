import logging
from src.main.models import Torrent
from google.appengine.api import mail
import requests
import arrow
import re
from bs4 import BeautifulSoup
from pprint import pprint


class Imdb():
    # urlBase = 'http://www.metacritic.com/search/%s/%s/results?sort=relevancy'
    urlSearch = r'http://www.imdb.com/find?q={0}&&s=tt&ref_=fn_tt_pop'

    def runMovies(self):
        logging.info('IMDB: movies running...')
        torrents = Torrent.query(Torrent.category == 'highres-movies', Torrent.rating == None).fetch()
        logging.info('{0} torrents fetched'.format(len(torrents)))
        results = {}
        for torrent in torrents:
            # find year
            matches = re.match(r'(.*)\(?(19[5-9]\d|20[0-1]\d)', torrent.title)
            if matches is None:
                results[torrent.title] = 'no match'
                logging.info('No match for {0}'.format(torrent.title))
            else:
                # remove brackets in title
                title = matches.group(1).replace('(', '') + matches.group(2)
                # get imdb search results
                links = self.searchTitle(title)
                rating, header = self.searchTitleRanking(links)
                if not rating or not header:
                    results[torrent.title] = 'no page'
                    logging.info('No page for {0}'.format(torrent.title))
                    continue
                logging.info('Found title as: {0}'.format(title.encode('utf-8')))

                if r'1080p' in torrent.title.lower():
                    torrent.resolution = 1080
                elif r'720p' in torrent.title.lower():
                    torrent.resolution = 720
                torrent.title_rating = header
                torrent.rating = rating
                torrent.rated_at = arrow.utcnow().datetime.replace(tzinfo=None)
                logging.info('Saved {0}'.format(torrent))
                torrent.put()
                results[torrent.title] = 'has rating {0}%'.format(rating)

        self.notify(results)
        logging.info('IMDB: movies ran')


    def searchTitle(self, title):
        logging.info('IMDB title searching {0}'.format(title.encode('utf-8')))
        links = []
        url = self.urlSearch.format(title.encode('utf-8'))
        s = requests.Session()
        a = requests.adapters.HTTPAdapter(max_retries=3)
        s.mount('http://', a)
        headers = {
            # 'X-Real-IP': '251.223.201.178',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0'
        }
        res = s.get(url, timeout=10, headers=headers)
        res.raise_for_status()
        # print res.content

        soup = BeautifulSoup(res.content)
        try:
            rows = soup.find('table', class_='findList').find_all('tr')
            for row in rows:
                links.append(row.find('a')['href'])
        except AttributeError:
            logging.error('No table or rows in response!')

        logging.info('IMDB title {0} found'.format(len(links)))
        return links


    def searchTitleRanking(self, links):
        for link in links:
            logging.info('IMDB search page {0}...'.format(link))
            url = 'http://www.imdb.com{0}'.format(link)
            s = requests.Session()
            a = requests.adapters.HTTPAdapter(max_retries=3)
            s.mount('http://', a)
            headers = {
                # 'X-Real-IP': '251.223.201.178',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0'
            }
            res = s.get(url, timeout=10, headers=headers)
            res.raise_for_status()
            # print res.content

            soup = BeautifulSoup(res.content)
            try:
                rating = soup.find(class_=['star-box', 'giga-star']).find(class_=['titlePageSprite', 'star-box-giga-star']).text.strip()
                header = soup.find('h1', class_='header').find('span', class_='itemprop').text.strip()
                rating = int(float(rating)*10)
                return [rating, header]
            except AttributeError:
                logging.error('No star box rating for title!')

        return [None, None]


    def notify(self, results):
        mail.send_mail(
            sender='jacoj82@gmail.com',
            to='jacoj82@gmail.com',
            subject="IMDB scraped",
            body='\n'.join(['{0} {1}'.format(k.encode('utf-8'), v) for k, v in results.iteritems()]),
        )
