from uw_canvas.assignments import Assignments
from uw_canvas.users import Users
import re


def collect_analytics_for_sis_course_id(course_id, time_period):
    users_sis_id = re.sub("--$", "", course_id)
    users = Users().get_users_for_sis_course_id(users_sis_id)

    assignments = Assignments().get_assignments_by_sis_id(course_id)
    return_values = []

    for user in users:
        for assignment in assignments:
            return_values.append({
                "login_name": user.login_id,
                "type": "Assignment Due Date - %s" % assignment.name,
                "value": str(assignment.due_at)
            })

    return return_values
