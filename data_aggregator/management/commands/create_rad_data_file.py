from django.core.management.base import BaseCommand
from data_aggregator.dao import LoadRadDAO


class Command(BaseCommand):

    help = ("Loads normalized Canvas assignment and participation analytics "
            "into RAD.")

    def handle(self, *args, **options):
        lrd = LoadRadDAO()
        rcd = lrd.get_rad_df()
        file_name = "rad_data/{}-week-{}-rad-data.csv".format(lrd.curr_term,
                                                              lrd.curr_week)
        file_obj = rcd.to_csv(sep=",", index=False, encoding="UTF-8")
        lrd.upload_to_gcs_bucket(file_name, file_obj)
