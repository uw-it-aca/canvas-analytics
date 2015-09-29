from restclients.canvas import Canvas
from restclients.canvas.sections import Sections
from restclients.canvas.enrollments import Enrollments

def get_all_person_sis_ids(course_ids):
    person_ids = {}
    for course_id in course_ids:
        print "CID: ", course_id
        try:
            #enrollments = Enrollments().get_enrollments_for_course_by_sis_id(course_id)
            print "Using section id: %s--" % course_id
            enrollments = Enrollments().get_enrollments_for_section_by_sis_id("%s--" % course_id)
            for enrollment in enrollments:
                try:
                    print "L: ", enrollment.login_id
                    person_ids[enrollment.login_id] = True
                except Exception as ex:
                    print "No login_id for ", enrollment.user_id
        except Exception as ex:
            print "E: ", ex

    person_list = []
    for person in person_ids:
        person_list.append(person)

    return person_list

    return ['pmichaud', 'jlaney']
    # Change this to use the Last User Access report
    # Root account name - uwcourse
    account_name = "uwcourse"

    # But we can't use sis_account_id:uwcourse - it gets us a 401.  So lookup
    # the account id.
    account_info = Canvas()._get_resource("/api/v1/accounts/sis_account_id:%s" % (account_name))
    account_id = account_info["root_account_id"]

    person_data = Canvas()._get_resource("/api/v1/accounts/%s/users?per_page=100" % (account_id))

    user_ids = []
    for person in person_data:
        user_ids.append(person["sis_user_id"])

    print "IDs: ", user_ids



