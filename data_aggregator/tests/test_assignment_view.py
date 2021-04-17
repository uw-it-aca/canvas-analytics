import unittest
from django.test import TestCase
from data_aggregator.utilities import get_view_name
from data_aggregator.tests.db_utils import get_row_count, \
    get_row_count_where_status_equals
from data_aggregator.management.commands.create_assignment_db_view \
    import create as create_assignment


class TestAssignmentView(TestCase):

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
        week = 2
        create_assignment(sis_term_id, week)
        super().setUpTestData()

    def test_get_view_name(self):
        """
        Test view name string creation
        """
        view_name = get_view_name("2013-spring", "1", "assignments")
        self.assertEqual(view_name, "2013_spring_week_1_assignments")
        view_name = get_view_name("2013-spring", "2", "assignments")
        self.assertEqual(view_name, "2013_spring_week_2_assignments")
        view_name = get_view_name("2021-winter", "2", "assignments")
        self.assertEqual(view_name, "2021_winter_week_2_assignments")

    def test_number_of_rows(self):
        """
        Test number of rows returned per week
        """
        sis_term_id = "2013-spring"
        week = 1
        label = "assignments"

        self.assertEqual(
            get_row_count(get_view_name(sis_term_id, week, label)),
            100)

        week = 2
        self.assertEqual(
            get_row_count(get_view_name(sis_term_id, week, label)),
            100)

    def test_row_status(self):
        """
        Test that the number of rows with each status is correct
        """
        sis_term_id = "2013-spring"
        week = 1
        label = "assignments"

        self.assertEqual(
            get_row_count_where_status_equals(
                get_view_name(sis_term_id, week, label),
                "missing"),
            15)
        self.assertEqual(
            get_row_count_where_status_equals(
                get_view_name(sis_term_id, week, label),
                "late"),
            2)
        self.assertEqual(
            get_row_count_where_status_equals(
                get_view_name(sis_term_id, week, label),
                "on_time"),
            83)

        week = 2
        self.assertEqual(
            get_row_count_where_status_equals(
                get_view_name(sis_term_id, week, label),
                "missing"),
            3)
        self.assertEqual(
            get_row_count_where_status_equals(
                get_view_name(sis_term_id, week, label),
                "late"),
            14)
        self.assertEqual(
            get_row_count_where_status_equals(
                get_view_name(sis_term_id, week, label),
                "on_time"),
            83)


if __name__ == "__main__":
    unittest.main()
