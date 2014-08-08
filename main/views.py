from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import logout
from main.models import *
# from main.tables import *
# from django_tables2 import RequestConfig


def home(request):
    categories = Category.objects.all()
    return render(request, 'main/home.html', {
        'categories': categories
    })


def category(request, code):
    category = get_object_or_404(Category, code=code)
    # table = TorrentTable(category.torrent_set.all())
    # RequestConfig(request).configure(table)
    context = {
        'category': category,
        # 'table': table,
    }
    return render(request, 'main/category.html', context)


# def logout(request):
#     logout(request)
#     return redirect('home')


def scrape(request):
    from main.scraper import Scraper
    scraper = Scraper()
    scraper.run()
    return HttpResponse(status=200)
