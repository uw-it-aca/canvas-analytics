import logging
import traceback
from django.conf import settings
from django.core.management.base import BaseCommand
from data_aggregator.models import Job
from multiprocessing.dummy import Pool as ThreadPool


class RunJobCommand(BaseCommand):

    job_type = ''

    def add_arguments(self, parser):
        parser.add_argument("--job_batch_size",
                            type=int,
                            help=("Number of jobs to process"),
                            default=100,
                            required=False)
        parser.add_argument("--num_parallel_jobs",
                            type=int,
                            help=("Size of job thread pool"),
                            default=20,
                            required=False)

    def work(self, job):
        '''
        Job work is performed here.
        '''
        raise NotImplementedError()

    def run_job(self, job):
        try:
            self.work(job)
        except Exception as err:
            # save error message if one occurs
            tb = traceback.format_exc()
            if tb:
                job.message = tb
                logging.error(tb)
            else:
                # Just in case the trace back is empty
                msg = "Unknown exception occured: {}".format(err)
                job.message = msg
                logging.error(msg)
            job.save()
        else:
            job.mark_end()

    def handle(self, *args, **options):
        """
        Queries the Job model to check for unstarted jobs (jobs
        where pid=None and start=None). For a batch of unstarted jobs,
        calls the run_job method for each job.
        """
        num_parallel_jobs = options["num_parallel_jobs"]
        job_batch_size = options["job_batch_size"]
        jobs = Job.objects.start_batch_of_jobs(
            self.job_type,
            batchsize=job_batch_size
        )
        try:
            if jobs:
                if settings.DATA_AGGREGATOR_THREADING_ENABLED:
                    with ThreadPool(processes=num_parallel_jobs) as pool:
                        pool.map(self.run_job, jobs)
                else:
                    if num_parallel_jobs > 1:
                        logging.warning(
                            "Running single threaded. Multithreading is "
                            "disabled in Django settings.")
                    for job in jobs:
                        self.run_job(job)
            else:
                logging.debug(f"No active {self.job_type} jobs.")
        except Exception as err:
            for job in jobs:
                if not job.message:
                    # save error message if one occurs but don't overwrite 
                    # an existing error
                    tb = traceback.format_exc()
                    if tb:
                        job.message = tb
                        logging.error(tb)
                    else:
                        # Just in case the trace back is empty
                        msg = "Unknown exception occured: {}".format(err)
                        job.message = msg
                        logging.error(msg)
                    job.save()
