# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


import logging
import os
import pymssql
from csv import DictReader
from django.conf import settings
from django.db import transaction, connection
from data_aggregator.models import Adviser, AdviserTypes, Assignment, Course, \
    Participation, TaskTypes, User, RadDbView, Term, Week, AnalyticTypes, \
    Job, CompassDbView
from data_aggregator.utilities import get_view_name, set_gcs_base_path, \
    get_term_number
from data_aggregator.report_builder import ReportBuilder
from restclients_core.exceptions import DataFailureException
from restclients_core.util.retry import retry
from uw_canvas import Canvas
from uw_canvas.analytics import Analytics
from uw_canvas.courses import Courses
from uw_canvas.enrollments import Enrollments
from uw_canvas.reports import Reports
from uw_canvas.terms import Terms
from uw_sws.term import get_current_term, get_term_after, \
    get_term_by_year_and_quarter
from uw_sws import PWS
from uw_sws.adviser import get_advisers_by_regid

import numpy as np
import pandas as pd
from io import IOBase, StringIO
from boto3 import client
from google.cloud import storage
from google.cloud.exceptions import NotFound
from datetime import datetime, timezone


class BaseDAO():
    """
    Data Access Object for common data access methods
    """

    def __init__(self, *args, **kwargs):
        self.configure_pandas()

    def configure_pandas(self):
        """
        Configure global pandas options
        """
        pd.options.mode.use_inf_as_na = True
        pd.options.display.max_rows = 500
        pd.options.display.precision = 3
        pd.options.display.float_format = '{:.3f}'.format

    def get_gcs_client(self):
        return storage.Client()

    def get_s3_client(self):
        return client('s3',
                      aws_access_key_id=settings.IDP_AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=settings.IDP_AWS_SECRET_ACCESS_KEY)

    def get_gcs_bucket_name(self):
        return getattr(settings, "RAD_METADATA_BUCKET_NAME", "")

    def get_s3_bucket_name(self):
        return getattr(settings, "IDP_AWS_STORAGE_BUCKET_NAME", "")

    def get_gcs_timeout(self):
        return getattr(settings, "GCS_TIMEOUT", 60)

    def get_gcs_num_retries(self):
        return getattr(settings, "GCS_NUM_RETRIES", 3)

    def get_filenames_from_gcs_bucket(self, url_path, ending="csv"):
        """
        Lists files a given url_key path from the configured GCS bucket.

        :param url_path: Path of the content in the GCS bucket
        :type url_path: str
        """
        gcs_client = self.get_gcs_client()
        gcs_bucket_name = self.get_gcs_bucket_name()
        bucket = gcs_client.get_bucket(gcs_bucket_name)
        files = []
        for blob in gcs_client.list_blobs(bucket, prefix=url_path):
            if blob.name.endswith(ending):
                files.append(blob.name)
        logging.debug(f"Found the following GCS bucket files: "
                      f"{','.join(files)}")
        return files

    def download_from_gcs_bucket(self, url_key):
        """
        Downloads file a given url_key path from the configured GCS bucket.

        :param url_key: Path of the content to upload
        :type url_key: str
        :param content: Content to upload
        :type content: str or file object
        """
        gcs_client = self.get_gcs_client()
        gcs_bucket_name = self.get_gcs_bucket_name()
        bucket = gcs_client.get_bucket(gcs_bucket_name)
        try:
            blob = bucket.get_blob(
                url_key,
                timeout=self.get_gcs_timeout())
            content = blob.download_as_string(
                timeout=self.get_gcs_timeout())
            if content:
                return content.decode('utf-8')
        except NotFound as ex:
            logging.error(f"gcp {url_key}: {ex}")
            raise

    def download_from_s3_bucket(self, url_key):
        """
        Downloads file a given url_key path from the configured S3 bucket.

        :param url_key: Path of the content to upload
        :type url_key: str
        :param content: Content to upload
        :type content: str or file object
        """
        s3_client = self.get_s3_client()
        s3_bucket_name = self.get_s3_bucket_name()
        idp_obj = s3_client.get_object(Bucket=s3_bucket_name,
                                       Key=url_key)
        content = idp_obj['Body'].read()
        return content.decode('utf-8')

    def upload_to_gcs_bucket(self, url_key, content):
        """
        Upload a string or file-like object contents to GCS bucket

        :param url_key: Path of the content to upload
        :type url_key: str
        :param content: Content to upload
        :type content: str or file object
        """
        gcs_client = self.get_gcs_client()
        gcs_bucket_name = self.get_gcs_bucket_name()
        bucket = gcs_client.get_bucket(gcs_bucket_name)
        blob = bucket.get_blob(
            url_key,
            timeout=self.get_gcs_timeout())
        if not blob:
            blob = bucket.blob(url_key)
        blob.custom_time = datetime.now(timezone.utc)
        if isinstance(content, IOBase):
            blob.upload_from_file(
                content,
                num_retries=self.get_gcs_num_retries(),
                timeout=self.get_gcs_timeout())
        else:
            blob.upload_from_string(
                str(content),
                num_retries=self.get_gcs_num_retries(),
                timeout=self.get_gcs_timeout())

    def delete_from_gcs_bucket(self, url_key):
        """
        Delete a file from the GCS bucket

        :param url_key: Path of the content to delete
        :type url_key: str
        """
        gcs_client = self.get_gcs_client()
        gcs_bucket_name = self.get_gcs_bucket_name()
        bucket = gcs_client.get_bucket(gcs_bucket_name)
        blob = bucket.get_blob(
            url_key,
            timeout=self.get_gcs_timeout())
        blob.delete()

    @retry(DataFailureException, tries=5, delay=2, backoff=2,
           status_codes=[0, 403, 408, 500])
    def get_sws_terms(self, sis_term_id=None):
        """
        Returns sws term objects for specified sis_term_id onward.

        :param sis_term_id: specify starting sis-term-id to load Term's for.
            For example, if sis_term_id=Spring-2018, then Term Spring-2018 is
            loaded as well as all later Terms in the sws. (defaults to current
            term)
        :type sis_term_id: str
        """
        if sis_term_id is None:
            sws_term = get_current_term()
        else:
            year, quarter = sis_term_id.split("-")
            sws_term = get_term_by_year_and_quarter(int(year), quarter)
        sws_terms = []
        while sws_term:
            sws_terms.append(sws_term)
            try:
                sws_term = get_term_after(sws_term)
            except DataFailureException:
                # next term is not defined
                break
        return sws_terms


