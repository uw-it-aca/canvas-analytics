from uw_canvas.assignments import Assignments
from uw_canvas.users import Users
import re


def collect_analytics_for_sis_course_id(course_id, time_period):
    assignments = Assignments().get_assignments_by_sis_id(course_id)

    person_map = {}
    return_values = []
    for assignment in assignments:
        per_user_counts = {}
        url = "/api/v1/courses/sis_course_id:%s/assignments/%s/submissions/" % (course_id, assignment.assignment_id)
        submissions = Assignments()._get_resource(url)
        for submission in submissions:
            user_id = submission['user_id']
            if user_id not in person_map:
                login = "unknown_user_%s" % (user_id)
                try:
                    user = Users().get_user(user_id)
                    login = user.login_id
                except Exception as ex:
                    pass
                person_map[user_id] = login

            if person_map[user_id] not in per_user_counts:
                per_user_counts[person_map[user_id]] = 0

            per_user_counts[person_map[user_id]] = per_user_counts[person_map[user_id]] + 1

        for user in per_user_counts:
            return_values.append({
                "login_name": user,
                "type": "Assignment submission count for %s" % (assignment.name),
                "value": per_user_counts[user],
            })

    return return_values
