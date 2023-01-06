# Copyright 2023 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0


import re
from gcs_clients import RestclientGCSClient

FOREVER = 0


class DataAggregatorGCSCache(RestclientGCSClient):

    def get_cache_expiration_time(self, service, url, status=None):
        if status != 200:
            return None
        if "canvas" == service:
            if re.match(r'^.*/api/v1/.*/analytics.*', url):
                return FOREVER
