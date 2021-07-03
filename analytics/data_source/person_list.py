from uw_canvas.enrollments import Enrollments


def get_all_person_sis_ids(course_ids):
    person_ids = {}
    for course_id in course_ids:
        try:
            enrollments = \
                Enrollments().get_enrollments_for_section_by_sis_id(
                     f"{course_id}--")
            for enrollment in enrollments:
                try:
                    person_ids[enrollment.login_id] = True
                except Exception:
                    print("No login_id for {}".format(enrollment.user_id))
        except Exception as ex:
            print("Error: {}".format(ex))

    person_list = []
    for person in person_ids:
        person_list.append(person)

    return person_list
