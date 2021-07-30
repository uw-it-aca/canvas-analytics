# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from data_aggregator.tests.view_utils import BaseViewTestCase
from data_aggregator.views.api.metadata import BaseMetadataView


class TestBaseMetadataView(BaseViewTestCase):

    def test_parse_file_name(self):
        bmv = BaseMetadataView()
        file_name = "2021-summer-eop-advisers.csv"
        self.assertEqual(bmv.parse_file_name(file_name),
                         ("2021-summer", "eop-advisers"))
        file_name = "2021-spring-iss-advisers.csv"
        self.assertEqual(bmv.parse_file_name(file_name),
                         ("2021-spring", "iss-advisers"))
        file_name = "2021-winter-pred-proba.csv"
        self.assertEqual(bmv.parse_file_name(file_name),
                         ("2021-winter", "pred-proba"))
        file_name = "2021-autumn-netid-name-stunum-categories.csv"
        self.assertEqual(bmv.parse_file_name(file_name),
                         ("2021-autumn", "netid-name-stunum-categories"))
        # test file with path
        file_name = ("application_metadata/student_categories/"
                     "2021-autumn-netid-name-stunum-categories.csv")
        self.assertEqual(bmv.parse_file_name(file_name),
                         ("2021-autumn", "netid-name-stunum-categories"))

    def test_get_full_file_path(self):
        bmv = BaseMetadataView()
        self.assertEqual(
            bmv.get_full_file_path("2021-summer-eop-advisers.csv"),
            "application_metadata/eop_advisers/2021-summer-eop-advisers.csv")
        self.assertEqual(
            bmv.get_full_file_path("2021-spring-iss-advisers.csv"),
            "application_metadata/iss_advisers/2021-spring-iss-advisers.csv")
        self.assertEqual(
            bmv.get_full_file_path("2021-winter-pred-proba.csv"),
            "application_metadata/predicted_probabilites/"
            "2021-winter-pred-proba.csv")
        self.assertEqual(
            bmv.get_full_file_path(
                "2021-autumn-netid-name-stunum-categories.csv"),
            "application_metadata/student_categories/"
            "2021-autumn-netid-name-stunum-categories.csv")
