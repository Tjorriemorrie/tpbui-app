import logging
from src.base import BaseHandler
from src.main.kickass import Kickass
from src.main.piratebay import PirateBay
from src.main.imdb import Imdb
from src.main.series import Series


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
        kickass = Kickass()
        kickass.clean()
        logging.info('Cron scrape clean end')
        self.response.status = '200 OK'
