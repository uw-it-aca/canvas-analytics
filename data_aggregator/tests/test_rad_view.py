# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

import unittest
from django.test import TestCase
from data_aggregator.utilities import get_view_name
from data_aggregator.tests.db_utils import get_row_count
from data_aggregator.dao import TaskDAO


class TestRadView(TestCase):

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
        td.create_assignment_db_view(sis_term_id, week)
        td.create_participation_db_view(sis_term_id, week)
        td.create_rad_db_view(sis_term_id, week)
        week = 2
        td.create_assignment_db_view(sis_term_id, week)
        td.create_participation_db_view(sis_term_id, week)
        td.create_rad_db_view(sis_term_id, week)
        super().setUpTestData()

    def test_get_view_name(self):
        view_name = get_view_name("2013-spring", "1", "rad")
        self.assertEqual(view_name, "2013_spring_week_1_rad")
        view_name = get_view_name("2013-spring", "2", "rad")
        self.assertEqual(view_name, "2013_spring_week_2_rad")
        view_name = get_view_name("2021-winter", "2", "rad")
        self.assertEqual(view_name, "2021_winter_week_2_rad")

    def test_number_of_rows(self):
        """
        Test number of rows returned per week
        """
        sis_term_id = "2013-spring"
        week = 1
        label = "rad"

        self.assertEqual(
            get_row_count(get_view_name(sis_term_id, week, label)),
            20)

        week = 2
        self.assertEqual(
            get_row_count(get_view_name(sis_term_id, week, label)),
            6)


if __name__ == "__main__":
    unittest.main()