class CanvasDAO(BaseDAO):
    """
    Data Access Object for accessing canvas data
    """

    def __init__(self, page_size=100):
        self.canvas = Canvas()
        self.courses = Courses()
        self.enrollments = Enrollments()
        self.analytics = Analytics()
        self.reports = Reports()
        self.terms = Terms()
        self.page_size = page_size
        super().__init__()

    @retry(DataFailureException, tries=5, delay=2, backoff=2,
           status_codes=[0, 403, 408, 500])
    def download_student_ids_for_course(self, canvas_course_id):
        """
        Download list of student ids in a canvas course

        :param canvas_course_id: canvas course id to download list of students
            for
        :type canvas_course_id: int
        """
        stus = self.enrollments.get_enrollments_for_course(
                    canvas_course_id,
                    params={
                        "type": ['StudentEnrollment'],
                        "state": ['active', 'deleted', 'inactive']
                    })
        return list({stu.user_id for stu in stus})

    @retry(DataFailureException, tries=3, delay=2, backoff=2,
           status_codes=[0, 403, 408, 500])
    def download_course(self, canvas_course_id):
        """
        Download canvas course metadata

        :param canvas_course_id: canvas course id to download metadata for
        :type canvas_course_id: int
        """
        try:
            return self.courses.get_course(canvas_course_id)
        except Exception as e:
            logging.error(e)

    @retry(DataFailureException, tries=3, delay=2, backoff=2,
           status_codes=[0, 403, 408, 500])
    def download_assignment_analytics(
            self, canvas_course_id, student_id):
        """
        Download raw assignment analytics for a given canvas course id and
        student

        :param canvas_course_id: canvas course id to download analytics for
        :type canvas_course_id: int
        :param student_id: canvas user id to download analytic for
        :type student_id: int
        """
        analytics = self.analytics.get_student_assignments_for_course(
                                            student_id, canvas_course_id)
        for analytic in analytics:
            analytic["canvas_user_id"] = student_id
            analytic["canvas_course_id"] = canvas_course_id
        return analytics

    @retry(DataFailureException, tries=3, delay=2, backoff=2,
           status_codes=[0, 403, 408, 500])
    def download_participation_analytics(
            self, canvas_course_id):
        """
        Download raw participation analytics for a given canvas course id and
        student

        :param canvas_course_id: canvas course id to download analytics for
        :type canvas_course_id: int
        """
        analytics = self.analytics.get_student_summaries_by_course(
                                canvas_course_id, per_page=self.page_size)
        for analytic in analytics:
            analytic["canvas_user_id"] = analytic.pop("id")
            analytic["canvas_course_id"] = canvas_course_id
        return analytics

    def download_raw_analytics_for_course(
            self, canvas_course_id, analytic_type):
        """
        Download raw analytics for a given canvas course id

        :param canvas_course_id: canvas course id to download analytics for
        :type canvas_course_id: int
        :param analytic_type:
        :type analytic_type: str (AnalyticTypes.assignment or
            AnalyticTypes.participation)
        """
        if analytic_type == AnalyticTypes.assignment:
            # we need to request assignment analytics per student
            user_ids = self.download_student_ids_for_course(canvas_course_id)
            for user_id in user_ids:
                try:
                    for analytic in self.download_assignment_analytics(
                                                    canvas_course_id, user_id):
                        yield analytic
                except DataFailureException as e:
                    if e.status == 404:
                        logging.warning(e)
                        continue
                    else:
                        raise
        elif analytic_type == AnalyticTypes.participation:
            # we request all student summaries for the entire course in one
            # request
            try:
                for analytic in self.download_participation_analytics(
                                                            canvas_course_id):
                    yield analytic
            except DataFailureException as e:
                if e.status == 404:
                    logging.warning(f"No participation analytics for course "
                                    f"{canvas_course_id}")
                    logging.warning(e)
                else:
                    raise
        else:
            raise ValueError(f"Unknown analytic type: {analytic_type}")

    def download_course_provisioning_report(self, sis_term_id=None):
        """
        Download canvas course provisioning report

        :param sis_term_id: sis term id to load course report for. (default is
            the current term)
        :type sis_term_id: str
        """
        term, _ = Term.objects.get_or_create_term_from_sis_term_id(
            sis_term_id=sis_term_id)
        # get canvas term using sis-term-id
        canvas_term = self.terms.get_term_by_sis_id(term.sis_term_id)
        # get courses provisioning report for canvas term
        course_report = self.reports.create_course_provisioning_report(
                    settings.ACADEMIC_CANVAS_ACCOUNT_ID,
                    term_id=canvas_term.term_id,
                    params={"created_by_sis": True})
        logging.info(f"Downloading course provisioning report: "
                     f"term={sis_term_id}")
        sis_data = self.reports.get_report_data(course_report)
        self.reports.delete_report(course_report)
        return sis_data

    def download_user_provisioning_report(self, sis_term_id=None):
        """
        Download canvas sis user provisioning report

        :param sis_term_id: sis term id to load users report for
        :type sis_term_id: str
        """
        term, _ = Term.objects.get_or_create_term_from_sis_term_id(
            sis_term_id=sis_term_id)
        # get canvas term using sis-term-id
        canvas_term = self.terms.get_term_by_sis_id(term.sis_term_id)
        # get users provisioning repmiort for canvas term
        user_report = self.reports.create_user_provisioning_report(
                    settings.ACADEMIC_CANVAS_ACCOUNT_ID,
                    term_id=canvas_term.term_id,
                    params={"created_by_sis": True})
        logging.info(f"Downloading user provisioning report: "
                     f"term={sis_term_id}")
        sis_data = self.reports.get_report_data(user_report)
        self.reports.delete_report(user_report)
        return sis_data


class JobDAO(BaseDAO):
    """
    Data Access Object for processing jobs stored in Job model table
    """

    def __init__(self):
        super().__init__()

    def delete_data_for_job(self, job):
        """
        Delete data associated with job

        :param job: Job to delete data for
        :type job: data_aggregator.models.Job
        """
        if job.type.type == AnalyticTypes.assignment:
            # get assignment data associated with job
            old_analytics = Assignment.objects.filter(job=job)
        elif job.type.type == AnalyticTypes.participation:
            # get participation data associated with job
            old_analytics = Participation.objects.filter(job=job)
        else:
            raise ValueError(f"Unable to delete records. Unknown job type "
                             f"{job.type.type}.")
        old_analytics.delete()

    def run_analytics_job(self, job):
        """
        Download analytics for the given job
        and save them to the database.

        :param job: Job associated with the analytics to save
        :type job: data_aggregator.models.Job
        """
        canvas_course_id = job.context["canvas_course_id"]
        sis_term_id = job.context["sis_term_id"]
        week_num = job.context["week"]
        analytic_type = job.type.type
        # in case gcs caching is enabled, set gcs base path env variable so
        # that cached responses are ordered by term and week
        set_gcs_base_path(sis_term_id, week_num)

        # delete existing assignment data in case of a job restart
        self.delete_data_for_job(job)

        cd = CanvasDAO()

        analytics = []
        for analytic in cd.download_raw_analytics_for_course(
                                            canvas_course_id, analytic_type):
            analytics.append(analytic)

        analytics_dao = AnalyticsDAO()
        if analytics and analytic_type == AnalyticTypes.assignment:
            # save remaining assignments to db
            analytics_dao.save_assignments_to_db(analytics, job)
        elif analytics and analytic_type == AnalyticTypes.participation:
            # save remaining participations to db
            analytics_dao.save_participations_to_db(analytics, job)

    def run_task_job(self, job):
        """
        Runs a single task job.

        :param job: Job associated for the task to run
        :type job: data_aggregator.models.Job
        """
        job_type = job.type.type
        sis_term_id = job.context.get("sis_term_id")
        week_num = job.context.get("week")
        subaccount_id = job.context.get("subaccount_id")
        if job_type == TaskTypes.create_terms:
            TaskDAO().create_terms(sis_term_id=sis_term_id)
        elif job_type == TaskTypes.create_or_update_courses:
            TaskDAO().create_or_update_courses(sis_term_id=sis_term_id)
        elif job_type == TaskTypes.create_or_update_users:
            TaskDAO().create_or_update_users(sis_term_id=sis_term_id)
        elif job_type == TaskTypes.create_student_categories_data_file:
            EdwDAO().create_student_categories_data_file(
                sis_term_id=sis_term_id)
        elif job_type == TaskTypes.reload_advisers:
            TaskDAO().reload_advisers()
        elif job_type == TaskTypes.create_assignment_db_view:
            TaskDAO().create_assignment_db_view(sis_term_id=sis_term_id,
                                                week_num=week_num)
        elif job_type == TaskTypes.create_participation_db_view:
            TaskDAO().create_participation_db_view(sis_term_id=sis_term_id,
                                                   week_num=week_num)
        elif job_type == TaskTypes.create_rad_db_view:
            TaskDAO().create_rad_db_view(sis_term_id=sis_term_id,
                                         week_num=week_num)
        elif job_type == TaskTypes.create_rad_data_file:
            LoadRadDAO().create_rad_data_file(
                sis_term_id=sis_term_id,
                week_num=week_num,
                force=job.context.get("force", False))
        elif job_type == TaskTypes.create_compass_db_view:
            TaskDAO().create_compass_db_view(sis_term_id=sis_term_id,
                                             week_num=week_num)
        elif job_type == TaskTypes.create_compass_data_file:
            LoadCompassDAO().create_compass_data_file(
                sis_term_id=sis_term_id,
                week_num=week_num,
                force=job.context.get("force", False))
        elif job_type == TaskTypes.build_subaccount_activity_report:
            ReportBuilder().build_subaccount_activity_report(
                subaccount_id, sis_term_id=sis_term_id, week_num=week_num)
        elif job_type == TaskTypes.export_subaccount_activity_report:
            ReportBuilder().export_subaccount_activity_report(
                sis_term_id=sis_term_id, week_num=week_num)
        else:
            raise ValueError(f"Unknown job type {job_type}")

    def run_job(self, job):
        """
        Runs a job.

        :param job: Job to run.
        :type job: data_aggregator.models.Job
        """
        job_type = job.type.type
        if job_type == AnalyticTypes.assignment or \
                job_type == AnalyticTypes.participation:
            # download and load all assignment analytics for job
            JobDAO().run_analytics_job(job)
        else:
            # run an individual task job
            JobDAO().run_task_job(job)

    def create_job(self, job_type, target_date_start, target_date_end,
                   context=None):
        """
        Create a job for the given type.
        """
        if context is None:
            context = {}
        job = Job()
        job.type = job_type
        job.target_date_start = target_date_start
        job.target_date_end = target_date_end
        job.context = context
        job.save()
        return job

    def create_analytic_jobs(self, job_type, target_date_start,
                             target_date_end, context=None):
        """
        For each course create an analytics job matching the given job type.
        If context is explicitly passed, only a single job will be created for
        that given context.
        """
        if context is None:
            context = {}
        jobs = []
        if job_type.type != AnalyticTypes.assignment and \
                job_type.type != AnalyticTypes.participation:
            raise ValueError(f"Job type {job_type.type} is not a vaild "
                             f"analytics type. Aborting creating analytic "
                             f"jobs.")
        if context and \
                context.get('canvas_course_id') is not None and \
                context.get('sis_course_id') is not None and \
                context.get('sis_term_id') is not None and \
                context.get('week') is not None:
            # manually supplied single job context
            logging.debug(
                f"Adding {job_type.type} job for course "
                f"{context['canvas_course_id']}")
            job = self.create_job(job_type, target_date_start, target_date_end,
                                  context=context)
            jobs.append(job)
        else:
            # create jobs for all courses in a term
            term, _ = Term.objects.get_or_create_term_from_sis_term_id(
                sis_term_id=context.get('sis_term_id'))
            week, _ = Week.objects.get_or_create_week(
                                        sis_term_id=context.get('sis_term_id'),
                                        week_num=context.get('week'))
            courses = Course.objects.filter(status='active').filter(term=term)
            course_count = courses.count()
            if course_count == 0:
                logging.warning(
                    f'No active courses in term {term.sis_term_id} to '
                    f'create {job_type.type} jobs for.')
            else:
                jobs_count = 0
                with transaction.atomic():
                    for course in courses:
                        # create jobs
                        logging.debug(
                            f"Adding {job_type.type} jobs for course "
                            f"{course.sis_course_id} "
                            f"({course.canvas_course_id})")
                        context["sis_term_id"] = term.sis_term_id
                        context["week"] = week.week
                        context["sis_course_id"] = course.sis_course_id
                        context["canvas_course_id"] = course.canvas_course_id
                        job = self.create_job(job_type, target_date_start,
                                              target_date_end, context=context)
                        jobs.append(job)
                        jobs_count += 1
                logging.info(f'Created {jobs_count} {job_type.type} jobs.')
        return jobs


