import os
from django.db import models
from django.utils import timezone
from course_data import utilities


class Week(models.Model):
    year = models.IntegerField()
    quarter = models.TextField()
    week = models.IntegerField()


class Course(models.Model):
    code = models.IntegerField()
    week = models.ForeignKey(Week,
                             on_delete=models.CASCADE)
    created = models.DateField(auto_now_add=True)

    @property
    def term_number(self):
        return utilities.get_term_number(self.quarter)

    @property
    def session_text(self):
        return ("{} {}, Week {}"
                .format(self.quarter.capitalize(),
                        self.year,
                        self.week))


class JobManager(models.Manager):
    def start_batch_of_assignment_jobs(self, batchsize=10):
        return self.start_batch_of_jobs("assignment", batchsize=batchsize)

    def start_batch_of_participation_jobs(self, batchsize=10):
        return self.start_batch_of_jobs("participation", batchsize=batchsize)

    def start_batch_of_jobs(self, jobtype, batchsize=10):
        jobs = (self.get_queryset()
                .select_related()
                .filter(type=jobtype)
                .filter(pid=None)
                [:batchsize]).mark_start()
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

    def json_data(self):
        return {"course": self.course.course_id,
                "type": self.type,
                "pid": self.pid,
                "start": self.start,
                "end": self.end,
                "message": self.message,
                "created": self.created}


class Assignment(models.Model):
    course = models.ForeignKey(Course,
                               on_delete=models.CASCADE)
    job = models.ForeignKey(Job,
                            on_delete=models.CASCADE)
    assignment_id = models.IntegerField(null=True)
    student_id = models.IntegerField(null=True)
    score = models.IntegerField(null=True)
    due_at = models.DateField(null=True)
    points_possible = models.IntegerField(null=True)
    status = models.TextField()

    def json_data(self):
        return {"assignment_id": self.assignment_id,
                "student_id": self.student_id,
                "score": self.score,
                "due_at": self.due_at,
                "points_possible": self.points_possible,
                "status": self.status}

    def csv_data(self, seperator="|"):
        line = [self.assignment_id,
                self.student_id,
                self.score,
                self.due_at,
                self.points_possible,
                self.status]
        line = seperator.join([str(x) for x in line])
        return line


class Participation(models.Model):
    course = models.ForeignKey(Course,
                               on_delete=models.CASCADE)
    job = models.ForeignKey(Job,
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

    def json_data(self):
        return {"page_views": self.page_views,
                "page_views_level": self.page_views_level,
                "participations": self.participations,
                "participations_level": self.participations_level,
                "time_tardy": self.time_tardy,
                "time_on_time": self.time_on_time,
                "time_late": self.time_late,
                "time_missing": self.time_missing,
                "time_floating": self.time_floating}

    def csv_data(self, seperator="|"):
        line = [self.page_views,
                self.page_views_level,
                self.participations,
                self.participations_level,
                self.time_tardy,
                self.time_on_time,
                self.time_late,
                self.time_missing,
                self.time_floating]
        line = seperator.join([str(x) for x in line])
        return line
