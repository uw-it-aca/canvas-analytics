from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^term/(?P<term>[a-z0-9\-]+)/(?P<week_id>[0-9]+)/(?P<course_id>.*).csv', 'analytics.views.data', name="course_data"),
    url(r'^term/(?P<term>[a-z0-9\-]+)/(?P<week_id>[0-9]+)', 'analytics.views.courses', name="courses_list"),
    url(r'^term/(?P<term>[a-z0-9\-]+)/', 'analytics.views.weeks', name="week_list"),
    url(r'^manage$', 'analytics.views.manage'),
    url(r'^$', 'analytics.views.home'),
)
