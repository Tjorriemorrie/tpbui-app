from main.models import *
import re
import time
import datetime


class Scraper():
    urlBase = 'http://thepiratebay.se'
    patternSize = re.compile(r'^.*?\([^\d]*(\d+)[^\d]*\).*$', re.U)


    def run(self):
        self.runDefault()


    def runDefault(self):
        categoryGroups = CategoryGroup.objects.all()
        for categoryGroup in categoryGroups:
            for category in categoryGroup.category_set.all():
                self.runCategory(category)
                time.sleep(10)


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
        # todo make the img a base64 encoded string
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
            item['title'] = det.find('div', id='title').text.strip()
            item['files'] = det.find_all('a')[8].text.strip()
            # self.patternSize.match(det.find_all('dd')[2].text).group()
            # print det.find_all('dd')[2].text.split('(')[1]
            # print 'size'
            # print det.find_all('dd')[2]
            item['size'] = self.patternSize.match(det.find_all('dd')[2].text).group(1)
            item['uploaded_at'] = datetime.datetime.strptime(det.find_all('dd')[4].text.strip(), '%Y-%m-%d %H:%M:%S %Z')
            item['user'] = det.find_all('dd')[5].text.strip()
            item['seeders'] = det.find_all('dd')[6].text.strip()
            item['leechers'] = det.find_all('dd')[7].text.strip()
            item['img'] = 'http:' + det.find_all('img', title='picture')[0]['src']
            item['magnet'] = det.find_all('a', title='Get this torrent')[0]['href']
            item['nfo'] = det.find_all('div', class_='nfo')[0].text.strip()
            data.append(item)
            # print 'item'
            # print item
            break
            time.sleep(1)
        return data


    def saveData(self, data, category):
        # todo add this to a transaction
        for item in data:
            item['category'] = category
            torrent, created = Torrent.objects.get_or_create(tpb_id=item['tpb_id'], defaults=item)
            for property, value in item.iteritems():
                setattr(torrent, property, value)
            torrent.save()

