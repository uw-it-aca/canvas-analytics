
import logging
import os
from django.core.management.base import BaseCommand
from uw_sws.term import get_current_term
from data_aggregator.utilities import get_week_of_term, get_view_name
from django.db import connection


def create(sis_term_id, week):
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
        create_action = "CREATE"
        cursor.execute(
            'DROP VIEW IF EXISTS "{view_name}"'.format(view_name=view_name)
        )
    else:
        create_action = "CREATE OR REPLACE"

    cursor.execute(
        '''
        {create_action} VIEW `{view_name}` AS
        SELECT DISTINCT
            u.canvas_user_id,
            u.full_name,
            '{sis_term_id}' as term,
            {week} as week,
            assignment_score,
            participation_score,
            grade
        FROM
        (
            SELECT
                norm_ra.user_id,
                AVG(normalized_assignment_score) AS assignment_score,
                AVG(normalized_participation_score) AS participation_score
            FROM 
            (
                SELECT
                    p1.user_id,
                    p1.course_id,
                    p1.week_id,
                    (
                    IFNULL(
                        ((p1.participations) - min_raw_participation_score) /
                        (NULLIF((max_raw_participation_score - min_raw_participation_score), 0) / 10), 0) - 5
                    ) AS normalized_participation_score,
                    (
                    IFNULL(
                        ((2 * p1.time_on_time + p1.time_late) - min_raw_assignment_score) /
                        (NULLIF((max_raw_assignment_score - min_raw_assignment_score), 0) / 10), 0) - 5
                    ) AS normalized_assignment_score
                FROM `{participations_view_name}` p1
                JOIN (
                    SELECT
                        course_id,
                        MIN(p2.participations) AS min_raw_participation_score,
                        MAX(p2.participations) AS max_raw_participation_score,
                        MIN(2 * p2.time_on_time + p2.time_late) AS min_raw_assignment_score,
                        MAX(2 * p2.time_on_time + p2.time_late) AS max_raw_assignment_score
                    FROM `{participations_view_name}` p2
                    GROUP BY 
                        course_id
                ) ra ON p1.course_id  = ra.course_id
                GROUP BY
                    p1.user_id,
                    p1.course_id,
                    p1.week_id,
                    participations,
                    p1.time_on_time,
                    p1.time_late
            ) norm_ra
            GROUP BY
                norm_ra.user_id
        ) AS p JOIN 
        (
            SELECT DISTINCT
                a1.user_id,
                AVG(normalized_score) AS grade
            FROM (
            SELECT
                a2.user_id,
                CASE
                WHEN (IFNULL(a2.max_score, 0) - IFNULL(a2.min_score, 0)) = 0 THEN 0
                WHEN a2.score  IS NULL THEN -5
                ELSE ((10 * (IFNULL(a2.score, 0) - IFNULL(a2.min_score, 0))) /
                        (IFNULL(a2.max_score, 0) - IFNULL(a2.min_score, 0))) - 5
                END AS 'normalized_score'
            FROM `{assignments_view_name}` a2
            WHERE a2.status = 'on_time' OR a2.status = 'late' OR a2.status = 'missing'
            GROUP BY a2.user_id, normalized_score 
            ) a1
            GROUP BY
                a1.user_id
        ) AS a
        ON p.user_id = a.user_id
        JOIN data_aggregator_user u ON p.user_id = u.id
                    '''.format(
						    create_action=create_action,
						    view_name=view_name,
                            week=week,
                            sis_term_id=sis_term_id,
                            participations_view_name=participations_view_name,
                            assignments_view_name=assignments_view_name)
    )
    return True


class Command(BaseCommand):

    help = ("Creates RAD db view for given week.")

    def handle(self, *args, **options):
        """
        Create rad db view for current week
        """
        sws_term = get_current_term()
        sis_term_id = sws_term.canvas_sis_id()
        week = get_week_of_term(sws_term.first_day_quarter)
        create(sis_term_id, week)
