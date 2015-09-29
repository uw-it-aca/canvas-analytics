from django.core.management.base import BaseCommand, CommandError
from analytics.weekly_data_builder import build_data


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        build_data()
