from .base_settings import *
import os

INSTALLED_APPS += [
    'data_aggregator.apps.DataAggregatorConfig',
    'webpack_loader',
]

if os.getenv('ENV') == 'localdev':
    DEBUG = True
    DATA_AGGREGATOR_ACCESS_GROUP = 'u_test_group'
    RESTCLIENTS_DAO_CACHE_CLASS = None
else:
    DATA_AGGREGATOR_ACCESS_GROUP = os.getenv('ACCESS_GROUP', '')
