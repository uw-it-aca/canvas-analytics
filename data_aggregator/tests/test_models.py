import unittest
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from data_aggregator.models import Job, JobType, AnalyticTypes
from data_aggregator.utilities import datestring_to_datetime
from mock import MagicMock, patch


class TestJob(TestCase):

    type = JobType()
    target_date_start = timezone.now()
    target_date_end = timezone.now() + timedelta(days=1)
    start = timezone.now()
    end = timezone.now() + timedelta(minutes=5)
    created = timezone.now()

    def get_test_job_full(self):
        # initialize job full of values
        job = Job()
        job.type = TestJob.type
        job.target_date_start = TestJob.target_date_start
        job.target_date_end = TestJob.target_date_end
        job.pid = 12345
        job.start = TestJob.start
        job.end = TestJob.end
        job.message = "mock_message"
        job.created = TestJob.created
        return job

    def test_status(self):
        job = Job()
        job.target_date_start = timezone.now()
        job.target_date_end = timezone.now() + timedelta(days=1)
        job.pid = None
        job.start = None
        job.end = None
        job.message = None
        self.assertEqual(job.status, "pending")
        job.pid = 12345
        self.assertEqual(job.status, "claimed")
        job.target_date_end = timezone.now() - timedelta(minutes=1)
        self.assertEqual(job.status, "expired")
        job.start = timezone.now()
        self.assertEqual(job.status, "running")
        job.end = timezone.now()
        self.assertEqual(job.status, "completed")
        job.message = "error"
        self.assertEqual(job.status, "failed")

    def test_restart(self):
        job = self.get_test_job_full()
        # retart job
        job.restart_job(save=False)
        # assert values after restart
        self.assertEqual(job.type, TestJob.type)
        self.assertNotEqual(job.target_date_start, None)
        self.assertNotEqual(job.target_date_end, None)
        self.assertEqual(job.pid, None)
        self.assertEqual(job.start, None)
        self.assertEqual(job.end, None)
        self.assertEqual(job.message, "")
        self.assertEqual(job.created, TestJob.created)

    def test_claim_job(self):
        job = self.get_test_job_full()
        job.pid = None  # set pid to None
        # claim job
        job.claim_job(save=False)
        # assert values after claim
        self.assertEqual(job.type, TestJob.type)
        self.assertNotEqual(job.target_date_start, None)
        self.assertNotEqual(job.target_date_end, None)
        self.assertNotEqual(job.pid, None)  # pid is set in job claim
        self.assertEqual(job.start, None)  # start is set to None in job claim
        self.assertEqual(job.end, None)  # end is set to None in job claim
        self.assertEqual(job.message, '')  # message is set to '' in job claim
        self.assertEqual(job.created, TestJob.created)

    def test_start_job(self):
        job = self.get_test_job_full()
        # claim job
        job.start_job(save=False)
        # assert values after claim
        self.assertEqual(job.type, TestJob.type)
        self.assertNotEqual(job.target_date_start, None)
        self.assertNotEqual(job.target_date_end, None)
        self.assertNotEqual(job.pid, None)
        self.assertNotEqual(job.start, None)  # start is set in job start
        self.assertEqual(job.end, None)  # end is set to None job start
        self.assertEqual(job.message, '')  # message is set to '' job start
        self.assertEqual(job.created, TestJob.created)

        job = self.get_test_job_full()
        with self.assertRaises(RuntimeError):
            # test that runtime error is raised when trying to start an
            # unclaimed job
            job.pid = None
            job.start_job(save=False)

    def test_end_job(self):
        job = self.get_test_job_full()
        # claim job
        job.end_job(save=False)
        # assert values after claim
        self.assertEqual(job.type, TestJob.type)
        self.assertNotEqual(job.target_date_start, None)
        self.assertNotEqual(job.target_date_end, None)
        self.assertNotEqual(job.pid, None)
        self.assertNotEqual(job.start, None)
        self.assertNotEqual(job.end, None)  # end is set in job end
        self.assertEqual(job.message, '')  # message is set to '' job end
        self.assertEqual(job.created, TestJob.created)

        job = self.get_test_job_full()
        with self.assertRaises(RuntimeError):
            # test that runtime error is raised when trying to start an
            # unclaimed job
            job.pid = None
            job.start_job(save=False)

        job = self.get_test_job_full()
        with self.assertRaises(RuntimeError):
            # test that runtime error is raised when trying to start an
            # unstarted job
            job.pid = None
            job.start = None
            job.start_job(save=False)


