from uw_canvas.discussions import Discussions
from uw_canvas.users import Users
import json
import re

def collect_analytics_for_sis_course_id(course_id, time_period):
    api = Discussions()
    users_sis_id = re.sub("--$", "", course_id)
    users = Users().get_users_for_sis_course_id(users_sis_id)

    course_id = re.sub("--$", "", course_id)
    login_by_id = {}
    counts_by_id = {}
    for user in users:
        login_by_id[user.user_id] = user.login_id
        counts_by_id[user.login_id] = 0

    topics = api.get_discussion_topics_for_sis_course_id(course_id)

    for topic in topics:
        entries = api.get_entries_for_topic(topic)
        for entry in entries:
            if entry.user_id not in login_by_id:
                login = "unknown_user_%s" % entry.user_id
                try:
                    user = Users().get_user(entry.user_id)
                    login = user.login_id
                except Exception as ex:
                    pass
                login_by_id[user.user_id] = login
                counts_by_id[login] = 0
            try:
                counts_by_id[login_by_id[entry.user_id]] += 1
            except Exception as ex:
                print "Error on ", entry.user_id, ex

    return_values = []

    for key in counts_by_id:
        return_values.append({
            "login_name": key,
            "type": "Discussion Board Posts",
            "value": counts_by_id[key],
        })


    return return_values
