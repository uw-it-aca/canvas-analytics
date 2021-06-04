
import logging
from data_aggregator.management.commands._base import CreateJobCommand
from data_aggregator.utilities import datestring_to_datetime
from data_aggregator.models import Course, Job, JobType
from data_aggregator.utilities import get_default_target_start, \
    get_default_target_end
from django.db.models import Q
from uw_sws.term import get_current_term


class Command(CreateJobCommand):

    help = ("Creates assignment jobs for active courses in current term.")

    def handle(self, *args, **options):
        """
        Load assignments jobs for all active courses in the current term
        """

        canvas_course_id = options["canvas_course_id"]
        sis_course_id = options["sis_course_id"]
        target_start_time = options["target_start_time"]
        target_end_time = options["target_end_time"]

        if target_start_time is None:
            target_date_start = get_default_target_start()
        else:
            target_date_start = datestring_to_datetime(target_start_time)

        if target_end_time is None:
            target_date_end = get_default_target_end()
        else:
            target_date_end = datestring_to_datetime(target_end_time)

        # get assignment job type
        assignment_type, _ = JobType.objects.get_or_create(type="assignment")

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
