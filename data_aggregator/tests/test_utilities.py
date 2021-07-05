# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

import datetime
import unittest
from django.test import TestCase
from data_aggregator import utilities
from django.utils import timezone
from pytz import timezone as tz


class TestUtilities(TestCase):

    def test_get_relative_week(self):
        tz_name = "US/Pacific"
        first_day_quarter = datetime.date(2021, 6, 20)
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
        """
        tests datestring_to_datetime
        """

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


if __name__ == "__main__":
    unittest.main()
