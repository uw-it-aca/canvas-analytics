from .base_settings import *
import os

INSTALLED_APPS += [
    'data_aggregator.apps.DataAggregatorConfig',
    'analytics.apps.AnalyticsConfig',
    'webpack_loader',
    'rest_framework'
]

if os.getenv('ENV') == 'localdev':
    DEBUG = True
    DATA_AGGREGATOR_ACCESS_GROUP = 'u_test_group'
    DATA_AGGREGATOR_THREADING_ENABLED = False
    RESTCLIENTS_DAO_CACHE_CLASS = None
    DATA_AGGREGATOR_THREADING_ENABLED = False
else:
    DATA_AGGREGATOR_ACCESS_GROUP = os.getenv('ACCESS_GROUP', '')
    DATA_AGGREGATOR_THREADING_ENABLED = True

WEBPACK_LOADER = {
    'DEFAULT': {
        'BUNDLE_DIR_NAME': 'data_aggregator/bundles/',
        'STATS_FILE': os.path.join(BASE_DIR, 'data_aggregator', 'static', 'webpack-stats.json'),
    }
}

RESTCLIENTS_CANVAS_POOL_SIZE = 50
RESTCLIENTS_CANVAS_TIMEOUT = 120
ACADEMIC_CANVAS_ACCOUNT_ID = '84378'
