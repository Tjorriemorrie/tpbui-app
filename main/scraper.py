from main.models import *
import re
import time
import datetime
import arrow
import requests
from bs4 import BeautifulSoup
import string


class Scraper():
    urlBase = 'http://thepiratebay.se'
    patternSize = re.compile(r'^.*?\([^\d]*(\d+)[^\d]*\).*$', re.U)
    group = None

    def __init__(self):
        from google.appengine.api import urlfetch
        urlfetch.set_default_fetch_deadline(60)
        self.group = (int(arrow.utcnow().format('HH')) % 6 + 1) * 100


    def run(self):
        categoryGroup = CategoryGroup.objects.get(code=self.group)
        for category in categoryGroup.category_set.all():
            # category = Category.objects.get(code=207)
            # print 'category'
            # print category
            pages = 3 if 200 < self.group < 300 else 1
            for p in xrange(pages):
                self.runCategory(category)
                # break
                time.sleep(5)


    def runCategory(self, category, page=0):
        resultList = self.scrapeBrowse(category, page)
        # print html
        data = self.parseResultList(resultList)
        self.saveData(data, category)


    def scrapeBrowse(self, category, page):
        import requests
        s = requests.Session()
        a = requests.adapters.HTTPAdapter(max_retries=3)
        s.mount('http://', a)
        res = s.get(self.urlBase + '/browse/' + str(category.code) + '/' + str(page) + '/7', timeout=10)
        res.raise_for_status()
        return res.content


    def scrapeDetail(self, link):
        s = requests.Session()
        a = requests.adapters.HTTPAdapter(max_retries=3)
        s.mount('http://', a)
        res = s.get(link, timeout=10)
        res.raise_for_status()
        return res.content


    def parseResultList(self, resultList):
        data = []
        soup = BeautifulSoup(resultList)
        # print soup.prettify().encode('utf8')
        for link in soup.find_all('a', class_='detLink'):
            item = {
                'tpb_id': link['href'].split('/')[2],
            }
            # print '<p>link = ' + link['href'] + '</p>'
            resultDetail = self.scrapeDetail(self.urlBase + link['href'])
            det = BeautifulSoup(resultDetail)
            # print det.prettify().encode('utf8')

            # requireds
            item['title'] = det.find('div', id='title').text.strip()
            item['files'] = det.find('dt', text=re.compile('Files:')).findNext('dd').text.strip()
            item['size'] = self.patternSize.match(det.find('dt', text=re.compile('Size:')).findNext('dd').text).group(1)
            item['uploaded_at'] = datetime.datetime.strptime(det.find('dt', text=re.compile('Uploaded:')).findNext('dd').text.strip(), '%Y-%m-%d %H:%M:%S %Z')
            item['user'] = det.find('dt', text=re.compile('By:')).findNext('dd').text.strip()
            item['seeders'] = det.find('dt', text=re.compile('Seeders:')).findNext('dd').text.strip()
            item['leechers'] = det.find('dt', text=re.compile('Leechers:')).findNext('dd').text.strip()
            item['magnet'] = det.find_all('a', title='Get this torrent')[0]['href']
            item['nfo'] = det.find_all('div', class_='nfo')[0].text.strip()

            # optionals
            if det.find('div', class_='torpicture'):
                item['img'] = 'http:' + det.find_all('img', title='picture')[0]['src']
            else:
                item['img'] = 'http://www.thepiratebay.se/static/img/tpblogo_sm_ny.gif'

            data.append(item)
            # print 'item'
            # print item
            # break
            time.sleep(1)
        return data


    def saveData(self, data, category):
        for item in data:
            item['category'] = category
            torrent, created = Torrent.objects.get_or_create(tpb_id=item['tpb_id'], defaults=item)
            for property, value in item.iteritems():
                setattr(torrent, property, value)
            torrent.save()


class Imdb():
    # urlBase = 'http://www.metacritic.com/search/%s/%s/results?sort=relevancy'
    urlSearch = r'http://www.imdb.com/find?q=%s&&s=tt&ref_=fn_tt_pop'

    def runMovies(self):
        categories = [201, 207]
        for code in categories:
            # print 'runmovies'
            category = Category.objects.get(code=code)
            # print category
            # print 'torrents'
            torrents = category.torrent_set.all()
            # print len(torrents)
            for torrent in torrents:
                if torrent.rated_at and arrow.get(torrent.rated_at) >= arrow.utcnow().replace(weeks=-1):
                    continue
                    # pass

                matches = re.match(r'(.*)\(?(194[5-9]|19[5-9]\d|200\d|201[0-9])', torrent.title)
                title = matches.group(1).replace('(', '') + matches.group(2)
                links = self.searchTitle(title)
                rating, header = self.searchTitleRanking(links)

                if r'1080p' in torrent.title.lower():
                    torrent.resolution = 1080
                elif r'720p' in torrent.title.lower():
                    torrent.resolution = 720
                torrent.title_rating = header
                torrent.rating = rating
                torrent.rated_at = arrow.utcnow().datetime
                torrent.save()
                time.sleep(1)
                # break


    def searchTitle(self, title):
        links = []
        url = self.urlSearch % (title,)
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
        rows = soup.find('table', class_='findList').find_all('tr')
        for row in rows:
            links.append(row.find('a')['href'])

        return links


    def searchTitleRanking(self, links):
        for link in links:
            url = r'http://www.imdb.com' + link
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
                continue
            # print 'rating='
            # print rating
        return [None, None]



class SeriesScraper():
    def __init__(self):
        from google.appengine.api import urlfetch
        urlfetch.set_default_fetch_deadline(60)


    def run(self):
        for code in [205, 208]:
            category = Category.objects.get(code=code)
            seriesTitles = self.extractSeriesTitles(category)
            self.scrapeSeriesTitles(seriesTitles, category)


    def extractSeriesTitles(self, category):
        titles = set()
        print 'category', category
        for torrent in category.torrent_set.all(): #filter(series_title__isnull=True):
            # print 'torrent', torrent
            titleGroups = re.match(r'(.*)(s\d{1,2})(e\d{1,2})', torrent.title, re.I)
            if titleGroups is not None:
                titles.add(titleGroups.group(0))
                torrent.series_title = titleGroups.group(1)
                torrent.series_season = int(titleGroups.group(2)[2:])
                torrent.series_episode = int(titleGroups.group(3)[2:])
                torrent.save()
        print 'series titles', titles
        return titles


    def scrapeSeriesTitles(self, seriesTitles, category):
        s = requests.Session()
        a = requests.adapters.HTTPAdapter(max_retries=3)
        s.mount('http://', a)
        for seriesTitle in seriesTitles:
            res = s.get('http://www.thepiratebay.se/search/{0}/0/7/{1}'.format(seriesTitle, category.code), timeout=10)
            res.raise_for_status()
            scraper = Scraper()
            data = scraper.parseResultList(res.content)
            scraper.saveData(data, category)
            time.sleep(1)


    def saveData(self, data, category):
        for item in data:
            item['category'] = category
            torrent, created = Torrent.objects.get_or_create(tpb_id=item['tpb_id'], defaults=item)
            for property, value in item.iteritems():
                setattr(torrent, property, value)
            torrent.save()