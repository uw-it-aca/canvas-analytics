import logging
from datetime import datetime
from django.conf import settings
from data_aggregator.models import Assignment, Participation, Week, Term, \
    Course
from data_aggregator import utilities
from restclients_core.exceptions import DataFailureException
from uw_sws.term import get_current_term
from uw_canvas import Canvas
from uw_canvas.courses import Courses
from uw_canvas.enrollments import Enrollments
from uw_canvas.analytics import Analytics
from uw_canvas.reports import Reports
from uw_canvas.terms import Terms


class CanvasDAO():
    """
    Query canvas for a course
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.canvas = Canvas()

    def _get_student_ids_for_course(self, canvas_course_id):
        enrollments = Enrollments()
        stus = enrollments.get_enrollments_for_course(
                    canvas_course_id,
                    params={
                        "type": ['StudentEnrollment'],
                        "state": ['active', 'deleted', 'inactive']
                    })
        res = [stu.user_id for stu in stus]
        return(res)

    def get_course(self, canvas_course_id):
        try:
            canvas = Courses()
            return canvas.get_course(canvas_course_id)
        except Exception as e:
            self.logger.error(e)

    def get_assignments(self, canvas_course_id):
        analytics = Analytics()
        students_ids = self._get_student_ids_for_course(canvas_course_id)
        curr_term = get_current_term()
        term = Term.objects.get(year=curr_term.year,
                                quarter=curr_term.quarter)
        course = (Course.objects.get(
                    canvas_course_id=canvas_course_id,
                    term=term))
        week, _ = Week.objects.get_or_create(
            week=utilities.get_week_of_term(curr_term.first_day_quarter),
            term=term)
        assignments = []
        for user_id in students_ids:
            try:
                res = analytics.get_student_assignments_for_course(
                        user_id, canvas_course_id)
                for i in res:
                    assignment = Assignment()
                    assignment.student_id = user_id
                    assignment.assignment_id = i.get('assignment_id')
                    assignment.title = i.get('title')
                    if i.get('unlock_at'):
                        assignment.due_at = \
                            datetime.strptime(i['unlock_at'],
                                              "%Y-%m-%dT%H:%M:%S%z")
                    assignment.points_possible = i.get('points_possible')
                    if i.get('non_digital_submission'):
                        assignment.non_digital_submission = \
                            bool(i['non_digital_submission'])
                    if i.get('due_at'):
                        assignment.due_at = \
                            datetime.strptime(i['due_at'],
                                              "%Y-%m-%dT%H:%M:%S%z")
                    assignment.status = i.get('status')
                    if i.get('muted'):
                        assignment.muted = bool(i['muted'])
                    assignment.max_score = i.get('max_score')
                    assignment.min_score = i.get('min_score')
                    assignment.first_quartile = i.get('first_quartile')
                    assignment.median = i.get('median')
                    assignment.third_quartile = i.get('third_quartile')
                    if i.get('excused'):
                        assignment.excused = bool(i['excused'])
                    submission = i.get('submission')
                    if submission:
                        assignment.score = submission['score']
                        if submission.get('posted_at'):
                            assignment.posted_at = \
                                datetime.strptime(submission['posted_at'],
                                                  "%Y-%m-%dT%H:%M:%S%z")
                        if submission.get('submitted_at'):
                            assignment.submitted_at = \
                                datetime.strptime(
                                    submission['submitted_at'],
                                    "%Y-%m-%dT%H:%M:%S%z")
                    assignment.week = week
                    assignment.course = course
                    assignments.append(assignment)
            except DataFailureException as e:
                self.logger.error(e)
                continue
        return assignments

    def get_participation(self, canvas_course_id):
        analytics = Analytics()
        students_ids = self._get_student_ids_for_course(canvas_course_id)
        curr_term = get_current_term()
        term = Term.objects.get(year=curr_term.year,
                                quarter=curr_term.quarter)
        course = (Course.objects.get(
                    canvas_course_id=canvas_course_id,
                    term=term))
        week, _ = Week.objects.get_or_create(
            week=utilities.get_week_of_term(curr_term.first_day_quarter),
            term=term)
        participations = []
        for user_id in students_ids:
            try:
                res = analytics.get_student_summaries_by_course(
                        canvas_course_id, student_id=user_id)
                for i in res:
                    partic = Participation()
                    partic.student_id = user_id
                    partic.week = week
                    partic.course = course
                    partic.page_views = i.get('page_views')
                    partic.page_views_level = \
                        i.get('page_views_level')
                    partic.participations = i.get('participations')
                    partic.participations_level = \
                        i.get('participations_level')
                    if i.get('tardiness_breakdown'):
                        partic.time_tardy = (i.get('tardiness_breakdown')
                                             .get('total'))
                        partic.time_on_time = (i.get('tardiness_breakdown')
                                                .get('on_time'))
                        partic.time_late = (i.get('tardiness_breakdown')
                                            .get('late'))
                        partic.time_missing = (i.get('tardiness_breakdown')
                                                .get('missing'))
                        partic.time_floating = (i.get('tardiness_breakdown')
                                                .get('floating'))
                    partic.page_views = i.get('page_views')
                    participations.append(partic)
            except DataFailureException as e:
                self.logger.error(e)
                continue
        return participations

    def get_canvas_course_provisioning_report(self, sis_term_id):
        # get canvas term using sis-term-id
        canvas_term = Terms().get_term_by_sis_id(sis_term_id)
        # get courses provisioning report for canvas term
        report_client = Reports()
        user_report = report_client.create_course_provisioning_report(
                    settings.RESTCLIENTS_CANVAS_ACCOUNT_ID,
                    term_id=canvas_term.term_id)
        sis_data = report_client.get_report_data(user_report)
        report_client.delete_report(user_report)
        return sis_data
