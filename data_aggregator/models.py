# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

import os
import logging
from datetime import datetime, date, timedelta
from django.db import models
from django.utils import timezone
from data_aggregator import utilities
from uw_sws.term import get_current_term, get_term_by_year_and_quarter
from uw_sws import SWS_TIMEZONE


class TermManager(models.Manager):

    def get_or_create_term_from_sis_term_id(self, sis_term_id=None):
        """
        Creates and/or queries for Term matching sis_term_id. If sis_term_id
        is not defined, creates and/or queries for Term object for current
        sws term.

        :param sis_term_id: sis term id to return Term object for
        :type sis_term_id: str
        """
        if sis_term_id is None:
            # try to lookup the current term based on the date
            curr_date = timezone.now()
            term = (Term.objects
                    .filter(first_day_quarter__lte=curr_date)
                    .filter(grade_submission_deadline__gte=curr_date)).first()
            if term:
                # return current term
                return term, False

        if sis_term_id:
            # lookup sws term object for supplied sis term id
            year, quarter = sis_term_id.split("-")
            sws_term = get_term_by_year_and_quarter(int(year), quarter)
        else:
            # lookup sws term object for current term
            sws_term = get_current_term()
        return self.get_or_create_from_sws_term(sws_term)

    def get_or_create_from_sws_term(self, sws_term):
        """
        Creates and/or queries for Term for sws_term object. If Term for
        sws_term is not defined in the database, a Term object is created.

        :param sws_term: sws_term object to create and or load
        :type sws_term: uw_sws.term
        """

        def sws_to_utc(dt):
            if isinstance(dt, date):
                # convert date to datetime
                dt = datetime.combine(dt, datetime.min.time())
                SWS_TIMEZONE.localize(dt)
                return dt.astimezone(timezone.utc)

        # get/create model for the term
        term, created = \
            Term.objects.get_or_create(sis_term_id=sws_term.canvas_sis_id())
        if created:
            # add current term info for course
            term.sis_term_id = sws_term.canvas_sis_id()
            term.year = sws_term.year
            term.quarter = sws_term.quarter
            term.label = sws_term.term_label()
            term.last_day_add = sws_to_utc(sws_term.last_day_add)
            term.last_day_drop = sws_to_utc(sws_term.last_day_drop)
            term.first_day_quarter = sws_to_utc(sws_term.first_day_quarter)
            term.census_day = sws_to_utc(sws_term.census_day)
            term.last_day_instruction = \
                sws_to_utc(sws_term.last_day_instruction)
            term.grading_period_open = sws_to_utc(sws_term.grading_period_open)
            term.aterm_grading_period_open = \
                sws_to_utc(sws_term.aterm_grading_period_open)
            term.grade_submission_deadline = \
                sws_to_utc(sws_term.grade_submission_deadline)
            term.last_final_exam_date = \
                sws_to_utc(sws_term.last_final_exam_date)
            term.save()
        return term, created


class Term(models.Model):

    objects = TermManager()
    sis_term_id = models.TextField(null=True)
    year = models.IntegerField(null=True)
    quarter = models.TextField(null=True)
    label = models.TextField(null=True)
    last_day_add = models.DateField(null=True)
    last_day_drop = models.DateField(null=True)
    first_day_quarter = models.DateField(null=True)
    census_day = models.DateField(null=True)
    last_day_instruction = models.DateField(null=True)
    grading_period_open = models.DateTimeField(null=True)
    aterm_grading_period_open = models.DateTimeField(null=True)
    grade_submission_deadline = models.DateTimeField(null=True)
    last_final_exam_date = models.DateTimeField(null=True)

    @property
    def term_number(self):
        return utilities.get_term_number(self.quarter)


