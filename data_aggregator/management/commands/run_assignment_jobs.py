import logging
import traceback
from django.core.management.base import BaseCommand
from data_aggregator.dao import CanvasDAO
from data_aggregator.models import Job


class Command(BaseCommand):

    help = ("Loads the assignment data for a batch of jobs. Designed to "
            "be run as a cron that is constantly checking for new jobs.")

    def add_arguments(self, parser):
        parser.add_argument("--job_batch_size",
                            type=int,
                            help=("Number of jobs to process"),
                            default=10,
                            required=False)

    def handle(self, *args, **options):
        """
        Queries the AssignmentJob model to check for unstarted jobs (jobs
        where pid=None and start=None). For a batch of unstarted jobs
        (default 10), queries the Canvas API for assignment data and stores
        the returned data as Assignment model instances.
        """
        logger = logging.getLogger(__name__)
        job_batch_size = options["job_batch_size"]
        jobs = Job.objects.start_batch_of_assignment_jobs(
            batchsize=job_batch_size
        )
        if jobs:
            for job in jobs:
                try:
                    job.mark_start()
                    canvas_course_id = job.context["canvas_course_id"]
                    assignments = (
                        CanvasDAO().get_assignments(canvas_course_id))
                    for assign in assignments:
                        assign.job = job
                        assign.save()
                    job.mark_end()
                except Exception:
                    # save error message if one occurs
                    job.message = traceback.format_exc()
                    job.save()
        else:
            logger.info("No active assignment jobs.")
