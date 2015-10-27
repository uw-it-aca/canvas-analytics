from dateutil import parser
from datetime import datetime
from restclients.canvas.reports import Reports
from restclients.canvas import Canvas
from restclients.sws import SWS
from restclients.dao_implementation.canvas import Live
from django.conf import settings

def get_all_course_sis_ids():
    return settings.ANALYTICS_SIS_COURSE_IDS

    # We originally thought it would be all courses!  Dead code below :(

    # Root account name - uwcourse
    account_name = "uwcourse"

    # But we can't use sis_account_id:uwcourse - it gets us a 401.  So lookup
    # the account id.
    account_info = Canvas()._get_resource("/api/v1/accounts/sis_account_id:%s" % (account_name))
    account_id = account_info["root_account_id"]

    current_sws_term = SWS().get_current_term()
    print "Term: ", current_sws_term.year, current_sws_term.quarter

    current_sis_id = "%s-%s" % (current_sws_term.year, current_sws_term.quarter)

    terms = Canvas()._get_resource("/api/v1/accounts/%s/terms" % (account_id), data_key="enrollment_terms")

    now = datetime.now()
    current_term = None
    for term in terms["enrollment_terms"]:
        if term["sis_term_id"] == current_sis_id:
            current_term = term
            break

    report = Reports().create_report("provisioning_csv", account_id, term['id'], params={"sections":"true" })

    data = Reports().get_report_data(report)
    courses = []
    for section in data:
        try:
            values = section.split(",")
            sis_id = values[1]

            courses.append(sis_id)
#            if "ENGL-13" in sis_id:
#                courses.append(sis_id)

        except Exception as ex:
            pass

    return courses
    raise Exception("Done")
    data = Canvas()._get_resource("/api/v1/accounts/sis_account_id:uwcourse/courses?enrollment_term_id=%s&with_enrollments=true&per_page=100" % (current_term["id"]))

    sis_course_ids = []
    for course in data:
        try:
            sis_id = course["sis_course_id"]
            sis_course_ids.append(sis_id)
        except:
            pass

    # Trying to approximate ODCP class volumes...
    limit = 20
    courses = []
    for course in sis_course_ids:
        if "ENGL-13" in sis_course_ids:
            courses.append(course)

    return courses

