from dateutil import parser
from datetime import datetime
from restclients.canvas.reports import Reports
from restclients.canvas import Canvas
from restclients.sws import SWS
from restclients.dao_implementation.canvas import Live

def get_all_course_sis_ids():
#    return ['2014-autumn-JSIS A-435-A']
#    return ['2014-autumn-ECFS-311-A']
    return ['2015-winter-ECFS-301-C',
            '2015-winter-ECFS-303-C',
            '2015-winter-ECFS-401-A',
            '2015-winter-ECFS-411-B',
            '2015-winter-ECFS-455-B',
            '2015-winter-NSG-432-A',
            '2015-winter-AES-489-B',
            '2015-winter-ANTH-478-A',
            '2015-winter-COM-220-B',
            '2015-winter-COM-468-C',
            '2015-winter-COM-489-B',
            '2015-winter-ECON-201-F',
            '2015-winter-GWSS-489-B',
            '2015-winter-ISS-355-A',
            '2015-winter-JSIS B-406-A',
            '2015-winter-JSIS B-416-A',
            '2015-winter-LSJ-327-A',
            '2015-winter-PHIL-343-B',
            '2015-winter-POL S-327-A',
            '2015-winter-POL S-432-A',
            '2015-winter-SOC-362-C']
#    return ['2015-spring-PSYCH-101-A', '2014-spring-BIOST-513-A']
##    return ['2014-spring-AFRAM-260-A--']
#    return ['2014-spring-LIS-590-A']
#    return ['2014-spring-ENGL-131-A1']
#    return ['2014-winter-ASTR-101-A']
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

