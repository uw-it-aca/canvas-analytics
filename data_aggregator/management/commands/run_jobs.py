# Copyright 2022 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from data_aggregator.management.commands._base import RunJobCommand


class Command(RunJobCommand):

    help = ("Run job(s) for the specified job type.")
