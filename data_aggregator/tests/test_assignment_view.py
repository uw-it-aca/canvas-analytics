import os
import unittest
from unittest import mock
from django.db import connection
from data_aggregator.utilities import get_view_name
from data_aggregator.tests.db_utils import get_row_count, \
    get_row_count_where_status_equals
from data_aggregator.management.commands.create_assignment_db_view \
    import create


class TestAssignmentView(unittest.TestCase):

    fixtures = ['/data_aggregator/fixtures/mock_data/*.json',]

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

    def test_create_assignment_db_view(self):
        """
        Test view creation
        """
        sis_term_id = "2013-spring"
        week = 1
        created = create(sis_term_id, week)
        self.assertEqual(created, True)
        sis_term_id = "2013-spring"
        week = 2
        created = create(sis_term_id, week)
        self.assertEqual(created, True)

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
