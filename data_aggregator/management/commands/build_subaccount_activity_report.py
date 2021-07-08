# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from data_aggregator.report_builder import ReportBuilder
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create report of subaccount activity."

    def add_arguments(self, parser):
        parser.add_argument(
            '-a', '--account', action='store', dest='subaccount_id',
            default='uwcourse', help='Subaccount sis_id for the report')
        parser.add_argument(
            '-t', '--term', action='store', dest='term_id', default='',
            help='Term sis_id for the report')

    def handle(self, *args, **options):
        report_builder = ReportBuilder()

        subaccount_id = options['subaccount_id']
        term_id = options['term_id']

        report_builder.build_subaccount_activity_report(subaccount_id, term_id)
