import django_tables2 as tables
import arrow
from main.models import *
from django.utils.safestring import mark_safe


class TorrentTable(tables.Table):
    download = tables.Column(verbose_name=' ', empty_values=())
    tr_class = tables.Column(visible=False, empty_values=())

    class Meta:
        model = Torrent
        fields = ('download', 'title', 'seeders', 'size', 'uploaded_at', 'user', 'files')
        sequence = ('download', 'title', 'seeders', '...', 'files')
        # add class="paleblue" to <table> tag
        # attrs = {"class": "paleblue"}

    def render_tr_class(self, record):
        ut = UserTorrent.objects.get(user=self.user, torrent=record)
        return 'downloaded' if ut else ''

    def render_download(self, record):
        html = r'<a href="%s" data-id="%s" target="_blank"><span class="glyphicon glyphicon-download"></span></a>' % (record.magnet, record.tpb_id)
        return mark_safe(html)

    def render_title(self, value, record):
        if record.rating:
            html = r'<span class="rating">%s</span> ' % (record.rating,)
        else:
            html = r''
        html += '<img src="%s" class="row-icon" />' % (record.img,)
        html += ' <a href="http://www.thepiratebay.se/torrent/%s" target="_newtab">%s</a>' % (record.tpb_id, value)
        return mark_safe(html)

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

    def render_uploaded_at(self, value):
        return arrow.get(value).humanize()