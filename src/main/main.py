import logging
from src.settings import JINJA_ENVIRONMENT
from src.base import BaseHandler
from src.main.models import Torrent, UserTorrent
from google.appengine.ext import ndb
from google.appengine.api import users
import arrow
from time import sleep
import datetime
from collections import OrderedDict


class IndexPage(BaseHandler):
    def get(self):
        logging.info('Index page requested')


        # new series
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=21)
        self.template_values['series_new'] = Torrent.findNewSeries(cutoff)

        cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        logging.info('Cutoff: {}'.format(cutoff))

        # new movies
        self.template_values['movies'] = Torrent.findLatestMovies(cutoff)

        episodes_new = []
        series_watching = []

        # watching series
        uts = UserTorrent.findWatchingSeries(cutoff)
        if uts:

            # get set of watching titles
            series_watching = OrderedDict()
            for ut in [ut for ut in uts if ut.torrent.get().series_title]:
                if ut.torrent.get().series_title not in series_watching:
                    series_watching[ut.torrent.get().series_title] = 0
            series_watching = series_watching.keys()

            # new episodes for series title
            if series_watching:
                episodes_new = Torrent.findWatchingEpisodes(series_watching, cutoff)

        self.template_values['series_watching'] = series_watching
        self.template_values['episodes_new'] = episodes_new

        # logging.info('{0}'.format(self.template_values))
        template = JINJA_ENVIRONMENT.get_template('templates/index.html')
        self.response.write(template.render(self.template_values))


class CategoryPage(BaseHandler):
    def get(self, cat):
        logging.info('cat {0}'.format(cat))
        self.template_values['cat'] = int(cat)

        # get torrents
        torrents = Torrent.query(Torrent.category_code == int(cat)).order(-Torrent.uploaded_at).fetch()
        self.template_values['torrents'] = torrents
        logging.info('torrents {0}'.format(len(torrents)))

        template = JINJA_ENVIRONMENT.get_template('templates/category.html')
        self.response.write(template.render(self.template_values))


class DownloadPage(BaseHandler):
    def get(self, key):
        logging.info('download {0}'.format(key))
        logging.info('user {0}'.format(self.user))
        torrent = ndb.Key(urlsafe=key).get()
        logging.info('torrent {0}'.format(torrent))
        ut = UserTorrent.query(UserTorrent.user == self.user, UserTorrent.torrent == torrent.key).get()
        if not ut:
            ut = UserTorrent(user=self.user, torrent=torrent.key, category_code=torrent.category_code)
            ut.put()
            logging.info('User Torrent saved')
        else:
            ut.key.delete()
            logging.info('User Torrent deleted')
        logging.info('User Torrent {0}'.format(ut))
        self.response.status = '200 OK'
