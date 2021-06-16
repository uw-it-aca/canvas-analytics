from data_aggregator.models import Assignment
from data_aggregator.management.commands._base import RunJobCommand
from data_aggregator.dao import RunJobDAO, AnalyticTypes


class Command(RunJobCommand):

    job_type = AnalyticTypes.assignment

    help = ("Loads the assignment data for a batch of jobs. Designed to "
            "be run as a cron that is constantly checking for new jobs.")

    def work(self, job):
        rjd = RunJobDAO()
        # delete existing assignment data in case of a job restart
        old_assignments = Assignment.objects.filter(job=job)
        old_assignments.delete()
        # download and load all assignment analytics for job
        rjd.load_all_analytics_for_job(job)
