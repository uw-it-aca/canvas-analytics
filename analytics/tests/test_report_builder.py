import os
from analytics.models import Report, SubaccountActivity
from analytics.report_builder import ReportBuilder
from django.test import TestCase
from mock import MagicMock
from csv import DictReader


class TestBuildSubAccountActivityReport(TestCase):

    def setUp(self):
        self.report_builder = ReportBuilder()
        self.report_builder._accounts = MagicMock()
        self.root_account = MagicMock()
        self.root_account.sis_account_id = "uwcourse"
        self.root_account.name = "uwcourse"
        self.report_builder._accounts.get_account_by_sis_id = \
            MagicMock(return_value=self.root_account)
        mock_sub_account = MagicMock()
        mock_sub_account.sis_account_id = "subaccount1"
        mock_sub_account.name = "subaccount1"
        self.report_builder._accounts.get_all_sub_accounts_by_sis_id = \
            MagicMock(return_value=[mock_sub_account])
        self.report_builder._reports = MagicMock()
        mock_xlist_provisioning_report = MagicMock()
        mock_xlist_provisioning_report.name = "xlist_provisioning_report"
        self.report_builder._reports.create_xlist_provisioning_report = \
            MagicMock(return_value=mock_xlist_provisioning_report)
        mock_course_provisioning_report = MagicMock()
        mock_course_provisioning_report.name = "course_provisioning_report"
        self.report_builder._reports.create_course_provisioning_report = \
            MagicMock(return_value=mock_course_provisioning_report)
        self.report_builder._reports.delete_report = MagicMock()
        self.report_builder._reports.get_report_data = \
            MagicMock(side_effect=self.mock_get_report)
        self.report_builder.get_statistics_by_account = \
            MagicMock(side_effect=self.mock_get_statistics_by_account)
        self.report_builder.get_activity_by_account = \
            MagicMock(side_effect=self.mock_get_activity_by_account)

    def mock_get_statistics_by_account(self, *args):
        mock_stats_by_account_file = os.path.join(
            os.path.dirname(__file__), 'test_data/account_statistics_data.csv')
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
                                                'test_data/xlist_data.csv')
            return open(mock_xlist_data_file).read().split("\n")
        if mock_report.name == "course_provisioning_report":
            mock_course_data_file = os.path.join(os.path.dirname(__file__),
                                                 'test_data/course_data.csv')
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
