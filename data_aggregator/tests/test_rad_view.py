import os
import unittest
from unittest import mock
from data_aggregator.utilities import get_view_name
from data_aggregator.management.commands.create_rad_db_view import create
from data_aggregator.tests.db_utils import get_row_count


class TestRadView(unittest.TestCase):

    fixtures = ['/data_aggregator/fixtures/mock_data/*.json',]

    def test_get_view_name(self):
        view_name = get_view_name("2013-spring", "1", "rad")
        self.assertEqual(view_name, "2013_spring_week_1_rad")
        view_name = get_view_name("2013-spring", "2", "rad")
        self.assertEqual(view_name, "2013_spring_week_2_rad")
        view_name = get_view_name("2021-winter", "2", "rad")
        self.assertEqual(view_name, "2021_winter_week_2_rad")

    def test_create_rad_db_view(self):
        sis_term_id = "2013-spring"
        week = 1
        created = create(sis_term_id, week)
        self.assertEqual(created, True)

        week = 2
        created = create(sis_term_id, week)
        self.assertEqual(created, True)

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
            20)

if __name__ == "__main__":
    unittest.main()