class AnalyticsDAO(BaseDAO):

    def save_assignments_to_db(self, assignment_dicts, job):
        """
        Save list of assignment dictionaries to the db for the given job

        :param assignment_dicts: List of dictionaries containing
            assignment analytic info
        :type assignment_dicts: dict
        :param job: Job associated with the assignment analytics to save
        :type job: data_aggregator.models.Job
        """
        canvas_course_id = job.context["canvas_course_id"]
        sis_term_id = job.context["sis_term_id"]
        week_num = job.context["week"]

        if assignment_dicts:
            course = Course.objects.get(
                        canvas_course_id=canvas_course_id,
                        term__sis_term_id=sis_term_id)
            week = Week.objects.get(
                        term__sis_term_id=sis_term_id,
                        week=week_num)
            update_count = 0
            create_count = 0
            with transaction.atomic():
                for raw_assign_dict in assignment_dicts:
                    _, created = (
                        Assignment.objects.create_or_update_assignment(
                            job, week, course, raw_assign_dict)
                    )
                    if created:
                        create_count += 1
                    else:
                        update_count += 1
            logging.info(f"Created {create_count} assignments for "
                         f"term={sis_term_id}, week={week_num}, "
                         f"course={canvas_course_id}")
            logging.info(f"Updated {update_count} assignments for "
                         f"term={sis_term_id}, week={week_num}, "
                         f"course={canvas_course_id}")

    def save_participations_to_db(self, participation_dicts, job):
        """
        Save list of participation dictionaries to the db for the given job

        :param participation_dicts: List of dictionaries containing
            participation analytic info
        :type participation_dicts: dict
        :param job: Job associated with the participation analytics to save
        :type job: data_aggregator.models.Job
        """
        canvas_course_id = job.context["canvas_course_id"]
        sis_term_id = job.context["sis_term_id"]
        week_num = job.context["week"]

        if participation_dicts:
            course = (Course.objects.get(
                        canvas_course_id=canvas_course_id,
                        term__sis_term_id=sis_term_id))
            week = Week.objects.get(
                        term__sis_term_id=sis_term_id,
                        week=week_num)
            update_count = 0
            create_count = 0

            with transaction.atomic():
                for raw_partic_dict in participation_dicts:
                    _, created = (
                        Participation.objects.create_or_update_participation(
                            job, week, course, raw_partic_dict)
                    )
                    if created:
                        create_count += 1
                    else:
                        update_count += 1
            logging.info(f"Created {create_count} participations for "
                         f"term={sis_term_id}, week={week_num}, "
                         f"course={canvas_course_id}")
            logging.info(f"Updated {update_count} participations for "
                         f"term={sis_term_id}, week={week_num}, "
                         f"course={canvas_course_id}")


