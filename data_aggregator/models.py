import os
import logging
from datetime import datetime, date
from django.db import models
from django.utils import timezone
from data_aggregator import utilities
from uw_sws.term import get_current_term
from uw_sws import SWS_TIMEZONE


class TermManager(models.Manager):
    def get_create_current_term(self, canvas_term_id, sws_term=None):

        def sws_to_utc(dt):
            if isinstance(dt, date):
                # convert date to datetime
                dt = datetime.combine(dt, datetime.min.time())
            SWS_TIMEZONE.localize(dt)
            return dt.astimezone(timezone.utc)

        # get/create model for the term
        term, created = Term.objects.get_or_create(
            canvas_term_id=canvas_term_id)
        if created:
            if not sws_term:
                sws_term = get_current_term()
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
    canvas_term_id = models.IntegerField()
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


class Week(models.Model):
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

    def claim_batch_of_jobs(self, jobtype, batchsize=None):
        # check for pending jobs to claim
        jobs = (self.get_queryset()
                .select_related()
                .filter(type__type=jobtype)
                .filter(pid=None)
                .filter(target_date_end__gte=timezone.now())
                .filter(target_date_start__lte=timezone.now()))

        if jobs.count() == 0:
            # Check to see if we can instead reclaim jobs in case another
            # process crashed and left the db in a stale state. This only
            # works since there is only one daemon process per job type so
            # worker cronjobs aren't competing with each other.
            jobs = (self.get_queryset()
                    .select_related()
                    .filter(type__type=jobtype)
                    .filter(end=None)  # not completed
                    .filter(message='')  # not failed
                    .filter(target_date_end__gte=timezone.now())
                    .filter(target_date_start__lte=timezone.now()))
            if jobs.count() > 0:
                logging.warning(f"Reclaiming {jobs.count()} jobs.")

        if batchsize is not None:
            jobs = jobs[:batchsize]

        for job in jobs:
            job.claim_job()

        return jobs


class JobType(models.Model):
    JOB_CHOICES = (
        ('assignment', 'AssignmentJob'),
        ('participation', 'ParticipationJob'),
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

    @property
    def status(self):
        # The order of these checks matters. We always want to display
        # completed and failed jobs, while pending, claimed, and running
        # jobs may expire.
        if (self.pid and self.start and self.end and not self.message):
            return JobStatusTypes.completed
        elif (self.message):
            return JobStatusTypes.failed
        elif self.target_date_end < timezone.now():
            return JobStatusTypes.expired
        elif (not self.pid and not self.start and not self.end and
                not self.message):
            return JobStatusTypes.pending
        elif (self.pid and not self.start and not self.end and
                not self.message):
            return JobStatusTypes.claimed
        elif (self.pid and self.start and not self.end and not self.message):
            return JobStatusTypes.running

    def claim_job(self, *args, **kwargs):
        self.pid = os.getpid()
        self.start = None
        super(Job, self).save(*args, **kwargs)

    def start_job(self, *args, **kwargs):
        if self.pid:
            self.start = timezone.now()
            self.end = None
            self.message = ''
            super(Job, self).save(*args, **kwargs)
        else:
            logging.warning("Trying to start a job that was never claimed "
                            "by a process. Unable to start a job that doesn't "
                            "have a set pid.")

    def end_job(self, *args, **kwargs):
        if self.pid and self.start:
            self.end = timezone.now()
            self.message = ''
            super(Job, self).save(*args, **kwargs)
        else:
            logging.warning("Trying to end a job that was never started "
                            "and/or claimed. Perhaps this was a running "
                            "job that was restarted.")


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
