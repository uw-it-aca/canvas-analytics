import logging
import traceback
from django.core.management.base import BaseCommand
from django.db import transaction
from data_aggregator.dao import CanvasDAO
from data_aggregator.models import Job, Participation


class Command(BaseCommand):

    help = ("Loads the participation data for a batch of jobs. Designed to "
            "be run as a cron that is constantly checking for new jobs.")

    def add_arguments(self, parser):
        parser.add_argument("--job_batch_size",
                            type=int,
                            help=("Number of jobs to process"),
                            default=10,
                            required=False)

    @transaction.atomic
    def run_job(self, job):
        try:
            # delete existing participation data in case of a job restart
            old_participation = Participation.objects.filter(job=job)
            old_participation.delete()
            # load participation data
            job.mark_start()
            canvas_course_id = job.context["canvas_course_id"]
            partics = (
                CanvasDAO().get_participation(canvas_course_id))
            for partic in partics:
                partic.job = job
            Participation.objects.bulk_create(partics)
            job.mark_end()
        except Exception:
            # save error message if one occurs
            job.message = traceback.format_exc()
            job.save()

    def handle(self, *args, **options):
        """
        Queries the Job model to check for unstarted jobs (jobs
        where pid=None and start=None). For a batch of unstarted jobs
        (default 10), queries the Canvas API for participation data and stores
        the returned data as Participation model instances.
        """
        logger = logging.getLogger(__name__)
        job_batch_size = options["job_batch_size"]
        jobs = Job.objects.start_batch_of_participation_jobs(
            batchsize=job_batch_size
        )
        if jobs:
            for job in jobs:
                self.run_job(job)
        else:
            logger.info("No active participation jobs.")
