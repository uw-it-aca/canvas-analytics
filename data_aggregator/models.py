# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


import os
import csv
import logging
from datetime import datetime, date, timedelta
from django.db import models, IntegrityError
from django.db.models import Q, Prefetch
from django.utils import timezone
from data_aggregator.exceptions import TermNotStarted
from data_aggregator import utilities
from uw_sws.term import get_term_by_date, get_term_by_year_and_quarter
from uw_sws import SWS_TIMEZONE


class TermManager(models.Manager):

    def get_term_for_sis_term_id(self, sis_term_id):
        """
        Return term for supplied sis_term_id

        :param sis_term_id: sis_term_id to return term for
        :type sis_term_id: str
        """
        term = (Term.objects
                .filter(sis_term_id=sis_term_id)).first()
        return term

    def get_term_for_date(self, date):
        """
        Return term intersecting with supplied date

        :param date: date to return term for
        :type date: datetime.datetime
        """
        term = (Term.objects
                .filter(first_day_quarter__lte=date)
                .filter(grade_submission_deadline__gte=date)).first()
        return term

    def get_or_create_term_from_sis_term_id(self, sis_term_id=None):
        """
        Creates and/or queries for Term matching sis_term_id. If sis_term_id
        is not defined, creates and/or queries for Term object for current
        sws term.

        :param sis_term_id: sis term id to return Term object for
        :type sis_term_id: str
        """
        if sis_term_id:
            # try to lookup the term in db for supplied sis_term_id
            term = self.get_term_for_sis_term_id(sis_term_id)
            if term:
                # return current term
                return term, False
            else:
                # lookup sws term object for supplied sis term id
                year, quarter = sis_term_id.split("-")
                sws_term = get_term_by_year_and_quarter(int(year), quarter)
                return self.get_or_create_from_sws_term(sws_term)
        else:
            # try to lookup the current term in db
            curr_date = timezone.now()
            term = self.get_term_for_date(curr_date)
            if term:
                # return current term
                return term, False
            else:
                # lookup sws term object for current term
                sws_term = get_term_by_date(curr_date.date())
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

    @property
    def end_date(self):
        date = self.term.first_day_quarter
        week_count = 0
        while week_count < self.week:
            date += timedelta(days=6-utilities.get_rad_weekday(date))
            week_count += 1
            if week_count < self.week:
                date += timedelta(days=1)
        return date

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


class AdviserTypes():

    eop = "eop"
    iss = "iss"


