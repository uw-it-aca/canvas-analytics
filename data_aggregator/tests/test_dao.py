# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

import os
import unittest
import pandas as pd
import numpy as np
from django.test import TestCase
from data_aggregator.dao import AnalyticTypes, CanvasDAO, JobDAO, LoadRadDAO, \
    BaseDAO, TaskDAO
from data_aggregator.models import JobType, TaskTypes
from mock import patch, MagicMock


class TestBaseDAO(TestCase):

    def get_test_base_dao(self):
        # mock gcs blob
        mock_gcs_blob = MagicMock()
        mock_gcs_blob.upload_from_file = MagicMock(return_value=True)
        mock_gcs_blob.download_as_string = \
            MagicMock(return_value=b"test-return-value")
        # mock gcs bucket
        mock_gcs_bucket = MagicMock()
        mock_gcs_bucket.get_blob = MagicMock(return_value=mock_gcs_blob)
        # mock gcs client
        mock_gcs_client = MagicMock()
        mock_gcs_client.get_bucket = MagicMock(return_value=mock_gcs_bucket)

        # mock content
        mock_s3_content = MagicMock()
        mock_s3_content.read = MagicMock(return_value=b"test-return-value")
        # mock s3 obj
        mock_s3_obj = MagicMock()
        mock_s3_obj.__getitem__.side_effect = \
            MagicMock(return_value=mock_s3_content)
        # mock s3 client
        mock_s3_client = MagicMock()
        mock_s3_client.get_object = MagicMock(return_value=mock_s3_obj)

        # mock base dao
        base_dao = BaseDAO()
        base_dao.get_gcs_bucket_name = \
            MagicMock(return_value="test_gcs_bucket")
        base_dao.get_gcs_client = MagicMock(return_value=mock_gcs_client)
        base_dao.get_s3_bucket_name = MagicMock(return_value="test_s3_bucket")
        base_dao.get_s3_client = MagicMock(return_value=mock_s3_client)
        return base_dao

    def test_download_from_gcs_bucket(self):
        base_dao = self.get_test_base_dao()
        content = base_dao.download_from_gcs_bucket("test_url_key")
        self.assertEqual(content, "test-return-value")

    def test_download_from_s3_bucket(self):
        base_dao = self.get_test_base_dao()
        content = base_dao.download_from_s3_bucket("test_url_key")
        self.assertEqual(content, "test-return-value")


class TestAnalyticTypes(TestCase):

    def test_types(self):
        self.assertEqual(AnalyticTypes.assignment, "assignment")
        self.assertEqual(AnalyticTypes.participation, "participation")


