import logging
from data_aggregator.models import Participation
from data_aggregator.management.commands._base import RunJobCommand
from data_aggregator.dao import CanvasDAO, AnalyticTypes


class Command(RunJobCommand):

    job_type = AnalyticTypes.participation

    help = ("Loads the participation data for a batch of jobs. Designed to "
            "be run as a cron that is constantly checking for new jobs.")

    def work(self, job):
        canvas_course_id = job.context["canvas_course_id"]
        analytic_type = AnalyticTypes.participation
        # download participations analtyics from Canvas API
        canvas_dao = CanvasDAO()
        participations = canvas_dao.download_raw_analytics_for_course(
            canvas_course_id, analytic_type)
        # delete existing participations data in case of a job restart
        old_participations = Participation.objects.filter(job=job)
        old_participations.delete()
        # save participations to db
        canvas_dao.save_participations_to_db(participations, job)
        logging.debug("Saved {} participation entries"
                      .format(len(participations)))
