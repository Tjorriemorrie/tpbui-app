from main.models import *


class Scraper():


    def run(self):
        self.runDefault()


    def runDefault(self):
        '''
        For every category group scrape every category's first page
        :return:
        '''
        for categoryGroup in CategoryGroup.objects.all():
            for category in categoryGroup.category_set.all():
                self.runCategory(category)


    def runCategory(self, category, page=0):
        '''
        Scrape from the piratebay
        :param category:
        :param page:
        :return:
        '''
        html = self.scrape(category, page)


    def scrape(self, category, page):
