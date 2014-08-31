from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import logout
from main.models import *
from main.tables import *
from django_tables2 import RequestConfig
import logging


def home(request):
    context = {}
    return render(request, 'main/home.html', context)


def category(request, code):
    category = get_object_or_404(Category, code=code)
    table = TorrentTable(category.torrent_set.all(), order_by=('-uploaded_at',))
    table.user = request.user
    RequestConfig(request, paginate={'per_page': 30}).configure(table)

    context = {
        'category': category,
        'table': table,
    }

    if category.code in [205, 208]:
        view = 'main/series.html'
    else:
        view = 'main/category.html'
    return render(request, view, context)


def scrape(request):
    from main.scraper import Scraper
    scraper = Scraper()
    scraper.run()
    return HttpResponse(status=200)


def download(request, tpb_id):
    torrent = get_object_or_404(Torrent, tpb_id=tpb_id)
    ut, created = UserTorrent.objects.get_or_create(user=request.user, torrent=torrent, category=torrent.category, categoryGroup=torrent.category.categoryGroup)
    ut.save()
    logging.info(str(request.user.username) + ' downloaded ' + str(tpb_id))
    return HttpResponse(status=200, content="Saved " + str(tpb_id))


def scrapeMovies(request):
    from main.scraper import Imdb
    imdb = Imdb()
    imdb.runMovies()
    return HttpResponse(status=200)


def scrapeSeries(request):
    from main.scraper import SeriesScraper
    seriesScraper = SeriesScraper()
    seriesScraper.run()
    return HttpResponse(status=200)
