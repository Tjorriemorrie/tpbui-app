import django_tables2 as tables
from main.models import *


class TorrentTable(tables.Table):
    title = tables.Column()
    created_at = tables.DateColumn()

    class Meta:
        model = Torrent
        # add class="paleblue" to <table> tag
        attrs = {"class": "paleblue"}
