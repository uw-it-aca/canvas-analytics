# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

import unittest
from django.db.utils import IntegrityError
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from data_aggregator.models import Assignment, Job, Participation, Term, \
    Week, Course, JobType, AnalyticTypes, User
from data_aggregator.utilities import datestring_to_datetime
from mock import MagicMock, patch


class TestTermManager(TestCase):

    def setUp(self):
        self.mock_get_current_term = \
            self.create_patch('data_aggregator.models.get_current_term')
        self.mock_get_term_by_year_and_quarter = self.create_patch(
            'data_aggregator.models.get_term_by_year_and_quarter')
        self.mock_get_or_create_from_sws_term = self.create_patch(
            'data_aggregator.models.TermManager.get_or_create_from_sws_term')

    def restart_all(self):
        self.mock_get_current_term.reset_mock()
        self.mock_get_or_create_from_sws_term.reset_mock()
        self.mock_get_term_by_year_and_quarter.reset_mock()

    def create_patch(self, name):
        patcher = patch(name)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def test_get_or_create_term_from_sis_term_id(self):

        # assert call sequence when NO sis_term_id is supplied and there is
        # no existing term for the current date does NOT EXIST
        Term.objects.get_term_for_date = MagicMock(return_value=None)
        Term.objects.get_or_create_term_from_sis_term_id()
        self.assertTrue(Term.objects.get_term_for_date.called)
        self.assertTrue(self.mock_get_current_term.called)
        self.assertFalse(self.mock_get_term_by_year_and_quarter.called)
        self.assertTrue(self.mock_get_or_create_from_sws_term.called)

        self.restart_all()

        # assert call sequence when NO sis_term_id is supplied and
        # an existing term for the current date EXISTS
        mock_existing_term = MagicMock()
        Term.objects.get_term_for_date = \
            MagicMock(return_value=mock_existing_term)
        term, created = Term.objects.get_or_create_term_from_sis_term_id()
        self.assertTrue(Term.objects.get_term_for_date.called)
        self.assertFalse(self.mock_get_current_term.called)
        self.assertFalse(self.mock_get_term_by_year_and_quarter.called)
        self.assertFalse(self.mock_get_or_create_from_sws_term.called)
        self.assertEqual((term, created), (mock_existing_term, False))

        self.restart_all()

        # assert call sequence when sis_term_id is supplied
        Term.objects.get_term_for_date = MagicMock(return_value=None)
        Term.objects.get_or_create_term_from_sis_term_id(
                                                    sis_term_id="2021-spring")
        self.assertFalse(Term.objects.get_term_for_date.called)
        self.assertFalse(self.mock_get_current_term.called)
        self.assertTrue(self.mock_get_term_by_year_and_quarter.called)
        self.assertTrue(self.mock_get_or_create_from_sws_term.called)


