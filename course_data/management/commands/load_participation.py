from django.core.management.base import BaseCommand
from course_data.logger import Logger
from course_data.dao import CanvasDAO
from course_data.models import Job


class Command(BaseCommand):

    help = ("Loads the participation data for a batch of jobs. Designed to "
            "be run as a cron that is constantly checking for new jobs.")

    def add_arguments(self, parser):
        parser.add_argument("--log_file",
                            type=str,
                            help=("Path of log file. If no log path is "
                                  "supplied then stdout is used"),
                            required=False)

    def handle(self, *args, **options):
        """
        Queries the ParticipationJob model to check for unstarted jobs (jobs
        where pid=None and start=None). For a batch of unstarted jobs
        (default 10), queries the Canvas API for participation data and stores
        the returned data as Participation model instances.
        """
        self.logger = Logger(logpath=options["log_file"])
        jobs = Job.objects.start_batch_of_participation_jobs()
        if jobs:
            for job in jobs:
                partics = CanvasDAO().get_participation(
                    job.course.course_id)
                for partic in partics:
                    partic.course = job.course
                    partic.job = job
                    partic.save()
                job.mark_end()
