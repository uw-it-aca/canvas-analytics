# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.core.management.base import BaseCommand
from data_aggregator.dao import TaskDAO


class Command(BaseCommand):

    help = ("Creates current term and all future terms.")

    def add_arguments(self, parser):
        parser.add_argument("--sis_term_id",
                            type=str,
                            help=("Starting term to create db entries for. "
                                  "(defaults to current term)"),
                            default=None,
                            required=False)

    def handle(self, *args, **options):
        sis_term_id = options["sis_term_id"]
        TaskDAO().create_terms(sis_term_id=sis_term_id)