class TestWeekManager(TestCase):

    def setUp(self):
        self.mock_week = MagicMock()
        self.mock_week_get_or_create = self.create_patch(
            'data_aggregator.models.WeekManager.get_or_create')
        self.mock_week_get_or_create.return_value = \
            self.mock_week, None
        self.mock_get_relative_week = self.create_patch(
            'data_aggregator.utilities.get_relative_week')
        self.mock_term = MagicMock()
        self.mock_get_or_create_term_from_sis_term_id = self.create_patch(
            'data_aggregator.models.TermManager.'
            'get_or_create_term_from_sis_term_id')
        self.mock_get_or_create_term_from_sis_term_id.return_value = \
            self.mock_term, None

    def restart_all(self):
        self.mock_week_get_or_create.reset_mock()
        self.mock_get_relative_week.reset_mock()
        self.mock_get_or_create_term_from_sis_term_id.reset_mock()

    def create_patch(self, name):
        patcher = patch(name)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def test_get_or_create_week(self):
        # assert call sequence when no parameters are passed
        Week.objects.get_or_create_week()
        self.assertTrue(self.mock_get_or_create_term_from_sis_term_id.called)
        self.assertTrue(self.mock_get_relative_week.called)
        self.assertTrue(self.mock_week_get_or_create.called)
        self.mock_week_get_or_create.assert_called_with(
            term=self.mock_term,
            week=self.mock_get_relative_week.return_value)

        self.restart_all()

        # assert call sequence when term is passed
        Week.objects.get_or_create_week(sis_term_id="2021-summer")
        self.assertTrue(self.mock_get_or_create_term_from_sis_term_id.called)
        self.mock_get_or_create_term_from_sis_term_id.assert_called_with(
            sis_term_id="2021-summer")
        self.assertTrue(self.mock_get_relative_week.called)
        self.assertTrue(self.mock_week_get_or_create.called)
        self.mock_week_get_or_create.assert_called_with(
            term=self.mock_term,
            week=self.mock_get_relative_week.return_value)

        self.restart_all()

        # assert call sequence when week is passed
        Week.objects.get_or_create_week(week_num=2)
        self.assertTrue(self.mock_get_or_create_term_from_sis_term_id.called)
        self.assertFalse(self.mock_get_relative_week.called)
        self.assertTrue(self.mock_week_get_or_create.called)
        self.mock_week_get_or_create.assert_called_with(
            term=self.mock_term,
            week=2)

        self.restart_all()

        # assert call sequence when term and week is passed
        Week.objects.get_or_create_week(sis_term_id="2021-summer", week_num=2)
        self.assertTrue(self.mock_get_or_create_term_from_sis_term_id.called)
        self.assertFalse(self.mock_get_relative_week.called)
        self.assertTrue(self.mock_week_get_or_create.called)
        self.mock_week_get_or_create.assert_called_with(
            term=self.mock_term,
            week=2)


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

    def test_restart_job(self):
        job = self.get_test_job_full()
        orig_target_date_start = job.target_date_start
        orig_target_date_end = job.target_date_end
        # retart job
        job.restart_job(save=False)
        # assert values after restart
        self.assertEqual(job.type, TestJob.type)
        self.assertNotEqual(job.target_date_start, orig_target_date_start)
        self.assertNotEqual(job.target_date_end, orig_target_date_end)
        self.assertEqual(job.pid, None)
        self.assertEqual(job.start, None)
        self.assertEqual(job.end, None)
        self.assertEqual(job.message, "")
        self.assertEqual(job.created, TestJob.created)

    def test_clear_job(self):
        job = self.get_test_job_full()
        orig_target_date_start = job.target_date_start
        orig_target_date_end = job.target_date_end
        # retart job
        job.clear_job(save=False)
        # assert values after restart
        self.assertEqual(job.type, TestJob.type)
        self.assertEqual(job.target_date_start, orig_target_date_start)
        self.assertEqual(job.target_date_end, orig_target_date_end)
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

    def test_restart_jobs(self):
        with patch.object(
                timezone, "now",
                return_value=datestring_to_datetime("2021-04-2T12:00:00.0Z")):
            mock_jm = self.get_mock_job_manager()
            # claim all active jobs in the target range
            active_jobs = mock_jm.get_active_jobs(AnalyticTypes.assignment)
            for job in active_jobs:
                job.claim_job()
                self.assertEqual(job.status, "claimed")
            job_ids = [job.id for job in active_jobs]
            # restart all active jobs in the target range
            mock_jm.restart_jobs(job_ids)
            # query for all active jobs again and ensure that they were
            # restarted
            active_jobs = mock_jm.get_active_jobs(AnalyticTypes.assignment)
            for job in active_jobs:
                self.assertEqual(job.status, "pending")

    def test_clear_jobs(self):
        with patch.object(
                timezone, "now",
                return_value=datestring_to_datetime("2021-04-2T12:00:00.0Z")):
            mock_jm = self.get_mock_job_manager()
            # claim all active jobs in the target range
            active_jobs = mock_jm.get_active_jobs(AnalyticTypes.assignment)
            for job in active_jobs:
                job.claim_job()
                self.assertEqual(job.status, "claimed")
            job_ids = [job.id for job in active_jobs]
            # restart all active jobs in the target range
            mock_jm.clear_jobs(job_ids)
            # query for all active jobs again and ensure that they were
            # restarted
            active_jobs = mock_jm.get_active_jobs(AnalyticTypes.assignment)
            for job in active_jobs:
                self.assertEqual(job.status, "pending")

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


