# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from data_aggregator.tests.view_utils import BaseViewTestCase
from data_aggregator.views.api.metadata import BaseMetadataView, \
    MetadataFileListView
from mock import MagicMock, patch
from collections import OrderedDict


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


class TestMetadataFileListView(BaseViewTestCase):

    @patch('data_aggregator.views.api.metadata.BaseDAO.'
           'get_filenames_from_gcs_bucket')
    @patch('data_aggregator.views.api.metadata.Term.objects')
    def test_get_metadata_files_dict(self, mock_term_manager,
                                     mock_get_filenames_from_gcs_bucket):
        mock_get_filenames_from_gcs_bucket.return_value = [
            'application_metadata/eop_advisers/2021-summer-eop-advisers.csv',
            'application_metadata/iss_advisers/2021-summer-iss-advisers.csv',
            'application_metadata/predicted_probabilites/'
            '2021-summer-pred-proba.csv',
            'application_metadata/student_categories/'
            '2021-summer-netid-name-stunum-categories.csv',
            'application_metadata/eop_advisers/2021-autumn-eop-advisers.csv',
            'application_metadata/iss_advisers/2021-autumn-iss-advisers.csv',
            'application_metadata/predicted_probabilites/'
            '2021-autumn-pred-proba.csv',
            'application_metadata/student_categories/'
            '2021-autumn-netid-name-stunum-categories.csv',
        ]
        term_1 = MagicMock()
        term_1.sis_term_id = "2021-summer"
        term_2 = MagicMock()
        term_2.sis_term_id = "2021-autumn"
        mock_term_manager.all.return_value = [term_1, term_2]

        mflv = MetadataFileListView()
        metadata_files = mflv.get_metadata_files_dict()
        self.assertEqual(
            metadata_files,
            OrderedDict([
                ('2021-summer',
                 {'eop-advisers': {
                     'file_name': '2021-summer-eop-advisers.csv'},
                  'iss-advisers': {
                      'file_name': '2021-summer-iss-advisers.csv'},
                  'pred-proba': {
                      'file_name': '2021-summer-pred-proba.csv'},
                  'netid-name-stunum-categories': {
                      'file_name': '2021-summer-netid-name-stunum-categories.csv'}  # noqa
                  }),
                ('2021-autumn',
                 {'eop-advisers': {
                     'file_name': '2021-autumn-eop-advisers.csv'},
                  'iss-advisers': {
                      'file_name': '2021-autumn-iss-advisers.csv'},
                  'pred-proba': {
                      'file_name': '2021-autumn-pred-proba.csv'},
                  'netid-name-stunum-categories': {
                      'file_name': '2021-autumn-netid-name-stunum-categories.csv'}  # noqa
                  })
            ]))
