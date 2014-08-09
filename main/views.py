from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import logout
from main.models import *
from main.tables import *
from django_tables2 import RequestConfig


def home(request):
    context = {}
    return render(request, 'main/home.html', context)


def category(request, code):
    category = get_object_or_404(Category, code=code)
    # uts = UserTorrent.objects.filter(user=request.user, )
    table = TorrentTable(category.torrent_set.all(), order_by=('-uploaded_at',))
    table.user = request.user
    RequestConfig(request).configure(table)
    context = {
        'category': category,
        'table': table,
    }
    return render(request, 'main/category.html', context)


def scrape(request):
    from main.scraper import Scraper
    scraper = Scraper()
    scraper.run()
    return HttpResponse(status=200)


def download(request, tpb_id):
    torrent = get_object_or_404(Torrent, tpb_id=tpb_id)
    ut = UserTorrent.objects.create(user=request.user, torrent=torrent, category=torrent.category, categoryGroup=torrent.category.categoryGroup)
    ut.save()
    return HttpResponse(status=200)