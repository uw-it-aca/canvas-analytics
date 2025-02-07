# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


import os
import io
from data_aggregator.models import Report, SubaccountActivity
from data_aggregator.report_builder import ReportBuilder
from django.test import TestCase
from mock import MagicMock, patch
from csv import DictReader


class TestBuildSubAccountActivityReport(TestCase):

    def setUp(self):
        self.report_builder = ReportBuilder()
        self.report_builder._accounts = MagicMock()
        self.root_account = MagicMock()
        self.root_account.sis_account_id = "uwcourse"
        self.root_account.name = "uwcourse"

        # mock subaccounts
        self.report_builder._accounts.get_account_by_sis_id = \
            MagicMock(return_value=self.root_account)
        mock_sub_account = MagicMock()
        mock_sub_account.sis_account_id = "subaccount1"
        mock_sub_account.name = "subaccount1"
        self.report_builder._accounts.get_all_sub_accounts_by_sis_id = \
            MagicMock(return_value=[mock_sub_account])

        # mock reports
        self.report_builder._reports = MagicMock()
        # mock xlist provisioning report
        mock_xlist_provisioning_report = MagicMock()
        mock_xlist_provisioning_report.name = "xlist_provisioning_report"
        self.report_builder._reports.create_xlist_provisioning_report = \
            MagicMock(return_value=mock_xlist_provisioning_report)
        # mock course provisioning report
        mock_course_provisioning_report = MagicMock()
        mock_course_provisioning_report.name = "course_provisioning_report"
        self.report_builder._reports.create_course_provisioning_report = \
            MagicMock(return_value=mock_course_provisioning_report)
        # mock delete report
        self.report_builder._reports.delete_report = MagicMock()
        self.report_builder._reports.get_report_data = \
            MagicMock(side_effect=self.mock_get_report)
        # mock account level stats
        self.report_builder.get_statistics_by_account = \
            MagicMock(side_effect=self.mock_get_statistics_by_account)
        self.report_builder.get_activity_by_account = \
            MagicMock(side_effect=self.mock_get_activity_by_account)

        # mock terms
        mock_term = MagicMock()
        mock_term.term_id = "2021-summer"
        mock_term.canvas_sis_id = MagicMock(return_value="2021-summer")
        mock_term.get_week_of_term = MagicMock(return_value=1)
        self.report_builder._terms = MagicMock()
        self.report_builder._terms.get_term_by_sis_id = \
            MagicMock(return_value=mock_term)

    def mock_get_statistics_by_account(self, *args):
        mock_stats_by_account_file = os.path.join(
                                os.path.dirname(__file__),
                                'test_data/saa_account_statistics_data.csv')
        reader = DictReader(mock_stats_by_account_file)
        return next(reader)

    def mock_get_activity_by_account(self, sis_account_id, sis_term_id):
        if sis_account_id == "uwcourse" and sis_term_id == "2021-summer":
            return \
                {'by_category':
                 [{'id': None, 'category': 'announcements', 'views': 6633},
                  {'id': None, 'category': 'assignments', 'views': 125248},
                  {'id': None, 'category': 'collaborations', 'views': 262},
                  {'id': None, 'category': 'conferences', 'views': 90},
                  {'id': None, 'category': 'discussions', 'views': 35606},
                  {'id': None, 'category': 'files', 'views': 105420},
                  {'id': None, 'category': 'general', 'views': 110181},
                  {'id': None, 'category': 'grades', 'views': 10362},
                  {'id': None, 'category': 'groups', 'views': 635},
                  {'id': None, 'category': 'modules', 'views': 55279},
                  {'id': None, 'category': 'other', 'views': 303319},
                  {'id': None, 'category': 'pages', 'views': 13656},
                  {'id': None, 'category': 'quizzes', 'views': 3244}]}
        elif (sis_account_id.startswith("subaccount") and
              sis_term_id == "2021-summer"):
            return \
                {'by_category':
                 [{'id': None, 'category': 'announcements', 'views': 3245},
                  {'id': None, 'category': 'assignments', 'views': 2342},
                  {'id': None, 'category': 'collaborations', 'views': 323},
                  {'id': None, 'category': 'conferences', 'views': 23},
                  {'id': None, 'category': 'discussions', 'views': 23425},
                  {'id': None, 'category': 'files', 'views': 83043},
                  {'id': None, 'category': 'general', 'views': 23432},
                  {'id': None, 'category': 'grades', 'views': 4353},
                  {'id': None, 'category': 'groups', 'views': 643},
                  {'id': None, 'category': 'modules', 'views': 43224},
                  {'id': None, 'category': 'other', 'views': 212452},
                  {'id': None, 'category': 'pages', 'views': 124232},
                  {'id': None, 'category': 'quizzes', 'views': 2123}]}

    def mock_get_report(self, mock_report):
        if mock_report.name == "xlist_provisioning_report":
            mock_xlist_data_file = os.path.join(os.path.dirname(__file__),
                                                'test_data/saa_xlist_data.csv')
            return open(mock_xlist_data_file).read().split("\n")
        if mock_report.name == "course_provisioning_report":
            mock_course_data_file = os.path.join(
                    os.path.dirname(__file__), 'test_data/saa_course_data.csv')
            return open(mock_course_data_file).read().split("\n")

    def test_get_account_activities_data(self):
        activities = self.report_builder.get_account_activities_data(
                                                            self.root_account,
                                                            "2021-summer")
        self.assertEqual(len(activities), 2)
        activity1 = activities[0]
        self.assertEqual(activity1.subaccount_id, "uwcourse")
        self.assertEqual(activity1.term_id, "2021-summer")
        self.assertEqual(activity1.announcements_views, 6633)
        self.assertEqual(activity1.assignments_views, 125248)
        self.assertEqual(activity1.collaborations_views, 262)
        self.assertEqual(activity1.conferences_views, 90)
        self.assertEqual(activity1.discussions_views, 35606)
        self.assertEqual(activity1.files_views, 105420)
        self.assertEqual(activity1.general_views, 110181)
        self.assertEqual(activity1.grades_views, 10362)
        self.assertEqual(activity1.groups_views, 635)
        self.assertEqual(activity1.modules_views, 55279)
        self.assertEqual(activity1.other_views, 303319)
        self.assertEqual(activity1.pages_views, 13656)
        self.assertEqual(activity1.quizzes_views, 3244)
        activity2 = activities[1]
        self.assertEqual(activity2.subaccount_id, "subaccount1")
        self.assertEqual(activity2.term_id, "2021-summer")
        self.assertEqual(activity2.announcements_views, 3245)
        self.assertEqual(activity2.assignments_views, 2342)
        self.assertEqual(activity2.collaborations_views, 323)
        self.assertEqual(activity2.conferences_views, 23)
        self.assertEqual(activity2.discussions_views, 23425)
        self.assertEqual(activity2.files_views, 83043)
        self.assertEqual(activity2.general_views, 23432)
        self.assertEqual(activity2.grades_views, 4353)
        self.assertEqual(activity2.groups_views, 643)
        self.assertEqual(activity2.modules_views, 43224)
        self.assertEqual(activity2.other_views, 212452)
        self.assertEqual(activity2.pages_views, 124232)
        self.assertEqual(activity2.quizzes_views, 2123)

    def test_get_xlist_courses(self):
        xlist_data = self.report_builder.get_xlist_courses(self.root_account,
                                                           "2021-summer")
        self.assertEqual(len(xlist_data), 20)

    def test_get_course_data(self):
        course_data = self.report_builder.get_course_data(self.root_account,
                                                          "2021-summer")
        self.assertEqual(len(course_data), 14)

    def test_build_subaccount_activity_report(self):
        mock_sub_account1 = MagicMock()
        mock_sub_account1.sis_account_id = "subaccount1"
        mock_sub_account1.name = "subaccount1"
        mock_sub_account2 = MagicMock()
        mock_sub_account2.sis_account_id = "subaccount2"
        mock_sub_account2.name = "subaccount2"
        mock_sub_account3 = MagicMock()
        mock_sub_account3.sis_account_id = "subaccount3"
        mock_sub_account3.name = "subaccount3"
        self.report_builder._accounts.get_all_sub_accounts_by_sis_id = \
            MagicMock(return_value=[mock_sub_account1, mock_sub_account2,
                                    mock_sub_account3])
        self.report_builder.build_subaccount_activity_report(12345,
                                                             "2021-summer")
        reports = Report.objects.all()
        self.assertEqual(reports.count(), 1)
        report = reports.first()
        self.assertEqual(report.report_type, "subaccount_activity")
        self.assertEqual(report.term_id, "2021-summer")

        activities = SubaccountActivity.objects.all()
        self.assertEqual(activities.count(), 4)


