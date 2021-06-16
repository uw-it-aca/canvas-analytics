
import logging
from csv import DictReader
from django.core.management.base import BaseCommand
from data_aggregator.models import Course, Term
from data_aggregator.dao import CanvasDAO


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
        term, _ = Term.objects.get_or_create_term(sis_term_id=sis_term_id)

        cd = CanvasDAO()
        # get provising data and load courses
        sis_data = \
            cd.download_course_provisioning_report(sis_term_id=sis_term_id)
        course_count = 0
        for row in DictReader(sis_data):
            if not len(row):
                continue
            created_by_sis = row['created_by_sis']
            if created_by_sis:
                canvas_course_id = row['canvas_course_id']
                # create / update course
                course, created_course = Course.objects.get_or_create(
                    canvas_course_id=canvas_course_id,
                    term=term)
                if created_course:
                    logging.info(f"Created course - {canvas_course_id}")
                else:
                    logging.info(f"Updated course - {canvas_course_id}")
                # we always update the course regardless if it is new or not
                course.sis_course_id = row['course_id']
                course.short_name = row['short_name']
                course.long_name = row['long_name']
                course.canvas_account_id = row['canvas_account_id']
                course.sis_account_id = row['account_id']
                course.status = row['status']
                course.save()
                course_count += 1
        logging.info(f'Created and/or updated {course_count} courses.')
