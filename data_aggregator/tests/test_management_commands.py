# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

import unittest
from data_aggregator.models import Job
from data_aggregator.management.commands._mixins import RunJobMixin
from django.test import TestCase
from mock import MagicMock, patch


class TestRunJobMixin(TestCase):

    @patch("data_aggregator.management.commands._mixins.JobDAO")
    def test_work(self, mock_job_dao):
        mixin = RunJobMixin()
        job = Job()
        mock_job_dao_inst = mock_job_dao()
        mixin.work(job)
        mock_job_dao_inst.run_job.assert_called_once_with(job)

    @patch("data_aggregator.management.commands._mixins.traceback")
    def test_run_job(self, mock_traceback):
        mixin = RunJobMixin()
        mixin.work = MagicMock()
        mock_job = MagicMock()

        completed_job = mixin.run_job(mock_job)
        mock_job.start_job.assert_called_once()
        mixin.work.assert_called_once()
        mock_job.end_job.assert_called_once()
        self.assertEqual(completed_job, mock_job)

        mixin.work.reset_mock()
        mock_job.reset_mock()

        mixin.work.side_effect = Exception
        mock_tb = "MOCK TRACEBACK"
        mock_traceback.format_exc.return_value = mock_tb

        completed_job = mixin.run_job(mock_job)
        mock_job.start_job.assert_called_once()
        mixin.work.assert_called_once()
        mock_job.end_job.assert_not_called()
        self.assertEqual(mock_job.message, mock_tb)
        mock_job.save.assert_called_once()
        self.assertEqual(completed_job, mock_job)


if __name__ == "__main__":
    unittest.main()
