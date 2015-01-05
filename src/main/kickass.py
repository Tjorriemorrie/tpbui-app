import logging
from src.main.models import Torrent
import requests
from bs4 import BeautifulSoup
from pprint import pprint


class Kickass():

    URL_BASE = 'http://kickass.so'
    CATEGORIES = [
        'highres-movies',
        'tv',
        'pc-games',
    ]


    def scrape(self):
        for category in self.CATEGORIES:
            logging.info('kickass cat {0}'.format(category))
            # get list of torrents per page
            for p in xrange(1, 5):
                logging.info('kickass p {0}'.format(p))
                list = self.scrapeList(category, p)
                self.saveList(list)


    def scrapeList(self, category, p):
        logging.info('Kickass scraping {0} page {1}'.format(category, p))
        res = requests.get('{0}/{1}/{2}'.format(self.URL_BASE, category, p), timeout=59)
        res.raise_for_status()
        soup = BeautifulSoup(res.content)
        table = soup.find('table', class_='data')
        list = []
        for tr in table.find_all('tr')[2:]:
            item = {}
            link = tr.find('a', class_='cellMainLink')
            item['url'] = link['href']
            item['title'] = link.text
            item['uploader'] = tr.find('div', class_='torrentname').find('a', class_='plain').text
            item['magnet'] = tr.find('a', class_='imagnet')['href']
            item['size'] = tr.find_all('td')[1].text
            item['files'] = tr.find_all('td')[2].text
            item['uploaded_at'] = tr.find_all('td')[3].text
            item['seeders'] = int(tr.find_all('td')[4].text)
            item['leechers'] = int(tr.find_all('td')[5].text)
            item['category'] = category
            pprint(item)
            list.append(item)
        logging.info('Kickass scraped {0} page {1} found {2}'.format(category, p, len(list)))
        return list


    def saveList(self, list):
        logging.info('list: saving...')
        for item in list:
            torrent = Torrent.query(Torrent.url == item['url'])
            if not torrent:
                torrent = Torrent(**item)
            torrent.populate(**item)
            torrent.put()
            logging.info('list: saved {0}'.format(torrent))
        logging.info('list: saved')