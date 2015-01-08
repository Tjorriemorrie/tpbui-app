import logging
from src.settings import JINJA_ENVIRONMENT
from src.base import BaseHandler
from src.main.models import Torrent, UserTorrent
from google.appengine.ext import ndb


class IndexPage(BaseHandler):
    def get(self):
        logging.info('{0}'.format(self.template_values))
        template = JINJA_ENVIRONMENT.get_template('main/templates/index.html')
        self.response.write(template.render(self.template_values))


class CategoryPage(BaseHandler):
    def get(self, cat):
        logging.info('cat {0}'.format(cat))
        self.template_values['cat'] = cat

        # get category
        if cat == 'movies':
            cat_filter = 'highres-movies'
        elif cat == 'tv':
            cat_filter = 'tv'
        elif cat == 'games':
            cat_filter = 'pc-games'

        # get torrents
        torrents = Torrent.query(Torrent.category == cat_filter).order(-Torrent.uploaded_at).fetch()
        self.template_values['torrents'] = torrents
        logging.info('torrents {0}'.format(len(torrents)))

        template = JINJA_ENVIRONMENT.get_template('main/templates/category.html')
        self.response.write(template.render(self.template_values))


class DownloadPage(BaseHandler):
    def get(self, key):
        logging.info('download {0}'.format(key))
        logging.info('user {0}'.format(self.user))
        torrent = ndb.Key(urlsafe=key).get()
        logging.info('torrent {0}'.format(torrent))
        ut = UserTorrent.query(UserTorrent.user == self.user, UserTorrent.torrent == str(torrent.key.id())).get()
        if not ut:
            ut = UserTorrent(user=self.user, torrent=str(torrent.key.id()))
            ut.put()
        logging.info('ut {0}'.format(ut))
        self.response.status = '200 OK'