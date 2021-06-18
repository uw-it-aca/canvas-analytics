import logging
import os
from csv import DictReader
from django.conf import settings
from django.db import transaction, connection
from data_aggregator.models import Assignment, Course, Participation, \
    User, RadDbView, Term, Week, AnalyticTypes
from data_aggregator.utilities import get_view_name
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
from uw_pws import PWS

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

    def set_gcs_base_path(self, sis_term_id, week_num):
        os.environ["GCS_BASE_PATH"] = f"{sis_term_id}/{week_num}/"

    def get_gcs_client(self):
        return storage.Client()

    def get_s3_client(self):
        return client('s3',
                      aws_access_key_id=settings.AWS_ACCESS_ID,
                      aws_secret_access_key=settings.AWS_ACCESS_KEY)

    def get_gcs_bucket_name(self):
        return getattr(settings, "RAD_METADATA_BUCKET_NAME", "")

    def get_s3_bucket_name(self):
        return getattr(settings, "IDP_BUCKET_NAME", "")

    def get_gcs_timeout(self):
        return getattr(settings, "GCS_TIMEOUT", 60)

    def get_gcs_num_retries(self):
        return getattr(settings, "GCS_NUM_RETRIES", 3)

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
        return self.analytics.get_student_assignments_for_course(
                                            student_id, canvas_course_id)

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
        return self.analytics.get_student_summaries_by_course(
                                canvas_course_id, per_page=self.page_size)

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
            user_ids = self.download_user_ids_for_course(canvas_course_id)
            for user_id in user_ids:
                try:
                    res = self.download_assignment_analytics(
                                                canvas_course_id, user_id)
                    for analytic in res:
                        analytic["canvas_user_id"] = user_id
                        analytic["canvas_course_id"] = canvas_course_id
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
                res = self.download_participation_analytics(canvas_course_id)
                for analytic in res:
                    analytic["canvas_user_id"] = analytic.pop("id")
                    analytic["canvas_course_id"] = canvas_course_id
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

    def save_assignments_to_db(self, assignment_dicts, job):
        """
        Save list of assignment dictionaries to the db for the given job

        :param assignment_dicts: List of dictionaries containing
            assignment analytic info
        :type assignment_dicts: dict
        :param job: Job associated with the assignment analytics to save
        :type job: data_aggregator.models.Job
        """

        def save(assign_objs, canvas_course_id, create=True):
            if create:
                if assign_objs:
                    Assignment.objects.bulk_create(assign_objs, batch_size=100)
                    logging.debug(f"Created {len(assign_objs)} "
                                  f"assignment records for Canvas course "
                                  f"{canvas_course_id}.")
            else:
                if assign_objs:
                    for assign in assign_objs:
                        assign.save()
                    logging.debug(f"Updated {len(assign_objs)} "
                                  f"assignment records for Canvas course "
                                  f"{canvas_course_id}.")

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
            assign_objs_create = []
            assign_objs_update = []
            for i in assignment_dicts:
                student_id = i.get('canvas_user_id')
                assignment_id = i.get('assignment_id')
                try:
                    user = User.objects.get(canvas_user_id=student_id)
                except User.DoesNotExist:
                    logging.warning(f"User with canvas_user_id {student_id} "
                                    f"does not exist in Canvas Analytics DB. "
                                    f"Skipping.")
                    continue
                try:
                    assign = (Assignment.objects
                              .get(user=user,
                                   assignment_id=assignment_id,
                                   week=week))
                    logging.warning(
                        f"Found existing assignment entry for "
                        f"canvas_course_id: {canvas_course_id}, "
                        f"user: {student_id}, sis-term-id: {sis_term_id}, "
                        f"week: {week_num}")
                    assign_objs_update.append(assign)
                except Assignment.DoesNotExist:
                    assign = Assignment()
                    assign_objs_create.append(assign)
                assign.job = job
                assign.user = user
                assign.assignment_id = assignment_id
                assign.week = week
                assign.title = i.get('title')
                assign.unlock_at = i.get('unlock_at')
                assign.points_possible = i.get('points_possible')
                assign.non_digital_submission = \
                    i.get('non_digital_submission')
                assign.due_at = i.get('due_at')
                assign.status = i.get('status')
                assign.muted = i.get('muted')
                assign.max_score = i.get('max_score')
                assign.min_score = i.get('min_score')
                assign.first_quartile = i.get('first_quartile')
                assign.median = i.get('median')
                assign.third_quartile = i.get('third_quartile')
                assign.excused = i.get('excused')
                submission = i.get('submission')
                if submission:
                    assign.score = submission.get('score')
                    assign.posted_at = submission.get('posted_at')
                    assign.submitted_at = \
                        submission.get('submitted_at')
                assign.course = course
            if assign_objs_create:
                # create new assignment entries
                save(assign_objs_create, canvas_course_id, create=True)
            if assign_objs_update:
                # update existing assignment entries
                save(assign_objs_update, canvas_course_id, create=False)
        else:
            logging.info("No assignment records to load.")

    def save_participations_to_db(self, participation_dicts, job):
        """
        Save list of participation dictionaries to the db for the given job

        :param participation_dicts: List of dictionaries containing
            participation analytic info
        :type participation_dicts: dict
        :param job: Job associated with the participation analytics to save
        :type job: data_aggregator.models.Job
        """

        def save(partic_objs, canvas_course_id, create=True):
            if create:
                Participation.objects.bulk_create(partic_objs, batch_size=100)
                logging.debug(f"Created {len(partic_objs)} "
                              f"participation records for Canvas course "
                              f"{canvas_course_id}.")
            else:
                for partic in partic_objs:
                    partic.save()
                logging.debug(f"Updated {len(partic_objs)} "
                              f"participation records for Canvas course "
                              f"{canvas_course_id}.")

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
            partic_objs_create = []
            partic_objs_update = []
            for i in participation_dicts:
                student_id = i.get('canvas_user_id')
                try:
                    user = User.objects.get(canvas_user_id=student_id)
                except User.DoesNotExist:
                    logging.warning(f"User with canvas_user_id {student_id} "
                                    f"does not exist in Canvas Analytics DB. "
                                    f"Skipping.")
                    continue
                try:
                    partic = (Participation.objects.get(user=user,
                                                        week=week,
                                                        course=course))
                    logging.warning(
                        f"Found existing participation entry for "
                        f"canvas_course_id: {canvas_course_id}, "
                        f"user: {student_id}, sis-term-id: {sis_term_id}, "
                        f"week: {week_num}")
                    partic_objs_update.append(partic)
                except Participation.DoesNotExist:
                    partic = Participation()
                    partic_objs_create.append(partic)
                partic.job = job
                partic.user = user
                partic.week = week
                partic.course = course
                partic.page_views = i.get('page_views')
                partic.page_views_level = \
                    i.get('page_views_level')
                partic.participations = i.get('participations')
                partic.participations_level = \
                    i.get('participations_level')
                if i.get('tardiness_breakdown'):
                    partic.time_tardy = (i.get('tardiness_breakdown')
                                         .get('total'))
                    partic.time_on_time = (i.get('tardiness_breakdown')
                                           .get('on_time'))
                    partic.time_late = (i.get('tardiness_breakdown')
                                        .get('late'))
                    partic.time_missing = (i.get('tardiness_breakdown')
                                           .get('missing'))
                    partic.time_floating = (i.get('tardiness_breakdown')
                                            .get('floating'))
                partic.page_views = i.get('page_views')
            if partic_objs_create:
                # create new participation entries
                save(partic_objs_create, canvas_course_id, create=True)
            if partic_objs_update:
                # update existing participation entries
                save(partic_objs_update, canvas_course_id, create=False)
            else:
                logging.info("No participation records to load.")

    def run_analytics_job(self, job):
        """
        Download analytics for the given job
        and save them to the database.

        :param analytic_type: type of analytics to load
        :type analytic_type: str (AnalyticTypes.assignment or
            AnalyticTypes.participation)
        :param job: Job associated with the analytics to save
        :type job: data_aggregator.models.Job
        """
        canvas_course_id = job.context["canvas_course_id"]
        sis_term_id = job.context["sis_term_id"]
        week_num = job.context["week"]
        analytic_type = job.type.type
        # in case gcs caching is enabled, set gcs base path env variable so
        # that cached responses are ordered by term and week
        self.set_gcs_base_path(sis_term_id, week_num)

        # delete existing assignment data in case of a job restart
        self.delete_data_for_job(job)

        cd = CanvasDAO()

        analytics = []
        for analytic in cd.download_raw_analytics_for_course(
                                            canvas_course_id, analytic_type):
            analytics.append(analytic)
            logging.debug(f"Saved {len(analytics)} {analytic_type} "
                          f"entries")
        if analytics and analytic_type == AnalyticTypes.assignment:
            # save remaining assignments to db
            self.save_assignments_to_db(analytics, job)
        elif analytics and analytic_type == AnalyticTypes.participation:
            # save remaining participations to db
            self.save_participations_to_db(analytics, job)


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

        course_count = 0
        for row in DictReader(sis_data):
            if not len(row):
                continue
            created_by_sis = row['created_by_sis']
            if created_by_sis:
                canvas_course_id = row['canvas_course_id']
                # create / update course
                course, created_course = Course.objects.get_or_create(
                    canvas_course_id=canvas_course_id,
                    term=term)
                if created_course:
                    logging.info(f"Created course - {canvas_course_id}")
                else:
                    logging.info(f"Updated course - {canvas_course_id}")
                # we always update the course regardless if it is new or not
                course.sis_course_id = row['course_id']
                course.short_name = row['short_name']
                course.long_name = row['long_name']
                course.canvas_account_id = row['canvas_account_id']
                course.sis_account_id = row['account_id']
                course.status = row['status']
                course.save()
                course_count += 1
        logging.info(f'Created and/or updated {course_count} courses.')
        return course_count

    @transaction.atomic
    def _create_users(self, user_dicts, batch_size=100):
        """
        Save list of new users to the database

        :param user_dicts: list of users to save
        :type user_dicts: list
        :param batch_size: number of users to save at one time. (default=250)
        :type batch_size: int
        """
        if user_dicts:
            User.objects.bulk_create(user_dicts, batch_size=batch_size)

    @transaction.atomic
    def _update_users(self, user_dicts, batch_size=250):
        """
        Update list of users in the database

        :param user_dicts: list of users to save
        :type user_dicts: list
        :param batch_size: number of users to save at one time. (default=250)
        :type batch_size: int
        """
        if user_dicts:
            User.objects.bulk_update(
                user_dicts,
                ["login_id", "sis_user_id", "first_name",
                 "last_name", "full_name", "sortable_name",
                 "email", "status"],
                batch_size=batch_size)

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
        existing_users = {}
        update = {}
        create = {}
        user_count = 0
        for user in User.objects.all():
            existing_users[int(user.canvas_user_id)] = user
        for row in DictReader(sis_data):
            if not len(row):
                continue
            created_by_sis = row['created_by_sis']
            status = row['status']
            sis_user_id = row['user_id']
            if created_by_sis == "true" and status == "active" and \
                    pws.valid_uwregid(sis_user_id):
                # we need to cast the canvas_user_id from the file to an int
                # so that the dictionary lookup works
                canvas_user_id = int(row['canvas_user_id'])
                user = existing_users.get(canvas_user_id)
                if user:
                    new_user = False
                else:
                    user = User()
                    user.canvas_user_id = canvas_user_id
                    new_user = True

                user.sis_user_id = sis_user_id
                user.login_id = row['login_id']
                user.first_name = row['first_name']
                user.last_name = row['last_name']
                user.full_name = row['full_name']
                user.sortable_name = row['sortable_name']
                user.email = row['email']
                user.status = status
                if new_user:
                    create[user.canvas_user_id] = user
                else:
                    update[user.canvas_user_id] = user
                user_count += 1

        users_to_create = list(create.values())
        self._create_users(users_to_create, batch_size=100)
        logging.info(f"Created {len(users_to_create)} user(s).")
        users_to_update = list(update.values())
        self._update_users(users_to_update, batch_size=100)
        logging.info(f"Updated {len(users_to_update)} user(s).")
        return user_count

    def create_rad_db_view(self, sis_term_id, week):
        """
        Create rad db view for given week and sis-term-id

        :param sis_term_id: sis term id to create view for. (default is
            the current term)
        :type sis_term_id: str
        :param week_num: week number to create view for . (default is
            the current week of term)
        :type week_num: int
        """

        view_name = get_view_name(sis_term_id, week, "rad")
        assignments_view_name = get_view_name(sis_term_id,
                                              week,
                                              "assignments")
        participations_view_name = get_view_name(sis_term_id,
                                                 week,
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
                            coalesce(
                                cast((p1.participations - min_raw_participation_score) as decimal) /
                                NULLIF( cast((max_raw_participation_score - min_raw_participation_score) as decimal) / 10, 0),
                            0) - 5
                        AS normalized_participation_score,
                            coalesce(
                                cast(((2 * p1.time_on_time + p1.time_late) - min_raw_assignment_score) as decimal) /
                                NULLIF( cast((max_raw_assignment_score - min_raw_assignment_score) as decimal) / 10, 0)
                                    , 0) - 5
                        AS normalized_assignment_score
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
                SELECT DISTINCT
                    a1.user_id,
                    AVG(normalized_score) AS grade
                FROM (
                SELECT
                    a2.user_id,
                    CASE
                    WHEN (COALESCE(a2.max_score, 0) - COALESCE(a2.min_score, 0)) = 0 THEN 0
                    WHEN a2.score  IS NULL THEN -5
                    ELSE ((10 * (COALESCE(a2.score, 0) - COALESCE(a2.min_score, 0))) /
                            (COALESCE(a2.max_score, 0) - COALESCE(a2.min_score, 0))) - 5
                    END AS normalized_score
                FROM "{assignments_view_name}" a2
                WHERE a2.status = 'on_time' OR a2.status = 'late' OR a2.status = 'missing'
                GROUP BY a2.user_id, normalized_score 
                ) a1
                GROUP BY
                    a1.user_id
            )
            SELECT DISTINCT
                u.canvas_user_id,
                u.full_name,
                '{sis_term_id}' as term,
                {week} as week,
                assignment_score,
                participation_score,
                grade
            FROM avg_norm_ap
            JOIN avg_norm_gr ON avg_norm_ap.user_id = avg_norm_gr.user_id
            JOIN data_aggregator_user u ON avg_norm_ap.user_id = u.id
            '''  # noqa
        )
        return True

    def create_participation_db_view(self, sis_term_id, week):
        """
        Create participation db view for given week and sis-term-id

        :param sis_term_id: sis term id to create view for. (default is
            the current term)
        :type sis_term_id: str
        :param week_num: week number to create view for . (default is
            the current week of term)
        :type week_num: int
        """
        view_name = get_view_name(sis_term_id, week, "participations")

        cursor = connection.cursor()

        env = os.getenv("ENV")
        if env == "localdev" or not env:
            create_action = f'CREATE VIEW "{view_name}"'
            cursor.execute(f'DROP VIEW IF EXISTS "{view_name}"')
        else:
            create_action = f'CREATE MATERIALIZED VIEW "{view_name}"'

        cursor.execute(
            f'''
            {create_action} AS
            SELECT
                data_aggregator_term.id AS term_id,
                data_aggregator_week.id AS week_id,
                p.course_id,
                p.user_id,
                p.participations AS participations,
                p.participations_level AS participations_level,
                p.page_views AS page_views,
                p.page_views_level AS page_views_level,
                p.time_tardy AS time_tardy,
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
            WHERE data_aggregator_week.week = {week}
            AND data_aggregator_term.sis_term_id = '{sis_term_id}'
            '''
        )
        return True

    def create_assignment_db_view(self, sis_term_id, week):
        """
        Create assignment db view for given week and sis-term-id

        :param sis_term_id: sis term id to create view for. (default is
            the current term)
        :type sis_term_id: str
        :param week_num: week number to create view for . (default is
            the current week of term)
        :type week_num: int
        """
        view_name = get_view_name(sis_term_id, week, "assignments")

        cursor = connection.cursor()

        env = os.getenv("ENV")
        if env == "localdev" or not env:
            create_action = f'CREATE VIEW "{view_name}"'
            cursor.execute(f'DROP VIEW IF EXISTS "{view_name}"')
        else:
            create_action = f'CREATE MATERIALIZED VIEW "{view_name}"'

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
            WHERE data_aggregator_week.week = {week} AND
            data_aggregator_term.sis_term_id = '{sis_term_id}'
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
        term, _ = Term.objects.get_or_create_term_from_sis_term_id(
            sis_term_id=sis_term_id)
        users_df = self.get_users_df()
        url_key = (f"application_metadata/student_categories/"
                   f"{term.sis_term_id}-netid-name-stunum-categories.csv")
        content = self.download_from_gcs_bucket(url_key)

        sdb_df = pd.read_csv(StringIO(content))

        i = list(sdb_df.columns[sdb_df.columns.str.startswith('regis_')])
        i.extend(['yrq', 'enroll_status'])
        sdb_df.drop(columns=i, inplace=True)
        sdb_df.drop_duplicates(inplace=True)

        sdb_df = sdb_df.merge(users_df, how='left', on='uw_netid')
        sdb_df.fillna(value={'canvas_user_id': -99}, inplace=True)
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
        Download eop advisors file from the configured GCS bucket
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
        return eop_df

    def get_iss_advisers_df(self, sis_term_id=None):
        """
        Download iss advisors file from the configured GCS bucket
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
            usecols=['Student_number', 'Adviser',
                     'Adviser_NetID'])
        iss_df.rename(columns={'Student_number': 'student_no',
                               'Adviser': 'adviser_name',
                               'Adviser_NetID': 'staff_id'},
                      inplace=True)
        # strip any whitespace
        iss_df['adviser_name'] = iss_df['adviser_name'].str.strip()
        iss_df['staff_id'] = iss_df['staff_id'].str.strip()
        return iss_df

    def get_rad_dbview_df(self, sis_term_id=None, week_num=None):
        """
        Query RAD canvas data from the canvas-analytics RAD db view for the
        current term and week and return pandas dataframe with contents

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
        # get eop advisors
        eop_advisors_df = self.get_eop_advisers_df(sis_term_id=sis_term_id)
        # get iss advisors
        iss_advisors_df = self.get_iss_advisers_df(sis_term_id=sis_term_id)
        # combine advisors
        combined_advisors_df = \
            pd.concat([eop_advisors_df, iss_advisors_df])
        # merge to create the final dataset
        joined_canvas_df = (
            pd.merge(sdb_df, rad_df, how='left', on='canvas_user_id')
              .merge(idp_df, how='left', on='uw_netid')
              .merge(probs_df, how='left', on='system_key')
              .merge(combined_advisors_df, how='left', on='student_no'))
        joined_canvas_df = joined_canvas_df[
            ['uw_netid', 'student_no', 'student_name_lowc', 'activity',
             'assignments', 'grades', 'pred', 'adviser_name',
             'staff_id', 'sign_in', 'stem', 'incoming_freshman', 'premajor',
             'eop_student', 'international_student', 'isso']]
        return joined_canvas_df

    def create_rad_data_file(self, sis_term_id=None, week_num=None):
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
        rcd = self.get_rad_df(sis_term_id=sis_term_id, week_num=week_num)
        file_name = (f"rad_data/{term.sis_term_id}-week-"
                     f"{week.week}-rad-data.csv")
        file_obj = rcd.to_csv(sep=",", index=False, encoding="UTF-8")
        self.upload_to_gcs_bucket(file_name, file_obj)
