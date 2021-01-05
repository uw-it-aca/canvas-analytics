from .base_settings import *
import os

INSTALLED_APPS += [
    'course_data.apps.CourseDataConfig',
]

if os.getenv('ENV') == 'localdev':
    DEBUG = True
    COURSE_DATA_ADMIN_GROUP = 'u_test_group'
    RESTCLIENTS_DAO_CACHE_CLASS = None
else:
    COURSE_DATA_ADMIN_GROUP = os.getenv('ADMIN_GROUP', '')