class TestAssignmentManager(TestCase):

    @patch("data_aggregator.models.Assignment")
    @patch("data_aggregator.models.User.objects.get")
    def test_create_or_update_assignment(self, mock_user_get,
                                         mock_assignment):
        job = Job()
        user = User()
        term = Term()
        week = Week()
        week.week = 1
        week.term = term

        course = Course()
        course.term = term

        raw_assign_dict = {
            'assignment_id': 6418106,
            'title': 'Basic python, submission',
            'unlock_at': None,
            'points_possible': 2.0,
            'non_digital_submission': False,
            'multiple_due_dates': False,
            'due_at': '2021-06-26T06:05:00Z',
            'status': 'on_time',
            'muted': False,
            'max_score': 2.0,
            'min_score': 0.0,
            'first_quartile': 2.0,
            'median': 2.0,
            'third_quartile': 2.0,
            'module_ids': [],
            'excused': False,
            'submission': {
                'posted_at': '2021-07-01T16:27:44Z',
                'score': 2.0,
                'submitted_at': '2021-06-25T05:47:51Z'},
            'canvas_user_id': 3933194,
            'canvas_course_id': 1458152}

        mock_user_get.return_value = user

        # check for create
        assign, created = Assignment.objects.create_or_update_assignment(
                                            job, week, course, raw_assign_dict)

        mock_user_get.assert_called_once()
        mock_assignment_inst = mock_assignment()
        mock_assignment_inst.save.assert_called_once()

        self.assertEqual(created, True)

        self.assertEqual(assign.job, job)
        self.assertEqual(assign.week, week)
        self.assertEqual(assign.course, course)
        self.assertEqual(assign.user, user)
        self.assertEqual(assign.assignment_id,
                         raw_assign_dict["assignment_id"])
        self.assertEqual(assign.title, raw_assign_dict["title"])
        self.assertEqual(assign.unlock_at, raw_assign_dict["unlock_at"])
        self.assertEqual(assign.points_possible,
                         raw_assign_dict["points_possible"])
        self.assertEqual(assign.non_digital_submission,
                         raw_assign_dict["non_digital_submission"])
        self.assertEqual(assign.due_at, raw_assign_dict["due_at"])
        self.assertEqual(assign.status, raw_assign_dict["status"])
        self.assertEqual(assign.muted, raw_assign_dict["muted"])
        self.assertEqual(assign.max_score, raw_assign_dict["max_score"])
        self.assertEqual(assign.first_quartile,
                         raw_assign_dict["first_quartile"])
        self.assertEqual(assign.median, raw_assign_dict["median"])
        self.assertEqual(assign.third_quartile,
                         raw_assign_dict["third_quartile"])
        self.assertEqual(assign.excused, raw_assign_dict["excused"])
        submission = raw_assign_dict["submission"]
        self.assertEqual(assign.score, submission["score"])
        self.assertEqual(assign.posted_at, submission["posted_at"])
        self.assertEqual(assign.submitted_at, submission["submitted_at"])

        # check update
        mock_assignment_inst.save.side_effect = IntegrityError
        mock_existing_assignment = mock_assignment.objects.get.return_value
        _, created = Assignment.objects.create_or_update_assignment(
                                        job, week, course, raw_assign_dict)
        self.assertEqual(created, False)
        mock_existing_assignment.save.assert_called_once()


class TestParticipationManager(TestCase):

    @patch("data_aggregator.models.Participation")
    @patch("data_aggregator.models.User.objects.get")
    def test_create_or_update_participation(self, mock_user_get,
                                            mock_participation):
        job = Job()
        user = User()
        term = Term()
        week = Week()
        week.week = 1
        week.term = term

        course = Course()
        course.term = term

        raw_partic_dict = {
            'page_views': 9,
            'max_page_views': 9,
            'page_views_level': 3,
            'participations': 0,
            'max_participations': 0,
            'participations_level': 0,
            'tardiness_breakdown': {
                'missing': 0,
                'late': 0,
                'on_time': 0,
                'floating': 0,
                'total': 0},
            'canvas_user_id': 3193994,
            'canvas_course_id': 835454}

        mock_user_get.return_value = user

        # check for create
        partic, created = Participation.objects.create_or_update_participation(
                                            job, week, course, raw_partic_dict)

        mock_user_get.assert_called_once()
        mock_participation_inst = mock_participation()
        mock_participation_inst.save.assert_called_once()

        self.assertEqual(created, True)

        self.assertEqual(partic.job, job)
        self.assertEqual(partic.week, week)
        self.assertEqual(partic.course, course)
        self.assertEqual(partic.user, user)
        self.assertEqual(partic.page_views, raw_partic_dict["page_views"])
        self.assertEqual(partic.max_page_views,
                         raw_partic_dict["max_page_views"])
        self.assertEqual(partic.page_views_level,
                         raw_partic_dict["page_views_level"])
        self.assertEqual(partic.participations,
                         raw_partic_dict["participations"])
        self.assertEqual(partic.max_participations,
                         raw_partic_dict["max_participations"])
        self.assertEqual(partic.participations_level,
                         raw_partic_dict["participations_level"])
        tardiness_breakdown = raw_partic_dict["tardiness_breakdown"]
        self.assertEqual(partic.time_missing, tardiness_breakdown["missing"])
        self.assertEqual(partic.time_late, tardiness_breakdown["late"])
        self.assertEqual(partic.time_on_time, tardiness_breakdown["on_time"])
        self.assertEqual(partic.time_floating, tardiness_breakdown["floating"])
        self.assertEqual(partic.time_total, tardiness_breakdown["total"])

        # check update
        mock_participation_inst.save.side_effect = IntegrityError
        mock_existing_participation = \
            mock_participation.objects.get.return_value
        _, created = Participation.objects.create_or_update_participation(
                                        job, week, course, raw_partic_dict)
        self.assertEqual(created, False)
        mock_existing_participation.save.assert_called_once()


if __name__ == "__main__":
    unittest.main()
