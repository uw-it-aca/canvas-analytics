from uw_canvas.users import Users
from uw_canvas.quizzes import Quizzes
import re


def collect_analytics_for_sis_course_id(course_id, time_period):
    q = Quizzes()

    course_id = re.sub("--$", "", course_id)
    quizzes = q.get_quizzes_by_sis_id(course_id)

    login_by_id = {}
    return_values = []
    for quiz in quizzes:
        per_user_counts = {}
        quiz_id = quiz.quiz_id
        submissions = q.get_submissions_for_sis_course_id_and_quiz_id(
            course_id, quiz_id)
        for s in submissions["quiz_submissions"]:
            if s["user_id"] not in login_by_id:
                login = "unknown_user_%s" % s["user_id"]
                try:
                    user = Users().get_user(s["user_id"])
                    login = user.login_id
                except Exception:
                    pass
                login_by_id[s["user_id"]] = login

            login_name = login_by_id[s["user_id"]]
            if login_name not in per_user_counts:
                per_user_counts[login_name] = 0

            per_user_counts[login_name] = per_user_counts[login_name] + 1
            score = s["kept_score"]
            possible = s["quiz_points_possible"]

            return_values.append({
                "login_name": login_by_id[s["user_id"]],
                "type": "Quiz - %s - Points Possible" % quiz.title,
                "value": possible,
            })

            try:
                return_values.append({
                    "login_name": login_by_id[s["user_id"]],
                    "type": "Quiz - %s - Percentage Score" % quiz.title,
                    "value": (float(score) / float(possible)) * 100.0,
                })
            except Exception:
                return_values.append({
                    "login_name": login_by_id[s["user_id"]],
                    "type": "Quiz - %s - Points" % quiz.title,
                    "value": score,
                })

        for login_name in per_user_counts:
            return_values.append({
                "login_name": login_name,
                "type": "Quiz Submissions Count - %s" % quiz.title,
                "value": per_user_counts[login_name],
            })
    return return_values
