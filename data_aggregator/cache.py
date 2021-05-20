# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from gcs_clients import RestclientGCSClient

FOREVER = 0


class DataAggregatorGCSCache(RestclientGCSClient):

    def get_cache_expiration_time(self, service, url, status=None):
        if "canvas" == service:
            return FOREVER
