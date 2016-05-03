import webapp2
from settings import *
from src.main import main, cron


wsgi = webapp2.WSGIApplication(
    [
        # cron
        webapp2.Route(r'/cron/clean', name='clean', handler=cron.CleanCtrl),
        webapp2.Route(r'/cron/tpb', name='tpb', handler=cron.TpbCtrl),

        # main
        webapp2.Route(r'/category/<cat:[0-9]+>', name='category', handler=main.CategoryPage),
        webapp2.Route(r'/download/<key:.+>', name='download', handler=main.DownloadPage),
        webapp2.Route(r'/', name='home', handler=main.IndexPage),
    ],
    debug=DEBUG,
    config=CONFIG
)
