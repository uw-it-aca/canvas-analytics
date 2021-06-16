from data_aggregator.models import Participation
from data_aggregator.management.commands._base import RunJobCommand
from data_aggregator.dao import JobDAO, AnalyticTypes


class Command(RunJobCommand):

    job_type = AnalyticTypes.participation

    help = ("Loads the participation data for a batch of jobs. Designed to "
            "be run as a cron that is constantly checking for new jobs.")

    def work(self, job):
        # download and load all participation analytics for job
        JobDAO().run_analytics_job(job)
