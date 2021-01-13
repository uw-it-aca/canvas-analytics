from django.core.management.base import BaseCommand
from course_data.logger import Logger
from course_data.dao import CanvasDAO
from course_data.models import Job


class Command(BaseCommand):

    help = ("Loads the assignment data for a batch of jobs. Designed to "
            "be run as a cron that is constantly checking for new jobs.")

    def add_arguments(self, parser):
        parser.add_argument("--log_file",
                            type=str,
                            help=("Path of log file. If no log path is "
                                  "supplied then stdout is used"),
                            required=False)

    def handle(self, *args, **options):
        """
        Queries the AssignmentJob model to check for unstarted jobs (jobs
        where pid=None and start=None). For a batch of unstarted jobs
        (default 10), queries the Canvas API for assignment data and stores
        the returned data as Assignment model instances.
        """
        self.logger = Logger(logpath=options["log_file"])
        jobs = Job.objects.start_batch_of_assignment_jobs()
        if jobs:
            for job in jobs:
                try:
                    job.mark_start()
                    course_id = job.context["course_id"]
                    assignments = (CanvasDAO().get_assignments(course_id))
                    for assign in assignments:
                        assign.job = job
                        assign.save()
                    job.mark_end()
                except Exception as e:
                    # save error message if one occurs
                    job.message = e.message
                    job.save()
