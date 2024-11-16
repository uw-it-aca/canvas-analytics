from .base_settings import *
import os

INSTALLED_APPS += [
    'data_aggregator.apps.DataAggregatorConfig',
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
    CSRF_TRUSTED_ORIGINS = ['https://' + os.getenv('CLUSTER_CNAME')]
    DATA_AGGREGATOR_ACCESS_GROUP = os.getenv('ACCESS_GROUP', '')
    DATA_AGGREGATOR_THREADING_ENABLED = True
    # Restclient cache configuration
    RESTCLIENTS_DAO_CACHE_CLASS = 'data_aggregator.cache.DataAggregatorGCSCache'
    if os.getenv('ENV') == 'test':
        GCS_BUCKET_NAME = 'canvas-analytics-test'
        RAD_METADATA_BUCKET_NAME = 'canvas-analytics-test'
    elif os.getenv('ENV') == 'prod':
        GCS_BUCKET_NAME = 'canvas-analytics'
        RAD_METADATA_BUCKET_NAME = 'canvas-analytics'

    EDW_HOSTNAME = 'localhost'
    EDW_USER = os.getenv('EDW_USER', '')
    EDW_PASSWORD = os.getenv('EDW_PASSWORD', '')

    GCS_REPLACE = False  # replace contents if already exists
    GCS_TIMEOUT = 10  # request timeout in seconds
    GCS_NUM_RETRIES = 3  # number of request retries

    IDP_AWS_STORAGE_BUCKET_NAME = os.getenv('IDP_AWS_STORAGE_BUCKET_NAME')
    IDP_AWS_ACCESS_KEY_ID = os.getenv('IDP_AWS_ACCESS_KEY_ID')
    IDP_AWS_SECRET_ACCESS_KEY = os.getenv('IDP_AWS_SECRET_ACCESS_KEY')

    EXPORT_AWS_STORAGE_BUCKET_NAME = os.getenv('EXPORT_AWS_STORAGE_BUCKET_NAME')
    EXPORT_AWS_ACCESS_KEY_ID = os.getenv('EXPORT_AWS_ACCESS_KEY_ID')
    EXPORT_AWS_SECRET_ACCESS_KEY = os.getenv('EXPORT_AWS_SECRET_ACCESS_KEY')

WEBPACK_LOADER = {
    'DEFAULT': {
        'BUNDLE_DIR_NAME': 'data_aggregator/bundles/',
        'STATS_FILE': os.path.join(BASE_DIR, 'data_aggregator', 'static', 'webpack-stats.json'),
    }
}

RESTCLIENTS_CANVAS_POOL_SIZE = 20
ACADEMIC_CANVAS_ACCOUNT_ID = '84378'
