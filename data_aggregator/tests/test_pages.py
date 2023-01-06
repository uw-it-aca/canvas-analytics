# Copyright 2023 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


import unittest
from data_aggregator.models import AnalyticTypes
from data_aggregator.views.pages import PageView, JobAdminView, \
    JobAdminDetailView, MetadataFileAdminView
from data_aggregator.tests.view_utils import BaseViewTestCase
from mock import MagicMock, patch


class TestPageView(BaseViewTestCase):

    def get_view(self):
        request = self.get_get_request('')
        page_view = PageView()
        page_view.request = request
        page_view.request.session = MagicMock()
        return page_view

    def test_get_context_data(self):
        page_view = self.get_view()
        context = page_view.get_context_data()
        self.assertIn("netid", context)
        self.assertIn("ga_key", context)


class TestJobAdminView(BaseViewTestCase):

    def get_view(self):
        request = self.get_get_request('')
        job_admin_view = JobAdminView()
        job_admin_view.request = request
        job_admin_view.request.session = MagicMock()
        return job_admin_view

    def test_template(self):
        self.assertEqual(JobAdminView.template_name, "admin/jobs.html")

    def test_get_context_data(self):
        request = self.get_get_request('')
        job_admin_view = JobAdminView()
        job_admin_view.request = request
        job_admin_view.request.session = MagicMock()
        context = job_admin_view.get_context_data()
        self.assertIn("terms", context)
        self.assertIn("jobtypes", context)
        self.assertIn("job_ranges", context)


class TestJobAdminDetailView(BaseViewTestCase):

    def get_view(self):
        request = self.get_get_request('')
        job_detail_view = JobAdminDetailView()
        job_detail_view.object = MagicMock()
        job_detail_view.request = request
        job_detail_view.request.session = MagicMock()
        return job_detail_view

    def test_template(self):
        self.assertEqual(JobAdminDetailView.template_name,
                         "admin/job_detail.html")

    @patch('data_aggregator.views.pages.Participation')
    @patch('data_aggregator.views.pages.Assignment')
    def test_get_related_objects(self, mock_assignment,
                                 mock_participation):
        job_detail_view = self.get_view()
        job_detail_view.get_object = MagicMock(return_value={})
        mock_job = job_detail_view.get_object.return_value
        mock_job["id"] = 12345

        mock_job["type"] = AnalyticTypes.assignment
        related_objects = job_detail_view.get_related_objects()
        mock_assignment.objects.filter.assert_called_with(
            job__id=mock_job["id"])
        mock_assignment.objects.filter().values.assert_called()
        mock_related_objects = \
            mock_participation.objects.filter().values.return_value
        self.assertEqual(related_objects, list(mock_related_objects))

        mock_job["type"] = AnalyticTypes.participation
        related_objects = job_detail_view.get_related_objects()
        mock_participation.objects.filter.assert_called_with(
            job__id=mock_job["id"])
        mock_participation.objects.filter().values.assert_called()
        mock_related_objects = \
            mock_participation.objects.filter().values.return_value
        self.assertEqual(related_objects, list(mock_related_objects))

    def test_get_context_data(self):
        job_detail_view = self.get_view()
        job_detail_view.get_related_objects = MagicMock()
        context = job_detail_view.get_context_data()
        self.assertIn("netid", context)
        self.assertIn("ga_key", context)
        self.assertIn("related_objects", context)


class TestMetadataFileAdminView(BaseViewTestCase):

    def get_view(self):
        request = self.get_get_request('')
        metadata_view = MetadataFileAdminView()
        metadata_view.request = request
        metadata_view.request.session = MagicMock()
        return metadata_view

    def test_template(self):
        self.assertEqual(MetadataFileAdminView.template_name,
                         "admin/metadata.html")

    def test_get_context_data(self):
        metadata_view = self.get_view()
        context = metadata_view.get_context_data()
        self.assertIn("netid", context)
        self.assertIn("ga_key", context)
        self.assertIn("terms", context)


if __name__ == "__main__":
    unittest.main()
