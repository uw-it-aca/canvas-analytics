
import unittest
from data_aggregator.models import Job
from django.test import TestCase, Client
from django.utils import timezone
from data_aggregator.utilities import datestring_to_datetime
from mock import patch


class TestJobRestartView(TestCase):

    fixtures = ['data_aggregator/fixtures/mock_data/da_job.json',
                'data_aggregator/fixtures/mock_data/da_jobtype.json']

    def test_post(self):
        with patch.object(
                timezone, "now",
                return_value=datestring_to_datetime("2021-04-2T12:00:00.0Z")):
            c = Client()

            """
            restart list of jobs and assert that their statuses changed
            """
            jobs_to_restart = Job.objects.filter(id__in=[1, 2])
            # claim jobs in order to reset the test
            for job in jobs_to_restart:
                self.assertEqual(job.status, "pending")
                job.claim_job()
                self.assertEqual(job.status, "claimed")
            # post to endpoint to restart jobs
            response = c.post('/api/internal/jobs/restart/',
                              {"job_ids": [1, 2]},
                              content_type="application/json")
            self.assertEqual(response.status_code, 200)
            # confirm that jobs were restarted and now pending
            reset_jobs = Job.objects.filter(id__in=[1, 2])
            for job in reset_jobs:
                self.assertEqual(job.status, "pending")

            """
            restart single of job and assert that other jobs are not effected
            """
            # claim both jobs #1 and #2
            for job in Job.objects.filter(id__in=[1, 2]):
                self.assertEqual(job.status, "pending")
                job.claim_job()
                self.assertEqual(job.status, "claimed")
            # post to endpoint to restart job #1
            response = c.post('/api/internal/jobs/restart/',
                              {"job_ids": [1]},
                              content_type="application/json")
            self.assertEqual(response.status_code, 200)
            # confirm that job #1 were restarted and now pending
            jobs_to_restart = Job.objects.filter(id__in=[1])
            for job in jobs_to_restart:
                self.assertEqual(job.status, "pending")
            # confirm that job #2 is still claimed
            job_to_exclude = Job.objects.get(id=2)
            self.assertEqual(job_to_exclude.status, "claimed")

        # assert that Job.objects.restart_jobs is called
        with patch.object(Job.objects, "restart_jobs") as mock_restart_jobs:
            c.post('/api/internal/jobs/restart/',
                   {"job_ids": [1]},
                   content_type="application/json")
            self.assertTrue(mock_restart_jobs.called)


class TestJobClearView(TestCase):

    fixtures = ['data_aggregator/fixtures/mock_data/da_job.json',
                'data_aggregator/fixtures/mock_data/da_jobtype.json']

    def test_post(self):
        with patch.object(
                timezone, "now",
                return_value=datestring_to_datetime("2021-04-2T12:00:00.0Z")):
            c = Client()

            """
            clear list of jobs and assert that their statuses changed
            """
            jobs_to_clear = Job.objects.filter(id__in=[1, 2])
            # claim jobs in order to reset the test
            for job in jobs_to_clear:
                self.assertEqual(job.status, "pending")
                job.claim_job()
                self.assertEqual(job.status, "claimed")
            # post to endpoint to clear jobs
            response = c.post('/api/internal/jobs/clear/',
                              {"job_ids": [1, 2]},
                              content_type="application/json")
            self.assertEqual(response.status_code, 200)
            # confirm that jobs were cleared and now pending
            reset_jobs = Job.objects.filter(id__in=[1, 2])
            for job in reset_jobs:
                self.assertEqual(job.status, "pending")

            """
            clear single of job and assert that other jobs are not effected
            """
            # claim both jobs #1 and #2
            for job in Job.objects.filter(id__in=[1, 2]):
                self.assertEqual(job.status, "pending")
                job.claim_job()
                self.assertEqual(job.status, "claimed")
            # post to endpoint to clear job #1
            response = c.post('/api/internal/jobs/clear/',
                              {"job_ids": [1]},
                              content_type="application/json")
            self.assertEqual(response.status_code, 200)
            # confirm that job #1 were cleared and now pending
            jobs_to_clear = Job.objects.filter(id__in=[1])
            for job in jobs_to_clear:
                self.assertEqual(job.status, "pending")
            # confirm that job #2 is still claimed
            job_to_exclude = Job.objects.get(id=2)
            self.assertEqual(job_to_exclude.status, "claimed")

        # assert that Job.objects.clear_jobs is called
        with patch.object(Job.objects, "clear_jobs") as mock_clear_jobs:
            c.post('/api/internal/jobs/clear/',
                   {"job_ids": [1]},
                   content_type="application/json")
            self.assertTrue(mock_clear_jobs.called)


if __name__ == "__main__":
    unittest.main()