import logging
from src.base import BaseHandler
from src.main.kickass import Kickass
from src.main.piratebay import PirateBay
from src.main.imdb import Imdb
from src.main.series import Series
from src.main.cleaner import Cleaner


class TpbCtrl(BaseHandler):
    def get(self):
        logging.info('Cron scrape tpb begin')
        tpb = PirateBay()
        tpb.scrape()
        logging.info('Cron scrape tpb end')
        self.response.status = '200 OK'


class KickassCtrl(BaseHandler):
    def get(self):
        logging.info('Cron scrape kickass begin')
        kickass = Kickass()
        kickass.scrape()
        logging.info('Cron scrape kickass end')
        self.response.status = '200 OK'


class KickassPageCtrl(BaseHandler):
    def post(self):
        logging.info('Cron scrape kickass page begin')
        req = self.request
        params = {
            'group_code': int(req.get('group_code')),
            'group_name': req.get('group_name'),
            'category_code': int(req.get('category_code')),
            'category_name': req.get('category_name'),
            'url_section': req.get('url'),
            'pages': int(req.get('pages')),
            'p': int(req.get('p')),
        }
        logging.info(params)
        kickass = Kickass()
        kickass.scrapePage(**params)
        logging.info('Cron scrape kickass page end')
        self.response.status = '200 OK'


class ImdbCtrl(BaseHandler):
    def get(self):
        logging.info('Cron scrape imdb begin')
        imdb = Imdb()
        imdb.runMovies()
        logging.info('Cron scrape imdb end')
        self.response.status = '200 OK'


class SeriesCtrl(BaseHandler):
    def get(self):
        logging.info('Cron scrape series begin')
        series = Series()
        series.extract()
        logging.info('Cron scrape series end')
        self.response.status = '200 OK'


class CleanCtrl(BaseHandler):
    def get(self):
        logging.info('Cron scrape clean begin')
        cleaner = Cleaner()
        cleaner.clean()
        logging.info('Cron scrape clean end')
        self.response.status = '200 OK'
