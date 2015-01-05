from google.appengine.ext import ndb
from google.appengine.api import users


class Torrent(ndb.Model):
    category = ndb.StringProperty()
    url = ndb.StringProperty()
    title = ndb.StringProperty()
    uploader = ndb.StringProperty()
    size = ndb.StringProperty()
    files = ndb.StringProperty()
    uploaded_at = ndb.StringProperty()
    seeders = ndb.IntegerProperty()
    leechers = ndb.IntegerProperty()
    magnet = ndb.StringProperty()
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)

    # movies (optional)
    # rating = ndb.IntegerField(null=True, blank=True)
    # rated_at = ndb.DateTimeField(null=True, blank=True)
    # title_rating = ndb.CharField(max_length=255)
    # resolution = ndb.IntegerField(null=True, blank=True)

    # series (optional)
    # series_title = ndb.CharField(max_length=45, null=True, blank=True)
    # series_season = ndb.IntegerField(null=True, blank=True)
    # series_episode = ndb.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return '{0}'.format(self.title)

    def is_downloaded(self):
        user = users.get_current_user()
        user_torrent = UserTorrent.query(UserTorrent.user == user, UserTorrent.torrent == str(self.key.id())).get()
        return True if user_torrent else False


class UserTorrent(ndb.Model):
    user = ndb.UserProperty()
    torrent = ndb.StringProperty()
    downloaded_at = ndb.DateTimeProperty(auto_now_add=True)
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)

    def __unicode__(self):
        return '{0} :|: {1}'.format(self.user, self.torrent)
