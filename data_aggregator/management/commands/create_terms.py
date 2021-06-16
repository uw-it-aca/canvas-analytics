from django.core.management.base import BaseCommand
from data_aggregator.dao import BaseDAO


class Command(BaseCommand):

    help = ("Creates current term and all future terms.")

    def handle(self, *args, **options):
        BaseDAO().create_terms()
