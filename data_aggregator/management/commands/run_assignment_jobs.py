import logging
from django.db import transaction
from data_aggregator.models import Assignment
from data_aggregator.management.commands._base import RunJobCommand
from data_aggregator.dao import CanvasDAO, CloudStorageDAO, AnalyticTypes


class Command(RunJobCommand):

    job_type = AnalyticTypes.assignment

    help = ("Loads the assignment data for a batch of jobs. Designed to "
            "be run as a cron that is constantly checking for new jobs.")

    def work(self, job):
        canvas_course_id = job.context["canvas_course_id"]
        sis_course_id = job.context["sis_course_id"]
        analytic_type = AnalyticTypes.assignment

        # download assignment analtyics from Canvas API
        canvas_dao = CanvasDAO()
        assignments = canvas_dao.download_raw_analytics_for_course(
            canvas_course_id, analytic_type)

        # upload assignments to GCS bucket
        try:
            cs_dao = CloudStorageDAO()
            cs_dao.upload_analytics_to_bucket(
                assignments, sis_course_id, analytic_type)
        except ValueError as e:
            logging.warning(e)
        else:
            # download assignments from GCS bucket
            cs_dao.download_analytics_from_bucket(sis_course_id, analytic_type)

            # delete existing assignment data in case of a job restart
            old_assignments = Assignment.objects.filter(job=job)
            old_assignments.delete()
            # save assignments to db
            canvas_dao.save_assignments_to_db(assignments, job)
