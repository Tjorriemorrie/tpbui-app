from google.appengine.ext import ndb
from google.appengine.api import users
import arrow


class Torrent(ndb.Model):
    category = ndb.StringProperty()
    url = ndb.StringProperty()
    title = ndb.StringProperty()
    uploader = ndb.StringProperty()
    size = ndb.StringProperty()
    files = ndb.StringProperty()
    uploaded_at = ndb.DateTimeProperty()
    seeders = ndb.IntegerProperty()
    leechers = ndb.IntegerProperty()
    magnet = ndb.StringProperty()
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
        return '{0}'.format(self.title)

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
        return '{0} :|: {1}'.format(self.user, self.torrent)
