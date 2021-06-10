import os
import unittest
import pandas as pd
import numpy as np
from io import StringIO
from django.test import TestCase
from data_aggregator.dao import AnalyticTypes, CanvasDAO, LoadRadDAO
from mock import patch, MagicMock
from restclients_core.exceptions import DataFailureException
from data_aggregator.management.commands.create_assignment_db_view \
    import create as create_assignment
from data_aggregator.management.commands.create_participation_db_view \
    import create as create_participation
from data_aggregator.management.commands.create_rad_db_view \
    import create as create_rad


class TestAnalyticTypes(TestCase):

    def test_types(self):
        self.assertEqual(AnalyticTypes.assignment, "assignment")
        self.assertEqual(AnalyticTypes.participation, "participation")


class TestCanvasDAO(TestCase):

    def get_test_canvas_dao(self):
        cd = CanvasDAO()
        cd.get_current_term_and_week = \
            MagicMock(return_value=("2021-spring", 1))
        return cd

    @patch('uw_canvas.enrollments.Enrollments')
    def test_download_student_ids_for_course(self, MockEnrollment):
        cd = self.get_test_canvas_dao()
        mock_enrollment_inst = MockEnrollment.return_value
        mock_return_values = []
        for user_id in [1234, 1234, 5432, 5432, 3456]:
            mock_user = MagicMock()
            mock_user.user_id = user_id
            mock_return_values.append(mock_user)
        mock_enrollment_inst.get_enrollments_for_course.return_value = \
            mock_return_values
        cd.enrollments = mock_enrollment_inst
        students = cd.download_student_ids_for_course(00000)
        self.assertEqual(sorted(students), [1234, 3456, 5432])

        # check that the mocked methods were called
        self.assertEqual(
            mock_enrollment_inst.get_enrollments_for_course.called, True)

    @patch('uw_canvas.courses.Courses')
    def test_download_course(self, MockCourse):
        cd = self.get_test_canvas_dao()
        mock_course_inst = MockCourse.return_value
        mock_course_inst.get_course.return_value = \
            mock_course_inst
        cd.courses = mock_course_inst
        self.assertEqual(cd.download_course(00000), mock_course_inst)
        self.assertNotEqual(cd.download_course(00000), True)
        self.assertNotEqual(cd.download_course(00000), False)
        self.assertNotEqual(cd.download_course(00000), None)

        # check that the mocked methods were called
        self.assertEqual(mock_course_inst.get_course.called, True)

    @patch('uw_canvas.analytics.Analytics')
    def test_download_raw_analytics_for_student(self, MockAnalytics):
        cd = self.get_test_canvas_dao()
        mock_analytics_inst = MockAnalytics.return_value
        mock_analytics_inst.get_student_assignments_for_course.return_value = \
            [{'assignment_1': 0,
              'canvas_course_id': 34567,
              'canvas_user_id': 12345},
             {'assignment_2': 1,
              'canvas_course_id': 34567,
              'canvas_user_id': 12345}]
        mock_analytics_inst = MockAnalytics.return_value
        mock_analytics_inst.get_student_summaries_by_course.return_value = \
            [{'participation_1': 0,
              'canvas_course_id': 76543,
              'canvas_user_id': 12345}]
        cd.analytics = mock_analytics_inst
        with self.assertRaises(ValueError):
            cd.download_raw_analytics_for_student(00000, 00000, "foobar")
        self.assertEqual(
            cd.download_raw_analytics_for_student(
                00000, 00000, AnalyticTypes.assignment),
            [{'assignment_1': 0,
              'canvas_course_id': 34567,
              'canvas_user_id': 12345},
             {'assignment_2': 1,
              'canvas_course_id': 34567,
              'canvas_user_id': 12345}])
        self.assertEqual(
            cd.download_raw_analytics_for_student(
                00000, 00000, AnalyticTypes.participation),
            [{'participation_1': 0,
              'canvas_course_id': 76543,
              'canvas_user_id': 12345}])

        # check that the mocked methods were called
        self.assertEqual(
            mock_analytics_inst.get_student_summaries_by_course.called, True)

    @patch('uw_canvas.analytics.Analytics')
    def test_download_raw_analytics_for_course(self, MockAnalytics):
        cd = self.get_test_canvas_dao()
        cd.download_student_ids_for_course = MagicMock()
        cd.download_student_ids_for_course.return_value = \
            [12345]
        mock_analytics_inst = MockAnalytics.return_value
        mock_analytics_inst.get_student_assignments_for_course.return_value = \
            [{"assignment_1": 0}, {"assignment_2": 1}]
        mock_analytics_inst = MockAnalytics.return_value
        mock_analytics_inst.get_student_summaries_by_course.return_value = \
            [{"participation_1": 0}]
        cd.analytics = mock_analytics_inst
        self.assertEqual(cd.download_raw_analytics_for_course(
            34567, AnalyticTypes.assignment),
            [{'assignment_1': 0,
              'canvas_course_id': 34567,
              'canvas_user_id': 12345},
             {'assignment_2': 1,
              'canvas_course_id': 34567,
              'canvas_user_id': 12345}])
        self.assertEqual(cd.download_raw_analytics_for_course(
            76543, AnalyticTypes.participation),
            [{'participation_1': 0,
              'canvas_course_id': 76543,
              'canvas_user_id': 12345}])

        # check that the mocked methods were called
        self.assertEqual(
            cd.download_student_ids_for_course.called, True)
        self.assertEqual(
            mock_analytics_inst.get_student_summaries_by_course.called, True)

        # mock skipping requests with 404 error
        cd.download_student_ids_for_course = MagicMock()
        cd.download_student_ids_for_course.side_effect = \
            DataFailureException("/bad/url", 404, 'not found')
        with self.assertRaises(DataFailureException):
            cd.download_student_ids_for_course.return_value = \
                [{"assignment_1": 0}, {"assignment_2": 1}]
            self.assertEqual(cd.download_raw_analytics_for_course(
                34567, AnalyticTypes.assignment),
                [{'assignment_1': 0,
                  'canvas_course_id': 34567,
                  'canvas_user_id': 12345},
                 {'assignment_2': 1,
                  'canvas_course_id': 34567,
                  'canvas_user_id': 12345}])
            cd.download_student_ids_for_course.return_value = \
                [{"participation_1": 0}]
            self.assertEqual(cd.download_raw_analytics_for_course(
                34567, AnalyticTypes.participation),
                [{'participation_1': 0,
                  'canvas_course_id': 76543,
                  'canvas_user_id': 12345}])
            self.assertNotEqual(cd.download_raw_analytics_for_course(
                                34567, AnalyticTypes.participation), [])

        # mock 500 error
        cd.download_student_ids_for_course = MagicMock()
        cd.download_student_ids_for_course.side_effect = \
            DataFailureException("/good/url", 500, 'server error')
        with self.assertRaises(DataFailureException):
            cd.download_raw_analytics_for_course(
                                            34567, AnalyticTypes.assignment)

    @patch('uw_canvas.reports.Reports')
    @patch('uw_canvas.terms.Terms')
    def test_download_course_provisioning_report(self, MockReports, MockTerms):
        cd = self.get_test_canvas_dao()
        mock_terms_inst = MockTerms.return_value
        mock_terms_inst.get_term_by_sis_id.return_value = \
            MagicMock(term_id="2021-spring")
        cd.terms = mock_terms_inst
        mock_reports_inst = MockReports.return_value
        mock_reports_inst.create_course_provisioning_report.return_value = True
        mock_reports_inst.get_report_data.return_value = \
            [{"entry1": ""}, {"entry2": ""}]
        mock_reports_inst.delete_report.return_value = True
        cd.reports = mock_reports_inst

        # call download_course_provisioning_report
        self.assertEqual(
            cd.download_course_provisioning_report("2021-spring"),
            [{"entry1": ""}, {"entry2": ""}])

        # check that the mocked methods were called
        self.assertEqual(
            mock_terms_inst.get_term_by_sis_id.called,
            True)
        self.assertEqual(
            mock_reports_inst.create_course_provisioning_report.called,
            True)
        self.assertEqual(
            mock_reports_inst.get_report_data.called,
            True)
        self.assertEqual(
            mock_reports_inst.delete_report.called,
            True)

    @patch('uw_canvas.reports.Reports')
    @patch('uw_canvas.terms.Terms')
    def test_download_user_provisioning_report(self, MockReports, MockTerms):
        cd = self.get_test_canvas_dao()
        mock_terms_inst = MockTerms.return_value
        mock_terms_inst.get_term_by_sis_id.return_value = \
            MagicMock(term_id="2021-spring")
        cd.terms = mock_terms_inst
        mock_reports_inst = MockReports.return_value
        mock_reports_inst.create_user_provisioning_report.return_value = True
        mock_reports_inst.get_report_data.return_value = \
            [{"entry1": ""}, {"entry2": ""}]
        mock_reports_inst.delete_report.return_value = True
        cd.reports = mock_reports_inst

        # call download_user_provisioning_report
        self.assertEqual(
            cd.download_user_provisioning_report("2021-spring"),
            [{"entry1": ""}, {"entry2": ""}])

        # check that the mocked methods were called
        self.assertEqual(
            mock_terms_inst.get_term_by_sis_id.called,
            True)
        self.assertEqual(
            mock_reports_inst.create_user_provisioning_report.called,
            True)
        self.assertEqual(
            mock_reports_inst.get_report_data.called,
            True)
        self.assertEqual(
            mock_reports_inst.delete_report.called,
            True)


