import os
from data_aggregator.management.commands._base import CreateDBViewCommand
from data_aggregator.utilities import get_view_name
from django.db import connection


def _create(sis_term_id, week):
    """
    Create rad db view for given week and sis-term-id
    """

    view_name = get_view_name(sis_term_id, week, "rad")
    assignments_view_name = get_view_name(sis_term_id,
                                          week,
                                          "assignments")
    participations_view_name = get_view_name(sis_term_id,
                                             week,
                                             "participations")

    cursor = connection.cursor()

    env = os.getenv("ENV")
    if env == "localdev" or not env:
        create_action = (
            'CREATE VIEW "{view_name}"'.format(view_name=view_name))
        cursor.execute(
            'DROP VIEW IF EXISTS "{view_name}"'.format(view_name=view_name)
        )
    else:
        create_action = (
            'CREATE OR REPLACE VIEW "{view_name}"'.format(view_name=view_name))

    cursor.execute(
        '''
        {create_action} AS
        WITH
        avg_norm_ap AS (
            SELECT
                norm_ap.user_id,
                AVG(normalized_assignment_score) AS assignment_score,
                AVG(normalized_participation_score) AS participation_score
            FROM (
                SELECT
                    p1.user_id,
                    p1.course_id,
                    p1.week_id,
                        coalesce(
                            cast((p1.participations - min_raw_participation_score) as decimal) /
                            NULLIF( cast((max_raw_participation_score - min_raw_participation_score) as decimal) / 10, 0),
                        0) - 5
                    AS normalized_participation_score,
                        coalesce(
                            cast(((2 * p1.time_on_time + p1.time_late) - min_raw_assignment_score) as decimal) /
                            NULLIF( cast((max_raw_assignment_score - min_raw_assignment_score) as decimal) / 10, 0)
                                , 0) - 5
                    AS normalized_assignment_score
                FROM "{participations_view_name}" p1
                JOIN (
                    SELECT
                        course_id,
                        MIN(p2.participations) AS min_raw_participation_score,
                        MAX(p2.participations) AS max_raw_participation_score,
                        MIN(2 * p2.time_on_time + p2.time_late) AS min_raw_assignment_score,
                        MAX(2 * p2.time_on_time + p2.time_late) AS max_raw_assignment_score
                    FROM "{participations_view_name}" p2
                    GROUP BY 
                        course_id
                ) raw_ap_bounds ON p1.course_id  = raw_ap_bounds.course_id
                GROUP BY
                    p1.user_id,
                    p1.course_id,
                    p1.week_id,
                    participations,
                    p1.time_on_time,
                    p1.time_late,
                    normalized_participation_score,
                    normalized_assignment_score
            ) AS norm_ap
            GROUP BY
                norm_ap.user_id
        ),
        avg_norm_gr AS (
            SELECT DISTINCT
                a1.user_id,
                AVG(normalized_score) AS grade
            FROM (
            SELECT
                a2.user_id,
                CASE
                WHEN (COALESCE(a2.max_score, 0) - COALESCE(a2.min_score, 0)) = 0 THEN 0
                WHEN a2.score  IS NULL THEN -5
                ELSE ((10 * (COALESCE(a2.score, 0) - COALESCE(a2.min_score, 0))) /
                        (COALESCE(a2.max_score, 0) - COALESCE(a2.min_score, 0))) - 5
                END AS normalized_score
            FROM "{assignments_view_name}" a2
            WHERE a2.status = 'on_time' OR a2.status = 'late' OR a2.status = 'missing'
            GROUP BY a2.user_id, normalized_score 
            ) a1
            GROUP BY
                a1.user_id
        )
        SELECT DISTINCT
            u.canvas_user_id,
            u.full_name,
            '{sis_term_id}' as term,
            {week} as week,
            assignment_score,
            participation_score,
            grade
        FROM avg_norm_ap
        JOIN avg_norm_gr ON avg_norm_ap.user_id = avg_norm_gr.user_id
        JOIN data_aggregator_user u ON avg_norm_ap.user_id = u.id
        '''  # noqa
        .format(
            create_action=create_action,
            week=week,
            sis_term_id=sis_term_id,
            participations_view_name=participations_view_name,
            assignments_view_name=assignments_view_name)
    )
    return True


class Command(CreateDBViewCommand):

    help = ("Creates RAD db view for given week.")

    def create(self, sis_term_id, week):
        _create(sis_term_id, week)
