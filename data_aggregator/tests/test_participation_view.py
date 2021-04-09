import os
import unittest
from unittest import mock
from data_aggregator.utilities import get_view_name
from data_aggregator.management.commands.create_participation_db_view \
    import create
from data_aggregator.tests.db_utils import get_row_count

class TestParticipationView(unittest.TestCase):

    fixtures = ['/data_aggregator/fixtures/mock_data/*.json',]

    def test_get_view_name(self):
        """
        Test view name string creation
        """
        view_name = get_view_name("2013-spring", "1", "participations")
        self.assertEqual(view_name, "2013_spring_week_1_participations")
        view_name = get_view_name("2013-spring", "2", "participations")
        self.assertEqual(view_name, "2013_spring_week_2_participations")
        view_name = get_view_name("2021-winter", "2", "participations")
        self.assertEqual(view_name, "2021_winter_week_2_participations")

    def test_create_participation_db_view(self):
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
        label = "participations"
        
        self.assertEqual(
            get_row_count(get_view_name(sis_term_id, week, label)),
            20)

        week = 2
        self.assertEqual(
            get_row_count(get_view_name(sis_term_id, week, label)),
            20)


if __name__ == "__main__":
    unittest.main()
