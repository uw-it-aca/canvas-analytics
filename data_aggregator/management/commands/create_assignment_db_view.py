import os
from django.core.management.base import BaseCommand
from uw_sws.term import get_current_term
from data_aggregator.utilities import get_week_of_term, get_view_name
from django.db import connection


def create(sis_term_id, week):
    """
    Create assignment db view for given week and sis-term-id
    """
    view_name = get_view_name(sis_term_id, week, "assignments")

    cursor = connection.cursor()

    env = os.getenv("ENV")
    if env == "localdev" or not env:
        create_action = ('CREATE VIEW "{view_name}"'
                         .format(view_name=view_name))
        cursor.execute(
            'DROP VIEW IF EXISTS "{view_name}"'.format(view_name=view_name)
        )
    else:
        create_action = ('CREATE MATERIALIZED VIEW "{view_name}"'
                         .format(view_name=view_name))

    cursor.execute(
        '''
        {create_action} AS
        SELECT 
            data_aggregator_term.id AS term_id,
            data_aggregator_week.id AS week_id,
            a.course_id,
            a.user_id,
            a.assignment_id,
            a.score,
            a.due_at,
            a.points_possible,
            a.status,
            a.excused,
            a.first_quartile,
            a.max_score,
            a.median,
            a.min_score,
            a.muted,
            a.non_digital_submission,
            a.posted_at,
            a.submitted_at,
            a.third_quartile,
            a.title
        FROM data_aggregator_assignment a
        JOIN data_aggregator_week ON a.week_id = data_aggregator_week.id
        JOIN data_aggregator_term ON
          data_aggregator_week.term_id = data_aggregator_term.id
        WHERE data_aggregator_week.week = {week} AND
          data_aggregator_term.sis_term_id = '{sis_term_id}'
        '''.format(create_action=create_action,
                   week=week,
                   sis_term_id=sis_term_id)
    )
    return True


class Command(BaseCommand):

    help = ("Creates assignment db view for given week.")

    def handle(self, *args, **options):
        sws_term = get_current_term()

        sis_term_id = sws_term.canvas_sis_id()
        week = get_week_of_term(sws_term.first_day_quarter)
        create(sis_term_id, week)
