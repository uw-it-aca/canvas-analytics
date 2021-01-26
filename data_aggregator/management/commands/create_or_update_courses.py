
import logging
from csv import DictReader
from django.core.management.base import BaseCommand
from data_aggregator.models import Term, Course
from data_aggregator.dao import CanvasDAO
from uw_sws.term import get_current_term


class Command(BaseCommand):

    help = ("Loads or updates list of courses for the current term.")

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)

        # get the current term object from sws
        sws_term = get_current_term()
        # get provising data and load courses
        sis_data = CanvasDAO().get_canvas_course_provisioning_report(
            sws_term.canvas_sis_id())
        course_count = 0
        for row in DictReader(sis_data):
            if not len(row):
                continue
            canvas_course_id = row['canvas_course_id']
            sis_course_id = row['course_id']
            short_name = row['short_name']
            long_name = row['long_name']
            canvas_account_id = row['canvas_account_id']
            sis_account_id = row['account_id']
            canvas_term_id = row['canvas_term_id']
            status = row['status']
            created_by_sis = row['created_by_sis']
            if created_by_sis:
                # get or create current term
                term, created_term = Term.objects.get_create_current_term(
                    canvas_term_id, sws_term=sws_term)
                if created_term:
                    logger.info(f"Created term - {canvas_term_id}")
                # create / update course
                course, created_course = Course.objects.get_or_create(
                    canvas_course_id=canvas_course_id,
                    term=term)
                if created_course:
                    logger.info(f"Created course - {canvas_course_id}")
                else:
                    logger.info(f"Updated course - {canvas_course_id}")
                # we always update the course regardless if it is new or not
                course.sis_course_id = sis_course_id
                course.short_name = short_name
                course.long_name = long_name
                course.canvas_account_id = canvas_account_id
                course.sis_account_id = sis_account_id
                course.status = status
                course.save()
                course_count += 1
        logger.info(f'Created and/or updated {course_count} courses.')