class TestLoadRadDAO(TestCase):

    fixtures = ['data_aggregator/fixtures/mock_data/da_assignment.json',
                'data_aggregator/fixtures/mock_data/da_course.json',
                'data_aggregator/fixtures/mock_data/da_job.json',
                'data_aggregator/fixtures/mock_data/da_jobtype.json',
                'data_aggregator/fixtures/mock_data/da_participation.json',
                'data_aggregator/fixtures/mock_data/da_term.json',
                'data_aggregator/fixtures/mock_data/da_user.json',
                'data_aggregator/fixtures/mock_data/da_week.json']

    @classmethod
    def setUpTestData(cls):
        # Set up data for the whole TestCase
        sis_term_id = "2013-spring"
        week = 1
        create_assignment(sis_term_id, week)
        create_participation(sis_term_id, week)
        create_rad(sis_term_id, week)
        week = 2
        create_assignment(sis_term_id, week)
        create_participation(sis_term_id, week)
        create_rad(sis_term_id, week)
        super().setUpTestData()

    def _get_test_load_rad_dao(self):
        lrd = LoadRadDAO()
        lrd.get_current_term_and_week = \
            MagicMock(return_value=("2013-spring", 1))
        lrd.curr_term = "2013-spring"
        lrd.curr_week = 1
        lrd._get_gcs_client = MagicMock()
        lrd._get_s3_client = MagicMock()
        return lrd

    def _get_mock_student_categories_df(self):
        lrd = self._get_test_load_rad_dao()
        mock_student_cat_file = \
            os.path.join(
                os.path.dirname(__file__),
                'test_data/2013-spring-netid-name-stunum-categories.csv')
        mock_student_cat = open(mock_student_cat_file).read()
        lrd.download_from_gcs_bucket = MagicMock(return_value=mock_student_cat)
        mock_student_categories_df = lrd.get_student_categories_df()
        return mock_student_categories_df

    def _get_mock_pred_proba_df(self):
        lrd = self._get_test_load_rad_dao()
        mock_pred_proba_file = \
            os.path.join(os.path.dirname(__file__),
                         'test_data/2013-spring-pred-proba.csv')
        mock_pred_proba = open(mock_pred_proba_file).read()
        lrd.download_from_gcs_bucket = MagicMock(return_value=mock_pred_proba)
        mock_pred_proba_df = lrd.get_pred_proba_scores_df()
        return mock_pred_proba_df

    def _get_mock_eop_advisers_df(self):
        lrd = self._get_test_load_rad_dao()
        mock_eop_advisers_file = \
            os.path.join(os.path.dirname(__file__),
                         'test_data/2013-spring-eop-advisers.csv')
        mock_eop_advisers = open(mock_eop_advisers_file).read()
        lrd.download_from_gcs_bucket = \
            MagicMock(return_value=mock_eop_advisers)
        mock_eop_advisers_df = lrd.get_eop_advisers_df()
        return mock_eop_advisers_df

    def _get_mock_iss_advisers_df(self):
        lrd = self._get_test_load_rad_dao()
        mock_iss_advisers_file = \
            os.path.join(os.path.dirname(__file__),
                         'test_data/2013-spring-iss-advisers.csv')
        mock_iss_advisers = open(mock_iss_advisers_file).read()
        lrd.download_from_gcs_bucket = \
            MagicMock(return_value=mock_iss_advisers)
        mock_iss_advisers_df = lrd.get_iss_advisers_df()
        return mock_iss_advisers_df

    def _get_mock_idp_df(self):
        lrd = self._get_test_load_rad_dao()
        mock_idp_file = \
            os.path.join(os.path.dirname(__file__),
                         'test_data/netid_logins_2013.csv')
        lrd.get_last_idp_file = MagicMock(return_value=mock_idp_file)
        mock_idp_data = open(mock_idp_file).read()
        lrd.download_from_s3_bucket = \
            MagicMock(return_value=StringIO(mock_idp_data))
        mock_idp_df = lrd.get_idp_df()
        return mock_idp_df

    def test__zero_range(self):
        lrd = self._get_test_load_rad_dao()
        df = pd.DataFrame([5, 10, 15], columns=['test'])
        self.assertFalse(lrd._zero_range(df['test']))
        df = pd.DataFrame([0, 0, 1], columns=['test'])
        self.assertFalse(lrd._zero_range(df['test']))
        df = pd.DataFrame([5, 5, 5], columns=['test'])
        self.assertTrue(lrd._zero_range(df['test']))

    def test__rescale_range(self):
        lrd = self._get_test_load_rad_dao()
        df = pd.DataFrame([5, 10, 15], columns=['test'])
        self.assertEqual(lrd._rescale_range(df['test']).to_list(),
                         [-5.0, 0.0, 5.0])
        df = pd.DataFrame([10, 10, 10], columns=['test'])
        self.assertEqual(lrd._rescale_range(df['test']).to_list(),
                         [0.0, 0.0, 0.0])
        df = pd.DataFrame([0, 0, 20, 30, 40], columns=['test'])
        self.assertEqual(lrd._rescale_range(df['test']).to_list(),
                         [-5.0, -5.0, 0, 2.5, 5.0])
        df = pd.DataFrame([None, None, None], columns=['test'])
        self.assertEqual(lrd._rescale_range(df['test']).to_list(),
                         [np.nan, np.nan, np.nan])

    def test_get_users_df(self):
        lrd = self._get_test_load_rad_dao()
        mock_users_df = lrd.get_users_df()
        self.assertEqual(
            mock_users_df.columns.values.tolist(),
            ["canvas_user_id", "uw_netid"])

    def test_get_rad_dbview_df(self):
        lrd = self._get_test_load_rad_dao()
        mock_rad_dbview_df = lrd.get_rad_dbview_df()
        self.assertEqual(
            mock_rad_dbview_df.columns.values.tolist(),
            ["canvas_user_id", "full_name", "term", "week", "assignments",
             "activity", "grades"])

    def test_get_student_categories_df(self):
        mock_student_categories_df = self._get_mock_student_categories_df()
        self.assertEqual(
            mock_student_categories_df.columns.values.tolist(),
            ["system_key", "uw_netid", "student_no", "student_name_lowc",
             "eop_student", "incoming_freshman", "international_student",
             "stem", "premajor", "isso", "canvas_user_id"])

    def test_get_pred_proba_scores_df(self):
        mock_pred_proba_df = self._get_mock_pred_proba_df()
        self.assertEqual(
            mock_pred_proba_df.columns.values.tolist(),
            ["system_key", "pred"])

    def test_get_eop_advisers_df(self):
        mock_eop_advisers_df = self._get_mock_eop_advisers_df()
        self.assertEqual(
            mock_eop_advisers_df.columns.values.tolist(),
            ["student_no", "adviser_name", "staff_id"])

    def test_get_iss_advisers_df(self):
        mock_iss_advisers_df = self._get_mock_iss_advisers_df()
        self.assertEqual(
            mock_iss_advisers_df.columns.values.tolist(),
            ["student_no", "adviser_name", "staff_id"])

    def test_get_idp_df(self):
        mock_idp_df = self._get_mock_idp_df()
        self.assertEqual(
            mock_idp_df.columns.values.tolist(),
            ["uw_netid", "sign_in"])

    def test_get_rad_df(self):
        lrd = self._get_test_load_rad_dao()
        lrd.get_student_categories_df = \
            MagicMock(return_value=self._get_mock_student_categories_df())
        lrd.get_idp_df = \
            MagicMock(return_value=self._get_mock_idp_df())
        lrd.get_pred_proba_scores_df = \
            MagicMock(return_value=self._get_mock_pred_proba_df())
        lrd.get_eop_advisers_df = \
            MagicMock(return_value=self._get_mock_eop_advisers_df())
        lrd.get_iss_advisers_df = \
            MagicMock(return_value=self._get_mock_iss_advisers_df())
        mock_rad_df = lrd.get_rad_df()
        self.assertEqual(mock_rad_df.columns.values.tolist(),
                         ["uw_netid", "student_no", "student_name_lowc",
                          "premajor", "activity", "assignments", "grades",
                          "pred", "adviser_name", "staff_id", "sign_in",
                          "stem", "incoming_freshman"])


if __name__ == "__main__":
    unittest.main()