class WeekManager(models.Manager):

    def get_or_create_week(self, sis_term_id=None, week_num=None):
        """
        Creates and/or queries for Week matching sis_term_id and week_num.
        If sis_term_id and/or week_num is not defined, creates and/or queries
        for Week object for current sws term and/or week_num.

        :param sis_term_id: sis term id to return Term object for
        :type sis_term_id: str
        :param week_num: week number to return Week object for
        :type week_num: int
        """
        term, _ = Term.objects.get_or_create_term_from_sis_term_id(
                                                    sis_term_id=sis_term_id)
        if week_num is None:
            # use current relative week number if not defined
            week_num = utilities.get_relative_week(term.first_day_quarter,
                                                   tz_name="US/Pacific")
        week, created = Week.objects.get_or_create(term=term, week=week_num)
        return week, created


class Week(models.Model):

    objects = WeekManager()
    term = models.ForeignKey(Term,
                             on_delete=models.CASCADE)
    week = models.IntegerField()

    class Meta:
        unique_together = ('term', 'week',)


class Course(models.Model):

    canvas_course_id = models.BigIntegerField()
    sis_course_id = models.TextField(null=True)
    short_name = models.TextField(null=True)
    long_name = models.TextField(null=True)
    canvas_account_id = models.BigIntegerField(null=True)
    sis_account_id = models.TextField(null=True)
    status = models.TextField(null=True)
    term = models.ForeignKey(Term,
                             on_delete=models.CASCADE)


class User(models.Model):

    canvas_user_id = models.BigIntegerField(unique=True)
    login_id = models.TextField(null=True)
    sis_user_id = models.TextField(null=True)
    first_name = models.TextField(null=True)
    last_name = models.TextField(null=True)
    full_name = models.TextField(null=True)
    sortable_name = models.TextField(null=True)
    email = models.TextField(null=True)
    status = models.TextField(null=True)


class JobManager(models.Manager):

    def get_active_jobs(self, jobtype):
        jobs = (self.get_queryset()
                .filter(type__type=jobtype)
                .filter(target_date_end__gte=timezone.now())
                .filter(target_date_start__lte=timezone.now()))
        return jobs

    def get_pending_jobs(self, jobtype):
        jobs = (self.get_active_jobs(jobtype)
                .filter(pid=None))
        return jobs

    def get_pending_or_running_jobs(self, jobtype):
        jobs = (self.get_active_jobs(jobtype)
                .filter(end=None)  # not completed
                .filter(message=''))  # not failed
        return jobs

    def claim_batch_of_jobs(self, jobtype, batchsize=None):
        # check for pending jobs to claim
        jobs = self.get_pending_jobs(jobtype)
        if jobs.count() == 0:
            # Check to see if we can instead reclaim jobs in case another
            # process crashed and left the db in a stale state. This only
            # works since there is only one daemon process per job type so
            # worker cronjobs aren't competing with each other.
            jobs = self.get_pending_or_running_jobs(jobtype)
            if jobs.count() > 0:
                logging.warning(f"Reclaiming {jobs.count()} jobs.")

        if batchsize is not None:
            jobs = jobs[:batchsize]

        for job in jobs:
            job.claim_job()

        return jobs

    def restart_jobs(self, job_ids, *args, **kwargs):
        jobs = self.filter(id__in=job_ids)
        for job in jobs:
            job.restart_job(*args, **kwargs)

    def clear_jobs(self, job_ids, *args, **kwargs):
        jobs = self.filter(id__in=job_ids)
        for job in jobs:
            job.clear_job(*args, **kwargs)


class AnalyticTypes():

    assignment = "assignment"
    participation = "participation"


class JobType(models.Model):

    JOB_CHOICES = (
        (AnalyticTypes.assignment, 'AssignmentJob'),
        (AnalyticTypes.participation, 'ParticipationJob'),
    )
    type = models.CharField(max_length=64, choices=JOB_CHOICES)


class JobStatusTypes():

    pending = "pending"
    claimed = "claimed"
    running = "running"
    completed = "completed"
    failed = "failed"
    expired = "expired"

    @classmethod
    def types(cls):
        return [JobStatusTypes.pending, JobStatusTypes.claimed,
                JobStatusTypes.running, JobStatusTypes.completed,
                JobStatusTypes.failed, JobStatusTypes.expired]


