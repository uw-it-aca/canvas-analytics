# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

import logging
import traceback
from data_aggregator.dao import JobDAO


class RunJobMixin():

    def work(self, job):
        '''
        Job work is performed here. Override this if you want something
        custom.
        '''
        JobDAO().run_job(job)

    def run_job(self, job):
        try:
            job.start_job()
            self.work(job)
            job.end_job()
        except Exception as err:
            # save error message if one occurs
            tb = traceback.format_exc()
            if tb:
                job.message = tb
                logging.error(tb)
            else:
                # Just in case the trace back is empty
                msg = f"Unknown exception occured: {err}"
                job.message = msg
                logging.error(msg)
            job.save()
        return job
