# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

import logging
import traceback
from django.conf import settings
from django.core.management.base import BaseCommand
from data_aggregator.management.commands._mixins import RunJobMixin
from data_aggregator.models import AnalyticTypes, Job, JobType, TaskTypes, \
    Term
from data_aggregator.utilities import datestring_to_datetime, get_relative_week
from data_aggregator.dao import JobDAO, TaskDAO
from data_aggregator.threads import ThreadPool


class RunJobCommand(BaseCommand, RunJobMixin):

    def add_arguments(self, parser):
        parser.add_argument("job_name",
                            type=str,
                            choices=[
                                AnalyticTypes.assignment,
                                AnalyticTypes.participation,
                                TaskTypes.create_terms,
                                TaskTypes.create_or_update_users,
                                TaskTypes.create_or_update_courses,
                                TaskTypes.create_or_update_advisers,
                                TaskTypes.create_assignment_db_view,
                                TaskTypes.create_participation_db_view,
                                TaskTypes.create_rad_db_view,
                                TaskTypes.create_rad_data_file,
                                TaskTypes.build_subaccount_activity_report],
                            help=("Name of job to run."))
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

    def handle(self, *args, **options):
        """
        Queries the Job model to check for unstarted jobs (jobs
        where pid=None and start=None). For a batch of unstarted jobs,
        calls the run_job method for each job.
        """
        job_name = options["job_name"]  # required
        num_parallel_jobs = options["num_parallel_jobs"]
        job_batch_size = options["job_batch_size"]  # defaults to all jobs

        jobs = Job.objects.claim_batch_of_jobs(
            job_name,
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
                logging.debug(f"No active {job_name} jobs.")
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

    def _add_subparser(self, subparsers, command_name,
                       command_help_message=None,
                       include_term=True, include_week=False,
                       include_course=False, include_account=False):
        subparser = subparsers.add_parser(
            command_name,
            help=(command_help_message if command_help_message else
                  f"Run {command_name} command")
        )
        # we add the job name as a hidden argument so that it can be read
        # when processing the command
        if include_week or include_term:
            # use current term and week of term as the default
            term, _ = Term.objects.get_or_create_term_from_sis_term_id()
            default_sis_term_id = term.sis_term_id
            default_week = get_relative_week(term.first_day_quarter,
                                             tz_name="US/Pacific")
        if include_term:
            subparser.add_argument(
                "--sis_term_id",
                type=str,
                help=("Term to run job for."),
                default=default_sis_term_id)
        if include_week:
            subparser.add_argument(
                "--week",
                type=int,
                help=("Week to run job for."),
                default=default_week)
        if include_course:
            subparser.add_argument(
                "--canvas_course_id",
                type=int,
                help=("Canvas course id to create a job for."),
                default=None,
                required=False)
            subparser.add_argument(
                "--sis_course_id",
                type=str,
                help=("The sis-course-id to create a job for."),
                default=None,
                required=False)
        if include_account:
            subparser.add_argument(
                '--subaccount_id',
                type=str,
                default='uwcourse',
                help='The subaccount to create a job for.')
        subparser.add_argument("--target_start_time",
                               type=str,
                               help=("iso8601 UTC start time for which the "
                                     "job is active. YYYY-mm-ddTHH:MM:SS.ss"),
                               default=None,
                               required=False)
        subparser.add_argument("--target_end_time",
                               type=str,
                               help=("iso8601 UTC end time for which the job "
                                     "is active. YYYY-mm-ddTHH:MM:SS.ss"),
                               default=None,
                               required=False)
        return subparsers

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(title="job_name",
                                           dest="job_name")
        subparsers.required = True

        subparsers = self._add_subparser(
            subparsers, TaskTypes.create_terms,
            include_term=False,
            command_help_message=(
                "Creates current term and all future terms."
            ))

        subparsers = self._add_subparser(
            subparsers, TaskTypes.create_or_update_courses,
            command_help_message=(
                "Loads or updates list of courses for the current term."
            ))

        subparsers = self._add_subparser(
            subparsers, TaskTypes.create_or_update_users,
            command_help_message=(
                "Loads or updates list of students for the current term."
            ))

        subparsers = self._add_subparser(
            subparsers, TaskTypes.create_or_update_advisers,
            command_help_message=(
                "Loads or updates list of advisers for all students in the db."
            ))

        subparsers = self._add_subparser(
            subparsers, TaskTypes.create_participation_db_view,
            include_week=True)

        subparsers = self._add_subparser(
            subparsers, TaskTypes.create_assignment_db_view, include_week=True)

        subparsers = self._add_subparser(
            subparsers, TaskTypes.create_rad_db_view, include_week=True)

        subparsers = self._add_subparser(
            subparsers, TaskTypes.create_rad_data_file, include_week=True)

        subparsers = self._add_subparser(
            subparsers, TaskTypes.build_subaccount_activity_report,
            include_week=True,
            include_account=True)

        subparsers = self._add_subparser(
            subparsers, AnalyticTypes.assignment,
            include_week=True, include_course=True)

        subparsers = self._add_subparser(
            subparsers, AnalyticTypes.participation,
            include_week=True, include_course=True)

    def get_job_context(self, options):
        context = {}
        for key, value in options.items():
            if value is not None:
                context[key] = value
        # don't include the job_name in the context since it is implied through
        # the job type
        context.pop("job_name")
        # remove django options from context
        context.pop("verbosity", None)
        context.pop("settings", None)
        context.pop("pythonpath", None)
        context.pop("traceback", None)
        context.pop("no_color", None)
        context.pop("force_color", None)
        context.pop("skip_checks", None)
        return context

    def create(self, options):
        job_name = options['job_name']
        target_start_time = options.get("target_start_time")
        target_end_time = options.get("target_end_time")

        if target_start_time is None:
            target_date_start = Job.get_default_target_start()
        else:
            target_date_start = datestring_to_datetime(target_start_time)

        if target_end_time is None:
            target_date_end = Job.get_default_target_end()
        else:
            target_date_end = datestring_to_datetime(target_end_time)

        context = self.get_job_context(options)

        jobs = []
        job_type, _ = JobType.objects.get_or_create(type=job_name)
        if job_type.type == AnalyticTypes.assignment or \
                job_type.type == AnalyticTypes.participation:
            jobs = JobDAO().create_analytic_jobs(
                job_type, target_date_start, target_date_end, context=context)
        else:
            # creates a single job or the given job type, target dates, and
            # context
            job = JobDAO().create_job(job_type, target_date_start,
                                      target_date_end, context=context)
            jobs.append(job)
        return jobs
