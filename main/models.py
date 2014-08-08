from django.db import models
from django.contrib.auth.models import User
from google.appengine.api import users


# class Gae(models.Model):
#     user = models.OneToOneField(User)
#     nickname = users.get_current_user().nickname()
#     email = users.get_current_user().email()
#
# User.gae = property(lambda u: Gae.objects.get_or_create(user=u)[0])


class CategoryGroup(models.Model):
    name = models.CharField(max_length=45)
    code = models.SmallIntegerField()

    def __unicode__(self):
        return '{0} {1}'.format(self.code, self.name)

    class Meta:
        ordering = [
            'code',
        ]


class Category(models.Model):
    categoryGroup = models.ForeignKey(CategoryGroup)
    name = models.CharField(max_length=45)
    code = models.SmallIntegerField()

    def __unicode__(self):
        return '{0} {1}'.format(self.code, self.name)

    class Meta:
        ordering = [
            'code',
        ]
        verbose_name_plural = 'categories'


class Torrent(models.Model):
    category = models.ForeignKey(Category)
    tpb_id = models.IntegerField()
    title = models.CharField(max_length=255)
    files = models.IntegerField()
    size = models.BigIntegerField()
    datetime = models.DateTimeField()
    user = models.CharField(max_length=45)
    seeders = models.IntegerField()
    leechers = models.IntegerField()
    img = models.CharField(max_length=255)
    magnet = models.CharField(max_length=255)
    nfo = models.TextField()

    def __unicode__(self):
        return '{0}'.format(self.title)
