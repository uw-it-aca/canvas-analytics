# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

import csv
from django.db import transaction
from django.test import override_settings
from logging import getLogger
from data_aggregator.models import Report, SubaccountActivity
from data_aggregator.utilities import set_gcs_base_path
from data_aggregator.exceptions import TermNotStarted
from restclients_core.util.retry import retry
from restclients_core.exceptions import DataFailureException
from uw_canvas.accounts import Accounts as CanvasAccounts
from uw_canvas.analytics import Analytics as CanvasAnalytics
from uw_canvas.reports import Reports as CanvasReports
from uw_canvas.terms import Terms as CanvasTerms

logger = getLogger(__name__)

RETRY_STATUS_CODES = [0, 408, 500, 502, 503, 504]
RETRY_MAX = 5
RETRY_DELAY = 5


class ReportBuilder():
    def __init__(self):
        self._accounts = CanvasAccounts(per_page=100)
        self._analytics = CanvasAnalytics()
        self._reports = CanvasReports()
        self._terms = CanvasTerms()

    @retry(DataFailureException, status_codes=RETRY_STATUS_CODES,
           tries=RETRY_MAX, delay=RETRY_DELAY, logger=logger)
    def get_statistics_by_account(self, sis_account_id, sis_term_id):
        return self._analytics.get_statistics_by_account(
            sis_account_id, sis_term_id)

    @retry(DataFailureException, status_codes=RETRY_STATUS_CODES,
           tries=RETRY_MAX, delay=RETRY_DELAY, logger=logger)
    def get_activity_by_account(self, sis_account_id, sis_term_id):
        return self._analytics.get_activity_by_account(
            sis_account_id, sis_term_id)

    @retry(DataFailureException, status_codes=RETRY_STATUS_CODES,
           tries=RETRY_MAX, delay=RETRY_DELAY, logger=logger)
    def get_account_activities_data(self, root_account, sis_term_id):
        activities = []
        accounts = []
        accounts.append(root_account)
        accounts.extend(
            self._accounts.get_all_sub_accounts_by_sis_id(
                root_account.sis_account_id))
        activities = []
        for account in accounts:
            sis_account_id = account.sis_account_id
            if sis_account_id is None:
                continue
            activity = SubaccountActivity(term_id=sis_term_id,
                                          subaccount_id=sis_account_id,
                                          subaccount_name=account.name)

            data = self.get_statistics_by_account(sis_account_id, sis_term_id)

            for key, val in data.items():
                if key == "courses":
                    continue
                setattr(activity, key, val)
            try:
                data = self.get_activity_by_account(sis_account_id,
                                                    sis_term_id)
                for item in data["by_category"]:
                    setattr(activity,
                            "{}_views".format(item["category"]),
                            item["views"])
            except DataFailureException as ex:
                if ex.status != 504:
                    raise
            activities.append(activity)
        return activities

    def get_xlist_courses(self, root_account, sis_term_id):
        # create xlist lookup
        term = self._terms.get_term_by_sis_id(sis_term_id)
        xlist_courses = set()
        xlist_prov_report = self._reports.create_xlist_provisioning_report(
            root_account.account_id, term.term_id,
            params={"include_deleted": True})

        xlist_data_file = self._reports.get_report_data(xlist_prov_report)
        reader = csv.reader(xlist_data_file)
        next(reader, None)  # skip the headers
        for row in reader:
            if not len(row):
                continue
            sis_course_id = row[6]
            if sis_course_id:
                xlist_courses.add(sis_course_id)
        self._reports.delete_report(xlist_prov_report)
        return xlist_courses

    def get_course_data(self, root_account, sis_term_id):
        # create course totals lookup
        term = self._terms.get_term_by_sis_id(sis_term_id)
        course_prov_report = self._reports.create_course_provisioning_report(
            root_account.account_id, term.term_id,
            params={"include_deleted": True})
        course_data_file = self._reports.get_report_data(course_prov_report)
        course_data = []
        reader = csv.reader(course_data_file)
        next(reader, None)  # skip the headers
        for row in reader:
            if not len(row):
                continue
            course_data.append(row)
        self._reports.delete_report(course_prov_report)
        return course_data

    @transaction.atomic
    @override_settings(RESTCLIENTS_CANVAS_TIMEOUT=90)
    def build_subaccount_activity_report(self, root_account_id,
                                         sis_term_id=None, week_num=None):
        try:
            report = Report.objects.get_or_create_report(
                Report.SUBACCOUNT_ACTIVITY,
                sis_term_id=sis_term_id,
                week_num=week_num)
        except TermNotStarted as ex:
            logger.info("Term {} not started".format(ex))
            return

        set_gcs_base_path(report.term_id, report.term_week)

        root_account = self._accounts.get_account_by_sis_id(root_account_id)

        account_courses = {}

        # save activities and initialize course totals
        activity_data = self.get_account_activities_data(root_account,
                                                         report.term_id)
        for activity in activity_data:
            account_courses[activity.subaccount_id] = {
                "courses": 0,
                "active_courses": 0,
                "ind_study_courses": 0,
                "active_ind_study_courses": 0,
                "xlist_courses": 0,
                "xlist_ind_study_courses": 0
            }

            activity.report = report
            activity.save()

        # calculate course totals
        xlist_courses = self.get_xlist_courses(root_account, report.term_id)
        course_data = self.get_course_data(root_account, report.term_id)
        for row in course_data:
            if not len(row):
                continue

            sis_course_id = row[1]
            sis_account_id = row[6]
            if (sis_course_id is None or sis_account_id is None or
                    sis_account_id not in account_courses):
                continue

            status = row[9]
            ind_study = (len(sis_course_id.split("-")) == 6)
            is_xlist = (sis_course_id in xlist_courses)
            is_active = (status == "active")
            for sis_id in account_courses.keys():
                if sis_account_id.find(sis_id) == 0:
                    account_courses[sis_id]["courses"] += 1
                    if is_xlist:
                        account_courses[sis_id]["xlist_courses"] += 1
                    elif is_active:
                        account_courses[sis_id]["active_courses"] += 1

                    if ind_study:
                        account_courses[sis_id][
                            "ind_study_courses"] += 1
                        if is_xlist:
                            account_courses[sis_id][
                                "xlist_ind_study_courses"] += 1
                        elif is_active:
                            account_courses[sis_id][
                                "active_ind_study_courses"] += 1

        # save course totals
        for sis_account_id in account_courses:
            try:
                totals = account_courses[sis_account_id]
                activity = SubaccountActivity.objects.get(
                    report=report, term_id=report.term_id,
                    subaccount_id=sis_account_id)
                activity.courses = totals["courses"]
                activity.active_courses = totals["active_courses"]
                activity.ind_study_courses = totals["ind_study_courses"]
                activity.active_ind_study_courses = \
                    totals["active_ind_study_courses"]
                activity.xlist_courses = totals["xlist_courses"]
                activity.xlist_ind_study_courses = \
                    totals["xlist_ind_study_courses"]
                activity.save()
            except SubaccountActivity.DoesNotExist:
                continue

        report.finished()
