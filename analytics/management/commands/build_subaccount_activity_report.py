from django.core.management.base import BaseCommand, CommandError               
from analytics.report_builder import ReportBuilder


class Command(BaseCommand):
    args = "<subaccount_id> <term_id>"
    help = "Create report of subaccount activity."

    def handle(self, *args, **options):
        report_builder = ReportBuilder()
        
        if len(args) == 2:
            subaccount_id = args[0]
            term_id = args[1]
        else:
            raise CommandError("build_subaccount_activity_report <subaccount_id> <term_id>")

        report_builder.build_subaccount_activity_report(subaccount_id, term_id)
