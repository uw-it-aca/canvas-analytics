from django.core.management.base import BaseCommand
from data_aggregator.dao import LoadRadDAO


class Command(BaseCommand):

    help = ("Loads normalized Canvas assignment and participation analytics "
            "into RAD.")

    def add_arguments(self, parser):
        parser.add_argument("--sis_term_id",
                            type=str,
                            help=("Term to generate RAD file for."),
                            default=None,
                            required=False)
        parser.add_argument("--week",
                            type=int,
                            help=("Week to generate RAD file for."),
                            default=None,
                            required=False)

    def handle(self, *args, **options):
        sis_term_id = options["sis_term_id"]
        week_num = options["week"]
        LoadRadDAO().create_rad_data_file(sis_term_id=sis_term_id,
                                          week_num=week_num)