class TaskDAO(BaseDAO):
    """
    Data Access Object for processing tasks necessary for running jobs
    """

    def create_or_update_courses(self, sis_term_id=None):
        """
        Create and or updates course list for a term

        :param sis_term_id: sis term id to load courses for. (default is
            the current term)
        :type sis_term_id: str
        """
        term, _ = Term.objects.get_or_create_term_from_sis_term_id(
            sis_term_id=sis_term_id)

        cd = CanvasDAO()
        # get provising data and load courses
        sis_data = \
            cd.download_course_provisioning_report(sis_term_id=sis_term_id)

        update_count = 0
        create_count = 0
        course_count = 0

        with transaction.atomic():
            for row in DictReader(sis_data):
                if not len(row):
                    continue
                created_by_sis = row['created_by_sis']
                if created_by_sis:
                    canvas_course_id = row['canvas_course_id']
                    try:
                        course = Course.objects.filter(
                                        canvas_course_id=canvas_course_id,
                                        term=term).get()
                        create_count += 1
                    except Course.DoesNotExist:
                        course = Course()
                        update_count += 1
                    # we always update the course data
                    course.canvas_course_id = canvas_course_id
                    course.term = term
                    course.sis_course_id = row['course_id']
                    course.short_name = row['short_name']
                    course.long_name = row['long_name']
                    course.canvas_account_id = row['canvas_account_id']
                    course.sis_account_id = row['account_id']
                    course.status = row['status']
                    course.save()
                    course_count += 1
        logging.info(f'Created {create_count} courses.')
        logging.info(f'Updated {update_count} courses.')
        return course_count

    def reload_advisers(self):
        """
        Create and or updates advisers for all users in the database
        """
        users = User.objects.filter(status='active')
        with transaction.atomic():
            Adviser.objects.all().delete()
            for user in users:
                try:
                    sws_advisers = get_advisers_by_regid(user.sis_user_id)
                    for sws_adviser in sws_advisers:
                        adviser = Adviser()
                        adviser.regid = sws_adviser.regid
                        adviser.uwnetid = sws_adviser.uwnetid
                        adviser.full_name = sws_adviser.full_name
                        adviser.pronouns = sws_adviser.pronouns
                        adviser.email_address = sws_adviser.email_address
                        adviser.phone_number = sws_adviser.phone_number
                        adviser.program = sws_adviser.program
                        adviser.booking_url = sws_adviser.booking_url
                        adviser.metadata = sws_adviser.metadata
                        adviser.is_active = sws_adviser.is_active
                        adviser.is_dept_adviser = sws_adviser.is_dept_adviser
                        adviser.timestamp = sws_adviser.timestamp
                        adviser.user = user
                        adviser.save()
                except DataFailureException:
                    logging.debug(f"No adviser found for user with login_id "
                                  f"{user.login_id}.")
                    pass

    def create_or_update_users(self, sis_term_id=None):
        """
        Create and or updates users list for a term

        :param sis_term_id: sis term id to load users for. (default is
            the current term)
        :type sis_term_id: str
        """
        cd = CanvasDAO()
        # get provising data and load courses
        sis_data = cd.download_user_provisioning_report(
            sis_term_id=sis_term_id)

        logging.info(f"Parsing Canvas user provisioning report "
                     f"containing {len(sis_data)} rows.")

        pws = PWS()
        update_count = 0
        create_count = 0
        user_count = 0

        with transaction.atomic():
            for row in DictReader(sis_data):
                if not len(row):
                    continue
                created_by_sis = row['created_by_sis']
                status = row['status']
                sis_user_id = row['user_id']
                if created_by_sis == "true" and status == "active" and \
                        pws.valid_uwregid(sis_user_id):

                    canvas_user_id = int(row['canvas_user_id'])
                    try:
                        user = User.objects.filter(
                                        canvas_user_id=canvas_user_id).get()
                        create_count += 1
                    except User.DoesNotExist:
                        user = User()
                        update_count += 1

                    user.canvas_user_id = canvas_user_id
                    user.sis_user_id = sis_user_id
                    user.login_id = row['login_id']
                    user.first_name = row['first_name']
                    user.last_name = row['last_name']
                    user.full_name = row['full_name']
                    user.sortable_name = row['sortable_name']
                    user.email = row['email']
                    user.status = status
                    user.save()
                    user_count += 1
        logging.info(f"Created {create_count} user(s).")
        logging.info(f"Updated {update_count} user(s).")
        return user_count

    def create_rad_db_view(self, sis_term_id=None, week_num=None):
        """
        Create rad db view for given week and sis-term-id

        :param sis_term_id: sis term id to create view for. (default is
            the current term)
        :type sis_term_id: str
        :param week_num: week number to create view for . (default is
            the current week of term)
        :type week_num: int
        """

        term, _ = Term.objects.get_or_create_term_from_sis_term_id(
            sis_term_id=sis_term_id)
        week, _ = Week.objects.get_or_create_week(sis_term_id=sis_term_id,
                                                  week_num=week_num)

        view_name = get_view_name(term.sis_term_id, week.week, "rad")
        assignments_view_name = get_view_name(term.sis_term_id,
                                              week.week,
                                              "assignments")
        participations_view_name = get_view_name(term.sis_term_id,
                                                 week.week,
                                                 "participations")

        cursor = connection.cursor()

        env = os.getenv("ENV")
        if env == "localdev" or not env:
            create_action = f'CREATE VIEW "{view_name}"'
            cursor.execute(f'DROP VIEW IF EXISTS "{view_name}"')
        else:
            create_action = f'CREATE OR REPLACE VIEW "{view_name}"'

        cursor.execute(
            f'''
            {create_action} AS
            WITH
            avg_norm_ap AS (
                SELECT
                    norm_ap.user_id,
                    AVG(normalized_assignment_score) AS assignment_score,
                    AVG(normalized_participation_score) AS participation_score
                FROM (
                    SELECT
                        p1.user_id,
                        p1.course_id,
                        p1.week_id,
                        CASE
                            WHEN (p1.participations IS NULL OR raw_ap_bounds.min_raw_participation_score IS NULL OR raw_ap_bounds.max_raw_participation_score IS NULL) THEN NULL 
                            ELSE ((p1.participations - min_raw_participation_score) * 10) / NULLIF(max_raw_participation_score - min_raw_participation_score, 0) - 5
                        END AS normalized_participation_score,
                        CASE
                            WHEN (p1.time_on_time IS NULL OR p1.time_late IS NULL OR raw_ap_bounds.min_raw_assignment_score IS NULL OR raw_ap_bounds.max_raw_assignment_score IS NULL) THEN NULL 
                            ELSE ((COALESCE(2 * p1.time_on_time + p1.time_late, 0) - min_raw_assignment_score) * 10) / NULLIF(max_raw_assignment_score - min_raw_assignment_score, 0) - 5
                        END AS normalized_assignment_score
                    FROM "{participations_view_name}" p1
                    JOIN (
                        SELECT
                            course_id,
                            MIN(p2.participations) AS min_raw_participation_score,
                            MAX(p2.participations) AS max_raw_participation_score,
                            MIN(2 * p2.time_on_time + p2.time_late) AS min_raw_assignment_score,
                            MAX(2 * p2.time_on_time + p2.time_late) AS max_raw_assignment_score
                        FROM "{participations_view_name}" p2
                        GROUP BY 
                            course_id
                    ) raw_ap_bounds ON p1.course_id  = raw_ap_bounds.course_id
                    GROUP BY
                        p1.user_id,
                        p1.course_id,
                        p1.week_id,
                        participations,
                        p1.time_on_time,
                        p1.time_late,
                        normalized_participation_score,
                        normalized_assignment_score
                ) AS norm_ap
                GROUP BY
                    norm_ap.user_id
            ),
            avg_norm_gr AS (
                WITH scores as (
                    SELECT course_id,
                        user_id,
                        points_possible,
                        CASE
                            WHEN a1.status = 'missing' AND score ISNULL THEN 0.0
                            WHEN a1.status = 'late' AND score ISNULL THEN 0.0
                            WHEN a1.status = 'on_time' AND score ISNULL THEN 0.0
                            WHEN points_possible = 0 AND score ISNULL THEN 0.0
                            ELSE score 
                        END AS new_score
                    FROM "{assignments_view_name}" a1 JOIN data_aggregator_course dac on
                        a1.course_id = dac.id
            	    WHERE (due_at NOTNULL AND due_at <= '{week.end_date.strftime("%Y-%m-%d")}'
                           AND dac.status = 'active' AND a1.status <> 'floating')
                ),
                user_total_scores as (
                    SELECT course_id,
                            user_id,
                            SUM(new_score) as total_score,
                            SUM(points_possible) as total_points_possible
                    FROM scores
                    GROUP BY course_id, user_id
                ),
                user_percentages AS (
                    SELECT course_id,
                            user_id,
                            CASE
                                WHEN total_score = 0 AND total_points_possible = 0 THEN 0.0
                                WHEN total_score > 0 AND total_points_possible = 0 THEN 1.0
                                ELSE total_score / total_points_possible
                            END AS user_course_percentage
                    FROM user_total_scores uts
                    GROUP BY course_id, user_id, total_score, total_points_possible
                ),
                course_percentages as (
                    SELECT 
                        course_id,
                        MIN(user_percentages.user_course_percentage) AS min_user_course_percentage,
                        MAX(user_percentages.user_course_percentage) AS max_user_course_percentage
                    FROM user_percentages
                    GROUP BY course_id
                ),
                norm_user_course_percentages AS (
                    SELECT
                        cp.course_id,
                        up.user_id,
                        CASE
                            WHEN up.user_course_percentage ISNULL OR cp.min_user_course_percentage ISNULL or
                                cp.max_user_course_percentage ISNULL THEN NULL
                            WHEN (cp.max_user_course_percentage - cp.min_user_course_percentage) = 0 THEN 0
                            ELSE (up.user_course_percentage - cp.min_user_course_percentage) * 10 / 
                            (cp.max_user_course_percentage - cp.min_user_course_percentage) - 5
                        END AS normalized_user_course_percentage
                    FROM user_percentages up
                        LEFT JOIN course_percentages cp ON up.course_id = cp.course_id
                    GROUP BY cp.course_id, up.user_id, normalized_user_course_percentage
                )
                SELECT nucp.user_id,
                    AVG(nucp.normalized_user_course_percentage) as grade
                FROM norm_user_course_percentages nucp JOIN data_aggregator_user on nucp.user_id = data_aggregator_user.id
                GROUP BY nucp.user_id, data_aggregator_user.login_id
            )
            SELECT DISTINCT
                u.canvas_user_id,
                u.full_name,
                '{term.sis_term_id}' as term,
                {week.week} as week,
                assignment_score,
                participation_score,
                grade
            FROM avg_norm_ap
            JOIN avg_norm_gr ON avg_norm_ap.user_id = avg_norm_gr.user_id
            JOIN data_aggregator_user u ON avg_norm_ap.user_id = u.id
            '''  # noqa
        )
        return True

    def create_compass_db_view(self, sis_term_id=None, week_num=None):
        """
        Create compass db view for given week and sis-term-id

        :param sis_term_id: sis term id to create view for. (default is
            the current term)
        :type sis_term_id: str
        :param week_num: week number to create view for . (default is
            the current week of term)
        :type week_num: int
        """

        term, _ = Term.objects.get_or_create_term_from_sis_term_id(
            sis_term_id=sis_term_id)
        week, _ = Week.objects.get_or_create_week(sis_term_id=sis_term_id,
                                                  week_num=week_num)

        view_name = get_view_name(term.sis_term_id, week.week, "compass")
        logging.info(
            f"Creating compass db view {view_name} for term={sis_term_id}, "
            f"week={week_num}"
        )
        assignments_view_name = get_view_name(term.sis_term_id,
                                              week.week,
                                              "assignments")
        participations_view_name = get_view_name(term.sis_term_id,
                                                 week.week,
                                                 "participations")

        cursor = connection.cursor()

        env = os.getenv("ENV")
        if env == "localdev" or not env:
            create_action = f'CREATE VIEW "{view_name}"'
            cursor.execute(f'DROP VIEW IF EXISTS "{view_name}"')
        else:
            create_action = f'CREATE OR REPLACE VIEW "{view_name}"'

        cursor.execute(
            f'''
            {create_action} AS
            WITH
            avg_norm_ap AS (
                SELECT /* student, course, week specific normalized participation and assignment scores */
                    p1.user_id,
                    p1.course_id,
                    p1.week_id,
                    CASE /* normalized participation score = ((10 * (raw - class min)) / (class max - class min)) - 5 */
                        WHEN (p1.participations IS NULL OR raw_ap_bounds.min_raw_participation_score IS NULL OR raw_ap_bounds.max_raw_participation_score IS NULL) THEN NULL 
                        ELSE ((p1.participations - min_raw_participation_score) * 10) / NULLIF(max_raw_participation_score - min_raw_participation_score, 0) - 5
                    END AS normalized_participation_score,
                    CASE  /* ((10 * (((2 * on time) + late) - class min)) / (class max - class min)) - 5 */
                        WHEN (p1.time_on_time IS NULL OR p1.time_late IS NULL OR raw_ap_bounds.min_raw_assignment_score IS NULL OR raw_ap_bounds.max_raw_assignment_score IS NULL) THEN NULL 
                        ELSE ((COALESCE(2 * p1.time_on_time + p1.time_late, 0) - min_raw_assignment_score) * 10) / NULLIF(max_raw_assignment_score - min_raw_assignment_score, 0) - 5
                    END AS normalized_assignment_score,
                    p1.participations AS raw_participations,
                    raw_ap_bounds.min_raw_participation_score,
                    raw_ap_bounds.max_raw_participation_score,
                    raw_ap_bounds.min_raw_assignment_score,
                    raw_ap_bounds.max_raw_assignment_score
                FROM "{participations_view_name}" p1
                JOIN ( /* For each course, get the min and max participation & assignment scores */
                    SELECT
                        course_id,
                        MIN(p2.participations) AS min_raw_participation_score,
                        MAX(p2.participations) AS max_raw_participation_score,
                        MIN(2 * p2.time_on_time + p2.time_late) AS min_raw_assignment_score,
                        MAX(2 * p2.time_on_time + p2.time_late) AS max_raw_assignment_score
                    FROM "{participations_view_name}" p2
                    GROUP BY 
                        course_id
                ) raw_ap_bounds ON p1.course_id  = raw_ap_bounds.course_id
                GROUP BY
                    p1.user_id,
                    p1.course_id,
                    p1.week_id,
                    participations,
                    p1.time_on_time,
                    p1.time_late,
                    normalized_participation_score,
                    normalized_assignment_score,
                    min_raw_participation_score,
                    max_raw_participation_score,
                    min_raw_assignment_score,
                    max_raw_assignment_score
            ),
            scores as (
                SELECT course_id,
                    user_id,
                    points_possible,
                    CASE
                        WHEN a1.status = 'missing' AND score ISNULL THEN 0.0
                        WHEN a1.status = 'late' AND score ISNULL THEN 0.0
                        WHEN a1.status = 'on_time' AND score ISNULL THEN 0.0
                        WHEN points_possible = 0 AND score ISNULL THEN 0.0
                        ELSE score 
                    END AS new_score
                FROM "{assignments_view_name}"  a1 JOIN data_aggregator_course dac on
                    a1.course_id = dac.id
                WHERE (due_at NOTNULL AND due_at <= '{week.end_date.strftime("%Y-%m-%d")}'
                        AND dac.status = 'active' AND a1.status <> 'floating')
            ),
            user_total_scores as (
                SELECT course_id,
                        user_id,
                        SUM(new_score) as total_score,
                        SUM(points_possible) as total_points_possible
                FROM scores
                GROUP BY course_id, user_id
            ),
            user_percentages AS (
                SELECT course_id,
                        user_id,
                        CASE
                            WHEN total_score = 0 AND total_points_possible = 0 THEN 0.0
                            WHEN total_score > 0 AND total_points_possible = 0 THEN 1.0
                            ELSE total_score / total_points_possible
                        END AS user_course_percentage
                FROM user_total_scores uts
                GROUP BY course_id, user_id, total_score, total_points_possible
            ),
            course_percentages as (
                SELECT 
                    course_id,
                    MIN(user_percentages.user_course_percentage) AS min_user_course_percentage,
                    MAX(user_percentages.user_course_percentage) AS max_user_course_percentage
                FROM user_percentages
                GROUP BY course_id
            ),
            norm_user_course_percentages AS (
                SELECT
                    cp.course_id,
                    up.user_id,
                    CASE
                        WHEN up.user_course_percentage ISNULL OR cp.min_user_course_percentage ISNULL or
                            cp.max_user_course_percentage ISNULL THEN NULL
                        WHEN (cp.max_user_course_percentage - cp.min_user_course_percentage) = 0 THEN 0
                        ELSE (up.user_course_percentage - cp.min_user_course_percentage) * 10 / 
                        (cp.max_user_course_percentage - cp.min_user_course_percentage) - 5
                    END AS normalized_user_course_percentage,
                    cp.max_user_course_percentage,
                    cp.min_user_course_percentage,
                    up.user_course_percentage
                FROM user_percentages up
                    LEFT JOIN course_percentages cp ON up.course_id = cp.course_id
                GROUP BY cp.course_id,
                    up.user_id,
                    normalized_user_course_percentage,
                    max_user_course_percentage,
                    min_user_course_percentage,
                    user_course_percentage
            )
            SELECT DISTINCT
                u.canvas_user_id,
                norm_user_course_percentages.course_id,
                u.full_name,
                '{term.sis_term_id}' as term,
                {week.week} as week,
                normalized_user_course_percentage,
                user_course_percentage,
                max_user_course_percentage,
                min_user_course_percentage,
                normalized_participation_score,
                normalized_assignment_score,
                min_raw_participation_score,
                max_raw_participation_score,
                min_raw_assignment_score,
                max_raw_assignment_score
            FROM avg_norm_ap
            JOIN norm_user_course_percentages on
                avg_norm_ap.user_id = norm_user_course_percentages.user_id and
                avg_norm_ap.course_id = norm_user_course_percentages.course_id
            JOIN data_aggregator_user u ON avg_norm_ap.user_id = u.id
            '''  # noqa
        )
        return True

    def create_participation_db_view(self, sis_term_id=None, week_num=None):
        """
        Create participation db view for given week and sis-term-id

        :param sis_term_id: sis term id to create view for. (default is
            the current term)
        :type sis_term_id: str
        :param week_num: week number to create view for . (default is
            the current week of term)
        :type week_num: int
        """

        term, _ = Term.objects.get_or_create_term_from_sis_term_id(
            sis_term_id=sis_term_id)
        week, _ = Week.objects.get_or_create_week(sis_term_id=sis_term_id,
                                                  week_num=week_num)

        view_name = get_view_name(term.sis_term_id, week.week,
                                  "participations")

        cursor = connection.cursor()

        env = os.getenv("ENV")
        if env == "localdev" or not env:
            create_action = f'CREATE VIEW "{view_name}"'
            cursor.execute(f'DROP VIEW IF EXISTS "{view_name}"')
        else:
            create_action = f'CREATE OR REPLACE VIEW "{view_name}"'

        cursor.execute(
            f'''
            {create_action} AS
            SELECT
                data_aggregator_term.id AS term_id,
                data_aggregator_week.id AS week_id,
                p.course_id,
                p.user_id,
                p.participations AS participations,
                p.max_participations AS max_participations,
                p.participations_level AS participations_level,
                p.page_views AS page_views,
                p.max_page_views AS max_page_views,
                p.page_views_level AS page_views_level,
                p.time_total AS time_total,
                p.time_on_time AS time_on_time,
                p.time_late AS time_late,
                p.time_missing AS time_missing,
                p.time_floating AS time_floating
            FROM
                data_aggregator_participation p
            JOIN data_aggregator_week on
                p.week_id = data_aggregator_week.id
            JOIN data_aggregator_term on
                data_aggregator_week.term_id = data_aggregator_term.id
            WHERE data_aggregator_week.week = {week.week}
            AND data_aggregator_term.sis_term_id = '{term.sis_term_id}'
            '''
        )
        return True

    def create_assignment_db_view(self, sis_term_id=None, week_num=None):
        """
        Create assignment db view for given week and sis-term-id

        :param sis_term_id: sis term id to create view for. (default is
            the current term)
        :type sis_term_id: str
        :param week_num: week number to create view for . (default is
            the current week of term)
        :type week_num: int
        """

        term, _ = Term.objects.get_or_create_term_from_sis_term_id(
            sis_term_id=sis_term_id)
        week, _ = Week.objects.get_or_create_week(sis_term_id=sis_term_id,
                                                  week_num=week_num)

        view_name = get_view_name(term.sis_term_id, week.week, "assignments")

        cursor = connection.cursor()

        env = os.getenv("ENV")
        if env == "localdev" or not env:
            create_action = f'CREATE VIEW "{view_name}"'
            cursor.execute(f'DROP VIEW IF EXISTS "{view_name}"')
        else:
            create_action = f'CREATE OR REPLACE VIEW "{view_name}"'

        cursor.execute(
            f'''
            {create_action} AS
            SELECT
                data_aggregator_term.id AS term_id,
                data_aggregator_week.id AS week_id,
                a.course_id,
                a.user_id,
                a.assignment_id,
                a.score,
                a.due_at,
                a.points_possible,
                a.status,
                a.excused,
                a.first_quartile,
                a.max_score,
                a.median,
                a.min_score,
                a.muted,
                a.non_digital_submission,
                a.posted_at,
                a.submitted_at,
                a.third_quartile,
                a.title
            FROM data_aggregator_assignment a
            JOIN data_aggregator_week ON a.week_id = data_aggregator_week.id
            JOIN data_aggregator_term ON
            data_aggregator_week.term_id = data_aggregator_term.id
            WHERE data_aggregator_week.week = {week.week} AND
            data_aggregator_term.sis_term_id = '{term.sis_term_id}'
            '''
        )
        return True

    def create_terms(self, sis_term_id=None):
        """
        Creates current term and all future terms

        :param sis_term_id: specify starting sis-term-id to load Term's for.
            For example, if sis_term_id=Spring-2018, then Term Spring-2018 is
            loaded as well as all later Terms in the sws. (defaults to current
            term)
        :type sis_term_id: str
        """
        sws_terms = self.get_sws_terms(sis_term_id=sis_term_id)
        for sws_term in sws_terms:
            term, created = \
                Term.objects.get_or_create_from_sws_term(sws_term)
            if created:
                logging.info(f"Created term {term.sis_term_id}")


