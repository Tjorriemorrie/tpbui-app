import webapp2
from settings import *
from src.main import main, cron


wsgi = webapp2.WSGIApplication(
    [
        # main
        webapp2.Route(r'/', name='home', handler=main.IndexPage),
        webapp2.Route(r'/category/<cat:[a-z]+>', name='category', handler=main.CategoryPage),
        webapp2.Route(r'/download/<key:.+>', name='download', handler=main.DownloadPage),
        # url(r'^download/(?P<tpb_id>[0-9]+)$', views.download, name='download'),

        # cron
        webapp2.Route(r'/scrape/kickass', name='scrape_kickass', handler=cron.KickassCtrl),
        webapp2.Route(r'/scrape/imdb', name='scrape_imdb', handler=cron.ImdbCtrl),
        webapp2.Route(r'/scrape/series', name='scrape_series', handler=cron.SeriesCtrl),
        webapp2.Route(r'/scrape/clean', name='scrape_clean', handler=cron.CleanCtrl),
    ],
    debug=DEBUG,
    config=CONFIG
)