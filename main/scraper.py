from main.models import *
import re
import time
import datetime
import arrow


class Scraper():
    urlBase = 'http://thepiratebay.se'
    patternSize = re.compile(r'^.*?\([^\d]*(\d+)[^\d]*\).*$', re.U)
    group = None

    def __init__(self):
        from google.appengine.api import urlfetch
        urlfetch.set_default_fetch_deadline(60)
        self.group = (int(arrow.utcnow().format('HH')) % 6 + 1) * 100


    def run(self):
        self.runDefault()


    def runDefault(self):
        categoryGroup = CategoryGroup.objects.get(code=self.group)
        for category in categoryGroup.category_set.all():
            # category = Category.objects.get(code=207)
            # print 'category'
            # print category
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
        import requests
        s = requests.Session()
        a = requests.adapters.HTTPAdapter(max_retries=3)
        s.mount('http://', a)
        res = s.get(link, timeout=10)
        res.raise_for_status()
        return res.content


    def parseResultList(self, resultList):
        data = []
        from bs4 import BeautifulSoup
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

