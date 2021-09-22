# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

import os
import datetime
import unittest
from django.test import TestCase
from data_aggregator import utilities
from django.utils import timezone
from pytz import timezone as tz


class TestUtilities(TestCase):

    def test_set_gcs_base_path(self):
        utilities.set_gcs_base_path("2021-summer", 1)
        self.assertEqual(os.environ["GCS_BASE_PATH"], "2021-summer/1/")
        utilities.set_gcs_base_path("2021-spring", 5)
        self.assertEqual(os.environ["GCS_BASE_PATH"], "2021-spring/5/")

    def test_get_relative_week(self):
        tz_name = "US/Pacific"
        first_day_quarter = datetime.date(2021, 6, 20)
        curr_date = timezone.make_aware(
            datetime.datetime(2020, 6, 20, 0, 0, 0),
            timezone=tz(tz_name))
        week = utilities.get_relative_week(
                            first_day_quarter,
                            cmp_dt=curr_date,
                            tz_name=tz_name)
        self.assertEqual(week, 0)
        curr_date = timezone.make_aware(
            datetime.datetime(2021, 6, 20, 0, 0, 0),
            timezone=tz(tz_name))
        week = utilities.get_relative_week(
                            first_day_quarter,
                            cmp_dt=curr_date,
                            tz_name=tz_name)
        self.assertEqual(week, 1)
        curr_date = timezone.make_aware(
            datetime.datetime(2021, 6, 26, 0, 0, 0),
            timezone=tz(tz_name))
        week = utilities.get_relative_week(
                            first_day_quarter,
                            cmp_dt=curr_date,
                            tz_name=tz_name)
        self.assertEqual(week, 1)
        curr_date = timezone.make_aware(
            datetime.datetime(2021, 6, 27, 0, 0, 0),
            timezone=tz(tz_name))
        week = utilities.get_relative_week(
                            first_day_quarter,
                            cmp_dt=curr_date,
                            tz_name=tz_name)
        self.assertEqual(week, 2)
        curr_date = timezone.make_aware(
            datetime.datetime(2021, 7, 3, 0, 0, 0),
            timezone=tz(tz_name))
        # ensure that UTC dates get converted to PDT
        week = utilities.get_relative_week(
                            first_day_quarter,
                            cmp_dt=curr_date,
                            tz_name=tz_name)
        self.assertEqual(week, 2)
        curr_date = timezone.make_aware(
            datetime.datetime(2021, 7, 4, 0, 0, 0),
            timezone=tz('UTC'))
        week = utilities.get_relative_week(
                            first_day_quarter,
                            cmp_dt=curr_date,
                            tz_name=tz_name)
        self.assertEqual(week, 2)
        curr_date = timezone.make_aware(
            datetime.datetime(2021, 7, 4, 0, 0, 0),
            timezone=tz(tz_name))
        week = utilities.get_relative_week(
                            first_day_quarter,
                            cmp_dt=curr_date,
                            tz_name=tz_name)
        self.assertEqual(week, 3)

    def test_datestring_to_datetime(self):
        # bad input string
        with self.assertRaises(ValueError):
            utilities.datestring_to_datetime("Bad string")

        # bad input not string or unicode
        with self.assertRaises(ValueError):
            utilities.datestring_to_datetime(int(19))

        # %Y-%m-%dT%H:%M:%S.%f good
        ret = utilities.datestring_to_datetime(
            "2019-01-01T23:59:59.999")
        self.assertTrue(ret)
        self.assertTrue(type(ret) is datetime.datetime)

        # %Y-%m-%dT%H:%M:%S.%f < 1900
        with self.assertRaises(ValueError):
            ret = utilities.datestring_to_datetime(
                "1777-01-01T23:59:59.999")

        # %Y-%m-%dT%H:%M:%S.%fZ good
        ret = utilities.datestring_to_datetime(
            "2019-01-01T23:59:59.999Z")
        self.assertTrue(ret)
        self.assertTrue(type(ret) is datetime.datetime)

        # %Y-%m-%dT%H:%M:%S.%fZ < 1900
        with self.assertRaises(ValueError):
            ret = utilities.datestring_to_datetime(
                "1777-01-01T23:59:59.999Z")

        # %Y-%m-%dT%H:%M:%S good
        ret = utilities.datestring_to_datetime(
            "2019-01-01T23:59:59")
        self.assertTrue(ret)
        self.assertTrue(type(ret) is datetime.datetime)

        # %Y-%m-%dT%H:%M:%S < 1900
        with self.assertRaises(ValueError):
            ret = utilities.datestring_to_datetime(
                "1777-01-01T23:59:59")

        # %Y-%m-%dT%H:%M:%SZ good
        ret = utilities.datestring_to_datetime(
            "2019-01-01T23:59:59Z")
        self.assertTrue(ret)
        self.assertTrue(type(ret) is datetime.datetime)

        # %Y-%m-%dT%H:%M:%SZ < 1900
        with self.assertRaises(ValueError):
            ret = utilities.datestring_to_datetime(
                "1777-01-01T23:59:59Z")

        # already a datetime object
        ret1 = utilities.datestring_to_datetime(ret)
        self.assertEqual(ret1, ret)

    def test_get_rad_weekday(self):
        # sunday
        dt = datetime.datetime(2021, 7, 18)
        self.assertEqual(utilities.get_rad_weekday(dt), 0)
        # monday
        dt = datetime.datetime(2021, 7, 19)
        self.assertEqual(utilities.get_rad_weekday(dt), 1)
        # tuesday
        dt = datetime.datetime(2021, 7, 20)
        self.assertEqual(utilities.get_rad_weekday(dt), 2)
        # wednesday
        dt = datetime.datetime(2021, 7, 21)
        self.assertEqual(utilities.get_rad_weekday(dt), 3)
        # thursday
        dt = datetime.datetime(2021, 7, 22)
        self.assertEqual(utilities.get_rad_weekday(dt), 4)
        # friday
        dt = datetime.datetime(2021, 7, 23)
        self.assertEqual(utilities.get_rad_weekday(dt), 5)
        # saturday
        dt = datetime.datetime(2021, 7, 24)
        self.assertEqual(utilities.get_rad_weekday(dt), 6)

    def test_get_term_number(self):
        self.assertEqual(utilities.get_term_number("winter"), 1)
        self.assertEqual(utilities.get_term_number("spring"), 2)
        self.assertEqual(utilities.get_term_number("summer"), 3)
        self.assertEqual(utilities.get_term_number("autumn"), 4)
        with self.assertRaises(ValueError):
            utilities.get_term_number("bad-term")

    def test_get_view_name(self):
        self.assertEqual(
            utilities.get_view_name("2021-summer", 4, "rad"),
            "2021_summer_week_4_rad")
        self.assertEqual(
            utilities.get_view_name("2021-spring", 3, "assignments"),
            "2021_spring_week_3_assignments")
        self.assertEqual(
            utilities.get_view_name("2019-winter", 9, "participations"),
            "2019_winter_week_9_participations")
        with self.assertRaises(ValueError):
            utilities.get_view_name("2021-summer", 4, "bad")

    def test_get_sortable_term_id(self):
        self.assertEqual(utilities.get_sortable_term_id("2021-winter"),
                         "2021-1")
        self.assertEqual(utilities.get_sortable_term_id("2021-spring"),
                         "2021-2")
        self.assertEqual(utilities.get_sortable_term_id("2021-summer"),
                         "2021-3")
        self.assertEqual(utilities.get_sortable_term_id("2021-autumn"),
                         "2021-4")


if __name__ == "__main__":
    unittest.main()
