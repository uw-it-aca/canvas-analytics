import unittest
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from data_aggregator.models import Job, JobType


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


if __name__ == "__main__":
    unittest.main()
