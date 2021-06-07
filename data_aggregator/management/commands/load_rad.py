import io
import logging
import numpy as np
import pandas as pd
from boto3 import client
from google.cloud import storage
from google.cloud.exceptions import NotFound
from django.conf import settings
from django.core.management.base import BaseCommand
from data_aggregator.models import User, RadDbView
from uw_sws.term import get_current_term
from data_aggregator.utilities import get_week_of_term, get_view_name


class Command(BaseCommand):

    help = ("Loads normalized Canvas assignment and participation analytics "
            "into RAD.")

    def __init__(self):
        self._configure_pandas()
        self.gcs_client = storage.Client()
        self.gcs_bucket_name = "canvas-analytics-test"
        self.s3_client = client('s3',
                                aws_access_key_id=settings.AWS_ACCESS_ID,
                                aws_secret_access_key=settings.AWS_ACCESS_KEY)
        self.s3_bucket_name = "uw-idp-data-files"

    def _configure_pandas(self):
        pd.options.mode.use_inf_as_na = True
        pd.options.display.max_rows = 500
        pd.options.display.precision = 3
        pd.options.display.float_format = '{:.3f}'.format

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
        content = io.BytesIO(idp_obj['Body'].read())
        return content

    def get_student_categories_df(self, term):
        users = User.objects.all().values("canvas_user_id", "login_id")
        users_df = pd.DataFrame(users)

        url_key = ("application_metadata/student_categories/"
                   "{}-netid-name-stunum-categories.csv".format(term))
        content = self.download_from_gcs_bucket(url_key)

        sdb_df = pd.read_csv(io.StringIO(content))
        i = list(sdb_df.columns[sdb_df.columns.str.startswith('regis_')])
        i.extend(['yrq', 'enroll_status', 'dept_abbrev',
                 'course_no', 'section_id', 'course_id'])
        sdb_df.drop(columns=i, inplace=True)
        sdb_df.drop_duplicates(inplace=True)
        sdb_df = sdb_df.merge(users_df.rename(
            columns={'login_id': 'uw_netid'}), how='left', on='uw_netid')
        sdb_df.fillna(value={'canvas_user_id': -99}, inplace=True)
        return sdb_df

    def get_pred_proba_scores_df(self, term):
        url_key = ("application_metadata/predicted_probabilites/"
                   "{}-pred-proba.csv".format(term))
        content = self.download_from_gcs_bucket(url_key)

        probs_df = pd.read_csv(
            io.StringIO(content),
            usecols=['system_key', 'pred0'])
        probs_df['pred0'] = probs_df['pred0'].transform(self.rescale_range)
        return probs_df


    def get_rad_dbview_df(self, sis_term_id, week):
        view_name = get_view_name(sis_term_id, week, "rad")
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
        idp_df['sign_in'] = self.rescale_range(idp_df['sign_in'])
        return idp_df

    def zero_range(self, x):
        '''
        Check range of series x is non-zero.
        Helper for rescaling.
        May choke if all x is na.
        '''
        zr = False
        if x.min() == x.max():
            zr = True
        return zr


    def rescale_range(self, x, min=-5, max=5):
        '''
        Scale numbers to an arbitray min/max range.
        '''
        if self.zero_range(x):
            return np.mean([min, max])
        elif x.isnull().all():
            return np.nan
        else:
            x += -(x.min())
            x /= x.max() / (max - min)
            x += min
            return x

    def handle(self, *args, **options):
        sws_term = get_current_term()
        sis_term_id = sws_term.canvas_sis_id()
        week = get_week_of_term(sws_term.first_day_quarter)

        sis_term_id = "2021-spring"
        week = 10

        # get rad canvas data
        rad_canvas_df = self.get_rad_dbview_df(sis_term_id, week)
        # get student categories
        sdb_df = self.get_student_categories_df(sis_term_id)
        # get idp data
        idp_df = self.get_idp_df()
        # get predicted probabilities
        probs_df = self.get_pred_proba_scores_df(sis_term_id)

        # merge to create the final dataset
        joined_canvas_df = (pd.merge(sdb_df, rad_canvas_df, how='left',
                                     on='canvas_user_id')
                              .merge(idp_df, how='left', on='uw_netid')
                              .merge(probs_df, how='left', on='system_key'))
        joined_canvas_df.to_csv("{}-week-{}-rad-data.csv"
                                .format(sis_term_id, week))