class TestCanvasDAO(TestCase):

    fixtures = ['data_aggregator/fixtures/mock_data/da_term.json',
                'data_aggregator/fixtures/mock_data/da_week.json']

    def get_test_canvas_dao(self):
        cd = CanvasDAO()
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
    def test_download_assignment_analytics(self, MockAnalytics):
        cd = self.get_test_canvas_dao()
        mock_analytics_inst = MockAnalytics.return_value
        mock_analytics_inst.get_student_assignments_for_course.return_value = \
            [{"assignment_1": 0}, {"assignment_2": 1}, {"assignment_3": 2}]
        cd.analytics = mock_analytics_inst
        self.assertEqual(cd.download_assignment_analytics(98765, 12345),
                         [{'assignment_1': 0,
                           'canvas_course_id': 98765,
                           'canvas_user_id': 12345},
                          {'assignment_2': 1,
                           'canvas_course_id': 98765,
                           'canvas_user_id': 12345},
                          {'assignment_3': 2,
                           'canvas_course_id': 98765,
                           'canvas_user_id': 12345}])
        self.assertEqual(
            mock_analytics_inst.get_student_assignments_for_course.called,
            True)

    @patch('uw_canvas.analytics.Analytics')
    def test_download_participation_analytics(self, MockAnalytics):
        cd = self.get_test_canvas_dao()
        mock_analytics_inst = MockAnalytics.return_value
        mock_analytics_inst.get_student_summaries_by_course.return_value = \
            [{"participation_1": 0, "id": 12457},
             {"participation_2": 1, "id": 43256},
             {"participation_3": 2, "id": 66453}]
        cd.analytics = mock_analytics_inst
        self.assertEqual(cd.download_participation_analytics(13579),
                         [{'participation_1': 0,
                           'canvas_course_id': 13579,
                           'canvas_user_id': 12457},
                          {'participation_2': 1,
                           'canvas_course_id': 13579,
                           'canvas_user_id': 43256},
                          {'participation_3': 2,
                           'canvas_course_id': 13579,
                           'canvas_user_id': 66453}])
        self.assertEqual(
            mock_analytics_inst.get_student_summaries_by_course.called,
            True)

    def test_download_raw_analytics_for_course(self):
        patcher = patch('uw_canvas.analytics.Analytics')

        # test assignments
        cd = self.get_test_canvas_dao()
        cd.download_student_ids_for_course = MagicMock()
        cd.download_student_ids_for_course.return_value = [12345]
        MockAnalytics = patcher.start()
        mock_analytics_inst = MockAnalytics.return_value
        mock_analytics_inst.get_student_assignments_for_course.return_value = \
            [{"assignment_1": 0}, {"assignment_2": 1}, {"assignment_3": 2}]
        cd.analytics = mock_analytics_inst
        test_result = [a for a in
                       cd.download_raw_analytics_for_course(
                           34567, AnalyticTypes.assignment)]
        self.assertEqual(test_result,
                         [{'assignment_1': 0,
                           'canvas_course_id': 34567,
                           'canvas_user_id': 12345},
                          {'assignment_2': 1,
                           'canvas_course_id': 34567,
                           'canvas_user_id': 12345},
                          {'assignment_3': 2,
                           'canvas_course_id': 34567,
                           'canvas_user_id': 12345}])
        # check that the mocked methods were called
        self.assertEqual(
            mock_analytics_inst.get_student_assignments_for_course.called,
            True)
        self.assertEqual(
            mock_analytics_inst.get_student_summaries_by_course.called,
            False)
        patcher.stop()

        # test participations
        cd = self.get_test_canvas_dao()
        MockAnalytics = patcher.start()
        mock_analytics_inst = MockAnalytics.return_value
        mock_analytics_inst.get_student_summaries_by_course.return_value = \
            [{"participation_1": 0, "id": 12345},
             {"participation_2": 1, "id": 12346}]
        cd.analytics = mock_analytics_inst
        test_result = [a for a in
                       cd.download_raw_analytics_for_course(
                           76543, AnalyticTypes.participation)]
        self.assertEqual(test_result,
                         [{'participation_1': 0,
                           'canvas_course_id': 76543,
                           'canvas_user_id': 12345},
                          {'participation_2': 1,
                           'canvas_course_id': 76543,
                           'canvas_user_id': 12346}])
        # check that the mocked methods were called
        self.assertEqual(
            mock_analytics_inst.get_student_assignments_for_course.called,
            False)
        self.assertEqual(
            mock_analytics_inst.get_student_summaries_by_course.called,
            True)
        patcher.stop()

    @patch('uw_canvas.reports.Reports')
    @patch('uw_canvas.terms.Terms')
    def test_download_course_provisioning_report(self, MockReports, MockTerms):
        cd = self.get_test_canvas_dao()
        mock_terms_inst = MockTerms.return_value
        mock_terms_inst.get_term_by_sis_id.return_value = \
            MagicMock(term_id="2013-spring")
        cd.terms = mock_terms_inst
        mock_reports_inst = MockReports.return_value
        mock_reports_inst.create_course_provisioning_report.return_value = True
        mock_reports_inst.get_report_data.return_value = \
            [{"entry1": ""}, {"entry2": ""}]
        mock_reports_inst.delete_report.return_value = True
        cd.reports = mock_reports_inst

        # call download_course_provisioning_report
        self.assertEqual(
            cd.download_course_provisioning_report("2013-spring"),
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
            MagicMock(term_id="2013-spring")
        cd.terms = mock_terms_inst
        mock_reports_inst = MockReports.return_value
        mock_reports_inst.create_user_provisioning_report.return_value = True
        mock_reports_inst.get_report_data.return_value = \
            [{"entry1": ""}, {"entry2": ""}]
        mock_reports_inst.delete_report.return_value = True
        cd.reports = mock_reports_inst

        # call download_user_provisioning_report
        self.assertEqual(
            cd.download_user_provisioning_report("2013-spring"),
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


class TestJobDAO(TestCase):

    @patch("data_aggregator.dao.Participation")
    @patch("data_aggregator.dao.Assignment")
    def test_delete_data_for_job(self, mock_assignment,
                                 mock_participation):

        mock_analytics = MagicMock()
        mock_analytics.delete = MagicMock()
        mock_assignment.objects.filter.return_value = mock_analytics
        mock_participation.objects.filter.return_value = mock_analytics

        job = MagicMock()
        job.type = MagicMock()
        job_dao = JobDAO()

        job.type.type = AnalyticTypes.assignment
        job_dao.delete_data_for_job(job)
        mock_assignment.objects.filter.assert_called_once_with(job=job)
        mock_analytics.delete.assert_called_once()

        mock_analytics.reset_mock()
        mock_assignment.objects.filter.reset_mock()
        mock_participation.objects.filter.reset_mock()

        job.type.type = AnalyticTypes.participation
        job_dao.delete_data_for_job(job)
        mock_participation.objects.filter.assert_called_once_with(job=job)
        mock_analytics.delete.assert_called_once()

    def test_create_job(self):
        job_type = JobType()
        target_date_start = MagicMock()
        target_date_end = MagicMock()
        context = MagicMock()
        with patch("data_aggregator.models.Job.save") as mock_job_save:
            job = JobDAO().create_job(job_type, target_date_start,
                                      target_date_end, context=context)
            mock_job_save.assert_called_once()
            self.assertEqual(job.type, job_type)
            self.assertEqual(job.target_date_start, target_date_start)
            self.assertEqual(job.target_date_end, target_date_end)
            self.assertEqual(job.context, context)

    def test_run_job(self):
        job = MagicMock()
        job.type = MagicMock()
        job.type.type = AnalyticTypes.assignment
        with patch("data_aggregator.dao.JobDAO.run_analytics_job") \
                as mock_run_analytics_job:
            JobDAO().run_job(job)
            mock_run_analytics_job.assert_called_once()
        job.type.type = AnalyticTypes.participation
        with patch("data_aggregator.dao.JobDAO.run_analytics_job") \
                as mock_run_analytics_job:
            JobDAO().run_job(job)
            mock_run_analytics_job.assert_called_once()
        job.type.type = TaskTypes.create_assignment_db_view
        with patch("data_aggregator.dao.JobDAO.run_task_job") \
                as mock_run_task_job:
            JobDAO().run_job(job)
            mock_run_task_job.assert_called_once()

    @patch('data_aggregator.dao.AnalyticsDAO')
    @patch('data_aggregator.dao.CanvasDAO')
    @patch('data_aggregator.dao.set_gcs_base_path')
    def test_run_analytics_job(self, mock_set_gcs_base_path, mock_canvas_dao,
                               mock_analytics_dao):
        job = MagicMock()
        job.type = MagicMock()
        job.context = {
            "canvas_course_id": 12345,
            "sis_term_id": "2021-summer",
            "week": 1
        }
        job_dao = JobDAO()
        job_dao.delete_data_for_job = MagicMock()
        mock_analytics = [MagicMock(), MagicMock()]
        mock_canvas_dao_inst = mock_canvas_dao()
        mock_canvas_dao_inst.download_raw_analytics_for_course = MagicMock(
            return_value=mock_analytics
        )
        mock_analytics_dao_inst = mock_analytics_dao()
        mock_analytics_dao_inst.save_assignments_to_db = MagicMock()
        mock_analytics_dao_inst.save_participations_to_db = MagicMock()

        job.type.type = AnalyticTypes.assignment
        job_dao.run_analytics_job(job)
        job_dao.delete_data_for_job.assert_called_once()
        mock_set_gcs_base_path.assert_called_once_with("2021-summer", 1)
        mock_canvas_dao_inst.download_raw_analytics_for_course \
            .assert_called_once_with(12345, AnalyticTypes.assignment)
        mock_analytics_dao_inst.save_assignments_to_db.assert_called_once()
        mock_analytics_dao_inst.save_assignments_to_db.assert_called_once_with(
            mock_analytics, job
        )

        # reset mock states
        job_dao.delete_data_for_job.reset_mock()
        mock_set_gcs_base_path.reset_mock()
        mock_canvas_dao_inst.reset_mock()
        mock_canvas_dao_inst.download_raw_analytics_for_course.reset_mock()
        mock_analytics_dao_inst.save_assignments_to_db.reset_mock()
        mock_analytics_dao_inst.save_participations_to_db.reset_mock()

        job.type.type = AnalyticTypes.participation
        job_dao.run_analytics_job(job)
        job_dao.delete_data_for_job.assert_called_once()
        mock_set_gcs_base_path.assert_called_once_with("2021-summer", 1)
        mock_canvas_dao_inst.download_raw_analytics_for_course \
            .assert_called_once_with(12345, AnalyticTypes.participation)
        mock_analytics_dao_inst.save_participations_to_db.assert_called_once()
        mock_analytics_dao_inst.save_participations_to_db \
            .assert_called_once_with(
                mock_analytics, job
            )

    def test_run_task_job(self):
        job = MagicMock()
        job.type = MagicMock()
        job.type.type = TaskTypes.create_terms
        job.context = {
            "sis_term_id": "2021-summer",
            "week": 4,
            "subaccount_id": "uwcourse"
        }

        with patch("data_aggregator.dao.TaskDAO.create_terms") \
                as mock_create_terms:
            JobDAO().run_task_job(job)
            mock_create_terms.assert_called_once_with(
                sis_term_id="2021-summer")
        job.type.type = TaskTypes.create_or_update_courses
        with patch("data_aggregator.dao.TaskDAO.create_or_update_courses") \
                as mock_create_or_update_courses:
            JobDAO().run_task_job(job)
            mock_create_or_update_courses.assert_called_once_with(
                sis_term_id="2021-summer")
        job.type.type = TaskTypes.create_or_update_users
        with patch("data_aggregator.dao.TaskDAO.create_or_update_users") \
                as mock_create_or_update_users:
            JobDAO().run_task_job(job)
            mock_create_or_update_users.assert_called_once_with(
                sis_term_id="2021-summer")
        job.type.type = TaskTypes.create_assignment_db_view
        with patch("data_aggregator.dao.TaskDAO.create_assignment_db_view") \
                as mock_create_assignment_db_view:
            JobDAO().run_task_job(job)
            mock_create_assignment_db_view.assert_called_once_with(
                 sis_term_id="2021-summer",
                 week_num=4)
        job.type.type = TaskTypes.create_participation_db_view
        with patch("data_aggregator.dao.TaskDAO."
                   "create_participation_db_view") \
                as mock_create_participation_db_view:
            JobDAO().run_task_job(job)
            mock_create_participation_db_view.assert_called_once_with(
                 sis_term_id="2021-summer",
                 week_num=4)
        job.type.type = TaskTypes.create_rad_db_view
        with patch("data_aggregator.dao.TaskDAO.create_rad_db_view") \
                as mock_create_rad_db_view:
            JobDAO().run_task_job(job)
            mock_create_rad_db_view.assert_called_once_with(
                 sis_term_id="2021-summer",
                 week_num=4)
        job.type.type = TaskTypes.create_rad_data_file
        with patch("data_aggregator.dao.LoadRadDAO.create_rad_data_file") \
                as mock_create_rad_data_file:
            JobDAO().run_task_job(job)
            mock_create_rad_data_file.assert_called_once_with(
                 sis_term_id="2021-summer",
                 week_num=4)
        job.type.type = TaskTypes.build_subaccount_activity_report
        with patch("data_aggregator.report_builder.ReportBuilder."
                   "build_subaccount_activity_report") \
                as mock_build_subaccount_activity_report:
            JobDAO().run_task_job(job)
            mock_build_subaccount_activity_report.assert_called_once_with(
                 "uwcourse",
                 sis_term_id="2021-summer",
                 week_num=4)
        job.type.type = "unknown-job-type"
        with self.assertRaises(ValueError):
            JobDAO().run_task_job(job)


class TestTaskDAO(TestCase):

    def get_test_task_dao(self):
        td = TaskDAO()
        return td

    def test_create_or_update_courses(self):
        td = self.get_test_task_dao()
        mock_course_provisioning_file = \
            os.path.join(
                os.path.dirname(__file__),
                'test_data/course_provisioning_report.csv')
        mock_course_data = \
            open(mock_course_provisioning_file).read().split("\n")
        self.assertEqual(len(mock_course_data), 3)
        with patch.object(CanvasDAO,
                          'download_course_provisioning_report',
                          return_value=mock_course_data):
            self.assertEqual(
                td.create_or_update_courses(sis_term_id="2021-spring"),
                1
            )

    def test_create_or_update_users(self):
        td = self.get_test_task_dao()
        mock_user_provisioning_file = \
            os.path.join(
                os.path.dirname(__file__),
                'test_data/user_provisioning_report.csv')
        mock_user_data = \
            open(mock_user_provisioning_file).read().split("\n")
        self.assertEqual(len(mock_user_data), 21)
        with patch.object(CanvasDAO,
                          'download_user_provisioning_report',
                          return_value=mock_user_data):
            self.assertEqual(
                td.create_or_update_users(sis_term_id="2021-spring"),
                20
            )


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
        td = TaskDAO()
        sis_term_id = "2013-spring"
        weeks = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        for week in weeks:
            td.create_assignment_db_view(sis_term_id=sis_term_id,
                                         week_num=week)
            td.create_participation_db_view(sis_term_id=sis_term_id,
                                            week_num=week)
            td.create_rad_db_view(sis_term_id=sis_term_id,
                                  week_num=week)
        super().setUpTestData()

    def _get_test_load_rad_dao(self):
        lrd = LoadRadDAO()
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
        mock_student_categories_df = \
            lrd.get_student_categories_df(sis_term_id="2013-spring")
        return mock_student_categories_df

    def _get_mock_pred_proba_df(self):
        lrd = self._get_test_load_rad_dao()
        mock_pred_proba_file = \
            os.path.join(os.path.dirname(__file__),
                         'test_data/2013-spring-pred-proba.csv')
        mock_pred_proba = open(mock_pred_proba_file).read()
        lrd.download_from_gcs_bucket = MagicMock(return_value=mock_pred_proba)
        mock_pred_proba_df = \
            lrd.get_pred_proba_scores_df(sis_term_id="2013-spring")
        return mock_pred_proba_df

    def _get_mock_eop_advisers_df(self):
        lrd = self._get_test_load_rad_dao()
        mock_eop_advisers_file = \
            os.path.join(os.path.dirname(__file__),
                         'test_data/2013-spring-eop-advisers.csv')
        mock_eop_advisers = open(mock_eop_advisers_file).read()
        lrd.download_from_gcs_bucket = \
            MagicMock(return_value=mock_eop_advisers)
        mock_eop_advisers_df = \
            lrd.get_eop_advisers_df(sis_term_id="2013-spring")
        return mock_eop_advisers_df

    def _get_mock_iss_advisers_df(self):
        lrd = self._get_test_load_rad_dao()
        mock_iss_advisers_file = \
            os.path.join(os.path.dirname(__file__),
                         'test_data/2013-spring-iss-advisers.csv')
        mock_iss_advisers = open(mock_iss_advisers_file).read()
        lrd.download_from_gcs_bucket = \
            MagicMock(return_value=mock_iss_advisers)
        mock_iss_advisers_df = \
            lrd.get_iss_advisers_df(sis_term_id="2013-spring")
        return mock_iss_advisers_df

    def _get_mock_idp_df(self):
        lrd = self._get_test_load_rad_dao()
        mock_idp_file = \
            os.path.join(os.path.dirname(__file__),
                         'test_data/netid_logins_2013.csv')
        lrd.get_last_idp_file = MagicMock(return_value=mock_idp_file)
        mock_idp_data = open(mock_idp_file).read()
        lrd.download_from_s3_bucket = \
            MagicMock(return_value=mock_idp_data)
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
        np.testing.assert_array_equal(
            lrd._rescale_range(df['test']).to_list(),
            [-5.0, 0.0, 5.0])
        df = pd.DataFrame([10, 10, 10], columns=['test'])
        np.testing.assert_array_equal(
            lrd._rescale_range(df['test']).to_list(),
            [0.0, 0.0, 0.0])
        df = pd.DataFrame([0, 0, 20, 30, 40], columns=['test'])
        np.testing.assert_array_equal(
            lrd._rescale_range(df['test']).to_list(),
            [-5.0, -5.0, 0, 2.5, 5.0])
        df = pd.DataFrame([None, None, None], columns=['test'])
        np.testing.assert_array_equal(
            lrd._rescale_range(df['test']).to_list(),
            [np.nan, np.nan, np.nan])

    def test_get_users_df(self):
        lrd = self._get_test_load_rad_dao()
        mock_users_df = lrd.get_users_df()
        self.assertEqual(
            mock_users_df.columns.values.tolist(),
            ["canvas_user_id", "uw_netid"])

    def test_get_rad_dbview_df(self):
        lrd = self._get_test_load_rad_dao()
        mock_rad_dbview_df = lrd.get_rad_dbview_df(sis_term_id="2013-spring",
                                                   week_num=3)
        self.assertEqual(
            mock_rad_dbview_df.columns.values.tolist(),
            ["canvas_user_id", "full_name", "term", "week", "assignments",
             "activity", "grades"])

    def test_get_student_categories_df(self):
        mock_student_categories_df = self._get_mock_student_categories_df()
        self.assertEqual(
            mock_student_categories_df.columns.values.tolist(),
            ["system_key", "uw_netid", "student_no", "student_name_lowc",
             "eop", "incoming_freshman", "international",
             "stem", "premajor", "isso", "campus_code", "summer",
             "canvas_user_id"])

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
        mock_rad_df = lrd.get_rad_df(sis_term_id="2013-spring", week_num=3)
        self.assertEqual(mock_rad_df.columns.values.tolist(),
                         ["uw_netid", "student_no", "student_name_lowc",
                          "activity", "assignments", "grades", "pred",
                          "adviser_name", "staff_id", "sign_in", "stem",
                          "incoming_freshman", "premajor", "eop",
                          "international", "isso", "campus_code",
                          "summer"])


if __name__ == "__main__":
    unittest.main()
