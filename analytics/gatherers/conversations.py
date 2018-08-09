from uw_canvas import Canvas
from uw_canvas.courses import Courses
from uw_canvas.groups import Groups
from uw_canvas.enrollments import Enrollments
from uw_canvas.models import CanvasEnrollment
from uw_canvas.conversations import Conversations
from random import random
import re
import json

__conversations_run_id = None
__conversation_data = {}


def collect_analytics_for_sis_person_id(person_id, time_period):
    return []
    # This is tricky!  We can only reliably get message *to* a user.  If I start
    # a conversation w/ a person, and they don't reply, that message shows up
    # for them, but not in my own search.  I don't think there's any way to do
    # a listing of the "Sent" view of conversations.  :(

    # If canvas only had one-on-one conversations, that would be the end of it.
    # But - there can be group conversations, so we need to make sure to not
    # double-count messages.  So, this will track an arbitrary __conversations_run_id, post_id,
    # and sender_id, and we'll need to aggregate that data after all users
    # have been processed.
    # XXX - expand the api definition to allow for that.

    global __conversation_data

    global __conversations_run_id
    if __conversations_run_id is None:
        __conversations_run_id = int(random() * 10000000)

    conversation_ids = Conversations().get_conversation_ids_for_sis_login_id(person_id)
    for conversation_id in conversation_ids:
        conversation = Conversations().get_data_for_conversation_id_as_sis_login_id(conversation_id, person_id)

        participants = conversation["participants"]
        context_name = conversation["context_name"]
        pids = []
        for participant in participants:
            pids.append(int(participant["id"]))

        if context_name not in __conversation_data:
            __conversation_data[context_name] = {}

        for message in conversation["messages"]:
            author_pid = int(message["author_id"])
            message_id = message["id"]
            for pid in pids:
                if pid != author_pid:
                    # Always put the author first - we only care about
                    # the messages that someone sends, not that they receive
                    if author_pid not in __conversation_data[context_name]:
                        __conversation_data[context_name][author_pid] = {}

                    if pid not in __conversation_data[context_name][author_pid]:
                        __conversation_data[context_name][author_pid][pid] = {}

                    __conversation_data[context_name][author_pid][pid][message_id] = True

    return []


def post_process(course_ids):
    global __conversation_data

    cid_for_name = {}
    role_in_course = {}
    peer_messages = {}
    instructor_messages = {}
    login_ids_for_user_ids = {}
    try:
        for cid in course_ids:
            raw_cid = cid
            cid = re.sub("--$", "", cid)
            course = Courses().get_course_by_sis_id(cid)
            cid_for_name[course.name] = cid

            instructor_messages[cid] = {}
            peer_messages[cid] = {}

            enrollments = Enrollments().get_enrollments_for_section_by_sis_id(raw_cid)
            for enrollment in enrollments:
                if enrollment.login_id not in role_in_course:
                    role_in_course[enrollment.user_id] = {}
                role_in_course[enrollment.user_id][cid] = enrollment.role
                instructor_messages[cid][enrollment.user_id] = 0
                peer_messages[cid][enrollment.user_id] = 0
                login_ids_for_user_ids[enrollment.user_id] = enrollment.login_id

            groups = Groups().get_groups_for_sis_course_id(cid)
            # XXX - haven't run analytics for a course using groups yet!

    except Exception as ex:
        pass
        # print "E: ", ex

    seen_keys = {}
    for key in __conversation_data:
        if key in cid_for_name:
            cid = cid_for_name[key]
            data = __conversation_data[key]
            for user1 in data:
                int_id = int(user1)
                role1 = role_in_course[int(user1)][cid]
                others = data[user1]
                for user2 in others:
                    found_match = False
                    user2 = int(user2)
                    role2 = role_in_course[int(user2)][cid]

                    if role1 == CanvasEnrollment.STUDENT:
                        if role2 == CanvasEnrollment.STUDENT:
                            peer_messages[cid][int_id] = peer_messages[cid][int_id] + 1
                            found_match = True
                        elif role2 == CanvasEnrollment.TA:
                            instructor_messages[cid][int_id] = instructor_messages[cid][int_id] + 1
                            found_match = True
                        elif role2 == CanvasEnrollment.TEACHER:
                            instructor_messages[cid][int_id] = instructor_messages[cid][int_id] + 1
                            found_match = True
                    elif role1 == CanvasEnrollment.TA:
                        # Wrong way, whatever
                        if role2 == CanvasEnrollment.STUDENT:
                            found_match = True
                    elif role1 == CanvasEnrollment.TEACHER:
                        # Wrong way, whatever
                        if role2 == CanvasEnrollment.STUDENT:
                            found_match = True

                    if not found_match:
                        pass
                        # print "R1: ", role1, role2, user1, user2

    return_values = []
    for cid in instructor_messages:
        class_messages = instructor_messages[cid]
        for sid in class_messages:
            if class_messages[sid] > 0:
                return_values.append({
                    "login_name": login_ids_for_user_ids[sid],
                    "course_id": cid,
                    "type": "Messsages to instructors",
                    "value": class_messages[sid],
                })

    for cid in peer_messages:
        class_messages = peer_messages[cid]
        for sid in class_messages:
            if class_messages[sid] > 0:
                return_values.append({
                    "login_name": login_ids_for_user_ids[sid],
                    "course_id": cid,
                    "type": "Messsages to students",
                    "value": class_messages[sid],
                })

    return return_values
