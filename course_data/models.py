import os
from django.db import models
from django.utils import timezone
from course_data import utilities


class Term(models.Model):
    year = models.IntegerField()
    quarter = models.TextField()
    label = models.TextField()
    last_day_add = models.DateField()
    last_day_drop = models.DateField()
    first_day_quarter = models.DateField()
    census_day = models.DateField()
    last_day_instruction = models.DateField()
    grading_period_open = models.DateTimeField()
    aterm_grading_period_open = models.DateTimeField()
    grade_submission_deadline = models.DateTimeField()
    last_final_exam_date = models.DateTimeField()

    @property
    def term_number(self):
        return utilities.get_term_number(self.quarter)

    @property
    def term_text(self):
        return ("{} {}"
                .format(self.quarter.capitalize(),
                        self.year))


class Week(models.Model):
    term = models.ForeignKey(Term,
                             on_delete=models.CASCADE)
    week = models.IntegerField()


class Course(models.Model):
    course_id = models.IntegerField()
    term = models.ForeignKey(Term,
                             on_delete=models.CASCADE)


class JobManager(models.Manager):
    def start_batch_of_assignment_jobs(self, batchsize=10):
        return self.start_batch_of_jobs("assignment", batchsize=batchsize)

    def start_batch_of_participation_jobs(self, batchsize=10):
        return self.start_batch_of_jobs("participation", batchsize=batchsize)

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
    score = models.IntegerField(null=True)
    due_at = models.DateField(null=True)
    points_possible = models.IntegerField(null=True)
    status = models.TextField()


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
