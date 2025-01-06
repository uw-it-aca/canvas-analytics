# Copyright 2025 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


from data_aggregator.management.commands._base import CreateJobCommand


class Command(CreateJobCommand):

    help = ("Create job(s) for the specified job type.")

    def handle(self, *args, **options):
        """
        Creates jobs to be processed
        """
        self.create(options)