class TestJobManager(TestCase):

    fixtures = ['data_aggregator/fixtures/mock_data/da_job.json',
                'data_aggregator/fixtures/mock_data/da_jobtype.json']

    def get_mock_job_manager(self):
        Job.objects.get_pending_jobs = \
            MagicMock(side_effect=Job.objects.get_pending_jobs)
        Job.objects.get_pending_or_running_jobs = \
            MagicMock(side_effect=Job.objects.get_pending_or_running_jobs)
        return Job.objects

    def test_get_active_jobs(self):
        with patch.object(
                timezone, "now",
                return_value=datestring_to_datetime("2021-04-2T12:00:00.0Z")):
            mock_jm = self.get_mock_job_manager()
            active_jobs = mock_jm.get_active_jobs(AnalyticTypes.assignment)
            self.assertEqual(len(active_jobs), 2)
            active_jobs = mock_jm.get_active_jobs(AnalyticTypes.participation)
            self.assertEqual(len(active_jobs), 1)
        with patch.object(
                timezone, "now",
                return_value=datestring_to_datetime("2021-04-1T12:00:00.0Z")):
            active_jobs = mock_jm.get_active_jobs(AnalyticTypes.assignment)
            self.assertEqual(len(active_jobs), 1)
            active_jobs = mock_jm.get_active_jobs(AnalyticTypes.participation)
            self.assertEqual(len(active_jobs), 3)
        with patch.object(
                timezone, "now",
                return_value=datestring_to_datetime("2021-03-2T12:00:00.0Z")):
            active_jobs = mock_jm.get_active_jobs(AnalyticTypes.assignment)
            self.assertEqual(len(active_jobs), 0)
            active_jobs = mock_jm.get_active_jobs(AnalyticTypes.participation)
            self.assertEqual(len(active_jobs), 0)

    def test_claim_batch_of_assignment_jobs(self):
        with patch.object(
                timezone, "now",
                return_value=datestring_to_datetime("2021-04-2T12:00:00.0Z")):

            mock_jm = self.get_mock_job_manager()
            # assert that all assignment jobs are initially unclaimed
            for job in mock_jm.get_active_jobs(AnalyticTypes.assignment):
                self.assertNotEqual(job.status, "claimed")
            # assert that participation jobs are correctly claimed
            claimed_assignment_jobs = \
                mock_jm.claim_batch_of_jobs(AnalyticTypes.assignment)
            self.assertEqual(len(claimed_assignment_jobs), 2)
            for job in claimed_assignment_jobs:
                self.assertEqual(job.status, "claimed")
                self.assertEqual(job.type.type, AnalyticTypes.assignment)
            self.assertEqual(mock_jm.get_pending_jobs.called, True)
            self.assertEqual(mock_jm.get_pending_or_running_jobs.called,
                             False)

            # assert that all assignment jobs are initially unclaimed
            for job in mock_jm.get_active_jobs(AnalyticTypes.assignment):
                self.assertEqual(job.status, "claimed")
            # assert reclaiming assignmetn jobs
            claimed_assignment_jobs = \
                mock_jm.claim_batch_of_jobs(AnalyticTypes.assignment)
            self.assertEqual(len(claimed_assignment_jobs), 2)
            for job in claimed_assignment_jobs:
                self.assertEqual(job.status, "claimed")
                self.assertEqual(job.type.type, AnalyticTypes.assignment)
            self.assertEqual(mock_jm.get_pending_jobs.called, True)
            self.assertEqual(mock_jm.get_pending_or_running_jobs.called,
                             True)

    def test_claim_batch_of_participation_jobs(self):
        with patch.object(
                timezone, "now",
                return_value=datestring_to_datetime("2021-04-2T12:00:00.0Z")):

            mock_jm = self.get_mock_job_manager()
            # assert that all participation jobs are initially unclaimed
            for job in mock_jm.get_active_jobs(AnalyticTypes.participation):
                self.assertNotEqual(job.status, "claimed")
            # assert that participation jobs are correctly claimed
            claimed_participation_jobs = \
                mock_jm.claim_batch_of_jobs(AnalyticTypes.participation)
            self.assertEqual(len(claimed_participation_jobs), 1)
            for job in claimed_participation_jobs:
                self.assertEqual(job.status, "claimed")
                self.assertEqual(job.type.type, AnalyticTypes.participation)
            self.assertEqual(mock_jm.get_pending_jobs.called, True)
            self.assertEqual(mock_jm.get_pending_or_running_jobs.called,
                             False)

            # assert that all participation jobs are initially claimed
            for job in mock_jm.get_active_jobs(AnalyticTypes.participation):
                self.assertEqual(job.status, "claimed")
            # assert reclaiming participation jobs
            claimed_participation_jobs = \
                mock_jm.claim_batch_of_jobs(AnalyticTypes.participation)
            self.assertEqual(len(claimed_participation_jobs), 1)
            for job in claimed_participation_jobs:
                self.assertEqual(job.status, "claimed")
                self.assertEqual(job.type.type, AnalyticTypes.participation)
            self.assertEqual(mock_jm.get_pending_jobs.called, True)
            self.assertEqual(mock_jm.get_pending_or_running_jobs.called,
                             True)


if __name__ == "__main__":
    unittest.main()
