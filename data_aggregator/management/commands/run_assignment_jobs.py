from data_aggregator.models import Assignment
from data_aggregator.management.commands._base import RunJobCommand
from data_aggregator.dao import JobDAO, AnalyticTypes


class Command(RunJobCommand):

    job_type = AnalyticTypes.assignment

    help = ("Loads the assignment data for a batch of jobs. Designed to "
            "be run as a cron that is constantly checking for new jobs.")

    def work(self, job):
        # download and load all assignment analytics for job
        JobDAO().run_analytics_job(job)
