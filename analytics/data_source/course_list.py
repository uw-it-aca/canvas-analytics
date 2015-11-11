from analytics.models import ManagedCourseSISIDs


def get_all_course_sis_ids():
    data = []
    all_course_sis_ids = ManagedCourseSISIDs.objects.all()
    for val in sorted(all_course_sis_ids, key=lambda x: x.sis_id):
        data.append(val.sis_id)

    return data
