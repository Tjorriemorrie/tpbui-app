import logging
from google.appengine.api import mail
from src.main.models import Torrent
from pprint import pprint
import arrow
import re


class Series():
    def extract(self):
        logging.info('series: extraction running...')
        cutoff = arrow.utcnow().replace(days=-7).datetime
        torrents = Torrent.query(Torrent.category == 'tv', Torrent.created_at > cutoff, Torrent.series_title == None).fetch(10)
        logging.info('{0} torrents fetched'.format(len(torrents)))
        results = {}
        for torrent in torrents:
            title_groups = re.match(r'(.*)(s\d{1,2})(e\d{1,2})', torrent.title, re.I)
            if title_groups is not None:
                torrent.series_title = title_groups.group(1).replace('.', ' ').strip()
                torrent.series_season = int(title_groups.group(2)[1:])
                torrent.series_episode = int(title_groups.group(3)[1:])
                torrent.put()
                # pprint(torrent)
                results[torrent.title] = 'found as {0} S{1} E{2}'.format(torrent.series_title, torrent.series_season, torrent.series_episode)
            else:
                results[torrent.title] = 'Not found'
        self.notify(results)


    def notify(self, results):
        mail.send_mail(
            sender='jacoj82@gmail.com',
            to='jacoj82@gmail.com',
            subject="Series extracted",
            body='\n'.join(['{0} {1}'.format(k, v) for k, v in results.iteritems()]),
        )
