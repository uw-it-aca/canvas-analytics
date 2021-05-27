
import logging
from django.core.management.base import BaseCommand
from data_aggregator.models import Course, Job, JobType
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, time, timedelta
from uw_sws.term import get_current_term


class Command(BaseCommand):

    help = ("Creates assignment jobs for active courses in current term.")

    def add_arguments(self, parser):
        parser.add_argument("--canvas_course_id",
                            type=int,
                            help=("Canvas course id to create a job for."),
                            default=None,
                            required=False)
        parser.add_argument("--sis_course_id",
                            type=int,
                            help=("Canvas sis-course-id to create a job for."),
                            default=None,
                            required=False)

    def handle(self, *args, **options):
        """
        Load assignments jobs for all active courses in the current term
        """

        canvas_course_id = options["canvas_course_id"]
        sis_course_id = options["sis_course_id"]

        # get assignment job type
        assignment_type, _ = JobType.objects.get_or_create(type="assignment")

        # make job active for the current day
        today = timezone.now().date()
        target_date_start = datetime.combine(today, time(00, 00, 00))
        target_date_end = datetime.combine(today, time(23, 59, 59))

        if canvas_course_id and sis_course_id:
            logging.info(
                f"Adding assignment job for course "
                f"{canvas_course_id}")
            job = Job()
            job.type = assignment_type
            job.target_date_start = target_date_start
            job.target_date_end = target_date_end
            job.context = {'canvas_course_id': canvas_course_id,
                           'sis_course_id': sis_course_id}
            job.save()
        else:
            sws_term = get_current_term()
            courses = (Course.objects.filter(
                Q(status='active') &
                Q(term__sis_term_id=sws_term.canvas_sis_id()))
            )
            course_count = courses.count()
            if course_count == 0:
                logging.info(
                    f'No active courses in term {sws_term.canvas_sis_id()} to '
                    f'create assignment jobs for.')
            else:
                jobs_count = 0
                for course in courses:
                    # create assignment jobs
                    logging.info(
                        f"Adding assignment jobs for course "
                        f"{course.sis_course_id} ({course.canvas_course_id})")
                    job = Job()
                    job.type = assignment_type
                    job.target_date_start = target_date_start
                    job.target_date_end = target_date_end
                    job.context = {'canvas_course_id': course.canvas_course_id,
                                   'sis_course_id': course.sis_course_id}
                    job.save()
                    jobs_count += 1
                logging.info(f'Created {jobs_count} assignment jobs.')
