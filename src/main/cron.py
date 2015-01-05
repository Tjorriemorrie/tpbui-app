import logging
from src.base import BaseHandler
from src.main.kickass import Kickass


class Scrape(BaseHandler):
    def get(self):
        logging.info('Cron scrape begin')
        kickass = Kickass()
        kickass.scrape()
        logging.info('Cron scrape end')
        self.response.status = '200 OK'
