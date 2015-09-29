from restclients.dao_implementation.canvas import Live
from restclients.canvas.page_views import PageViews
from restclients.canvas.assignments import Assignments
from restclients.canvas.quizzes import Quizzes
import re
import json


def collect_analytics_for_sis_person_id(person_id, time_period):
    return_values = []
    try:
        data = PageViews().get_pageviews_for_sis_login_id_from_start_date(person_id, time_period.start_date.strftime("%Y-%m-%d"))

        others = 0

        counts_by_page_type = {}
        user_assignment_views = {}
        user_submitted_assignment_views = {}
#        counts_by_page_type["assignments"] = 0
#        counts_by_page_type["collaboration"] = 0
#        counts_by_page_type["conference"] = 0
#        counts_by_page_type["discussion"] = 0
#        counts_by_page_type["general"] = 0
#        counts_by_page_type["module"] = 0
#        counts_by_page_type["quizzes"] = 0
        for entry in data:
            url = entry["url"]

            if not url.startswith("https://canvas.uw.edu/courses/"):
                continue

            try:
                course_id = re.match("https://canvas.uw.edu/courses/([\d]+).*", url).group(1)
                _add_course_id(counts_by_page_type, course_id)
            except Exception as ex:
                print "Error: ", url

            controller = entry["controller"]

            if "discussion_topics" == controller:
                counts_by_page_type[course_id]["discussion"] += 1
            elif "assignments" == controller or "submissions" == controller:
                counts_by_page_type[course_id]["assignments"] += 1

                if re.match("https://canvas.uw.edu/courses/([\d]+)/assignments/([\d]+)/submissions", url):
                    try:
                        assignment_id = re.match("https://canvas.uw.edu/courses/([\d]+)/assignments/([\d]+)", url).group(2)
                        if not course_id in user_submitted_assignment_views:
                            user_submitted_assignment_views[course_id] = {}
                        if not assignment_id in user_submitted_assignment_views[course_id]:
                            user_submitted_assignment_views[course_id][assignment_id] = 0

                        current = user_submitted_assignment_views[course_id][assignment_id]
                        user_submitted_assignment_views[course_id][assignment_id] = current + 1
                    except Exception as ex:
                        print "Oops: ", ex

                elif re.match("https://canvas.uw.edu/courses/([\d]+)/assignments/([\d]+)", url):
                    try:
                        assignment_id = re.match("https://canvas.uw.edu/courses/([\d]+)/assignments/([\d]+)", url).group(2)
                        if not course_id in user_assignment_views:
                            user_assignment_views[course_id] = {}
                        if not assignment_id in user_assignment_views[course_id]:
                            user_assignment_views[course_id][assignment_id] = 0

                        current = user_assignment_views[course_id][assignment_id]
                        user_assignment_views[course_id][assignment_id] = current + 1
                    except Exception as ex:
                        print "Oops: ", ex

            elif "courses" == controller:
                counts_by_page_type[course_id]["general"] += 1
            elif "collaborations" == controller:
                counts_by_page_type[course_id]["collaboration"] += 1
            elif "quizzes/quizzes" == controller:
                counts_by_page_type[course_id]["quizzes"] += 1
            elif "conferences" == controller:
                counts_by_page_type[course_id]["conference"] += 1
            elif "context_modules" == controller:
                counts_by_page_type[course_id]["module"] += 1
            elif "announcements" == controller:
                counts_by_page_type[course_id]["announcements"] += 1
            elif "files" == controller and "module_item_id" in url:
                counts_by_page_type[course_id]["module"] += 1
            elif "files" == controller:
                counts_by_page_type[course_id]["files"] += 1
            elif "gradebooks" == controller:
                counts_by_page_type[course_id]["grades"] += 1
            elif controller in ["courses", "wiki_pages"]:
                counts_by_page_type[course_id]["pages"] += 1

            elif controller in ["context", "external_tools"]:
                counts_by_page_type[course_id]["other"] += 1
            else:
                counts_by_page_type[course_id]["other"] += 1
                print "P: ", person_id, " C: ", entry["controller"]
                print "E: ", entry


        for course_id in counts_by_page_type:
            for page_type in counts_by_page_type[course_id]:
                return_values.append({
                    "course_canvas_id": course_id,
                    "type": "Page Views - %s" % page_type,
                    "value": counts_by_page_type[course_id][page_type],
                })

        for course_id in user_assignment_views:
            for assignment_id in user_assignment_views[course_id]:
                assignment = get_assignment_by_course_id_and_assignment_id(course_id, assignment_id)

                name = assignment.name
#            print "Name: ", assignment_lookup[assignment_id]
                return_values.append({
                    "course_canvas_id": course_id,
                    "type": "Assignment Views - %s" % name,
                    "value": user_assignment_views[course_id][assignment_id],
                })

        for course_id in user_submitted_assignment_views:
            for assignment_id in user_submitted_assignment_views[course_id]:
                assignment = get_assignment_by_course_id_and_assignment_id(course_id, assignment_id)

                name = assignment.name
#            print "Name: ", assignment_lookup[assignment_id]
                return_values.append({
                    "course_canvas_id": course_id,
                    "type": "Assignment Submission Views - %s" % name,
                    "value": user_submitted_assignment_views[course_id][assignment_id],
                })

    except Exception as ex:
        print "Error: ", ex

    return return_values

def _add_course_id(counts, course_id):
    if course_id in counts:
        return
    counts[course_id] = {}
    counts[course_id]["assignments"] = 0
    counts[course_id]["collaboration"] = 0
    counts[course_id]["conference"] = 0
    counts[course_id]["discussion"] = 0
    counts[course_id]["general"] = 0
    counts[course_id]["module"] = 0
    counts[course_id]["quizzes"] = 0
    counts[course_id]["announcements"] = 0
    counts[course_id]["files"] = 0
    counts[course_id]["grades"] = 0
    counts[course_id]["pages"] = 0
    counts[course_id]["other"] = 0


def get_assignment_by_course_id_and_assignment_id(course_id, assignment_id):
    assign = Assignments()
    url = "/api/v1/courses/%s/assignments/%s" % (course_id, assignment_id)
    data = assign._get_resource(url)

    return assign._assignment_from_json(data)


