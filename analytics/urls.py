from django.conf.urls import url
from analytics.views import data, courses, weeks, manage, home


urlpatterns = [
    url(
        r'^term/(?P<term>[a-z0-9\-]+)/(?P<week_id>[0-9]+)/'
        r'(?P<course_id>.*).csv', data, name="course_data"),
    url(
        r'^term/(?P<term>[a-z0-9\-]+)/(?P<week_id>[0-9]+)',
        courses, name="courses_list"),
    url(r'^term/(?P<term>[a-z0-9\-]+)/', weeks, name="week_list"),
    url(r'^manage$', manage),
    url(r'^$', home),
]
