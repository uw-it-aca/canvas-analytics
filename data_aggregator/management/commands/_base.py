import logging
import traceback
from django.core.management.base import BaseCommand
from data_aggregator.models import Job


class RunJobCommand(BaseCommand):

    job_type = ''

    def add_arguments(self, parser):
        parser.add_argument("--job_batch_size",
                            type=int,
                            help=("Number of jobs to process"),
                            default=10,
                            required=False)

    def run_job(self, job):
        '''
        Job work is performed here
        '''
        raise NotImplementedError()

    def handle(self, *args, **options):
        """
        Queries the Job model to check for unstarted jobs (jobs
        where pid=None and start=None). For a batch of unstarted jobs
        (default 10), calls the run_job method for each job.
        """
        self.logger = logging.getLogger(__name__)
        job_batch_size = options["job_batch_size"]
        jobs = Job.objects.start_batch_of_jobs(
            self.job_type,
            batchsize=job_batch_size
        )
        if jobs:
            for job in jobs:
                try:
                    self.run_job(job)
                except Exception:
                    # save error message if one occurs
                    tb = traceback.format_exc()
                    job.message = tb
                    job.save()
                    self.logger.error(tb)
                else:
                    job.mark_end()
        else:
            self.logger.info(f"No active {self.job_type} jobs.")
