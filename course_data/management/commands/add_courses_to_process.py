
from csv import DictReader
from django.core.management.base import BaseCommand
from course_data.logger import Logger
from course_data.models import Term, Course, Job, JobType
from course_data.dao import CanvasDAO
from django.utils import timezone
from datetime import timedelta
from uw_sws.term import get_current_term


class Command(BaseCommand):

    help = ("Loads the list of courses to process from SWS.")

    def add_arguments(self, parser):
        parser.add_argument("--log_file",
                            type=str,
                            help=("Path of log file. If no log path is "
                                  "supplied then stdout is used"),
                            required=False)

    def handle(self, *args, **options):
        """
        Load assignments and participation for the list of courses
        """
        self.logger = Logger(logpath=options["log_file"])

        # get job types
        assignment_type, _ = JobType.objects.get_or_create(type="assignment")
        partic_type, _ = JobType.objects.get_or_create(type="participation")

        # set target bounds from monday to sunday (work week)
        today = timezone.now().date()
        target_date_start = today - timedelta(days=today.weekday())
        target_date_end = target_date_start + timedelta(days=6)

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
                    self.logger.info(f"Created term - {canvas_term_id}")
                # create / update course
                course, created_course = Course.objects.get_or_create(
                    canvas_course_id=canvas_course_id,
                    term=term)
                if created_course:
                    self.logger.info(f"Created course - {canvas_course_id}")
                else:
                    self.logger.info(f"Updated course - {canvas_course_id}")
                # we always update the course regardless if it is new or not
                course.sis_course_id = sis_course_id
                course.short_name = short_name
                course.long_name = long_name
                course.canvas_account_id = canvas_account_id
                course.sis_account_id = sis_account_id
                course.status = status
                course.save()
                course_count += 1
                if status == 'active':
                    # create assignment and participation jobs
                    self.logger.info(
                        f"Adding jobs for course {canvas_course_id}")
                    job = Job()
                    job.type = assignment_type
                    job.target_date_start = target_date_start
                    job.target_date_end = target_date_end
                    job.context = {'canvas_course_id': canvas_course_id}
                    job.save()
                    job = Job()
                    job.type = partic_type
                    job.target_date_start = target_date_start
                    job.target_date_end = target_date_end
                    job.context = {'canvas_course_id': canvas_course_id}
                    job.save()
        self.logger.info(f'Created and/or updated {course_count} courses.')
