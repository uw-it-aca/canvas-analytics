from uw_canvas.authentications import Authentications


def collect_analytics_for_sis_person_id(person_id, time_period):
    try:
        count = (Authentications()
                 .get_authentication_count_for_sis_login_id_from_start_date(
                     person_id, time_period.start_date.strftime("%Y-%m-%d")))

        return [{"type": "All Logins", "value": count}]
    except Exception as ex:
        print("Error: {}".format(ex))
