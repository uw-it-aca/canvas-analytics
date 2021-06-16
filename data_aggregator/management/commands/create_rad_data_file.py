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

        lrd = LoadRadDAO()
        rcd = lrd.get_rad_df(sis_term_id=sis_term_id, week_num=week_num)
        file_name = "rad_data/{}-week-{}-rad-data.csv".format(lrd.curr_term,
                                                              lrd.curr_week)
        file_obj = rcd.to_csv(sep=",", index=False, encoding="UTF-8")
        lrd.upload_to_gcs_bucket(file_name, file_obj)
