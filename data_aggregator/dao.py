import os
import logging
import json
from io import StringIO
from django.conf import settings
from data_aggregator.models import Assignment, Course, Participation, \
    Term, User, Week
from data_aggregator.utilities import get_week_of_term
from restclients_core.exceptions import DataFailureException
from restclients_core.util.retry import retry
from uw_sws.term import get_current_term
from uw_canvas import Canvas
from uw_canvas.analytics import Analytics
from uw_canvas.courses import Courses
from uw_canvas.enrollments import Enrollments
from uw_canvas.reports import Reports
from uw_canvas.terms import Terms


class AnalyticTypes():

    assignment = "assignment"
    participation = "participation"


class CanvasDAO():
    """
    Query canvas for analytics
    """

    def __init__(self):
        self.canvas = Canvas()
        self.courses = Courses()
        self.enrollments = Enrollments()
        self.analytics = Analytics()
        self.reports = Reports()
        self.terms = Terms()
        sws_term = get_current_term()
        self.curr_term = sws_term.canvas_sis_id()
        self.curr_week = get_week_of_term(sws_term.first_day_quarter)


    @retry(DataFailureException, tries=5, delay=3, backoff=2,
           status_codes=[0, 403, 500])
    def download_student_ids_for_course(self, canvas_course_id):
        stus = self.enrollments.get_enrollments_for_course(
                    canvas_course_id,
                    params={
                        "type": ['StudentEnrollment'],
                        "state": ['active', 'deleted', 'inactive']
                    })
        res = list({stu.user_id for stu in stus})
        return(res)

    @retry(DataFailureException, tries=5, delay=3, backoff=2,
           status_codes=[0, 403, 500])
    def download_course(self, canvas_course_id):
        try:
            return self.courses.get_course(canvas_course_id)
        except Exception as e:
            logging.error(e)

    @retry(DataFailureException, tries=5, delay=3, backoff=2,
           status_codes=[0, 403, 500])
    def download_raw_analytics_for_student(
            self, canvas_course_id, student_id, analytic_type):
        if analytic_type == AnalyticTypes.assignment:
            return self.analytics.get_student_assignments_for_course(
                student_id, canvas_course_id,
                term=self.curr_term, week=self.curr_week)
        elif analytic_type == AnalyticTypes.participation:
            return self.analytics.get_student_summaries_by_course(
                canvas_course_id, student_id=student_id,
                term=self.curr_term, week=self.curr_week)
        else:
            raise ValueError(f"Unknown analytic type: {analytic_type}")

    def download_raw_analytics_for_course(
            self, canvas_course_id, analytic_type):
        students_ids = self.download_student_ids_for_course(canvas_course_id)
        analytics = []
        for student_id in students_ids:
            try:
                res = self.download_raw_analytics_for_student(
                    canvas_course_id, student_id, analytic_type=analytic_type)
                for analytic in res:
                    analytic["canvas_user_id"] = student_id
                    analytic["canvas_course_id"] = canvas_course_id
                    analytics.append(analytic)
            except DataFailureException as e:
                if e.status == 404:
                    logging.warning(e)
                    continue
                else:
                    raise
        return analytics

    def save_assignments_to_db(self, assignment_dicts, job):
        if assignment_dicts:
            canvas_course_id = assignment_dicts[0]["canvas_course_id"]
            curr_term = get_current_term()
            term = Term.objects.get(year=curr_term.year,
                                    quarter=curr_term.quarter)
            course = (Course.objects.get(
                        canvas_course_id=canvas_course_id,
                        term=term))
            week, _ = Week.objects.get_or_create(
                week=get_week_of_term(curr_term.first_day_quarter),
                term=term)
            assign_objs = []
            for i in assignment_dicts:
                student_id = i.get('canvas_user_id')
                assignment_id = i.get('assignment_id')
                try:
                    user = User.objects.get(canvas_user_id=student_id)
                except User.DoesNotExist:
                    logging.warning(f"User with canvas_user_id {student_id} "
                                    f"does not exist in Canvas Analytics DB. "
                                    f"Skipping.")
                    continue
                try:
                    assign = (Assignment.objects
                             .get(user=user,
                                  assignment_id=assignment_id,
                                  week=week))
                except Assignment.DoesNotExist:
                    assign = Assignment()
                assign.job = job
                assign.user = user
                assign.assignment_id = assignment_id
                assign.week = week
                assign.title = i.get('title')
                assign.unlock_at = i.get('unlock_at')
                assign.points_possible = i.get('points_possible')
                assign.non_digital_submission = \
                    i.get('non_digital_submission')
                assign.due_at = i.get('due_at')
                assign.status = i.get('status')
                assign.muted = i.get('muted')
                assign.max_score = i.get('max_score')
                assign.min_score = i.get('min_score')
                assign.first_quartile = i.get('first_quartile')
                assign.median = i.get('median')
                assign.third_quartile = i.get('third_quartile')
                assign.excused = i.get('excused')
                submission = i.get('submission')
                if submission:
                    assign.score = submission.get('score')
                    assign.posted_at = submission.get('posted_at')
                    assign.submitted_at = \
                        submission.get('submitted_at')
                assign.course = course
                assign_objs.append(assign)
            # save assignment data
            Assignment.objects.bulk_create(assign_objs)
            logging.info(f"Loaded {len(assign_objs)} assignment records.")
        else:
            logging.info("No assignment records to load.")

    def save_participations_to_db(self, participation_dicts, job):
        if participation_dicts:
            canvas_course_id = participation_dicts[0]["canvas_course_id"]
            curr_term = get_current_term()
            term = Term.objects.get(year=curr_term.year,
                                    quarter=curr_term.quarter)
            course = (Course.objects.get(
                        canvas_course_id=canvas_course_id,
                        term=term))
            week, _ = Week.objects.get_or_create(
                week=get_week_of_term(curr_term.first_day_quarter),
                term=term)
            partic_objs = []
            for i in participation_dicts:
                student_id = i.get('canvas_user_id')
                try:
                    user = User.objects.get(canvas_user_id=student_id)
                except User.DoesNotExist:
                    logging.warning(f"User with canvas_user_id {student_id} "
                                    f"does not exist in Canvas Analytics DB. "
                                    f"Skipping.")
                    continue
                try:
                    partic = (Participation.objects.get(user=user,
                                                        week=week))
                except Participation.DoesNotExist:
                    partic = Participation()
                partic.job = job
                partic.user = user
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
                partic_objs.append(partic)
            # save assignment data
            Participation.objects.bulk_create(partic_objs)
            logging.info(f"Loaded {len(partic_objs)} participation records.")
        else:
            logging.info("No participation records to load.")

    def download_course_provisioning_report(self, sis_term_id):
        # get canvas term using sis-term-id
        canvas_term = self.terms.get_term_by_sis_id(sis_term_id)
        # get courses provisioning report for canvas term
        user_report = self.reports.create_course_provisioning_report(
                    settings.ACADEMIC_CANVAS_ACCOUNT_ID,
                    term_id=canvas_term.term_id)
        sis_data = self.reports.get_report_data(user_report)
        self.reports.delete_report(user_report)
        return sis_data

    def download_user_provisioning_report(self, sis_term_id):
        # get canvas term using sis-term-id
        canvas_term = self.terms.get_term_by_sis_id(sis_term_id)
        # get users provisioning report for canvas term
        user_report = self.reports.create_user_provisioning_report(
                    settings.ACADEMIC_CANVAS_ACCOUNT_ID,
                    term_id=canvas_term.term_id)
        sis_data = self.reports.get_report_data(user_report)
        self.reports.delete_report(user_report)
        return sis_data
