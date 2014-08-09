from google.appengine.api import users
from django.contrib.auth.models import User


class GaeMiddleware(object):
    def process_request(self, request):
        userGae = users.get_current_user()
        request.user, created = User.objects.get_or_create(email=userGae.email().lower())
        request.user.username = userGae.nickname()
        request.user.save()


