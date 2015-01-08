import logging
from src.base import BaseHandler
from src.main.kickass import Kickass
from src.main.imdb import Imdb


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
