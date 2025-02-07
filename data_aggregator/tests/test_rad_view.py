# Copyright 2025 UW-IT, University of Washington
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
        weeks = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        for week in weeks:
            td.create_assignment_db_view(sis_term_id=sis_term_id,
                                         week_num=week)
            td.create_participation_db_view(sis_term_id=sis_term_id,
                                            week_num=week)
            td.create_rad_db_view(sis_term_id=sis_term_id,
                                  week_num=week)
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
        label = "rad"

        week = 1
        self.assertEqual(
            get_row_count(get_view_name(sis_term_id, week, label)),
            0)
        week = 2
        self.assertEqual(
            get_row_count(get_view_name(sis_term_id, week, label)),
            0)
        week = 3
        self.assertEqual(
            get_row_count(get_view_name(sis_term_id, week, label)),
            20)
        week = 4
        self.assertEqual(
            get_row_count(get_view_name(sis_term_id, week, label)),
            20)
        week = 5
        self.assertEqual(
            get_row_count(get_view_name(sis_term_id, week, label)),
            20)
        week = 6
        self.assertEqual(
            get_row_count(get_view_name(sis_term_id, week, label)),
            0)
        week = 7
        self.assertEqual(
            get_row_count(get_view_name(sis_term_id, week, label)),
            0)
        week = 8
        self.assertEqual(
            get_row_count(get_view_name(sis_term_id, week, label)),
            20)
        week = 9
        self.assertEqual(
            get_row_count(get_view_name(sis_term_id, week, label)),
            0)
        week = 10
        self.assertEqual(
            get_row_count(get_view_name(sis_term_id, week, label)),
            20)
        week = 11
        self.assertEqual(
            get_row_count(get_view_name(sis_term_id, week, label)),
            0)
        week = 12
        self.assertEqual(
            get_row_count(get_view_name(sis_term_id, week, label)),
            0)


if __name__ == "__main__":
    unittest.main()
