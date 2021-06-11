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
from io import IOBase, StringIO
from boto3 import client
from google.cloud import storage
from google.cloud.exceptions import NotFound
from datetime import datetime, timezone


class AnalyticTypes():

    assignment = "assignment"
    participation = "participation"


class BaseDao():

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
            logging.error("gcp {}: {}".format(url_key, ex))
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

    def get_current_term_and_week(self, sis_term_id=None, week=None):
        """
        Return tuple containing current sis-term-id and week number
        """
        if sis_term_id is not None and week is not None:
            return sis_term_id, week
        else:
            sws_term = get_current_term()
            curr_term, curr_week = \
                sws_term.canvas_sis_id(), \
                get_week_of_term(sws_term.first_day_quarter)
            if sis_term_id:
                curr_term = sis_term_id
            else:
                curr_term = curr_term
            if week:
                curr_week = week
            else:
                curr_week = curr_week
            return curr_term, curr_week


class CanvasDAO(BaseDao):
    """
    Query canvas for analytics
    """

    def __init__(self, sis_term_id=None, week=None):
        self.canvas = Canvas()
        self.courses = Courses()
        self.enrollments = Enrollments()
        self.analytics = Analytics()
        self.reports = Reports()
        self.terms = Terms()
        self.curr_term, self.curr_week = \
            self.get_current_term_and_week(sis_term_id=sis_term_id,
                                           week=week)
        os.environ["GCS_BASE_PATH"] = \
            "{}/{}/".format(self.curr_term, self.curr_week)
        super().__init__()

    @retry(DataFailureException, tries=5, delay=10, backoff=2,
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
        res = list({stu.user_id for stu in stus})
        return(res)

    @retry(DataFailureException, tries=5, delay=10, backoff=2,
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

    @retry(DataFailureException, tries=5, delay=10, backoff=2,
           status_codes=[0, 403, 408, 500])
    def download_raw_analytics_for_student(
            self, canvas_course_id, student_id, analytic_type):
        """
        Download raw analytics for a given canvas course id and student

        :param canvas_course_id: canvas course id to download analytics for
        :type canvas_course_id: int
        :param student_id: canvas user id to download analytic for
        :type student_id: int
        :param analytic_type:
        :type analytic_type: str (AnalyticTypes.assignment or
            AnalyticTypes.participation)
        """
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
        """
        Download raw analytics for a given canvas course id

        :param canvas_course_id: canvas course id to download analytics for
        :type canvas_course_id: int
        :param analytic_type:
        :type analytic_type: str (AnalyticTypes.assignment or
            AnalyticTypes.participation)
        """
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
        """
        Save list of assignment dictionaries to the db

        :param assignment_dicts: List of dictionaries containing
            assignment analytic info
        :type assignment_dicts: dict
        :param job: Job associated with the assignment analytics to save
        :type job: data_aggregator.models.Job
        """

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
        """
        Save list of participation dictionaries to the db

        :param participation_dicts: List of dictionaries containing
            participation analytic info
        :type participation_dicts: dict
        :param job: Job associated with the participation analytics to save
        :type job: data_aggregator.models.Job
        """

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
        """
        Download canvas course provisioning report

        :param sis_term_id: sis term id to load course report for
        :type sis_term_id: numeric
        """
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
        """
        Download canvas sis user provisioning report

        :param sis_term_id: sis term id to load users report for
        :type sis_term_id: numeric
        """
        # get canvas term using sis-term-id
        canvas_term = self.terms.get_term_by_sis_id(sis_term_id)
        # get users provisioning report for canvas term
        user_report = self.reports.create_user_provisioning_report(
                    settings.ACADEMIC_CANVAS_ACCOUNT_ID,
                    term_id=canvas_term.term_id)
        sis_data = self.reports.get_report_data(user_report)
        self.reports.delete_report(user_report)
        return sis_data


class LoadRadDAO(BaseDao):

    def __init__(self, sis_term_id=None, week=None):
        self.curr_term, self.curr_week = \
            self.get_current_term_and_week(sis_term_id=sis_term_id,
                                           week=week)
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

    def get_student_categories_df(self):
        """
        Download student categories file from the configured GCS bucket
        and return pandas dataframe with contents
        """
        users_df = self.get_users_df()

        url_key = ("application_metadata/student_categories/"
                   "{}-netid-name-stunum-categories.csv"
                   .format(self.curr_term))
        content = self.download_from_gcs_bucket(url_key)

        sdb_df = pd.read_csv(StringIO(content))

        i = list(sdb_df.columns[sdb_df.columns.str.startswith('regis_')])
        i.extend(['yrq', 'enroll_status'])
        sdb_df.drop(columns=i, inplace=True)
        sdb_df.drop_duplicates(inplace=True)

        sdb_df = sdb_df.merge(users_df, how='left', on='uw_netid')
        sdb_df.fillna(value={'canvas_user_id': -99}, inplace=True)
        return sdb_df

    def get_pred_proba_scores_df(self):
        """
        Download predicted probabilities file from the configured GCS bucket
        and return pandas dataframe with contents
        """
        url_key = ("application_metadata/predicted_probabilites/"
                   "{}-pred-proba.csv".format(self.curr_term))
        content = self.download_from_gcs_bucket(url_key)

        probs_df = pd.read_csv(
            StringIO(content),
            usecols=['system_key', 'pred0'])
        probs_df['pred0'] = probs_df['pred0'].transform(self._rescale_range)
        probs_df.rename(columns={'pred0': 'pred'},
                        inplace=True)
        return probs_df

    def get_eop_advisers_df(self):
        """
        Download eop advisors file from the configured GCS bucket
        and return pandas dataframe with contents
        """
        url_key = ("application_metadata/eop_advisers/"
                   "{}-eop-advisers.csv".format(self.curr_term))
        content = self.download_from_gcs_bucket(url_key)
        eop_df = pd.read_csv(
            StringIO(content),
            usecols=['student_no', 'adviser_name', 'staff_id'])
        # strip any whitespace
        eop_df['adviser_name'] = eop_df['adviser_name'].str.strip()
        eop_df['staff_id'] = eop_df['staff_id'].str.strip()
        return eop_df

    def get_iss_advisers_df(self):
        """
        Download iss advisors file from the configured GCS bucket
        and return pandas dataframe with contents
        """
        url_key = ("application_metadata/iss_advisers/"
                   "{}-iss-advisers.csv".format(self.curr_term))
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

    def get_rad_dbview_df(self):
        """
        Query RAD canvas data from the canvas-analytics RAD db view for the
        current term and week and return pandas dataframe with contents
        """
        view_name = get_view_name(self.curr_term, self.curr_week, "rad")
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

    def get_rad_df(self):
        """
        Get a pandas dataframe containing the contents of the
        rad data file
        """
        # get rad canvas data
        rad_df = self.get_rad_dbview_df()
        # get student categories
        sdb_df = self.get_student_categories_df()
        # get idp data
        idp_df = self.get_idp_df()
        # get predicted probabilities
        probs_df = self.get_pred_proba_scores_df()
        # get eop advisors
        eop_advisors_df = self.get_eop_advisers_df()
        # get iss advisors
        iss_advisors_df = self.get_iss_advisers_df()
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
