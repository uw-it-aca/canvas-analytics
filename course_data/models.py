import os
from django.db import models
from django.utils import timezone
from course_data import utilities


class Course(models.Model):
    course_id = models.IntegerField()
    year = models.IntegerField()
    quarter = models.TextField()

    @property
    def term_number(self):
        return utilities.get_term_number(self.quarter)

    @property
    def session_text(self):
        return ("{} {}"
                .format(self.quarter.capitalize(),
                        self.year))


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
    JOB_CHOICES = (
        ('assignment', 'AssignmentJob'),
        ('participation', 'ParticipationJob'),
    )

    objects = JobManager()
    course = models.ForeignKey(Course,
                               on_delete=models.CASCADE)
    type = models.ForeignKey(JobType,
                             on_delete=models.CASCADE)
    week = models.IntegerField()
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
    week = models.IntegerField()
    assignment_id = models.IntegerField(null=True)
    student_id = models.IntegerField(null=True)
    score = models.IntegerField(null=True)
    due_at = models.DateField(null=True)
    points_possible = models.IntegerField(null=True)
    status = models.TextField()

    class Meta:
        indexes = [
            models.Index(fields=['week']),
        ]


class Participation(models.Model):
    course = models.ForeignKey(Course,
                               on_delete=models.CASCADE)
    job = models.ForeignKey(Job,
                            on_delete=models.CASCADE)
    week = models.IntegerField()
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
        indexes = [
            models.Index(fields=['week']),
        ]
