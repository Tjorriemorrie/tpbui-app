from django.template import Library, Node

register = Library()

class NavNode(Node):
    def render(self, context):
        from main.models import CategoryGroup
        context['categoryGroups'] = CategoryGroup.objects.all()
        return ''
    
@register.tag
def getNavCategoryGroups(parser, token):
    return NavNode()


class NavUrlLogout(Node):
    def render(self, context):
        from google.appengine.api import users
        context['urlLogout'] = users.create_logout_url('/')
        return ''

@register.tag
def getNavUrlLogout(parser, token):
    return NavUrlLogout()