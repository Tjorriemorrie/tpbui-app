from django.db import models
from django.contrib.auth.models import User


class CategoryGroup(models.Model):
    name = models.CharField(max_length=45)
    code = models.SmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)


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
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

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
    uploaded_at = models.DateTimeField()
    user = models.CharField(max_length=45)
    seeders = models.IntegerField()
    leechers = models.IntegerField()
    img = models.CharField(max_length=255)
    magnet = models.CharField(max_length=255)
    nfo = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # movies (optional)
    rating = models.IntegerField(null=True, blank=True)
    rated_at = models.DateTimeField(null=True, blank=True)
    title_rating = models.CharField(max_length=255)
    resolution = models.IntegerField(null=True, blank=True)
    # series (optional)
    series_title = models.CharField(max_length=45, null=True, blank=True)
    series_season = models.IntegerField(null=True, blank=True)
    series_episode = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return '{0}'.format(self.title)


class UserTorrent(models.Model):
    user = models.ForeignKey(User)
    torrent = models.ForeignKey(Torrent)
    category = models.ForeignKey(Category)
    categoryGroup = models.ForeignKey(CategoryGroup)
    downloaded_at = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '{0} :|: {1}'.format(self.user, self.torrent)
