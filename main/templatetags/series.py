from django.template import Library, Node, Variable
from main.models import *
import arrow

register = Library()


@register.tag
def getSeriesNew(parser, token):
    return SeriesNewNode()

class SeriesNewNode(Node):
    def render(self, context):
        seriesNew = {}

        # get user torrents from user for category
        category = context['category']
        user = context['user']
        userTorrents = category.usertorrent_set.select_related('torrent').filter(user=user)

        # get unique series titles
        titles = set()
        for userTorrent in userTorrents:
            if userTorrent.torrent.series_title is not None:
                titles.add(userTorrent.torrent.series_title)

        # get latest new episodes for each title
        weekAgo = arrow.utcnow().replace(days=-21)
        for title in titles:
            torrents = Torrent.objects.filter(uploaded_at__gte=weekAgo.datetime, series_title=title).order_by('-uploaded_at')
            if torrents:
                # order (as not possible with datastore)
                torrents = sorted(torrents, key=lambda torrent: torrent.seeders, reverse=True)
                torrents = sorted(torrents, key=lambda torrent: torrent.series_episode, reverse=True)
                torrents = sorted(torrents, key=lambda torrent: torrent.series_season, reverse=True)
                for torrent in torrents:
                    for userTorrent in userTorrents:
                        if userTorrent.torrent == torrent:
                            torrent.row_class = 'downloaded'
                            break
                    # ut = UserTorrent.objects.get(user=user, torrent=torrent)
                seriesNew[title] = torrents

        context['seriesNew'] = seriesNew
        return ''


@register.tag
def getSeriesReleases(parser, token):
    return SeriesReleasesNode()

class SeriesReleasesNode(Node):
    def render(self, context):
        category = context['category']

        torrents = category.torrent_set.filter(series_episode=1)

        # get unique series titles
        titles = set()
        for torrent in torrents:
            if torrent.series_title is not None:
                titles.add(torrent.series_title)

        # get user torrents from user for category
        user = context['user']
        userTorrents = category.usertorrent_set.select_related('torrent').filter(user=user)

        seriesReleases = {}
        # # get latest new episodes for each title
        weekAgo = arrow.utcnow().replace(days=-14)
        for title in titles:
            torrents = Torrent.objects.filter(uploaded_at__gte=weekAgo.datetime, series_title=title, series_episode=1).order_by('-uploaded_at')
            if torrents:
                # order (as not possible with datastore)
                torrents = sorted(torrents, key=lambda torrent: torrent.seeders, reverse=True)
                torrents = sorted(torrents, key=lambda torrent: torrent.series_episode, reverse=True)
                torrents = sorted(torrents, key=lambda torrent: torrent.series_season, reverse=True)
                for torrent in torrents:
                    for userTorrent in userTorrents:
                        if userTorrent.torrent == torrent:
                            torrent.row_class = 'downloaded'
                            break
                    # ut = UserTorrent.objects.get(user=user, torrent=torrent)
                seriesReleases[title] = torrents

        context['seriesReleases'] = seriesReleases
        return ''
