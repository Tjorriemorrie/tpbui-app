import logging
from google.appengine.ext import ndb
from google.appengine.api import users
import arrow


class Torrent(ndb.Model):
    group_name = ndb.StringProperty()
    group_code = ndb.IntegerProperty()
    category_name = ndb.StringProperty()
    category_code = ndb.IntegerProperty()

    title = ndb.StringProperty()
    url = ndb.StringProperty()
    magnet = ndb.StringProperty()

    uploaded_at = ndb.DateTimeProperty()
    uploaded_week = ndb.IntegerProperty()
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
    series_complete = ndb.BooleanProperty()

    def __unicode__(self):
        return u'{0}'.format(self.title)

    def is_downloaded(self):
        user = users.get_current_user()
        user_torrent = UserTorrent.query(UserTorrent.user == user, UserTorrent.torrent == self.key).get()
        return True if user_torrent else False

    def uploaded_time_ago(self):
        return arrow.get(self.uploaded_at).humanize()

    def size_humanize(self):
        # thousands
        if self.size >= 10**9:
            val = self.size / 10.**9
            tail = 'GB'
        elif self.size >= 10**6:
            val = self.size / 10.**6
            tail = 'MB'
        elif self.size >= 10**3:
            val = self.size / 10.**3
            tail = 'KB'
        else:
            val = self.size
            tail = 'B'
        # rounding
        if val < 10:
            return '{0:.2f} {1}'.format(val, tail)
        elif val < 100:
            return '{0:.1f} {1}'.format(val, tail)
        else:
            return '{0:.0f} {1}'.format(val, tail)

    @staticmethod
    def findLatestMovies(cutoff):
        movies = Torrent.query(
            Torrent.category_code == 207,
            Torrent.uploaded_at >= cutoff
        ).order(
            -Torrent.uploaded_at
        ).fetch()
        logging.info('[Torrent] findLatestMovies: found {} since {}'.format(len(movies), cutoff))
        return movies

    @staticmethod
    def findNewSeries(cutoff):
        series = Torrent.query(
            Torrent.category_code == 205,
            Torrent.series_episode == 1,
            Torrent.uploaded_at >= cutoff
        ).order(-Torrent.uploaded_at).fetch()
        logging.info('[Torrent] findNewSeries: found {} since {}'.format(len(series), cutoff))
        return series

    @staticmethod
    def findWatchingEpisodes(series_watching, cutoff):
        episodes = Torrent.query(
            Torrent.series_title.IN(series_watching),
            # Torrent.uploaded_at > cutoff,
            Torrent.category_code == 205
        # ).order(
        #     -Torrent.series_episode,
        #     -Torrent.uploaded_at,
        ).fetch()
        logging.info('[Torrent] findWatchingEpisodes: found {} for {} since {}'.format(len(episodes), series_watching, cutoff))
        return episodes


    @staticmethod
    def findNewGames(cutoff):
        games = Torrent.query(
            Torrent.category_code == 401,
            Torrent.uploaded_at > cutoff
        ).order(
            -Torrent.uploaded_at,
        ).fetch()
        logging.info('[Torrent] findNewGames: found {} since {}'.format(len(games), cutoff))
        return games


class UserTorrent(ndb.Model):
    user = ndb.UserProperty()
    torrent = ndb.KeyProperty(kind=Torrent)
    category_code = ndb.IntegerProperty()
    downloaded_at = ndb.DateTimeProperty(auto_now_add=True)
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)

    def __unicode__(self):
        return u'{0} :|: {1}'.format(self.user, self.torrent)

    @staticmethod
    def findWatchingSeries(cutoff):
        series = UserTorrent.query(
            UserTorrent.user == users.get_current_user(),
            UserTorrent.category_code == 205,
            # Torrent.created_at > cutoff
        ).order(-UserTorrent.created_at).fetch()
        logging.info('[UserTorrent] findWatchingSeries: found {} since {}'.format(len(series), cutoff))
        return series
