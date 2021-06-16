from django.core.management.base import BaseCommand
from data_aggregator.dao import BaseDAO


class Command(BaseCommand):

    help = ("Creates current term and all future terms.")

    def add_arguments(self, parser):
        parser.add_argument("--sis_term_id",
                            type=str,
                            help=("Starting term to create entries for."),
                            default=None,
                            required=False)

    def handle(self, *args, **options):
        sis_term_id = options["sis_term_id"]
        BaseDAO().create_terms(sis_term_id=sis_term_id)
