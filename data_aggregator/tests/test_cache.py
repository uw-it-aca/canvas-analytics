# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

import unittest
from django.test import TestCase
from data_aggregator.cache import DataAggregatorGCSCache


class TestDataAggregatorGCSCache(TestCase):

    def test_get_cache_expiration_time(self):
        cache = DataAggregatorGCSCache()
        # valid analytics urls
        self.assertEqual(
            cache.get_cache_expiration_time(
                "canvas",
                "/api/v1/courses/1392640/analytics/student_summaries.json"),
            0)
        self.assertEqual(
            cache.get_cache_expiration_time(
                "canvas",
                "/api/v1/courses/1452786/analytics/student_summaries.json"
                "?per_page=100"),
            0)
        self.assertEqual(
            cache.get_cache_expiration_time(
                "canvas",
                "/api/v1/courses/1399587/analytics/users/3562797/"
                "assignments.json"),
            0)
        # valid subaccount report urls
        self.assertEqual(
            cache.get_cache_expiration_time(
                "canvas",
                "/api/v1/accounts/sis_account_id:account_103831/analytics/"
                "terms/sis_term_id:2021-spring/activity.json"),
            0)
        self.assertEqual(
            cache.get_cache_expiration_time(
                "canvas",
                "/api/v1/accounts/sis_account_id:uwcourse:seattle:"
                "information-school:inform:ita:future/analytics/"
                "terms/sis_term_id:2021-spring/statistics.json"),
            0)
        # unknown service
        self.assertEqual(
            cache.get_cache_expiration_time(
                "foobar",
                "/api/v1/courses/1392640/analytics/"),
            None)
        # bad url
        self.assertEqual(
            cache.get_cache_expiration_time(
                "canvas",
                "/api/v2/courses/1392640/analytics/"),
            None)
        # subaccount urls to ignore
        self.assertEqual(
            cache.get_cache_expiration_time(
                "canvas",
                "/api/v1/accounts/sis_account_id:uwcourse/sub_accounts"
                "?recursive=true&page=2&per_page=100"),
            None)


if __name__ == "__main__":
    unittest.main()