class LoadRadDAO(BaseDAO):
    """
    Data Access Object for creating file for loading RAD
    """

    def __init__(self):
        super().__init__()

    def _zero_range(self, x):
        """
        Check range of series x is non-zero.
        Helper for rescaling.
        May choke if all x is na.
        """
        zr = False
        if x.min() == x.max():
            zr = True
        return zr

    def _rescale_range(self, x, min=-5, max=5):
        """
        Scale numbers to an arbitray min/max range.

        :param x: Pandas numeric column to rescale
        :type x: Pandas column
        :param min: Mimimum scaled value
        :type min: numeric
        :param max: Maximum scaled value
        :type max: numeric
        """
        if self._zero_range(x):
            x[::] = np.mean([min, max])
        elif x.isnull().all():
            x[::] = np.nan
        else:
            x += -(x.min())
            x /= x.max() / (max - min)
            x += min
        return x

    def get_users_df(self):
        """
        Get pandas dataframe with users table contents
        """
        users = User.objects.all().values("canvas_user_id", "login_id")
        users_df = pd.DataFrame(users)
        users_df.rename(columns={'login_id': 'uw_netid'}, inplace=True)
        return users_df

    def get_student_categories_df(self, sis_term_id=None):
        """
        Download student categories file from the configured GCS bucket
        and return pandas dataframe with contents

        :param sis_term_id: sis term id to create data frame for. (default is
            the current term)
        :type sis_term_id: str
        """
        users_df = self.get_users_df()
        Term.objects.get_or_create_term_from_sis_term_id
        term, _ = Term.objects.get_or_create_term_from_sis_term_id(
            sis_term_id=sis_term_id)
        url_key = (f"application_metadata/student_categories/"
                   f"{term.sis_term_id}-netid-name-stunum-categories.csv")
        content = self.download_from_gcs_bucket(url_key)
        sdb_df = pd.read_csv(StringIO(content))
        sdb_df["uw_netid"] = sdb_df["uw_netid"].str.strip()
        sdb_df.drop_duplicates(inplace=True)
        sdb_df = sdb_df.merge(users_df, how='left', on='uw_netid')
        return sdb_df

    def get_pred_proba_scores_df(self, sis_term_id=None):
        """
        Download predicted probabilities file from the configured GCS bucket
        and return pandas dataframe with contents

        :param sis_term_id: sis term id to create data frame for. (default is
            the current term)
        :type sis_term_id: str
        """
        term, _ = Term.objects.get_or_create_term_from_sis_term_id(
            sis_term_id=sis_term_id)
        url_key = (f"application_metadata/predicted_probabilites/"
                   f"{term.sis_term_id}-pred-proba.csv")
        content = self.download_from_gcs_bucket(url_key)

        probs_df = pd.read_csv(
            StringIO(content),
            usecols=['system_key', 'pred0'])
        probs_df['pred0'] = probs_df['pred0'].transform(self._rescale_range)
        probs_df.rename(columns={'pred0': 'pred'},
                        inplace=True)
        return probs_df

    def get_eop_advisers_df(self, sis_term_id=None):
        """
        Download eop advisers file from the configured GCS bucket
        and return pandas dataframe with contents

        :param sis_term_id: sis term id to create data frame for. (default is
            the current term)
        :type sis_term_id: str
        """
        term, _ = Term.objects.get_or_create_term_from_sis_term_id(
            sis_term_id=sis_term_id)
        url_key = (f"application_metadata/eop_advisers/"
                   f"{term.sis_term_id}-eop-advisers.csv")
        content = self.download_from_gcs_bucket(url_key)
        eop_df = pd.read_csv(
            StringIO(content),
            usecols=['student_no', 'adviser_name', 'staff_id'])
        # strip any whitespace
        eop_df['adviser_name'] = eop_df['adviser_name'].str.strip()
        eop_df['staff_id'] = eop_df['staff_id'].str.strip()
        eop_df['adviser_type'] = AdviserTypes.eop
        return eop_df

    def get_iss_advisers_df(self, sis_term_id=None):
        """
        Download iss advisers file from the configured GCS bucket
        and return pandas dataframe with contents

        :param sis_term_id: sis term id to create data frame for. (default is
            the current term)
        :type sis_term_id: str
        """
        term, _ = Term.objects.get_or_create_term_from_sis_term_id(
            sis_term_id=sis_term_id)
        url_key = (f"application_metadata/iss_advisers/"
                   f"{term.sis_term_id}-iss-advisers.csv")
        content = self.download_from_gcs_bucket(url_key)
        iss_df = pd.read_csv(
            StringIO(content),
            usecols=['student_no', 'adviser_name',
                     'staff_id'])
        # strip any whitespace
        iss_df['adviser_name'] = iss_df['adviser_name'].str.strip()
        iss_df['staff_id'] = iss_df['staff_id'].str.strip()
        iss_df['adviser_type'] = AdviserTypes.iss
        return iss_df

    def get_rad_dbview_df(self, sis_term_id=None, week_num=None):
        """
        Query RAD canvas data from the canvas-analytics RAD db view for the
        current term and week and return pandas dataframe with contents

        :param sis_term_id: sis term id to create data frame for. (default is
            the current term)
        :type sis_term_id: str
        :param week_num: week number to create data frame for. (default is
            the current week of term)
        :type week_num: int
        """
        term, _ = Term.objects.get_or_create_term_from_sis_term_id(
            sis_term_id=sis_term_id)
        week, _ = Week.objects.get_or_create_week(sis_term_id=sis_term_id,
                                                  week_num=week_num)
        view_name = get_view_name(term.sis_term_id, week.week, "rad")
        rad_db_model = RadDbView.setDb_table(view_name)
        rad_canvas_qs = rad_db_model.objects.all().values()
        rad_df = pd.DataFrame(rad_canvas_qs)
        rad_df.rename(columns={'assignment_score': 'assignments',
                               'grade': 'grades',
                               'participation_score': 'activity'},
                      inplace=True)
        return rad_df

    def get_last_idp_file(self):
        """
        Get latest idp file from AWS bucket and return pandas dataframe
        with contents
        """
        s3_client = self.get_s3_client()
        s3_bucket_name = self.get_s3_bucket_name()
        bucket_objects = \
            s3_client.list_objects_v2(Bucket=s3_bucket_name)
        last_idp_file = bucket_objects['Contents'][-1]['Key']
        return last_idp_file

    def _remove_outlying_idp_signins(self, idp_df):
        """
        Cap max number of sign ins to 100
        """
        idp_df['sign_in'] = idp_df['sign_in'].clip(upper=100)
        return idp_df

    def get_idp_df(self):
        """
        Download latest idp file found in the s3 bucket and return pandas
        dataframe with contents
        """
        last_idp_file = self.get_last_idp_file()
        logging.info(f'Using {last_idp_file} as idp file.')
        content = self.download_from_s3_bucket(last_idp_file)
        idp_df = pd.read_csv(StringIO(content),
                             header=None,
                             names=['uw_netid', 'sign_in'])
        # set ceiling for scores
        idp_df = self._remove_outlying_idp_signins(idp_df)
        # normalize sign-in score
        idp_df['sign_in'] = np.log(idp_df['sign_in']+1)
        idp_df['sign_in'] = self._rescale_range(idp_df['sign_in'])
        return idp_df

    def get_rad_df(self, sis_term_id=None, week_num=None):
        """
        Get a pandas dataframe containing the contents of the
        rad data file

        :param sis_term_id: sis term id to create data frame for. (default is
            the current term)
        :type sis_term_id: str
        :param week_num: week number to create data frame for . (default is
            the current week of term)
        :type week_num: int
        """
        # get rad canvas data
        rad_df = self.get_rad_dbview_df(sis_term_id=sis_term_id,
                                        week_num=week_num)
        # get student categories
        sdb_df = self.get_student_categories_df(sis_term_id=sis_term_id)
        # get idp data
        idp_df = self.get_idp_df()
        # get predicted probabilities
        probs_df = self.get_pred_proba_scores_df(sis_term_id=sis_term_id)
        # get eop advisers
        eop_advisers_df = self.get_eop_advisers_df(sis_term_id=sis_term_id)
        # get iss advisers
        iss_advisers_df = self.get_iss_advisers_df(sis_term_id=sis_term_id)
        # combine advisers
        combined_advisers_df = \
            pd.concat([eop_advisers_df, iss_advisers_df])
        # merge to create the final dataset
        joined_canvas_df = (
            pd.merge(sdb_df, rad_df, how='left', on='canvas_user_id')
              .merge(idp_df, how='left', on='uw_netid')
              .merge(probs_df, how='left', on='system_key')
              .merge(combined_advisers_df, how='left', on='student_no'))
        joined_canvas_df = joined_canvas_df[
            ['uw_netid', 'student_no', 'student_name_lowc', 'activity',
             'assignments', 'grades', 'pred', 'adviser_name', 'adviser_type',
             'staff_id', 'sign_in', 'stem', 'incoming_freshman', 'premajor',
             'eop', 'international', 'isso', 'engineering', 'informatics',
             'campus_code', 'summer', 'class_code', 'sport_code']]
        return joined_canvas_df

    def create_rad_data_file(self, sis_term_id=None, week_num=None,
                             force=False):
        """
        Creates RAD data file and uploads it to the GCS bucket

        :param sis_term_id: sis term id to create data frame for. (default is
            the current term)
        :type sis_term_id: str
        :param week_num: week number to create data frame for . (default is
            the current week of term)
        :type week_num: int
        """
        term, _ = Term.objects.get_or_create_term_from_sis_term_id(
            sis_term_id=sis_term_id)
        week, _ = Week.objects.get_or_create_week(sis_term_id=sis_term_id,
                                                  week_num=week_num)
        running_assign_jobs = Job.objects.get_running_jobs_for_term_week(
            AnalyticTypes.assignment, term.sis_term_id, week.week)
        running_partic_jobs = Job.objects.get_running_jobs_for_term_week(
            AnalyticTypes.participation, term.sis_term_id, week.week)
        if ((running_assign_jobs.count() == 0 and
             running_partic_jobs.count() == 0) or force is True):
            rcd = self.get_rad_df(sis_term_id=sis_term_id, week_num=week_num)
            file_name = (f"rad_data/{term.sis_term_id}-week-"
                         f"{week.week}-rad-data.csv")
            file_obj = rcd.to_csv(sep=",", index=False, encoding="UTF-8")
            self.upload_to_gcs_bucket(file_name, file_obj)
        else:
            error_msg = (
                f"Skipping creating RAD file. There are "
                f"{running_assign_jobs.count()} running assignment jobs and "
                f"{running_partic_jobs.count()} running participation jobs "
                f"for term {sis_term_id} and week {week_num}. Creation of "
                f"the RAD data file could result in incomplete data.")
            logging.critical(error_msg)
            raise RuntimeError(error_msg)


