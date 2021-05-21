from data_aggregator.models import Assignment
from data_aggregator.management.commands._base import RunJobCommand
from data_aggregator.dao import CanvasDAO, AnalyticTypes


class Command(RunJobCommand):

    job_type = AnalyticTypes.assignment

    help = ("Loads the assignment data for a batch of jobs. Designed to "
            "be run as a cron that is constantly checking for new jobs.")

    def work(self, job):
        canvas_course_id = job.context["canvas_course_id"]
        analytic_type = AnalyticTypes.assignment
        # download assignment analtyics from Canvas API
        canvas_dao = CanvasDAO()
        assignments = canvas_dao.download_raw_analytics_for_course(
            canvas_course_id, analytic_type)
        # delete existing assignment data in case of a job restart
        old_assignments = Assignment.objects.filter(job=job)
        old_assignments.delete()
        # save assignments to db
        canvas_dao.save_assignments_to_db(assignments, job)
        print("Saved {} assignment entries".format(len(assignments)))
