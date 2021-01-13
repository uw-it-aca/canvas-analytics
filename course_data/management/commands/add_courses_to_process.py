from django.core.management.base import BaseCommand
from course_data.logger import Logger
from course_data.models import Term, Course, Job, JobType
from course_data import utilities
from uw_sws.term import get_current_term
from datetime import datetime, timedelta


class Command(BaseCommand):

    help = ("Loads the list of courses to process from SWS.")

    def add_arguments(self, parser):
        parser.add_argument("--infile",
                            type=str,
                            help="List of course codes",
                            required=True)
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
        self.in_file = options["infile"]
        # get current term for course
        curr_term = get_current_term()
        term, _ = Term.objects.get_or_create(
            year=curr_term.year,
            quarter=curr_term.quarter,
            label=curr_term.term_label(),
            last_day_add=curr_term.last_day_add,
            last_day_drop=curr_term.last_day_drop,
            first_day_quarter=curr_term.first_day_quarter,
            census_day=curr_term.census_day,
            last_day_instruction=curr_term.last_day_instruction,
            grading_period_open=curr_term.grading_period_open,
            aterm_grading_period_open=curr_term.aterm_grading_period_open,
            grade_submission_deadline=curr_term.grade_submission_deadline,
            last_final_exam_date=curr_term.last_final_exam_date,
        )
        # get job types
        assignment_type, _ = JobType.objects.get_or_create(type="assignment")
        partic_type, _ = JobType.objects.get_or_create(type="participation")
        # set target bounds from monday to sunday (work week)
        today = datetime.now().date()
        target_date_start = today - timedelta(days=today.weekday())
        target_date_end = target_date_start + timedelta(days=6)

        courses = utilities.read_courses(self.in_file)
        for course_id in courses:
            print("Adding jobs for course {}".format(course_id))
            # create course record if it doesn't exist for the given term
            Course.objects.get_or_create(
                course_id=course_id,
                term=term)
            job = Job()
            job.type = assignment_type
            job.target_date_start = target_date_start
            job.target_date_end = target_date_end
            job.context = {'course_id': course_id}
            job.save()
            job = Job()
            job.type = partic_type
            job.target_date_start = target_date_start
            job.target_date_end = target_date_end
            job.context = {'course_id': course_id}
            job.save()
