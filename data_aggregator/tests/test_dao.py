import unittest
from django.test import TestCase
from data_aggregator.dao import AnalyticTypes, CanvasDAO, CloudStorageDAO
from mock import patch, MagicMock
from restclients_core.exceptions import DataFailureException


class TestAnalyticTypes(TestCase):

    def test_types(self):
        self.assertEqual(AnalyticTypes.assignment, "assignment")
        self.assertEqual(AnalyticTypes.participation, "participation")


class TestCanvasDAO(TestCase):

    @patch('uw_canvas.enrollments.Enrollments')
    def test_download_student_ids_for_course(self, MockEnrollment):
        cd = CanvasDAO()
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
        cd = CanvasDAO()
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
        cd = CanvasDAO()
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
    @patch('uw_canvas.enrollments.Enrollments')
    def test_download_raw_analytics_for_course(
                self, MockAnalytics, MockEnrollment):
        cd = CanvasDAO()
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
        cd = CanvasDAO()
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
        cd = CanvasDAO()
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


class TestCloudStorageDAO(TestCase):

    def test_get_relative_file_path(self):
        csd = CloudStorageDAO()
        csd.get_sis_term_id = MagicMock(return_value="2021-spring")
        csd.get_week_of_term = MagicMock(return_value=1)
        self.assertEqual(csd.get_relative_file_path(), "2021-spring/1/")

if __name__ == "__main__":
    unittest.main()
