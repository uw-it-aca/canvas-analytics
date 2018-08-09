from django.conf import settings
from django.utils.timezone import utc
from uw_canvas.accounts import Accounts as CanvasAccounts
from uw_canvas.analytics import Analytics as CanvasAnalytics
from uw_canvas.reports import Reports as CanvasReports
from uw_canvas.terms import Terms as CanvasTerms
from restclients_core.exceptions import DataFailureException
from analytics.models import Report, SubaccountActivity
from datetime import datetime
from time import sleep
import json
import csv


class ReportBuilder():
    def __init__(self):
        self._accounts = CanvasAccounts(per_page=50)
        self._analytics = CanvasAnalytics()
        self._reports = CanvasReports()

    def build_subaccount_activity_report(self, root_account_id, sis_term_id):
        report = Report(report_type=Report.SUBACCOUNT_ACTIVITY,
                        started_date=datetime.utcnow().replace(tzinfo=utc))
        report.save()

        accounts = []
        account_courses = {}

        root_account = self._accounts.get_account_by_sis_id(root_account_id)
        accounts.append(root_account)
        accounts.extend(self._accounts.get_all_sub_accounts_by_sis_id(root_account_id))

        for account in accounts:
            sis_account_id = account.sis_account_id
            if sis_account_id is None:
                continue

            account_courses[sis_account_id] = {
                "courses": 0,
                "active_courses": 0,
                "ind_study_courses": 0,
                "active_ind_study_courses": 0,
            }

            activity = SubaccountActivity(report=report,
                                          term_id=sis_term_id,
                                          subaccount_id=sis_account_id,
                                          subaccount_name=account.name)

            data = self._analytics.get_statistics_by_account(sis_account_id,
                                                             sis_term_id)

            for key, val in data.items():
                if key == "courses":
                    continue

                setattr(activity, key, val)

            data = self._analytics.get_activity_by_account(sis_account_id,
                                                           sis_term_id)

            for item in data["by_category"]:
                setattr(activity, "%s_views" % item["category"], item["views"])

            activity.save()

        # Generate course totals
        term = CanvasTerms().get_term_by_sis_id(sis_term_id)
        course_prov_report = self._reports.create_course_provisioning_report(
            root_account.account_id, term.term_id,
            params={"include_deleted": True})

        course_data = self._reports.get_report_data(course_prov_report)
        header = course_data.pop(0)
        for row in csv.reader(course_data):
            if not len(row):
                continue

            sis_course_id = row[1]
            sis_account_id = row[6]
            if (sis_course_id is None or sis_account_id is None or
                    sis_account_id not in account_courses):
                continue

            status = row[9]
            ind_study = True if len(sis_course_id.split("-")) == 6 else False
            is_active = True if status == "active" else False
            for sis_id in account_courses:
                if sis_account_id.find(sis_id) == 0:
                    account_courses[sis_id]["courses"] += 1
                    if is_active:
                        account_courses[sis_id]["active_courses"] += 1
                    if ind_study:
                        account_courses[sis_id]["ind_study_courses"] += 1
                        if is_active:
                            account_courses[sis_id]["active_ind_study_courses"] += 1

        # Save course totals
        for sis_account_id in account_courses:
            try:
                totals = account_courses[sis_account_id]
                activity = SubaccountActivity.objects.get(
                    report=report, term_id=sis_term_id,
                    subaccount_id=sis_account_id)
                activity.courses = totals["courses"]
                activity.active_courses = totals["active_courses"]
                activity.ind_study_courses = totals["ind_study_courses"]
                activity.active_ind_study_courses = totals["active_ind_study_courses"]
                activity.save()
            except SubaccountActivity.DoesNotExist:
                continue

        report.finished_date = datetime.utcnow().replace(tzinfo=utc)
        report.save()
