# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from data_aggregator.management.commands._base import CreateJobCommand
from data_aggregator.dao import AnalyticTypes


class Command(CreateJobCommand):

    help = ("Creates participation jobs for active courses in current term.")

    def handle(self, *args, **options):
        """
        Load participation jobs for all active courses in the current term
        """
        self.create(options, AnalyticTypes.participation)
