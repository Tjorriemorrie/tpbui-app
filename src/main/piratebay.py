import logging
from src.main.models import CategoryGroup, Category
from src.settings import CATEGORIES


class PirateBay():

    @staticmethod
    def createCategories():
        for group in CATEGORIES:
            # group
            key_name = '{0}_{1}'.format(group['code'], group['name'])
            categoryGroup = CategoryGroup.get_or_insert(key_name, code=group['code'], name=group['name'])
            logging.info('Category Group {0}'.format(categoryGroup))

            # categories
            for category_info in group['categories']:
                category_info['category_group'] = categoryGroup
                key_name = '{0}_{1}'.format(category_info['code'], category_info['name'])
                category = Category.get_or_insert(key_name, code=category_info['code'], name=category_info['name'], category_group=categoryGroup)
                logging.info('Category {0}'.format(category))