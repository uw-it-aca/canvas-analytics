from datetime import datetime
from uw_canvas import Canvas
from uw_canvas.courses import Courses
from uw_canvas.enrollments import Enrollments
from uw_canvas.analytics import Analytics
from restclients_core.exceptions import DataFailureException
from course_data.logger import Logger
from course_data.models import Assignment, Participation


class CanvasDAO():
    """
    Query canvas for a course
    """

    def __init__(self):
        self.logger = Logger()
        self.canvas = Canvas()

    def _get_student_ids_for_course(self, course):
        enrollments = Enrollments()
        stus = enrollments.get_enrollments_for_course(
                    course.course_id,
                    params={
                        "type": ['StudentEnrollment'],
                        "state": ['active', 'deleted', 'inactive']
                    })
        res = [stu.user_id for stu in stus]
        return(res)

    def get_course(self, course_id):
        try:
            canvas = Courses()
            return canvas.get_course(course_id)
        except Exception as e:
            self.logger.error(e)

    def get_assignments(self, course_id):
        analytics = Analytics()
        course = self.get_course(course_id)
        students_ids = self._get_student_ids_for_course(course)
        assignments = []
        for user_id in students_ids:
            try:
                res = analytics.get_student_assignments_for_course(
                        user_id, course.course_id)
                for i in res:
                    assignment = Assignment()
                    assignment.assignment_id = i.get('assignment_id')
                    assignment.student_id = user_id
                    if i.get('submission'):
                        assignment.score = i.get('submission').get('score')
                    if i.get('due_at'):
                        assignment.due_at = \
                            datetime.strptime(i.get('due_at'),
                                              "%Y-%m-%dT%H:%M:%S%z")
                    assignment.points_possible = i.get('points_possible')
                    assignment.status = i.get('status')
                    assignments.append(assignment)
            except DataFailureException as e:
                self.logger.error(e)
                continue
        return assignments

    def get_participation(self, course_id):
        analytics = Analytics()
        course = self.get_course(course_id)
        students_ids = self._get_student_ids_for_course(course)
        participations = []
        for user_id in students_ids:
            try:
                res = analytics.get_student_summaries_by_course(
                        course.course_id, student_id=user_id)
                for i in res:
                    partic = Participation()
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
