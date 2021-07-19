# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

import unittest
from django.test import TestCase
from data_aggregator.utilities import get_view_name
from data_aggregator.tests.db_utils import get_row_count, \
    get_row_count_where_status_equals
from data_aggregator.dao import TaskDAO


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
        td = TaskDAO()
        sis_term_id = "2013-spring"
        week = 1
        td.create_assignment_db_view(sis_term_id=sis_term_id, week_num=week)
        week = 2
        td.create_assignment_db_view(sis_term_id=sis_term_id, week_num=week)
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
            12)

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
            1)
        self.assertEqual(
            get_row_count_where_status_equals(
                get_view_name(sis_term_id, week, label),
                "late"),
            9)
        self.assertEqual(
            get_row_count_where_status_equals(
                get_view_name(sis_term_id, week, label),
                "on_time"),
            2)


if __name__ == "__main__":
    unittest.main()
