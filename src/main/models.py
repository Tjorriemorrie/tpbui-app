from google.appengine.ext import ndb



class Painting(ndb.Model):
    CHOICES_GALLERIES = ['figures', 'abstract', 'flowers', 'cityscapes', 'landscapes', 'cafe', 'unique']
    image = ndb.BlobProperty()
    image_name = ndb.StringProperty()
    gallery = ndb.StringProperty(choices=CHOICES_GALLERIES)
    name = ndb.StringProperty(default='')
    description = ndb.StringProperty(default='')
    price = ndb.IntegerProperty()
    special = ndb.BooleanProperty(default=False)
    sold = ndb.BooleanProperty(default=False)
    copy = ndb.BooleanProperty(default=False)
    copy_price = ndb.IntegerProperty()
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    updated_at = ndb.DateTimeProperty(auto_now=True)

    def __unicode__(self):
        return self.name