class Adviser(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(null=True)
    is_dept_adviser = models.BooleanField(null=True)
    full_name = models.TextField(null=True)
    pronouns = models.TextField(null=True)
    email_address = models.TextField(null=True)
    phone_number = models.TextField(null=True)
    uwnetid = models.TextField(null=True)
    regid = models.TextField(null=True)
    program = models.TextField(null=True)
    booking_url = models.TextField(null=True)
    metadata = models.TextField(null=True)
    timestamp = models.DateTimeField(null=True)


class JobManager(models.Manager):

    def get_jobs(self, jobtype):
        jobs = (self.get_queryset()
                .filter(type__type=jobtype))
        return jobs

    def get_active_jobs(self, jobtype):
        jobs = (self.get_jobs(jobtype)
                .filter(type__type=jobtype)
                .filter(target_date_end__gte=timezone.now())
                .filter(target_date_start__lte=timezone.now()))
        return jobs

    def get_pending_jobs(self, jobtype):
        jobs = (self.get_active_jobs(jobtype)
                .filter(pid=None))
        return jobs

    def get_running_jobs(self, jobtype):
        jobs = (self.get_jobs(jobtype)
                .filter(~Q(pid=None))  # running
                .filter(end=None)  # not completed
                .filter(message=''))  # not failed
        return jobs

    def get_running_jobs_for_term_week(self, jobtype, sis_term_id, week):
        jobs = self.get_running_jobs(jobtype)
        if jobtype in (AnalyticTypes.assignment,
                       AnalyticTypes.participation,
                       TaskTypes.build_subaccount_activity_report,
                       TaskTypes.export_subaccount_activity_report,
                       TaskTypes.create_rad_db_view,
                       TaskTypes.create_assignment_db_view,
                       TaskTypes.create_participation_db_view,
                       TaskTypes.create_rad_data_file):
            return (jobs.filter(context__sis_term_id=sis_term_id)
                        .filter(context__week=week))
        else:
            raise ValueError(f"Job type '{jobtype}'' does not have a  "
                             f"sis_term_id and week attribute.")

    def get_pending_or_running_jobs(self, jobtype):
        jobs = self.get_pending_jobs(jobtype) | self.get_running_jobs(jobtype)
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


class TaskTypes():

    create_terms = "create_terms"
    create_or_update_courses = "create_or_update_courses"
    create_or_update_users = "create_or_update_users"
    create_student_categories_data_file = "create_student_categories_data_file"
    reload_advisers = "reload_advisers"
    create_assignment_db_view = "create_assignment_db_view"
    create_participation_db_view = "create_participation_db_view"
    create_rad_db_view = "create_rad_db_view"
    create_rad_data_file = "create_rad_data_file"
    create_compass_db_view = "create_compass_db_view"
    create_compass_data_file = "create_compass_data_file"
    build_subaccount_activity_report = "build_subaccount_activity_report"
    export_subaccount_activity_report = "export_subaccount_activity_report"


class JobType(models.Model):

    JOB_CHOICES = (
        (AnalyticTypes.assignment, 'AssignmentJob'),
        (AnalyticTypes.participation, 'ParticipationJob'),
        (TaskTypes.create_terms, 'CreateTermsJob'),
        (TaskTypes.create_or_update_courses, 'CreateOrUpdateCoursesJob'),
        (TaskTypes.create_or_update_users, 'CreateOrUpdateUsersJob'),
        (TaskTypes.create_assignment_db_view, 'CreateAssignmentDBViewJob'),
        (TaskTypes.create_participation_db_view,
         'CreateParticipationDBViewJob'),
        (TaskTypes.create_rad_db_view, 'CreateRadDBViewJob'),
        (TaskTypes.create_rad_data_file, 'CreateRadDataFileJob'),
        (TaskTypes.create_compass_db_view, 'CreateCompassDBViewJob'),
        (TaskTypes.create_compass_data_file, 'CreateCompassDataFileJob'),
        (TaskTypes.create_student_categories_data_file,
         'CreateStudentCategoriesDataFileJob'))
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

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type.type,
            "status": self.status,
            "target_date_start": self.target_date_start,
            "target_date_end": self.target_date_end,
            "context": self.context,
            "pid": self.pid,
            "start": self.start,
            "end": self.end,
            "message": self.message,
            "created": self.created
        }

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


class AssignmentManager(models.Manager):

    def _map_assignment_data(self, assign, raw_assign_dict):
        assign.title = raw_assign_dict.get('title')
        assign.unlock_at = raw_assign_dict.get('unlock_at')
        assign.points_possible = raw_assign_dict.get('points_possible')
        assign.non_digital_submission = \
            raw_assign_dict.get('non_digital_submission')
        assign.due_at = raw_assign_dict.get('due_at')
        assign.status = raw_assign_dict.get('status')
        assign.muted = raw_assign_dict.get('muted')
        assign.max_score = raw_assign_dict.get('max_score')
        assign.min_score = raw_assign_dict.get('min_score')
        assign.first_quartile = raw_assign_dict.get('first_quartile')
        assign.median = raw_assign_dict.get('median')
        assign.third_quartile = raw_assign_dict.get('third_quartile')
        assign.excused = raw_assign_dict.get('excused')
        submission = raw_assign_dict.get('submission')
        if submission:
            assign.score = submission.get('score')
            assign.posted_at = submission.get('posted_at')
            assign.submitted_at = \
                submission.get('submitted_at')
        return assign

    def create_or_update_assignment(self, job, week, course, raw_assign_dict):
        created = True
        assignment_id = raw_assign_dict.get('assignment_id')
        student_id = raw_assign_dict.get('canvas_user_id')
        try:
            user = User.objects.get(canvas_user_id=student_id)
        except User.DoesNotExist:
            logging.warning(
                f"User with canvas_user_id {student_id} does not "
                f"exist in Canvas Analytics DB. Skipping.")
            return None, created
        assign = Assignment()
        assign.job = job
        assign.user = user
        assign.week = week
        assign.course = course
        assign.assignment_id = assignment_id
        assign = self._map_assignment_data(assign, raw_assign_dict)
        try:
            assign.save()
        except IntegrityError:
            # we update only if the unique contraint isn't satisified in order
            # to avoid checking for an assignment on every insert
            created = False
            assign = (Assignment.objects
                      .get(user=user,
                           assignment_id=assignment_id,
                           week=week))
            assign = self._map_assignment_data(assign, raw_assign_dict)
            assign.save()
            logging.warning(
                f"Found existing assignment entry for "
                f"canvas_course_id: {course.canvas_course_id}, "
                f"user: {user.canvas_user_id}, "
                f"sis-term-id: {week.term.sis_term_id}, "
                f"week: {week.week}")

        return assign, created


