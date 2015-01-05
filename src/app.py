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

        # scrape
        webapp2.Route(r'/scrape', name='scrape', handler=cron.Scrape),
    ],
    debug=DEBUG,
    config=CONFIG
)