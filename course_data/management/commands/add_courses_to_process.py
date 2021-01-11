from django.core.management.base import BaseCommand
from course_data.logger import Logger
from course_data.models import Course, Job, JobType
from course_data import utilities
from uw_sws.term import get_current_term


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
        term_obj = get_current_term()
        week = utilities.get_week_of_term(term_obj.first_day_quarter)
        courses = utilities.read_courses(self.in_file)
        assignment_type, _ = JobType.objects.get_or_create(type="assignment")
        partic_type, _ = JobType.objects.get_or_create(type="participation")
        for course_id in courses:
            print("Adding jobs for course {}".format(course_id))
            c = Course()
            c.course_id = course_id
            c.year = term_obj.year
            c.quarter = term_obj.quarter
            c.save()
            job = Job()
            job.course = c
            job.week = week
            job.type = assignment_type
            job.save()
            job = Job()
            job.course = c
            job.week = week
            job.type = partic_type
            job.save()
