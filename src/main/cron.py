import logging
from src.base import BaseHandler
from src.main.piratebay import PirateBay
from src.main.cleaner import Cleaner


class CleanCtrl(BaseHandler):
    def get(self):
        logging.info('clean begin')
        cleaner = Cleaner()
        cleaner.clean()
        logging.info('clean end')
        self.response.status = '200 OK'


class TpbCtrl(BaseHandler):
    def get(self):
        logging.info('TPB begin')
        tpb = PirateBay()
        tpb.scrape()
        logging.info('TPB end')
        self.response.status = '200 OK'


# class TpbCategoryCtrl(BaseHandler):
#     def get(self, category):
#         logging.info('Cron scrape tpb category'.format(category))
#         tpb = PirateBay()
#         if category == 'series':
#             group = {'code': 200, 'name': 'Video'}
#             category = {'code': 205, 'name': 'TV Shows', 'pages': 1}
#             tpb.scrape_category(group, category)
#         else:
#             raise ValueError('unknown category')
#         self.response.status = '200 OK'
#
#
# class KickassCtrl(BaseHandler):
#     def get(self):
#         logging.info('Cron scrape kickass begin')
#         kickass = Kickass()
#         kickass.scrape()
#         logging.info('Cron scrape kickass end')
#         self.response.status = '200 OK'
#
#
# class ImdbCtrl(BaseHandler):
#     def get(self):
#         logging.info('Cron scrape imdb begin')
#         imdb = Imdb()
#         imdb.runMovies()
#         logging.info('Cron scrape imdb end')
#         self.response.status = '200 OK'
#
#
# class SeriesCtrl(BaseHandler):
#     def get(self):
#         logging.info('Cron scrape series begin')
#         series = Series()
#         series.extract()
#         logging.info('Cron scrape series end')
#         self.response.status = '200 OK'
