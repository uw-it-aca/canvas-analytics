from django.core.management.base import BaseCommand, CommandError
from analytics.report_builder import ReportBuilder


class Command(BaseCommand):
    help = "Create report of subaccount activity."

    def add_arguments(self, parser):
        parser.add_argument(
            '-a', '--account', action='store', dest='subaccount_id',
            default='uwcourse', help='Subaccount sis_id for the report')
        parser.add_argument(
            '-t', '--term', action='store', dest='term_id', default='',
            help='Term sis_id for the report')

    def handle(self, *args, **options):
        report_builder = ReportBuilder()

        subaccount_id = options['subaccount_id']
        term_id = options['term_id']

        report_builder.build_subaccount_activity_report(subaccount_id, term_id)
