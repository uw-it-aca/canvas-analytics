import os
from django.db import models
from django.utils import timezone
from data_aggregator import utilities
from uw_sws.term import get_current_term


class TermManager(models.Manager):
    def get_create_current_term(self, canvas_term_id, sws_term=None):
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
            term.last_day_add = sws_term.last_day_add
            term.last_day_drop = sws_term.last_day_drop
            term.first_day_quarter = sws_term.first_day_quarter
            term.census_day = sws_term.census_day
            term.last_day_instruction = sws_term.last_day_instruction
            term.grading_period_open = sws_term.grading_period_open
            term.aterm_grading_period_open = \
                sws_term.aterm_grading_period_open
            term.grade_submission_deadline = \
                sws_term.grade_submission_deadline
            term.last_final_exam_date = sws_term.last_final_exam_date
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


class Course(models.Model):
    canvas_course_id = models.IntegerField()
    sis_course_id = models.TextField(null=True)
    short_name = models.TextField(null=True)
    long_name = models.TextField(null=True)
    canvas_account_id = models.IntegerField(null=True)
    sis_account_id = models.TextField(null=True)
    status = models.TextField(null=True)
    term = models.ForeignKey(Term,
                             on_delete=models.CASCADE)


class User(models.Model):
    canvas_user_id = models.IntegerField(unique=True)
    login_id = models.TextField(null=True)
    sis_user_id = models.TextField(null=True)
    first_name = models.TextField(null=True)
    last_name = models.TextField(null=True)
    full_name = models.TextField(null=True)
    sortable_name = models.TextField(null=True)
    short_name = models.TextField(null=True)
    email = models.TextField(null=True)
    status = models.TextField(null=True)


class JobManager(models.Manager):

    def start_batch_of_jobs(self, jobtype, batchsize=10):
        jobs = (self.get_queryset()
                .select_related()
                .filter(type__type=jobtype)
                .filter(pid=None)
                [:batchsize])
        for job in jobs:
            job.mark_start()
        return jobs


class JobType(models.Model):
    JOB_CHOICES = (
        ('assignment', 'AssignmentJob'),
        ('participation', 'ParticipationJob'),
    )
    type = models.CharField(max_length=64, choices=JOB_CHOICES)


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
    created = models.DateField(auto_now_add=True)

    @property
    def status(self):
        if (not self.pid and not self.start and not self.end and
                not self.message) and self.target_date_end < timezone.now():
            return "expired"
        elif (not self.pid and not self.start and not self.end and
                not self.message):
            return "pending"
        elif (self.pid and self.start and not self.end and not self.message):
            return "running"
        elif (self.pid and self.start and self.end and not self.message):
            return "completed"
        elif (self.message):
            return "failed"

    def mark_start(self, *args, **kwargs):
        self.pid = os.getpid()
        self.start = timezone.now()
        super(Job, self).save(*args, **kwargs)

    def mark_end(self, *args, **kwargs):
        self.end = timezone.now()
        super(Job, self).save(*args, **kwargs)


class Assignment(models.Model):
    course = models.ForeignKey(Course,
                               on_delete=models.CASCADE)
    job = models.ForeignKey(Job,
                            on_delete=models.CASCADE)
    week = models.ForeignKey(Week,
                             on_delete=models.CASCADE)
    assignment_id = models.IntegerField(null=True)
    student_id = models.IntegerField(null=True)
    title = models.TextField(null=True)
    unlock_at = models.DateTimeField(null=True)
    points_possible = \
        models.DecimalField(null=True, max_digits=7, decimal_places=2)
    non_digital_submission = models.BooleanField(null=True)
    due_at = models.DateTimeField(null=True)
    status = models.TextField(null=True)
    muted = models.BooleanField(null=True)
    min_score = models.DecimalField(null=True, max_digits=7, decimal_places=2)
    max_score = models.DecimalField(null=True, max_digits=7, decimal_places=2)
    first_quartile = models.IntegerField(null=True)
    median = models.IntegerField(null=True)
    third_quartile = models.IntegerField(null=True)
    excused = models.BooleanField(null=True)
    score = models.DecimalField(null=True, max_digits=7, decimal_places=2)
    posted_at = models.DateTimeField(null=True)
    submitted_at = models.DateTimeField(null=True)


class Participation(models.Model):
    course = models.ForeignKey(Course,
                               on_delete=models.CASCADE)
    job = models.ForeignKey(Job,
                            on_delete=models.CASCADE)
    week = models.ForeignKey(Week,
                             on_delete=models.CASCADE)
    student_id = models.IntegerField(null=True)
    page_views = models.IntegerField(null=True)
    page_views_level = models.IntegerField(null=True)
    participations = models.IntegerField(null=True)
    participations_level = models.IntegerField(null=True)
    time_tardy = models.IntegerField(null=True)
    time_on_time = models.IntegerField(null=True)
    time_late = models.IntegerField(null=True)
    time_missing = models.IntegerField(null=True)
    time_floating = models.IntegerField(null=True)
