import os
from django.core.management.base import BaseCommand
from uw_sws.term import get_current_term
from data_aggregator.utilities import get_week_of_term, get_view_name
from django.db import connection


def create(sis_term_id, week):
    """
    Create participation db view for given week and sis-term-id
    """
    view_name = get_view_name(sis_term_id, week, "participations")

    cursor = connection.cursor()

    env = os.getenv("ENV")
    if env == "localdev" or not env:
        create_action = ("CREATE VIEW `{view_name}`"
                         .format(view_name=view_name))
        cursor.execute(
            'DROP VIEW IF EXISTS `{view_name}`'.format(view_name=view_name)
        )
    else:
        create_action = ("CREATE MATERIALIZED VIEW {view_name}"
                         .format(view_name=view_name))

    cursor.execute(
        '''
        {create_action} AS
        SELECT
            data_aggregator_term.id AS term_id,
            data_aggregator_week.id AS week_id,
            p.course_id,
            p.user_id,
            p.participations AS participations,
            p.participations_level AS participations_level,
            p.page_views AS page_views,
            p.page_views_level AS page_views_level,
            p.time_tardy AS time_tardy,
            p.time_on_time AS time_on_time,
            p.time_late AS time_late,
            p.time_missing AS time_missing,
            p.time_floating AS time_floating
        FROM
            data_aggregator_participation p
        JOIN data_aggregator_week on
            p.week_id = data_aggregator_week.id
        JOIN data_aggregator_term on
            data_aggregator_week.term_id = data_aggregator_term.id
        WHERE data_aggregator_week.week = {week}
        AND data_aggregator_term.sis_term_id = '{sis_term_id}'
        '''.format(create_action=create_action,
                   week=week,
                   sis_term_id=sis_term_id)
    )
    return True


class Command(BaseCommand):

    help = ("Creates participation db view for given week.")

    def handle(self, *args, **options):
        """
        Create participation db view for current week
        """
        sws_term = get_current_term()

        sis_term_id = sws_term.canvas_sis_id()
        week = get_week_of_term(sws_term.first_day_quarter)
        create(sis_term_id, week)
