from django.db import models


class Report(models.Model):
    """ Represents a report.
    """
    SUBACCOUNT_ACTIVITY = "subaccount_activity"

    TYPE_CHOICES = (
        (SUBACCOUNT_ACTIVITY, "SubAccount Activity"),
    )

    report_type = models.CharField(max_length=80, choices=TYPE_CHOICES)
    started_date = models.DateTimeField()
    finished_date = models.DateTimeField(null=True)
    term_id = models.CharField(max_length=20)
    term_week = models.PositiveIntegerField(null=True)

    class Meta:
        managed = False


class SubaccountActivity(models.Model):
    """ Represents activity by sub-account and term
    """
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

    class Meta:
        managed = False


class WeeklyDataTimePeriod(models.Model):
    """ Tracks period of time for a weekly report.  Should be... weekly...
        but it does the best it can.
    """
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    term = models.CharField(max_length=50, db_index=True)

    class Meta:
        managed = False


class WeeklyDataDataPoint(models.Model):
    time_period = models.ForeignKey(WeeklyDataTimePeriod,
                                    on_delete=models.CASCADE,
                                    db_index=True)
    course_id = models.CharField(max_length=100, db_index=True, null=True)
    login_name = models.CharField(max_length=100, db_index=True)
    key = models.CharField(max_length=500, db_index=True)
    value = models.TextField(null=True)

    class Meta:
        managed = False


class ManagedCurrentTerm(models.Model):
    """
    Somewhat hacky - there can/should only be one.
    Configured through the web front-end.
    """
    start_date = models.DateField()
    end_date = models.DateField()
    quarter = models.CharField(max_length=50)
    year = models.PositiveIntegerField()

    class Meta:
        managed = False


class ManagedCourseSISIDs(models.Model):
    """
    Just tracks the list of current courses.  Nothing tracks past courses,
    except any data that may have been stored!
    """
    sis_id = models.CharField(max_length=200)

    class Meta:
        managed = False