class Assignment(models.Model):

    objects = AssignmentManager()

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


class ParticipationManager(models.Manager):

    def _map_participation_data(self, partic, raw_partic_dict):
        partic.page_views = raw_partic_dict.get('page_views')
        partic.max_page_views = raw_partic_dict.get('max_page_views')
        partic.page_views_level = \
            raw_partic_dict.get('page_views_level')
        partic.participations = raw_partic_dict.get('participations')
        partic.max_participations = raw_partic_dict.get('max_participations')
        partic.participations_level = \
            raw_partic_dict.get('participations_level')
        if raw_partic_dict.get('tardiness_breakdown'):
            partic.time_total = (raw_partic_dict.get('tardiness_breakdown')
                                 .get('total'))
            partic.time_on_time = (raw_partic_dict.get('tardiness_breakdown')
                                   .get('on_time'))
            partic.time_late = (raw_partic_dict.get('tardiness_breakdown')
                                .get('late'))
            partic.time_missing = (raw_partic_dict.get('tardiness_breakdown')
                                   .get('missing'))
            partic.time_floating = (raw_partic_dict.get('tardiness_breakdown')
                                    .get('floating'))
        return partic

    def create_or_update_participation(self, job, week, course,
                                       raw_partic_dict):
        created = True
        student_id = raw_partic_dict.get('canvas_user_id')
        try:
            user = User.objects.get(canvas_user_id=student_id)
        except User.DoesNotExist:
            logging.warning(
                f"User with canvas_user_id {student_id} does not "
                f"exist in Canvas Analytics DB. Skipping.")
            return None, created
        partic = Participation()
        partic.job = job
        partic.user = user
        partic.week = week
        partic.course = course
        partic = self._map_participation_data(partic, raw_partic_dict)
        try:
            partic.save()
        except IntegrityError:
            # we update only if the unique contraint isn't satisified in order
            # to avoid checking for a participation on every insert
            created = False
            partic = (Participation.objects.get(user=user,
                                                week=week,
                                                course=course))
            partic = self._map_participation_data(partic, raw_partic_dict)
            partic.save()
            logging.warning(
                f"Found existing participation entry for "
                f"canvas_course_id: {course.canvas_course_id}, "
                f"user: {user.canvas_user_id}, "
                f"sis-term-id: {week.term.sis_term_id}, "
                f"week: {week.week}")
        return partic, created


class Participation(models.Model):

    objects = ParticipationManager()

    course = models.ForeignKey(Course,
                               on_delete=models.CASCADE)
    job = models.ForeignKey(Job,
                            on_delete=models.CASCADE)
    week = models.ForeignKey(Week,
                             on_delete=models.CASCADE)
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE)
    page_views = models.IntegerField(null=True)
    max_page_views = models.IntegerField(null=True)
    page_views_level = models.IntegerField(null=True)
    participations = models.IntegerField(null=True)
    max_participations = models.IntegerField(null=True)
    participations_level = models.IntegerField(null=True)
    time_total = models.IntegerField(null=True)
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


class CompassDbView(models.Model):
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
    normalized_assignment_score = \
        models.DecimalField(null=True, max_digits=13, decimal_places=3)
    normalized_participation_score = \
        models.DecimalField(null=True, max_digits=13, decimal_places=3)
    normalized_user_course_percentage = \
        models.DecimalField(null=True, max_digits=13, decimal_places=3)
    course_id = models.TextField(null=True)


class ReportManager(models.Manager):
    def get_or_create_report(self, report_type,
                             sis_term_id=None, week_num=None):
        term, _ = Term.objects.get_or_create_term_from_sis_term_id(
            sis_term_id=sis_term_id)
        week, _ = Week.objects.get_or_create_week(
            sis_term_id=term.sis_term_id,
            week_num=week_num)

        if week.week < 1:
            raise TermNotStarted(term.sis_term_id)

        started_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
        report, report_created = Report.objects.get_or_create(
            report_type=report_type,
            term_id=term.sis_term_id,
            term_week=week.week, defaults={"started_date": started_dt})

        if not report_created:
            # re-running an existing report, so flush existing data
            SubaccountActivity.objects.filter(report=report).delete()

            # reset dates
            report.started_date = started_dt
            report.finished_date = None
            report.save()

        return report

    def get_subaccount_activity(self, sis_term_id=None, week_num=None):
        kwargs = {
            "report_type": Report.SUBACCOUNT_ACTIVITY,
            "finished_date__isnull": False,
            "term_week__isnull": False,
        }
        if sis_term_id is not None:
            kwargs["term_id"] = sis_term_id

        if week_num is not None:
            kwargs["term_week"] = week_num
        else:
            kwargs["term_week__lte"] = 10

        prefetch = Prefetch(
            "subaccountactivity_set",
            queryset=SubaccountActivity.objects.filter(
                Q(subaccount_id__startswith="uwcourse"),
                ~Q(subaccount_id__endswith="nqpilot"),
                    ).order_by("subaccount_id"),
            to_attr="subaccounts")

        return super().get_queryset().prefetch_related(prefetch).filter(
            **kwargs).order_by("-finished_date")


