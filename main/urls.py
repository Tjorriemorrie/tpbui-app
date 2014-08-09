from django.conf.urls import url
from main import views


urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^logout$', 'django.contrib.auth.views.logout', {'next_page': '/'}),
    url(r'^category/(?P<code>[0-9]+)$', views.category, name='category'),
    url(r'^scrape$', views.scrape, name='scrape'),
    url(r'^download/(?P<tpb_id>[0-9]+)$', views.download, name='download'),
]