from django.core.management.base import BaseCommand
from data_aggregator.dao import TaskDAO


class Command(BaseCommand):

    help = ("Loads or updates list of courses for the current term.")

    def add_arguments(self, parser):
        parser.add_argument("--sis_term_id",
                            type=str,
                            help=("Term to update courses for."),
                            default=None,
                            required=False)

    def handle(self, *args, **options):
        sis_term_id = options["sis_term_id"]
        TaskDAO().create_or_update_courses(sis_term_id=sis_term_id)