class LoadCompassDAO(LoadRadDAO):
    """
    Data Access Object for creating file for loading Compass
    """

    def _get_course_df(self, sis_term_id=None):
        term, _ = Term.objects.get_or_create_term_from_sis_term_id(
            sis_term_id=sis_term_id)
        course_qs = (Course.objects.filter(term=term)
                     .values('id', 'short_name'))
        course_df = pd.DataFrame(course_qs)
        course_df.rename(columns={'short_name': 'course_code'},
                         inplace=True)
        return course_df

    def get_compass_dbview_df(self, sis_term_id=None, week_num=None):
        """
        Query Compass canvas data from the canvas-analytics Compass db view for
        the current term and week and return pandas dataframe with contents

        :param sis_term_id: sis term id to create data frame for. (default is
            the current term)
        :type sis_term_id: str
        :param week_num: week number to create data frame for. (default is
            the current week of term)
        :type week_num: int
        """
        term, _ = Term.objects.get_or_create_term_from_sis_term_id(
            sis_term_id=sis_term_id)
        week, _ = Week.objects.get_or_create_week(sis_term_id=sis_term_id,
                                                  week_num=week_num)
        view_name = get_view_name(term.sis_term_id, week.week, "compass")
        compass_db_model = CompassDbView.setDb_table(view_name)
        compass_canvas_qs = compass_db_model.objects.all().values()
        compass_df = pd.DataFrame(compass_canvas_qs)
        col_map = {'normalized_assignment_score': 'assignments',
                   'normalized_user_course_percentage': 'grades',
                   'normalized_participation_score': 'activity'}
        compass_df.rename(columns=col_map,
                          inplace=True)
        return compass_df

    def get_compass_df(self, sis_term_id=None, week_num=None):
        """
        Get pandas dataframe from compass db view
        """
        # get compass canvas data
        compass_df = self.get_compass_dbview_df(sis_term_id=sis_term_id,
                                                week_num=week_num)
        # get student categories
        sdb_df = self.get_student_categories_df(sis_term_id=sis_term_id)
        # get idp data
        idp_df = self.get_idp_df()
        # get predicted probabilities
        probs_df = self.get_pred_proba_scores_df(sis_term_id=sis_term_id)
        # get course id lookup
        course_df = self._get_course_df(sis_term_id=sis_term_id)
        # merge to create the final dataset
        joined_canvas_df = (
            pd.merge(sdb_df, compass_df, how='left', on='canvas_user_id')
            .merge(idp_df, how='left', on='uw_netid')
            .merge(probs_df, how='left', on='system_key')
            .merge(course_df, how='left', left_on='course_id', right_on='id'))
        joined_canvas_df = joined_canvas_df[
            ['uw_netid', 'student_no', 'student_name_lowc', 'course_code',
             'activity', 'assignments', 'grades', 'pred', 'sign_in', 'stem',
             'incoming_freshman', 'premajor', 'eop', 'international', 'isso',
             'engineering', 'informatics', 'campus_code', 'summer',
             'class_code', 'sport_code']]
        return joined_canvas_df

    def create_compass_data_file(self, sis_term_id=None, week_num=None,
                                 force=False):
        """
        Create compass data file and upload it to the GCS bucket

        :param sis_term_id: sis term id to create data frame for. (default is
            the current term)
        :type sis_term_id: str
        :param week_num: week number to create data frame for . (default is
            the current week of term)
        :type week_num: int
        """
        term, _ = Term.objects.get_or_create_term_from_sis_term_id(
            sis_term_id=sis_term_id)
        week, _ = Week.objects.get_or_create_week(sis_term_id=sis_term_id,
                                                  week_num=week_num)
        running_assign_jobs = Job.objects.get_running_jobs_for_term_week(
            AnalyticTypes.assignment, term.sis_term_id, week.week)
        running_partic_jobs = Job.objects.get_running_jobs_for_term_week(
            AnalyticTypes.participation, term.sis_term_id, week.week)
        if ((running_assign_jobs.count() == 0 and
             running_partic_jobs.count() == 0) or force is True):
            cdf = self.get_compass_df(sis_term_id=sis_term_id,
                                      week_num=week_num)
            file_name = (f"compass_data/{term.sis_term_id}-week-"
                         f"{week.week}-compass-data.csv")
            logging.info(f"Creating Compass data file {file_name}")
            file_obj = cdf.to_csv(sep=",", index=False, encoding="UTF-8")
            self.upload_to_gcs_bucket(file_name, file_obj)
        else:
            error_msg = (
                f"Skipping creating Compass file. There are "
                f"{running_assign_jobs.count()} running assignment jobs and "
                f"{running_partic_jobs.count()} running participation jobs "
                f"for term {sis_term_id} and week {week_num}. Creation of "
                f"the Compass data file could result in incomplete data.")
            logging.critical(error_msg)
            raise RuntimeError(error_msg)


