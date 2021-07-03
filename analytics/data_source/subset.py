from uw_canvas import Canvas
from uw_canvas.reports import Reports
from uw_sws.term import get_current_term


def get_all_course_sis_ids():
    # provisioning_csv
    # Root account name - uwcourse
    account_name = "uwcourse"

    # But we can't use sis_account_id:uwcourse - it gets us a 401.  So lookup
    # the account id.
    account_info = \
        Canvas()._get_resource(
            f"/api/v1/accounts/sis_account_id:{account_name}")
    account_id = account_info["root_account_id"]

    current_sws_term = get_current_term()
    current_sis_id = f"{current_sws_term.year}-{current_sws_term.quarter}"

    terms = Canvas()._get_resource(f"/api/v1/accounts/{account_id}/terms",
                                   data_key="enrollment_terms")

    current_term = None
    for term in terms["enrollment_terms"]:
        if term["sis_term_id"] == current_sis_id:
            current_term = term
            break

    report = Reports().create_report(
        "provisioning_csv", account_id, term['id'],
        params={"enrollments": "true"})

    data = Reports().get_report_data(report)
    print("Data: {}".format(data))
    print("Current term: {}".format(current_term))