class Job(models.Model):

    objects = JobManager()
    type = models.ForeignKey(JobType,
                             on_delete=models.CASCADE)
    target_date_start = models.DateTimeField()
    target_date_end = models.DateTimeField()
    context = models.JSONField()
    pid = models.IntegerField(null=True)
    start = models.DateTimeField(null=True)
    end = models.DateTimeField(null=True)
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def get_default_target_start():
        return timezone.now()

    @staticmethod
    def get_default_target_end():
        now = timezone.now()
        tomorrow = now + timedelta(days=1)
        return tomorrow

    @property
    def status(self):
        # The order of these checks matters. We always want to display
        # completed, failed, aand running jobs, while pending and claimed
        # jobs may expire.
        if (self.pid and self.start and self.end and not self.message):
            return JobStatusTypes.completed
        elif (self.message):
            return JobStatusTypes.failed
        elif (self.pid and self.start and not self.end and not self.message):
            return JobStatusTypes.running
        elif self.target_date_end < timezone.now():
            return JobStatusTypes.expired
        elif (not self.pid and not self.start and not self.end and
                not self.message):
            return JobStatusTypes.pending
        elif (self.pid and not self.start and not self.end and
                not self.message):
            return JobStatusTypes.claimed

    def claim_job(self, *args, **kwargs):
        self.pid = os.getpid()
        self.start = None
        self.end = None
        self.message = ''
        if kwargs.get("save", True) is True:
            super(Job, self).save(*args, **kwargs)

    def start_job(self, *args, **kwargs):
        if self.pid:
            self.start = timezone.now()
            self.end = None
            self.message = ''
            if kwargs.get("save", True) is True:
                super(Job, self).save(*args, **kwargs)
        else:
            raise RuntimeError("Trying to start a job that was never claimed "
                               "by a process. Unable to start a job that "
                               "doesn't have a set pid.")

    def end_job(self, *args, **kwargs):
        if self.pid and self.start:
            self.end = timezone.now()
            self.message = ''
            if kwargs.get("save", True) is True:
                super(Job, self).save(*args, **kwargs)
        else:
            raise RuntimeError("Trying to end a job that was never started "
                               "and/or claimed. Perhaps this was a running "
                               "job that was restarted.")

    def restart_job(self, *args, **kwargs):
        self.pid = None
        self.start = None
        self.end = None
        self.target_date_start = Job.get_default_target_start()
        self.target_date_end = Job.get_default_target_end()
        self.message = ""
        if kwargs.get("save", True) is True:
            super(Job, self).save(*args, **kwargs)

    def clear_job(self, *args, **kwargs):
        self.pid = None
        self.start = None
        self.end = None
        self.message = ""
        if kwargs.get("save", True) is True:
            super(Job, self).save(*args, **kwargs)


class Assignment(models.Model):

    course = models.ForeignKey(Course,
                               on_delete=models.CASCADE)
    job = models.ForeignKey(Job,
                            on_delete=models.CASCADE)
    week = models.ForeignKey(Week,
                             on_delete=models.CASCADE)
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE)
    assignment_id = models.IntegerField(null=True)
    title = models.TextField(null=True)
    unlock_at = models.DateTimeField(null=True)
    points_possible = \
        models.DecimalField(null=True, max_digits=13, decimal_places=3)
    non_digital_submission = models.BooleanField(null=True)
    due_at = models.DateTimeField(null=True)
    status = models.TextField(null=True)
    muted = models.BooleanField(null=True)
    min_score = models.DecimalField(null=True, max_digits=13, decimal_places=3)
    max_score = models.DecimalField(null=True, max_digits=13, decimal_places=3)
    first_quartile = models.IntegerField(null=True)
    median = models.IntegerField(null=True)
    third_quartile = models.IntegerField(null=True)
    excused = models.BooleanField(null=True)
    score = models.DecimalField(null=True, max_digits=13, decimal_places=3)
    posted_at = models.DateTimeField(null=True)
    submitted_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'course', 'assignment_id',
                                            'week'],
                                    name='unique_assignment')
        ]


