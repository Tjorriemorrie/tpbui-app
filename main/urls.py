from django.conf.urls import url
from main import views


urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^category/(?P<categoryId>[0-9]+)$', views.category, name='category'),
]