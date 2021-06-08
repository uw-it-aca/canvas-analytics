import logging
import os
from django.conf import settings
from data_aggregator.models import Assignment, Course, Participation, \
    Term, User, Week, RadDbView
from data_aggregator.utilities import get_week_of_term, get_view_name
from restclients_core.exceptions import DataFailureException
from restclients_core.util.retry import retry
from uw_sws.term import get_current_term
from uw_canvas import Canvas
from uw_canvas.analytics import Analytics
from uw_canvas.courses import Courses
from uw_canvas.enrollments import Enrollments
from uw_canvas.reports import Reports
from uw_canvas.terms import Terms

import numpy as np
import pandas as pd
from io import IOBase, StringIO, BytesIO
from boto3 import client
from google.cloud import storage
from google.cloud.exceptions import NotFound
from datetime import datetime, timezone


class AnalyticTypes():

    assignment = "assignment"
    participation = "participation"


class CanvasDAO():
    """
    Query canvas for analytics
    """

    def __init__(self):
        self.canvas = Canvas()
        self.courses = Courses()
        self.enrollments = Enrollments()
        self.analytics = Analytics()
        self.reports = Reports()
        self.terms = Terms()
        sws_term = get_current_term()
        self.curr_term = sws_term.canvas_sis_id()
        self.curr_week = get_week_of_term(sws_term.first_day_quarter)
        os.environ["GCS_BASE_PATH"] = \
            "{}/{}/".format(self.curr_term, self.curr_week)

    @retry(DataFailureException, tries=5, delay=10, backoff=2,
           status_codes=[0, 403, 408, 500])
    def download_student_ids_for_course(self, canvas_course_id):
        stus = self.enrollments.get_enrollments_for_course(
                    canvas_course_id,
                    params={
                        "type": ['StudentEnrollment'],
                        "state": ['active', 'deleted', 'inactive']
                    })
        res = list({stu.user_id for stu in stus})
        return(res)

    @retry(DataFailureException, tries=5, delay=10, backoff=2,
           status_codes=[0, 403, 408, 500])
    def download_course(self, canvas_course_id):
        try:
            return self.courses.get_course(canvas_course_id)
        except Exception as e:
            logging.error(e)

    @retry(DataFailureException, tries=5, delay=10, backoff=2,
           status_codes=[0, 403, 408, 500])
    def download_raw_analytics_for_student(
            self, canvas_course_id, student_id, analytic_type):
        if analytic_type == AnalyticTypes.assignment:
            return self.analytics.get_student_assignments_for_course(
                student_id, canvas_course_id)
        elif analytic_type == AnalyticTypes.participation:
            return self.analytics.get_student_summaries_by_course(
                canvas_course_id, student_id=student_id)
        else:
            raise ValueError(f"Unknown analytic type: {analytic_type}")

    def download_raw_analytics_for_course(
            self, canvas_course_id, analytic_type):
        students_ids = self.download_student_ids_for_course(canvas_course_id)
        analytics = []
        for student_id in students_ids:
            try:
                res = self.download_raw_analytics_for_student(
                    canvas_course_id, student_id, analytic_type=analytic_type)
                for analytic in res:
                    analytic["canvas_user_id"] = student_id
                    analytic["canvas_course_id"] = canvas_course_id
                    analytics.append(analytic)
            except DataFailureException as e:
                if e.status == 404:
                    logging.warning(e)
                    continue
                else:
                    raise
        return analytics

    def save_assignments_to_db(self, assignment_dicts, job):

        def save(assign_objs, canvas_course_id, create=True):
            if create:
                if assign_objs:
                    Assignment.objects.bulk_create(assign_objs)
                    logging.info(f"Created {len(assign_objs)} "
                                 f"assignment records for Canvas course "
                                 f"{canvas_course_id}.")
            else:
                if assign_objs:
                    for assign in assign_objs:
                        assign.save()
                    logging.info(f"Updated {len(assign_objs)} "
                                 f"assignment records for Canvas course "
                                 f"{canvas_course_id}.")

        if assignment_dicts:
            canvas_course_id = assignment_dicts[0]["canvas_course_id"]
            curr_term = get_current_term()
            term = Term.objects.get(year=curr_term.year,
                                    quarter=curr_term.quarter)
            course = (Course.objects.get(
                        canvas_course_id=canvas_course_id,
                        term=term))
            curr_week = get_week_of_term(curr_term.first_day_quarter)
            week, _ = Week.objects.get_or_create(
                week=curr_week,
                term=term)
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
                        "Found existing assignment entry for user: {}, "
                        "week: {}, year: {}, quarter: {} course: {}"
                        .format(student_id, curr_week, curr_term.year,
                                curr_term.quarter, canvas_course_id))
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
                if (len(assign_objs_create) > 0 and
                        len(assign_objs_create) % 50 == 0):
                    # create new assignment entries
                    save(assign_objs_create, canvas_course_id, create=True)
                    assign_objs_create = []
                if (len(assign_objs_update) > 0 and
                        len(assign_objs_update) % 50 == 0):
                    # update existing assignment entries
                    save(assign_objs_update, canvas_course_id, create=False)
                    assign_objs_update = []
            if assign_objs_create:
                # create new assignment entries
                save(assign_objs_create, canvas_course_id, create=True)
            if assign_objs_update:
                # update existing assignment entries
                save(assign_objs_update, canvas_course_id, create=False)
        else:
            logging.info("No assignment records to load.")

    def save_participations_to_db(self, participation_dicts, job):

        def save(partic_objs, canvas_course_id, create=True):
            if create:
                Participation.objects.bulk_create(partic_objs)
                logging.info(f"Created {len(partic_objs)} "
                             f"participation records for Canvas course "
                             f"{canvas_course_id}.")
            else:
                for partic in partic_objs:
                    partic.save()
                logging.info(f"Updated {len(partic_objs)} "
                             f"participation records for Canvas course "
                             f"{canvas_course_id}.")

        if participation_dicts:
            canvas_course_id = participation_dicts[0]["canvas_course_id"]
            curr_term = get_current_term()
            term = Term.objects.get(year=curr_term.year,
                                    quarter=curr_term.quarter)
            course = (Course.objects.get(
                        canvas_course_id=canvas_course_id,
                        term=term))
            curr_week = get_week_of_term(curr_term.first_day_quarter)
            week, _ = Week.objects.get_or_create(
                week=curr_week,
                term=term)
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
                        "Found existing participation entry for user: {}, "
                        "week: {}, year: {}, quarter: {} course: {}"
                        .format(student_id, curr_week, curr_term.year,
                                curr_term.quarter, canvas_course_id))
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
                if (len(partic_objs_create) > 0 and
                        len(partic_objs_create) % 50 == 0):
                    # create new participation entries
                    save(partic_objs_create, canvas_course_id, create=True)
                    partic_objs_create = []
                if (len(partic_objs_update) > 0 and
                        len(partic_objs_update) % 50 == 0):
                    # update existing participation entries
                    save(partic_objs_update, canvas_course_id, create=False)
                    partic_objs_update = []
            if partic_objs_create:
                # create new participation entries
                save(partic_objs_create, canvas_course_id, create=True)
            if partic_objs_update:
                # update existing participation entries
                save(partic_objs_update, canvas_course_id, create=False)
            else:
                logging.info("No participation records to load.")

    def download_course_provisioning_report(self, sis_term_id):
        # get canvas term using sis-term-id
        canvas_term = self.terms.get_term_by_sis_id(sis_term_id)
        # get courses provisioning report for canvas term
        user_report = self.reports.create_course_provisioning_report(
                    settings.ACADEMIC_CANVAS_ACCOUNT_ID,
                    term_id=canvas_term.term_id)
        sis_data = self.reports.get_report_data(user_report)
        self.reports.delete_report(user_report)
        return sis_data

    def download_user_provisioning_report(self, sis_term_id):
        # get canvas term using sis-term-id
        canvas_term = self.terms.get_term_by_sis_id(sis_term_id)
        # get users provisioning report for canvas term
        user_report = self.reports.create_user_provisioning_report(
                    settings.ACADEMIC_CANVAS_ACCOUNT_ID,
                    term_id=canvas_term.term_id)
        sis_data = self.reports.get_report_data(user_report)
        self.reports.delete_report(user_report)
        return sis_data