class Participation(models.Model):

    course = models.ForeignKey(Course,
                               on_delete=models.CASCADE)
    job = models.ForeignKey(Job,
                            on_delete=models.CASCADE)
    week = models.ForeignKey(Week,
                             on_delete=models.CASCADE)
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE)
    page_views = models.IntegerField(null=True)
    page_views_level = models.IntegerField(null=True)
    participations = models.IntegerField(null=True)
    participations_level = models.IntegerField(null=True)
    time_tardy = models.IntegerField(null=True)
    time_on_time = models.IntegerField(null=True)
    time_late = models.IntegerField(null=True)
    time_missing = models.IntegerField(null=True)
    time_floating = models.IntegerField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'course', 'week'],
                                    name='unique_participation')
        ]


class RadDbView(models.Model):

    class Meta:
        abstract = True

    @classmethod
    def setDb_table(Class, tableName):
        class Meta:
            managed = False
            db_table = tableName

        attrs = {
            '__module__': Class.__module__,
            'Meta': Meta
        }
        return type(tableName, (Class,), attrs)

    canvas_user_id = models.BigIntegerField(unique=True, primary_key=True)
    full_name = models.TextField(null=True)
    term = models.TextField(null=True)
    week = models.IntegerField()
    assignment_score = \
        models.DecimalField(null=True, max_digits=13, decimal_places=3)
    participation_score = \
        models.DecimalField(null=True, max_digits=13, decimal_places=3)
    grade = \
        models.DecimalField(null=True, max_digits=13, decimal_places=3)


class Report(models.Model):
    """
    Represents a report
    """

    class Meta:
        db_table = 'analytics_report'

    SUBACCOUNT_ACTIVITY = "subaccount_activity"

    TYPE_CHOICES = (
        (SUBACCOUNT_ACTIVITY, "SubAccount Activity"),
    )

    report_type = models.CharField(max_length=80, choices=TYPE_CHOICES)
    started_date = models.DateTimeField()
    finished_date = models.DateTimeField(null=True)
    term_id = models.CharField(max_length=20)
    term_week = models.PositiveIntegerField(null=True)


class SubaccountActivity(models.Model):
    """
    Represents activity by sub-account and term
    """

    class Meta:
        db_table = 'analytics_subaccountactivity'

    report = models.ForeignKey(Report, on_delete=models.CASCADE)
    term_id = models.CharField(max_length=20)
    subaccount_id = models.CharField(max_length=100)
    subaccount_name = models.CharField(max_length=200)
    courses = models.PositiveIntegerField(default=0)
    active_courses = models.PositiveIntegerField(default=0)
    ind_study_courses = models.PositiveIntegerField(default=0)
    active_ind_study_courses = models.PositiveIntegerField(default=0)
    xlist_courses = models.PositiveIntegerField(default=0)
    xlist_ind_study_courses = models.PositiveIntegerField(default=0)
    teachers = models.PositiveIntegerField(default=0)
    unique_teachers = models.PositiveIntegerField(default=0)
    students = models.PositiveIntegerField(default=0)
    unique_students = models.PositiveIntegerField(default=0)
    discussion_topics = models.PositiveIntegerField(default=0)
    discussion_replies = models.PositiveIntegerField(default=0)
    media_objects = models.PositiveIntegerField(default=0)
    attachments = models.PositiveIntegerField(default=0)
    assignments = models.PositiveIntegerField(default=0)
    submissions = models.PositiveIntegerField(default=0)
    announcements_views = models.PositiveIntegerField(default=0)
    assignments_views = models.PositiveIntegerField(default=0)
    collaborations_views = models.PositiveIntegerField(default=0)
    conferences_views = models.PositiveIntegerField(default=0)
    discussions_views = models.PositiveIntegerField(default=0)
    files_views = models.PositiveIntegerField(default=0)
    general_views = models.PositiveIntegerField(default=0)
    grades_views = models.PositiveIntegerField(default=0)
    groups_views = models.PositiveIntegerField(default=0)
    modules_views = models.PositiveIntegerField(default=0)
    other_views = models.PositiveIntegerField(default=0)
    pages_views = models.PositiveIntegerField(default=0)
    quizzes_views = models.PositiveIntegerField(default=0)
