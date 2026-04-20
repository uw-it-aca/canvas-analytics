# Copyright 2026 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.urls import re_path
from data_aggregator.views.pages import APIDocumentationView, JobAdminView, \
    JobAdminDetailView, MetadataFileAdminView
from data_aggregator.views.api.jobs import JobView, JobRestartView, \
    JobChartDataView
from data_aggregator.views.api.metadata import MetadataFileListView, \
    MetadataFileUploadView, MetadataFileDeleteView
from data_aggregator.views.api.analytics import AccountAssignmentView, \
    AccountParticipationView, TermAssignmentView, TermParticipationView, \
    UserView, UserAssignmentView, UserParticipationView

urlpatterns = [
    re_path(r'api/internal/metadata/$', MetadataFileListView.as_view()),
    re_path(r'api/internal/metadata/upload/$',
            MetadataFileUploadView.as_view()),
    re_path(r'api/internal/metadata/delete/$',
            MetadataFileDeleteView.as_view()),
    re_path(r'api/internal/jobs/$', JobView.as_view()),
    re_path(r'api/internal/jobs-chart-data/$', JobChartDataView.as_view()),
    re_path(r'api/internal/jobs/restart/$', JobRestartView.as_view()),
    re_path(r'api/$', APIDocumentationView.as_view(), name="api_analytics"),
    re_path(r'api/(?P<version>v[1])/$', APIDocumentationView.as_view()),
    re_path(r'api/(?P<version>v[1])/user/$', UserView.as_view()),
    re_path(r'api/(?P<version>v[1])/user/(?P<sis_user_id>[-@:\w]+)/'
            r'assignment/$',
            UserAssignmentView.as_view()),
    re_path(r'api/(?P<version>v[1])/user/(?P<sis_user_id>[-@:\w]+)/'
            r'participation/$',
            UserParticipationView.as_view()),
    re_path(r'api/(?P<version>v[1])/account/(?P<sis_account_id>[-@:\w]+)/'
            r'assignment/$',
            AccountAssignmentView.as_view()),
    re_path(r'api/(?P<version>v[1])/account/(?P<sis_account_id>[-@:\w]+)/'
            r'participation/$',
            AccountParticipationView.as_view()),
    re_path(r'api/(?P<version>v[1])/term/(?P<sis_term_id>[-@:\w]+)/'
            r'assignment/$',
            TermAssignmentView.as_view()),
    re_path(r'api/(?P<version>v[1])/term/(?P<sis_term_id>[-@:\w]+)/'
            r'participation/$',
            TermParticipationView.as_view()),
]
