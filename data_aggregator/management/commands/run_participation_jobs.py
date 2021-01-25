import traceback
from django.core.management.base import BaseCommand
from data_aggregator.logger import Logger
from data_aggregator.dao import CanvasDAO
from data_aggregator.models import Job


class Command(BaseCommand):

    help = ("Loads the participation data for a batch of jobs. Designed to "
            "be run as a cron that is constantly checking for new jobs.")

    def add_arguments(self, parser):
        parser.add_argument("--job_batch_size",
                            type=int,
                            help=("Number of jobs to process"),
                            default=10,
                            required=False)
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
        self.job_batch_size = options["job_batch_size"]
        jobs = Job.objects.start_batch_of_participation_jobs(
            batchsize=self.job_batch_size
        )
        if jobs:
            for job in jobs:
                try:
                    job.mark_start()
                    canvas_course_id = job.context["canvas_course_id"]
                    partics = (
                        CanvasDAO().get_participation(canvas_course_id))
                    for partic in partics:
                        partic.job = job
                        partic.save()
                    job.mark_end()
                except Exception:
                    # save error message if one occurs
                    job.message = traceback.format_exc()
                    job.save()
        else:
            self.logger.info("No active participation jobs.")
