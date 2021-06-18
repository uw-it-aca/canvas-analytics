import logging
import traceback
from django.conf import settings
from django.core.management.base import BaseCommand
from data_aggregator.models import Job, JobType, Course, Term, Week
from data_aggregator.utilities import datestring_to_datetime
from multiprocessing.dummy import Pool as ThreadPool


class RunJobCommand(BaseCommand):

    job_type = ''

    def add_arguments(self, parser):
        parser.add_argument("--job_batch_size",
                            type=int,
                            help=("Number of jobs to process. Default is all "
                                  "jobs."),
                            default=None,
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
            job.start_job()
            self.work(job)
        except Exception as err:
            # save error message if one occurs
            tb = traceback.format_exc()
            if tb:
                job.message = tb
                logging.error(tb)
            else:
                # Just in case the trace back is empty
                msg = f"Unknown exception occured: {err}"
                job.message = msg
                logging.error(msg)
            job.save()
        else:
            job.end_job()

    def handle(self, *args, **options):
        """
        Queries the Job model to check for unstarted jobs (jobs
        where pid=None and start=None). For a batch of unstarted jobs,
        calls the run_job method for each job.
        """
        num_parallel_jobs = options["num_parallel_jobs"]
        job_batch_size = options["job_batch_size"]  # defaults to all jobs

        jobs = Job.objects.claim_batch_of_jobs(
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
                        msg = f"Unknown exception occured: {err}"
                        job.message = msg
                        logging.error(msg)
                    job.save()


class CreateJobCommand(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("--sis_term_id",
                            type=str,
                            help=("Term to create jobs for."),
                            default=None,
                            required=False)
        parser.add_argument("--week",
                            type=int,
                            help=("Week to create jobs for."),
                            default=None,
                            required=False)
        parser.add_argument("--canvas_course_id",
                            type=int,
                            help=("Canvas course id to create a job for."),
                            default=None,
                            required=False)
        parser.add_argument("--sis_course_id",
                            type=int,
                            help=("Canvas sis-course-id to create a job for."),
                            default=None,
                            required=False)
        parser.add_argument("--target_start_time",
                            type=str,
                            help=("iso8601 UTC start time for which the job "
                                  "is active. YYYY-mm-ddTHH:MM:SS.ss"),
                            default=None,
                            required=False)
        parser.add_argument("--target_end_time",
                            type=str,
                            help=("iso8601 UTC end time for which the job "
                                  "is active. YYYY-mm-ddTHH:MM:SS.ss"),
                            default=None,
                            required=False)

    def create(self, options, analytic_type):
        sis_term_id = options["sis_term_id"]
        week_num = options["week"]
        canvas_course_id = options["canvas_course_id"]
        sis_course_id = options["sis_course_id"]
        target_start_time = options["target_start_time"]
        target_end_time = options["target_end_time"]


        job = Job()
        if target_start_time is None:
            target_date_start = job.get_default_target_start()
        else:
            target_date_start = datestring_to_datetime(target_start_time)

        if target_end_time is None:
            target_date_end = job.get_default_target_end()
        else:
            target_date_end = datestring_to_datetime(target_end_time)

        # get job type
        job_type, _ = JobType.objects.get_or_create(type=analytic_type)

        if sis_term_id and week_num and canvas_course_id and sis_course_id:
            logging.debug(
                f"Adding {analytic_type} job for course "
                f"{canvas_course_id}")
            job.type = job_type
            job.target_date_start = target_date_start
            job.target_date_end = target_date_end
            job.context = {'canvas_course_id': canvas_course_id,
                           'sis_course_id': sis_course_id,
                           'sis_term_id': sis_term_id,
                           'week': week_num}
            job.save()
        else:
            term, _ = Term.objects.get_or_create_term_from_sis_term_id(
                sis_term_id=sis_term_id)
            week, _ = Week.objects.get_or_create_week(sis_term_id=sis_term_id,
                                                      week_num=week_num)
            courses = Course.objects.filter(status='active').filter(term=term)
            course_count = courses.count()
            if course_count == 0:
                logging.warning(
                    f'No active courses in term {term.sis_term_id} to '
                    f'create {analytic_type} jobs for.')
            else:
                jobs_count = 0
                for course in courses:
                    # create jobs
                    logging.debug(
                        f"Adding {analytic_type} jobs for course "
                        f"{course.sis_course_id} ({course.canvas_course_id})")
                    job = Job()
                    job.type = job_type
                    job.target_date_start = target_date_start
                    job.target_date_end = target_date_end
                    job.context = {'canvas_course_id': course.canvas_course_id,
                                   'sis_course_id': course.sis_course_id,
                                   'sis_term_id': term.sis_term_id,
                                   'week': week.week}
                    job.save()
                    jobs_count += 1
                logging.info(f'Created {jobs_count} {analytic_type} jobs.')


class CreateDBViewCommand(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("--sis_term_id",
                            type=str,
                            help=("Term to generate db view for."),
                            default=None,
                            required=False)
        parser.add_argument("--week",
                            type=int,
                            help=("Week to generate db view for."),
                            default=None,
                            required=False)

    def create(self, sis_term_id, week):
        return NotImplementedError()

    def handle(self, *args, **options):
        """
        Create db view for given term and week
        """
        sis_term_id = options["sis_term_id"]
        week_num = options["week"]
        term, _ = Term.objects.get_or_create_term_from_sis_term_id(
            sis_term_id=sis_term_id)
        week, _ = Week.objects.get_or_create_week(sis_term_id=sis_term_id,
                                                  week_num=week_num)
        self.create(term.sis_term_id, week.week)
