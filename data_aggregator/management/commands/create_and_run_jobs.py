# Copyright 2022 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from data_aggregator.management.commands._base import CreateJobCommand
from data_aggregator.management.commands._mixins import RunJobMixin


class Command(CreateJobCommand, RunJobMixin):

    help = ("Create job(s) for the specified job type and runs them.")

    def handle(self, *args, **options):
        """
        Creates jobs to be processed and runs them
        """
        jobs = self.create(options)
        for job in jobs:
            job.claim_job()
            self.run_job(job)
