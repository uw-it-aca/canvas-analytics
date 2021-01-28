from django.db import transaction
from data_aggregator.dao import CanvasDAO
from data_aggregator.models import Participation
from data_aggregator.management.commands._base import RunJobCommand


class Command(RunJobCommand):

    job_type = "participation"

    help = ("Loads the participation data for a batch of jobs. Designed to "
            "be run as a cron that is constantly checking for new jobs.")

    @transaction.atomic
    def work(self, job):
        # delete existing participation data in case of a job restart
        old_participation = Participation.objects.filter(job=job)
        old_participation.delete()
        # load participation data
        canvas_course_id = job.context["canvas_course_id"]
        partics = (
            CanvasDAO().get_participation(canvas_course_id))
        for partic in partics:
            partic.job = job
        Participation.objects.bulk_create(partics)