class TestExportSubAccountActivityReport(TestCase):
    fixtures = [
        'data_aggregator/fixtures/mock_data/da_report.json',
        'data_aggregator/fixtures/mock_data/da_subaccountactivity.json',
    ]

    def setUp(self):
        self.report_builder = ReportBuilder()
        self.term_id = "2013-spring"
        self.week = 10
        self.csv_data = "A,B,C\n10,20,30\n100,200,300\n"

    @patch.object(ReportBuilder, "generate_report_csv")
    @patch.object(ReportBuilder, "upload_csv_file")
    def test_export_subaccount_activity_report(self, mock_upload, mock_create):
        mock_create.return_value = self.csv_data
        self.report_builder.export_subaccount_activity_report(self.term_id,
                                                              self.week)
        mock_upload.assert_called_once_with(mock_create.return_value)

    def test_generate_report_csv(self):
        reports = Report.objects.get_subaccount_activity(
            sis_term_id=self.term_id, week_num=self.week)

        csv_data = self.report_builder.generate_report_csv(reports)

        self.maxDiff = None
        self.assertMultiLineEqual(csv_data, (
            "term_sis_id,week_num,subaccount_id,subaccount_name,campus,"
            "college,department,adoption_rate,courses,active_courses,"
            "ind_study_courses,active_ind_study_courses,xlist_courses,"
            "xlist_ind_study_courses,teachers,unique_teachers,students,"
            "unique_students,discussion_topics,discussion_replies,"
            "media_objects,attachments,assignments,submissions,"
            "announcements_views,assignments_views,collaborations_views,"
            "conferences_views,discussions_views,files_views,general_views,"
            "grades_views,groups_views,modules_views,other_views,pages_views,"
            "quizzes_views\n"
            "2013-spring,10,uwcourse:tacoma,Tacoma,Tacoma,,,30.0,595,151,91,"
            "3,12,1,1154,1121,11678,11528,1112,11631,113,118,1165,11786,11453,"
            "11678,112,1123,11456,11776,11900,114,1141,1133,1177,1176,1198\n"
            "2013-spring,10,uwcourse:tacoma:test-college,College of Test,"
            "Tacoma,Test College,,95.2,268,202,51,2,8,1,154,121,1678,1528,"
            "112,1631,13,18,165,1786,1453,1678,12,123,1456,1776,1900,14,141,"
            "133,177,176,198\n"
            "2013-spring,10,uwcourse:tacoma:test-college:test-department,"
            "Test Department,Tacoma,Test College,Test Department,73.8,199,"
            "122,33,1,2,0,54,21,678,528,12,631,3,8,65,786,453,678,2,23,456,"
            "776,900,4,41,33,77,76,98\n"))
