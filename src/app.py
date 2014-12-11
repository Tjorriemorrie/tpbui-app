import webapp2
from settings import *
from src.main import main


wsgi = webapp2.WSGIApplication(
    [
        webapp2.Route(r'/', name='home', handler=main.Index),
    ],
    debug=DEBUG,
    config=CONFIG
)