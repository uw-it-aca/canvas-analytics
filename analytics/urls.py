from django.urls import re_path
from analytics.views import data, courses, weeks, manage, home

urlpatterns = [
    re_path((
        r'^term/(?P<term>[a-z0-9\-]+)/(?P<week_id>[0-9]+)/'
        r'(?P<course_id>.*).csv'), data, name="course_data"),
    re_path(r'^term/(?P<term>[a-z0-9\-]+)/(?P<week_id>[0-9]+)',
            courses, name="courses_list"),
    re_path(r'^term/(?P<term>[a-z0-9\-]+)/', weeks, name="week_list"),
    re_path(r'^manage$', manage, name="manage"),
    re_path(r'^$', home, name="home"),
]
