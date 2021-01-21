from .base_settings import *
import os

INSTALLED_APPS += [
    'data_aggregator.apps.DataAggregatorConfig',
]

if os.getenv('ENV') == 'localdev':
    DEBUG = True
    DATA_AGGREGATOR_ADMIN_GROUP = 'u_test_group'
    RESTCLIENTS_DAO_CACHE_CLASS = None
else:
    DATA_AGGREGATOR__ADMIN_GROUP = os.getenv('ADMIN_GROUP', '')
