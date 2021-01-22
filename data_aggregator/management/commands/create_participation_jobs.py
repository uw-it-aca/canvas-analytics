
from django.core.management.base import BaseCommand
from data_aggregator.logger import Logger
from data_aggregator.models import Course, Job, JobType
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from uw_sws.term import get_current_term


class Command(BaseCommand):

    help = ("Creates participation jobs for active courses in current term.")

    def add_arguments(self, parser):
        parser.add_argument("--log_file",
                            type=str,
                            help=("Path of log file. If no log path is "
                                  "supplied then stdout is used"),
                            required=False)

    def handle(self, *args, **options):
        """
        Load assignments jobs for all active courses in the current term
        """
        self.logger = Logger(logpath=options["log_file"])

        # get participation job type
        partic_type, _ = JobType.objects.get_or_create(type="participation")

        # set target bounds from monday to sunday (work week)
        today = timezone.now().date()
        target_date_start = today - timedelta(days=today.weekday())
        target_date_end = target_date_start + timedelta(days=6)

        jobs_count = 0
        sws_term = get_current_term()
        courses = (Course.objects.filter(
            Q(status='active') & Q(term__sis_term_id=sws_term.canvas_sis_id()))
        )
        course_count = courses.count()
        if course_count == 0:
            self.logger.info(
                f'No active courses in term {sws_term.canvas_sis_id()} to '
                f'create participation jobs for.')
        else:
            for course in courses:
                # create participation jobs
                self.logger.info(
                    f"Adding participation jobs for course "
                    f"{course.canvas_course_id}")
                job = Job()
                job.type = partic_type
                job.target_date_start = target_date_start
                job.target_date_end = target_date_end
                job.context = {'canvas_course_id': course.canvas_course_id}
                job.save()
                jobs_count += 1
        self.logger.info(f'Created {jobs_count} participation jobs.')