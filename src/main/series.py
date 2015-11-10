import logging
from google.appengine.api import mail
from src.main.models import Torrent
from pprint import pprint
import arrow
import re


class Series():
    def extract(self):
        logging.info('series: extraction running...')
        cutoff = arrow.utcnow().replace(days=-3).datetime
        torrents = Torrent.query(Torrent.category_code == 205, Torrent.series_title == None, Torrent.created_at > cutoff).fetch()
        logging.info('{0} torrents fetched'.format(len(torrents)))
        results = []
        for torrent in torrents:
            try:
                msg = self.parseSeries(torrent)
            except Exception as e:
                msg = e.message
            results.append(msg)
            logging.info(msg)
        self.notify(results)

    def parseSeries(self, torrent):
        logging.info('parsing {0}...'.format(torrent.title.encode('utf-8')))

        # plain and simple e.g. xxx S##E##
        title_groups = re.match(r'(.*)\s(s\d{1,2})(e\d{1,2})\s', torrent.title.replace('.', ' ').strip(), re.I)
        if title_groups is not None:
            logging.info('series and episode found {0}'.format(title_groups.groups()))
            torrent.series_title = title_groups.group(1)
            torrent.series_season = int(title_groups.group(2)[1:])
            torrent.series_episode = int(title_groups.group(3)[1:])
            torrent.put()
            # pprint(torrent)
            msg = '[200] {0} S{1} E{2}'.format(torrent.series_title.encode('utf-8'), torrent.series_season, torrent.series_episode)
        else:
            logging.info('series and episode not found')

            # only episode given e.g. xxx E###
            title_groups = re.match(r'(.*)\s(e\d{1,3})\s', torrent.title.replace('.', ' ').strip(), re.I)
            if title_groups is not None:
                logging.info('only episode found')
                torrent.series_title = title_groups.group(1).replace('.', ' ').strip()
                torrent.series_season = None
                torrent.series_episode = int(title_groups.group(2)[1:])
                torrent.put()
                # pprint(torrent)
                msg = '[200] {0} E{1}'.format(torrent.series_title.encode('utf-8'), torrent.series_episode)
            else:
                logging.info('only episode not found')

                # simple version e.g. ##x##_
                title_groups = re.match(r'(.*)(\d{1,2})x(\d{1,2})\s', torrent.title.replace('.', ' ').strip(), re.I)
                if title_groups is not None:
                    logging.info('series x episode found')
                    torrent.series_title = title_groups.group(1).replace('.', ' ').strip()
                    torrent.series_season = int(title_groups.group(2))
                    torrent.series_episode = int(title_groups.group(3))
                    torrent.put()
                    # pprint(torrent)
                    msg = '[200] <= {0} S{1} E{2}'.format(torrent.series_title.encode('utf-8'), torrent.series_season, torrent.series_episode)
                else:
                    logging.info('simple version not found')

                    # pilot?
                    title_groups = re.match(r'(.*)(-pilot)', torrent.title.replace('.', ' ').strip(), re.I)
                    if title_groups is not None:
                        logging.info('pilot episode found')
                        torrent.series_title = title_groups.group(1).replace('.', ' ').strip()
                        torrent.series_season = 1
                        torrent.series_episode = 1
                        torrent.put()
                        # pprint(torrent)
                        msg = '[200] <= {0} S{1} E{2}'.format(torrent.series_title.encode('utf-8'), torrent.series_season, torrent.series_episode)
                    else:
                        logging.info('absolutely not found')
                        msg = '[404] <= {0}'.format(torrent.title.encode('utf-8'))
        return msg

    def notify(self, results):
        mail.send_mail(
            sender='jacoj82@gmail.com',
            to='jacoj82@gmail.com',
            subject="Series extracted",
            body='\n'.join(results),
        )
