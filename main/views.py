from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404

from models import Category


def home(request):
    context = {
        'anser': 'baz'
    }
    return render(request, 'main/home.html', context)


def category(request, categoryId):
    category = get_object_or_404(Category, pk=categoryId)
    context = {
        'category': category
    }
    return render(request, 'main/category.html', context)