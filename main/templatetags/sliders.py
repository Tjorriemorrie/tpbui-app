from django.template import Library, Node, Variable

register = Library()


@register.tag
def getSliderMovies(parser, token):
    tagName, rows = token.contents.split()
    return SliderMoviesNode(rows)

class SliderMoviesNode(Node):
    def __init__(self, rows):
        self.rows = Variable(rows)

    def render(self, context):
        self.rows = self.rows.resolve(context)
        movies = [row.record for row in self.rows if row.record.title_rating]
        # print movies
        movies = sorted(movies, key=lambda movie: movie.resolution, reverse=True)
        movies = sorted(movies, key=lambda movie: movie.seeders, reverse=True)
        movies = sorted(movies, key=lambda movie: movie.rating, reverse=True)
        movieTitles = []
        movieSliders = []
        for movie in movies:
            if movie.title_rating not in movieTitles:
                movieTitles.append(movie.title_rating)
                movieSliders.append(movie)
        context['sliderMovies'] = movieSliders[:6]
        return ''
