import webapp2
from src.settings import JINJA_ENVIRONMENT


class Index(webapp2.RequestHandler):
    def get(self):
        template_values = {
            'nav': 'home',
        }
        template = JINJA_ENVIRONMENT.get_template('main/templates/index.html')
        self.response.write(template.render(template_values))
