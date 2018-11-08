from uw_canvas import Canvas
from django.utils import timezone
import traceback
from restclients_core.exceptions import DataFailureException
from uw_canvas.analytics import Analytics
from uw_canvas.users import Users
from dateutil import parser
import datetime
import re


def collect_analytics_for_sis_course_id(course_id, time_period):
    users_sis_id = re.sub("--$", "", course_id)
    users = Users().get_users_for_sis_course_id(users_sis_id)
    analytics = Analytics()
    course_id = re.sub("--$", "", course_id)

    return_values = []

    for user in users:
        person_id = user.user_id

        ontime_count = 0
        late_count = 0
        missing_count = 0
        # If an enrollment doesn't have assignments, this is a 404.
        # XXX - is this only when there are no assignments?
        try:
            assignment_data = Analytics().get_student_assignments_for_sis_course_id_and_canvas_user_id(course_id, person_id)
            for assignment in assignment_data:
                if "Lesson 08 Presentation 8-1 (9:43)" == assignment["title"]:
                    print("Title: {}".format(assignment["title"]))
                missing_assignment = True
                if "submission" in assignment:
                    if assignment["status"] != "missing":
                        return_values.append({
                            "login_name": user.login_id,
                            "type": "Missing Assignment - %s" % assignment["title"],
                            "value": "0"
                        })

                    get_days_late = False
                    if assignment["status"] == "on_time":
                        missing_assignment = False
                        ontime_count += 1
                    elif assignment["status"] == "late":
                        missing_assignment = False
                        get_days_late = True
                        late_count += 1
                    elif assignment["status"] == "missing":
                        get_days_late = True
                        missing_count += 1
                        return_values.append({
                            "login_name": user.login_id,
                            "type": "Missing Assignment - %s" % assignment["title"],
                            "value": "1"
                        })

                    return_values.append({
                        "login_name": user.login_id,
                        "type": "Assignment submission date - %s" % assignment["title"],
                        "value": assignment["submission"]["submitted_at"],
                    })
                    # Get the number of days late an assignment is...
                    if get_days_late:
                        try:
                            date_due = parser.parse(assignment["due_at"])
                            date_against = None  # Either the day turned in, or today
                            if assignment["status"] == "late":
                                date_against = parser.parse(assignment["submission"]["submitted_at"])
                            elif assignment["status"] == "missing":
                                date_against = timezone.now()

                            delta = (date_against - date_due).days

                            late_assignment_data = {
                                "login_name": user.login_id,
                                "type": "Assignment - %s - days late" % assignment["title"],
                                "value": delta,
                            }
                            return_values.append(late_assignment_data)

                        except Exception as ex:
                            print("Error: {}".format(ex))
                            # Maybe the due date isn't parseable?
                            pass

                    else:
                        late_assignment_data = {
                            "login_name": user.login_id,
                            "type": "Assignment - %s - days late" % assignment["title"],
                            "value": 0,
                        }
                        return_values.append(late_assignment_data)

                    # This is for scores.  I *think* each assignment is points-based, with different displays.
                    # This tries to turn them into a percentage, so there's some normalization.  If that fails,
                    # It'll return a raw score instead, which hopefully covers any other bad assumptions made.
                    try:
                        missing_assignment = False
                        score = assignment["submission"]["score"]
                        possible = assignment["points_possible"]

                        assignment_grade_data = {
                            "login_name": user.login_id,
                            "type": "Assignment - %s - Points Possible" % assignment["title"],
                            "value": possible
                        }
                        return_values.append(assignment_grade_data)

                        # Should this record a blank score instead?
                        if score is None:
                            score = 0

                        if possible is None or possible == 0:
                            assignment_grade_data = {
                                "login_name": user.login_id,
                                "type": "Assignment - %s - Points" % assignment["title"],
                                "value": score
                            }
                        else:
                            assignment_grade_data = {
                                "login_name": user.login_id,
                                "type": "Assignment - %s - Percentage Score" % assignment["title"],
                                "value": (float(score) / float(possible)) * 100.0
                            }
                        return_values.append(assignment_grade_data)

                    except Exception as ex:
                        print("Assignment: {}".format(assignment["title"]))
                        print("Score: {}, Possible: {}".format(score, possible))
                        print("Error: {}".format(ex))
                        assignment_grade_data = {
                            "login_name": user.login_id,
                            "type": "Assignment - %s - ERROR" % assignment["title"],
                            "value": str(ex)
                        }
                        return_values.append(assignment_grade_data)
                        # @lyle3: ok, thanks. Could you only include percentage score in the spreadsheet? Even though I told Decisive Data to ignore "score" and "percentage", I got a flurry of questions about these fields.
#                        score = assignment["submission"]["score"]
#
#                        assignment_grade_data = {
#                            "login_name": user.login_id,
#                            "type": "Assignment - %s - Score" % assignment["title"],
#                            "value": score
#                        }
#                        return_values.append(assignment_grade_data)

                else:
                    missing_count += 1
                    assignment_grade_data = {
                        "login_name": user.login_id,
                        "type": "Assignment - %s - Percentage" % assignment["title"],
                        "value": 0
                    }
                    #  @lyle3: ok, thanks. Could you only include percentage score in the spreadsheet? Even though I told Decisive Data to ignore "score" and "percentage", I got a flurry of questions about these fields.
                    # return_values.append(assignment_grade_data)
                    return_values.append({
                        "login_name": user.login_id,
                        "type": "Missing Assignment - %s" % assignment["title"],
                        "value": "1"
                    })

                    try:
                        date_due = parser.parse(assignment["due_at"])
                        date_against = datetime.datetime.now()

                        delta = (date_against - date_due).days

                        late_assignment_data = {
                            "login_name": user.login_id,
                            "type": "Assignment - %s - days late" % assignment["title"],
                            "value": delta,
                        }
                        return_values.append(late_assignment_data)

                    except Exception as ex:
                        pass

            return_values.append({
                "login_name": user.login_id,
                "type": "ontime_assignments",
                "value": ontime_count,
            })

            return_values.append({
                "login_name": user.login_id,
                "type": "late_assignments",
                "value": late_count,
            })

            return_values.append({
                "login_name": user.login_id,
                "type": "missing_assignments",
                "value": missing_count,
            })

            # Use "status" for on time, late.
            # "submission"["submitted_at"] and "due_at" for days_late
            # "score" for score - include "max_score"?
        except DataFailureException as ex:
            pass
        except Exception as e2:
            print("Error: {}".format(e2))
            print(traceback.format_exc())

    return return_values