class EdwDAO(BaseDAO):

    def get_connection(self, database):
        password = getattr(settings, "EDW_PASSWORD")
        user = getattr(settings, "EDW_USER")
        hostname = getattr(settings, "EDW_HOSTNAME")
        conn = pymssql.connect(hostname, user, password, database)
        logging.debug(f"Connected to {hostname}.{database} with user {user}")
        return conn

    def create_student_categories_data_file(self, sis_term_id=None):
        term, _ = Term.objects.get_or_create_term_from_sis_term_id(
            sis_term_id=sis_term_id)
        stu_cat_df = self.get_student_categories_df(
            sis_term_id=sis_term_id)
        url_key = (f"application_metadata/student_categories/"
                   f"{term.sis_term_id}-netid-name-stunum-categories.csv")
        file_obj = stu_cat_df.to_csv(sep=",", index=False, encoding="UTF-8")
        self.upload_to_gcs_bucket(url_key, file_obj)

    def get_student_categories_df(self, sis_term_id=None):
        year = None
        quarter_num = None
        if sis_term_id is not None:
            parts = sis_term_id.split("-")
            year = parts[0]
            quarter_num = str(get_term_number(parts[1]))
        if year is None:
            year = datetime.now(timezone.utc).year
        if quarter_num is None:
            curr_term, _ = Term.objects.get_or_create_term_from_sis_term_id()
            quarter_num = curr_term.term_number
        yrq = "".join([str(year), str(quarter_num)])
        conn = self.get_connection("UWSDBDataStore")
        stu_cat_df = pd.read_sql(
            f"""
            WITH enrolled_cte AS (
                SELECT 
                    enr.AcademicYrQtr,
                    enr.SystemKey,
                    enr.StudentNumber,
                    enr.StudentName,
                    enr.CampusCode,
                    enr.CampusDesc,
                    enr.NewContinuingReturningCode,
                    enr.ClassCode,
                    stu1.uw_netid,
                    international_student = CASE WHEN enr.ResidentCode IN (5,6) THEN 1 ELSE 0 END,
                    enr.ResidentDesc,
                    eop = CASE WHEN enr.SpecialProgramCode IN ('1', '2', '13', '14', '16', '17', '31', '32', '33') OR
                                    stu1.spcl_program IN ('1', '2', '13', '14', '16', '17', '31', '32', '33') THEN 1
                               ELSE 0
                          END,
                    incoming_freshman = CASE WHEN enr.ClassCode <= 1 AND enr.NewContinuingReturningCode = 1 THEN 1 ELSE 0 END
                FROM EDWPresentation.sec.EnrolledStudent AS enr
                LEFT JOIN UWSDBDataStore.sec.student_1 AS stu1 ON enr.SystemKey = stu1.system_key
                WHERE AcademicYrQtr = {yrq} AND RegisteredInQuarter = 'Y'
            ),
            major_calcs as (
                SELECT 
                    cm.system_key,
                    isso = max( CASE WHEN smc.major_abbr = 'ISS O' THEN 1 ELSE 0 END),
                    stem = max( CASE WHEN c.FederalStemInd = 'Y' THEN 1 ELSE 0 END ),
                    premajor = max( CASE WHEN smc.major_premaj = 1 OR major_premaj_ext = 1 THEN 1 ELSE 0 END),
                    engineering = max( CASE WHEN smc.major_abbr IN ('A A', 'BIOEN', 'BSE', 'C SCI', 'CHEM E', 'CIV E', 'CMP E', 'E E', 'ENGRUD', 'ENV E', 'HCDE', 'IND E', 'INT EN', 'M E', 'MS E', 'PREBSE', 'STARS') THEN 1 ELSE 0 END),
                    informatics = max( CASE WHEN smc.major_abbr = 'INFO' THEN 1 ELSE 0 END)
                FROM UWSDBDataStore.sec.student_1_college_major AS cm
                LEFT JOIN UWSDBDataStore.sec.sr_major_code AS smc ON cm.major_abbr = smc.major_abbr AND smc.major_pathway = cm.pathway
                LEFT JOIN EDWPresentation.sec.dimCIPCurrent AS c ON smc.major_cip_code = c.CIPCode
                WHERE cm.system_key IN (SELECT e.SystemKey FROM enrolled_cte AS e)
                GROUP BY cm.system_key
            ),
            summer_regis AS (
                SELECT DISTINCT 
                    system_key,
                    AcademicYrQtr = (regis_yr * 10) + regis_qtr,
                    summer_term = COALESCE(NULLIF(summer_term, ''), 'Full')
                FROM UWSDBDataStore.sec.registration_courses
                WHERE (regis_yr * 10) + regis_qtr = {yrq} AND request_status IN ('A', 'C', 'R')
            ),
            agg_summer AS ( 
                SELECT
                    system_key,
                    summer = string_agg(summer_term, '-') WITHIN group (ORDER BY summer_term)
                FROM summer_regis GROUP BY system_key
            )
            SELECT DISTINCT
                SystemKey AS system_key,
                uw_netid,
                StudentNumber AS student_no,
                StudentName AS student_name_lowc,
                eop,
                incoming_freshman,
                international_student AS international,
                m.stem,
                m.premajor,
                isso,
                engineering,
                informatics,
                CampusCode AS campus_code,
                s.summer,
                ClassCode AS class_code,
                sport.sport_code
            FROM enrolled_cte AS e 
            LEFT JOIN major_calcs AS m ON e.SystemKey = m.system_key 
            LEFT JOIN agg_summer as s ON e.SystemKey = s.system_key
            LEFT JOIN UWSDBDataStore.sec.student_2_sport_code as sport on e.SystemKey = sport.system_key
            WHERE e.ClassCode IN ('0', '1', '2', '3', '4') OR sport.sport_code > 0
            ORDER BY SystemKey
            """,  # noqa
            conn
        )
        stu_cat_df["uw_netid"] = stu_cat_df["uw_netid"].str.strip()
        # combine sport codes into single list per student
        stu_cat_df = stu_cat_df.groupby(
            ["system_key", "uw_netid", "student_no", "student_name_lowc",
             "eop", "incoming_freshman", "international", "stem", "premajor",
             "isso", "engineering", "informatics", "campus_code", "summer",
             "class_code"])['sport_code'].apply(list).reset_index()
        stu_cat_df["sport_code"] = \
            [",".join([str(int(c)) for c in codes if not pd.isna(c)])
             for codes in stu_cat_df["sport_code"] if codes]
        return stu_cat_df
