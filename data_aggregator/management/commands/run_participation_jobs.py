from data_aggregator.models import Participation
from data_aggregator.management.commands._base import RunJobCommand
from data_aggregator.dao import RunJobDAO, AnalyticTypes


class Command(RunJobCommand):

    job_type = AnalyticTypes.participation

    help = ("Loads the participation data for a batch of jobs. Designed to "
            "be run as a cron that is constantly checking for new jobs.")

    def work(self, job):
        rjd = RunJobDAO()
        # delete existing participations data in case of a job restart
        old_participations = Participation.objects.filter(job=job)
        old_participations.delete()
        # download and load all participation analytics for job
        rjd.load_all_analytics_for_job(job)
