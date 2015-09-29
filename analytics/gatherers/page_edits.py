from restclients.canvas import Canvas
from restclients.canvas.users import Users
import json

def collect_analytics_for_sis_course_id(course_id, timeperiod):
    url = "/api/v1/courses/sis_course_id:%s/pages" % course_id
    data = Canvas()._get_resource(url)

    edit_counts = {}
    person_map = {}
    for page in data:
        rurl = "/api/v1/courses/sis_course_id:%s/pages/%s/revisions" % (course_id, page['url'])
        revision_data = Canvas()._get_resource(rurl)
        for revision in revision_data:
            surl = "/api/v1/courses/sis_course_id:%s/pages/%s/revisions/%s?summary=true" % (course_id, page['url'], revision['revision_id'])
            summary_data = Canvas()._get_resource(surl)

            if 'edited_by' in summary_data:
                editor_id = summary_data['edited_by']['id']
                if editor_id not in person_map:
                    login = "unknown_user_%s" % (editor_id)
                    try:
                        user = Users().get_user(editor_id)
                        login = user.login_id
                    except Exception as ex:
                        pass
                    person_map[editor_id] = login
                    edit_counts[login] = 0
                edit_counts[person_map[editor_id]] = edit_counts[person_map[editor_id]] + 1

    return_values = []
    for login in edit_counts:
        return_values.append({
            "login_name": login,
            "type": "Page Edits",
            "value": edit_counts[login],
        })

    return return_values
