from google.appengine.ext import ndb
from google.appengine.api import users
import arrow
import logging


class Torrent(ndb.Model):
    group_name = ndb.StringProperty()
    group_code = ndb.IntegerProperty()
    category_name = ndb.StringProperty()
    category_code = ndb.IntegerProperty()

    title = ndb.StringProperty()
    url = ndb.StringProperty()
    magnet = ndb.StringProperty()

    uploaded_at = ndb.DateTimeProperty()
    size = ndb.IntegerProperty()
    uploader = ndb.StringProperty()

    seeders = ndb.IntegerProperty()
    leechers = ndb.IntegerProperty()

    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)

    # movies
    #   (optional)
    #   from imdb
    rating = ndb.IntegerProperty()
    rated_at = ndb.DateTimeProperty()
    title_rating = ndb.StringProperty()
    resolution = ndb.IntegerProperty()

    # series
    #   (optional)
    #   no scraping, just extraction
    series_title = ndb.StringProperty()
    series_season = ndb.IntegerProperty()
    series_episode = ndb.IntegerProperty()

    def __unicode__(self):
        return u'{0}'.format(self.title)

    def is_downloaded(self):
        user = users.get_current_user()
        user_torrent = UserTorrent.query(UserTorrent.user == user, UserTorrent.torrent == str(self.key.id())).get()
        return True if user_torrent else False

    def uploaded_time_ago(self):
        return arrow.get(self.uploaded_at).humanize()


class UserTorrent(ndb.Model):
    user = ndb.UserProperty()
    torrent = ndb.StringProperty()
    downloaded_at = ndb.DateTimeProperty(auto_now_add=True)
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)

    def __unicode__(self):
        return u'{0} :|: {1}'.format(self.user, self.torrent)

    def get_torrent(self):
        torrent = Torrent.get_by_id(int(self.torrent))
        logging.info('torrent fetched from ut {0} is {1}'.format(self.torrent, torrent))
        return torrent


