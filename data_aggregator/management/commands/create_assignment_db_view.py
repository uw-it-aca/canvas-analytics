import os
from data_aggregator.management.commands._base import CreateDBViewCommand
from data_aggregator.utilities import get_view_name
from django.db import connection


def _create(sis_term_id, week):
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


class Command(CreateDBViewCommand):

    help = ("Creates assignment db view for given week.")

    def create(self, sis_term_id, week):
        _create(sis_term_id, week)