class Report(models.Model):
    """
    Represents a report
    """
    objects = ReportManager()

    class Meta:
        db_table = "analytics_report"

    SUBACCOUNT_ACTIVITY = "subaccount_activity"

    TYPE_CHOICES = (
        (SUBACCOUNT_ACTIVITY, "SubAccount Activity"),
    )

    report_type = models.CharField(max_length=80, choices=TYPE_CHOICES)
    started_date = models.DateTimeField()
    finished_date = models.DateTimeField(null=True)
    term_id = models.CharField(max_length=20)
    term_week = models.PositiveIntegerField(null=True)

    def finished(self):
        self.finished_date = datetime.utcnow().replace(tzinfo=timezone.utc)
        self.save()

    def subaccount_activity_header(self):
        return [
            "term_sis_id", "week_num", "subaccount_id", "subaccount_name",
            "campus", "college", "department", "adoption_rate", "courses",
            "active_courses", "ind_study_courses", "active_ind_study_courses",
            "xlist_courses", "xlist_ind_study_courses", "teachers",
            "unique_teachers", "students", "unique_students",
            "discussion_topics", "discussion_replies", "media_objects",
            "attachments", "assignments", "submissions", "announcements_views",
            "assignments_views", "collaborations_views", "conferences_views",
            "discussions_views", "files_views", "general_views",
            "grades_views", "groups_views", "modules_views", "other_views",
            "pages_views", "quizzes_views"
        ]


class SubaccountActivity(models.Model):
    """
    Represents activity by sub-account and term
    """

    class Meta:
        db_table = "analytics_subaccountactivity"

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

    @staticmethod
    def format_name(s):
        return "Continuum" if (
            s == "uweo") else s.replace("-", " ").title().replace("Uw", "UW")

    def adoption_rate(self):
        courses = self.courses or 0
        active_courses = self.active_courses or 0
        ind_study_courses = self.ind_study_courses or 0
        active_ind_study_courses = self.active_ind_study_courses or 0
        xlist_courses = self.xlist_courses or 0
        xlist_ind_study_courses = self.xlist_ind_study_courses or 0

        try:
            rate = round(
                ((active_courses - active_ind_study_courses) /
                    (courses - xlist_courses - ind_study_courses -
                        xlist_ind_study_courses)) * 100, ndigits=2)
        except ZeroDivisionError:
            rate = 0.00

        return rate

    def csv_export_data(self):
        accounts = self.subaccount_id.split(":")
        return [
            self.report.term_id,
            self.report.term_week,
            self.subaccount_id,
            self.subaccount_name,
            self.format_name(accounts[1]) if (1 < len(accounts)) else "",
            self.format_name(accounts[2]) if (2 < len(accounts)) else "",
            self.format_name(accounts[3]) if (3 < len(accounts)) else "",
            self.adoption_rate(),
            self.courses or 0,
            self.active_courses or 0,
            self.ind_study_courses or 0,
            self.active_ind_study_courses or 0,
            self.xlist_courses or 0,
            self.xlist_ind_study_courses or 0,
            self.teachers or 0,
            self.unique_teachers or 0,
            self.students or 0,
            self.unique_students or 0,
            self.discussion_topics or 0,
            self.discussion_replies or 0,
            self.media_objects or 0,
            self.attachments or 0,
            self.assignments or 0,
            self.submissions or 0,
            self.announcements_views or 0,
            self.assignments_views or 0,
            self.collaborations_views or 0,
            self.conferences_views or 0,
            self.discussions_views or 0,
            self.files_views or 0,
            self.general_views or 0,
            self.grades_views or 0,
            self.groups_views or 0,
            self.modules_views or 0,
            self.other_views or 0,
            self.pages_views or 0,
            self.quizzes_views or 0,
        ]
