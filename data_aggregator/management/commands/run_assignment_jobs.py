from django.db import transaction
from data_aggregator.dao import CanvasDAO
from data_aggregator.models import Assignment
from data_aggregator.management.commands._base import RunJobCommand


class Command(RunJobCommand):

    job_type = "assignment"

    help = ("Loads the assignment data for a batch of jobs. Designed to "
            "be run as a cron that is constantly checking for new jobs.")

    @transaction.atomic
    def work(self, job):
        # delete existing assignment data in case of a job restart
        old_assignments = Assignment.objects.filter(job=job)
        old_assignments.delete()
        # load assignment data
        canvas_course_id = job.context["canvas_course_id"]
        assignments = (
            CanvasDAO().get_assignments(canvas_course_id))
        for assign in assignments:
            assign.job = job
        Assignment.objects.bulk_create(assignments)