class LoadRadDao():

    def __init__(self):
        self._configure_pandas()
        self.gcs_client = storage.Client()
        self.gcs_bucket_name = settings.RAD_METADATA_BUCKET_NAME
        self.s3_client = client('s3',
                                aws_access_key_id=settings.AWS_ACCESS_ID,
                                aws_secret_access_key=settings.AWS_ACCESS_KEY)
        self.s3_bucket_name = settings.IDP_BUCKET_NAME
        sws_term = get_current_term()
        self.curr_term = sws_term.canvas_sis_id()
        self.curr_week = get_week_of_term(sws_term.first_day_quarter)

    def _configure_pandas(self):
        pd.options.mode.use_inf_as_na = True
        pd.options.display.max_rows = 500
        pd.options.display.precision = 3
        pd.options.display.float_format = '{:.3f}'.format

    def _zero_range(self, x):
        '''
        Check range of series x is non-zero.
        Helper for rescaling.
        May choke if all x is na.
        '''
        zr = False
        if x.min() == x.max():
            zr = True
        return zr

    def _rescale_range(self, x, min=-5, max=5):
        '''
        Scale numbers to an arbitray min/max range.
        '''
        if self._zero_range(x):
            return np.mean([min, max])
        elif x.isnull().all():
            return np.nan
        else:
            x += -(x.min())
            x /= x.max() / (max - min)
            x += min
            return x

    def download_from_gcs_bucket(self, url_key):
        bucket = self.gcs_client.get_bucket(self.gcs_bucket_name)
        try:
            blob = bucket.get_blob(url_key)
            content = blob.download_as_string()
            if content:
                return content.decode('utf-8')
        except NotFound as ex:
            logging.error("gcp {}: {}".format(url_key, ex))
            raise

    def download_from_s3_bucket(self, url_key):
        idp_obj = self.s3_client.get_object(Bucket=self.s3_bucket_name,
                                            Key=url_key)
        content = BytesIO(idp_obj['Body'].read())
        return content

    def upload_to_gcs_bucket(self, url_key, content):
        """
        Upload a string or file-like object contents to GCS bucket

        :param url_key: URL response to cache
        :type url_key: str
        :param content: Content to cache
        :type content: str or file object
        """
        bucket = self.gcs_client.get_bucket(self.gcs_bucket_name)
        blob = bucket.get_blob(url_key)
        if not blob:
            blob = bucket.blob(url_key)
        blob.custom_time = datetime.now(timezone.utc)
        if isinstance(content, IOBase):
            blob.upload_from_file(content,
                                  num_retries=5,
                                  timeout=30)
        else:
            blob.upload_from_string(str(content),
                                    num_retries=5,
                                    timeout=30)

    def get_student_categories_df(self):
        users = User.objects.all().values("canvas_user_id", "login_id")
        users_df = pd.DataFrame(users)

        url_key = ("application_metadata/student_categories/"
                   "{}-netid-name-stunum-categories.csv"
                   .format(self.curr_term))
        content = self.download_from_gcs_bucket(url_key)

        sdb_df = pd.read_csv(StringIO(content))
        i = list(sdb_df.columns[sdb_df.columns.str.startswith('regis_')])
        i.extend(['yrq', 'enroll_status', 'dept_abbrev',
                 'course_no', 'section_id', 'course_id'])
        sdb_df.drop(columns=i, inplace=True)
        sdb_df.drop_duplicates(inplace=True)
        sdb_df = sdb_df.merge(users_df.rename(
            columns={'login_id': 'uw_netid'}), how='left', on='uw_netid')
        sdb_df.fillna(value={'canvas_user_id': -99}, inplace=True)
        return sdb_df

    def get_pred_proba_scores_df(self):
        url_key = ("application_metadata/predicted_probabilites/"
                   "{}-pred-proba.csv".format(self.curr_term))
        content = self.download_from_gcs_bucket(url_key)

        probs_df = pd.read_csv(
            StringIO(content),
            usecols=['system_key', 'pred0'])
        probs_df['pred0'] = probs_df['pred0'].transform(self._rescale_range)
        return probs_df

    def get_rad_dbview_df(self):
        view_name = get_view_name(self.curr_term, self.curr_week, "rad")
        rad_db_model = RadDbView.setDb_table(view_name)
        rad_canvas_qs = rad_db_model.objects.all().values()
        return pd.DataFrame(rad_canvas_qs)

    def get_idp_df(self):
        '''
        Returns a pandas dataframe containing the contents of the
        last idp object found in the s3 bucket.
        '''
        bucket_objects = \
            self.s3_client.list_objects_v2(Bucket=self.s3_bucket_name)
        last_idp_file = bucket_objects['Contents'][-1]['Key']
        logging.info(f'Using {last_idp_file} as idp file.')
        content = self.download_from_s3_bucket(last_idp_file)
        idp_df = pd.read_csv(content,
                             header=0,
                             names=['uw_netid', 'sign_in'])
        # normalize sign-in score
        idp_df['sign_in'] = np.log(idp_df['sign_in']+1)
        idp_df['sign_in'] = self._rescale_range(idp_df['sign_in'])
        return idp_df

    def get_rad_cavas_df(self):
        # get rad canvas data
        rad_canvas_df = self.get_rad_dbview_df()
        # get student categories
        sdb_df = self.get_student_categories_df()
        # get idp data
        idp_df = self.get_idp_df()
        # get predicted probabilities
        probs_df = self.get_pred_proba_scores_df()

        # merge to create the final dataset
        joined_canvas_df = (pd.merge(sdb_df, rad_canvas_df, how='left',
                                     on='canvas_user_id')
                              .merge(idp_df, how='left', on='uw_netid')
                              .merge(probs_df, how='left', on='system_key'))
        return joined_canvas_df
