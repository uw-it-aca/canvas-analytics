import logging
from django.conf import settings
from data_aggregator.models import Assignment, Participation, Week, Term, \
    Course, User
from data_aggregator.utilities import get_week_of_term
from restclients_core.exceptions import DataFailureException
from restclients_core.util.retry import retry
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

    def get_student_ids_for_course(self, canvas_course_id):
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

    @retry(DataFailureException, tries=5, delay=3, backoff=2,
           status_codes=[0, 403, 500])
    def get_assignment_for_student(self, canvas_course_id, student_id):
        return Analytics().get_student_assignments_for_course(
            student_id, canvas_course_id)

    def get_assignments(self, canvas_course_id):
        students_ids = self.get_student_ids_for_course(canvas_course_id)
        curr_term = get_current_term()
        term = Term.objects.get(year=curr_term.year,
                                quarter=curr_term.quarter)
        course = (Course.objects.get(
                    canvas_course_id=canvas_course_id,
                    term=term))
        week, _ = Week.objects.get_or_create(
            week=get_week_of_term(curr_term.first_day_quarter),
            term=term)
        num_students_in_course = len(students_ids)
        num_students_wo_assignment = 0
        num_assignments = 0
        assignments = []
        for student_id in students_ids:
            try:
                res = self.get_assignment_for_student(
                        canvas_course_id, student_id)
                for i in res:
                    assignment = Assignment()
                    try:
                        user = User.objects.get(canvas_user_id=student_id)
                    except User.DoesNotExist:
                        logging.warning("User with canvas_user_id {} does not "
                                        "exist in Canvas Analytics DB. "
                                        "Skipping."
                                        .format(student_id))
                        continue
                    assignment.user = user
                    assignment.assignment_id = i.get('assignment_id')
                    assignment.title = i.get('title')
                    assignment.due_at = i.get('unlock_at')
                    assignment.points_possible = i.get('points_possible')
                    assignment.non_digital_submission = \
                        i.get('non_digital_submission')
                    assignment.due_at = i.get('due_at')
                    assignment.status = i.get('status')
                    assignment.muted = i.get('muted')
                    assignment.max_score = i.get('max_score')
                    assignment.min_score = i.get('min_score')
                    assignment.first_quartile = i.get('first_quartile')
                    assignment.median = i.get('median')
                    assignment.third_quartile = i.get('third_quartile')
                    assignment.excused = i.get('excused')
                    submission = i.get('submission')
                    if submission:
                        assignment.score = submission.get('score')
                        assignment.posted_at = submission.get('posted_at')
                        assignment.submitted_at = \
                            submission.get('submitted_at')
                    assignment.week = week
                    assignment.course = course
                    assignments.append(assignment)
                    num_assignments += 1
            except DataFailureException as e:
                if e.status == 404:
                    num_students_wo_assignment += 1
                    self.logger.warning(e)
                    continue
                else:
                    raise
        self.logger.info(f"Loaded {num_assignments} assignment records "
                         f"for {num_students_in_course} students. "
                         f"Skipped {num_students_wo_assignment} "
                         f"students who did not have assignment data.")
        return assignments

    @retry(DataFailureException, tries=5, delay=3, backoff=2,
           status_codes=[0, 403, 500])
    def get_participation_for_student(self, canvas_course_id, student_id):
        return Analytics().get_student_summaries_by_course(
            canvas_course_id, student_id=student_id)

    def get_participation(self, canvas_course_id):
        students_ids = self.get_student_ids_for_course(canvas_course_id)
        curr_term = get_current_term()
        term = Term.objects.get(year=curr_term.year,
                                quarter=curr_term.quarter)
        course = (Course.objects.get(
                    canvas_course_id=canvas_course_id,
                    term=term))
        week, _ = Week.objects.get_or_create(
            week=get_week_of_term(curr_term.first_day_quarter),
            term=term)
        num_students_in_course = len(students_ids)
        num_students_wo_participation = 0
        num_participation = 0
        participations = []
        for student_id in students_ids:
            try:
                res = self.get_participation_for_student(
                    canvas_course_id, student_id)
                for i in res:
                    partic = Participation()
                    try:
                        user = User.objects.get(canvas_user_id=student_id)
                    except User.DoesNotExist:
                        logging.warning("User with canvas_user_id {} does not "
                                        "exist in Canvas Analytics DB. "
                                        "Skipping."
                                        .format(student_id))
                        continue
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
                    participations.append(partic)
                    num_participation += 1
            except DataFailureException as e:
                if e.status == 404:
                    num_students_wo_participation += 1
                    self.logger.warning(e)
                    continue
                else:
                    raise
        self.logger.info(f"Loaded {num_participation} participation records "
                         f"for {num_students_in_course} students. "
                         f"Skipped {num_students_wo_participation} "
                         f"students who did not have participation data.")
        return participations

    def get_canvas_course_provisioning_report(self, sis_term_id):
        # get canvas term using sis-term-id
        canvas_term = Terms().get_term_by_sis_id(sis_term_id)
        # get courses provisioning report for canvas term
        report_client = Reports()
        user_report = report_client.create_course_provisioning_report(
                    settings.ACADEMIC_CANVAS_ACCOUNT_ID,
                    term_id=canvas_term.term_id)
        sis_data = report_client.get_report_data(user_report)
        report_client.delete_report(user_report)
        return sis_data

    def get_canvas_user_provisioning_report(self, sis_term_id):
        # get canvas term using sis-term-id
        canvas_term = Terms().get_term_by_sis_id(sis_term_id)
        # get users provisioning report for canvas term
        report_client = Reports()
        user_report = report_client.create_user_provisioning_report(
                    settings.ACADEMIC_CANVAS_ACCOUNT_ID,
                    term_id=canvas_term.term_id)
        sis_data = report_client.get_report_data(user_report)
        report_client.delete_report(user_report)
        return sis_data
