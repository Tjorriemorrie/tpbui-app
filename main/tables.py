import django_tables2 as tables
from main.models import *


class TorrentTable(tables.Table):
    # title = tables.Column(verbose_name="fuck")
    # created_at = tables.DateColumn()

    class Meta:
        model = Torrent
        # fields = ('tpb_id',)
        # sequence = ('tpb_id',)
        exclude = (
            'id',
            'category',
            'img',
            'magnet',
            'nfo',
            'created_at',
            'updated_at',
        )
        # add class="paleblue" to <table> tag
        attrs = {"class": "paleblue"}

    def render_size(self, value):
        levels = ['B', 'KB', 'MB', 'GB', 'TB']

        cnt = 0
        while value >= 1024 and cnt < len(levels):
            cnt += 1
            value /= 1024.

        if value < 10:
            value = round(value, 2)
        elif value < 100:
            value = round(value, 1)
        else:
            value = int(value)

        return '{0} {1}'.format(value, levels[cnt])
