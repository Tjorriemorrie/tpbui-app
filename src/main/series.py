import logging
import re


def extract(torrent):
    logging.info('parsing {}...'.format(torrent.title.encode('utf-8')))

    # plain and simple e.g. xxx S##E##
    title_groups = re.match(r'(.*)\s(s\d{1,2})(e\d{1,2})\s', torrent.title.replace('.', ' ').strip(), re.I)
    if title_groups is not None:
        logging.info('series and episode found {0}'.format(title_groups.groups()))
        torrent.series_title = title_groups.group(1)
        torrent.series_season = int(title_groups.group(2)[1:])
        torrent.series_episode = int(title_groups.group(3)[1:])
    else:
        logging.info('series and episode not found')

        # only episode given e.g. xxx E###
        title_groups = re.match(r'(.*)\s(e\d{1,3})\s', torrent.title.replace('.', ' ').strip(), re.I)
        if title_groups is not None:
            logging.info('only episode found')
            torrent.series_title = title_groups.group(1).replace('.', ' ').strip()
            torrent.series_season = None
            torrent.series_episode = int(title_groups.group(2)[1:])
        else:
            logging.info('only episode not found')

            # simple version e.g. ##x##_
            title_groups = re.match(r'(.*)(\d{1,2})x(\d{1,2})\s', torrent.title.replace('.', ' ').strip(), re.I)
            if title_groups is not None:
                logging.info('series x episode found')
                torrent.series_title = title_groups.group(1).replace('.', ' ').strip()
                torrent.series_season = int(title_groups.group(2))
                torrent.series_episode = int(title_groups.group(3))
            else:
                logging.info('simple version not found')

                # pilot?
                title_groups = re.match(r'(.*)(-pilot)', torrent.title.replace('.', ' ').strip(), re.I)
                if title_groups is not None:
                    logging.info('pilot episode found')
                    torrent.series_title = title_groups.group(1).replace('.', ' ').strip()
                    torrent.series_season = 1
                    torrent.series_episode = 1
                else:
                    logging.info('absolutely not found')
