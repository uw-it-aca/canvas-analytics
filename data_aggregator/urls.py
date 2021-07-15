# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

"""data_aggregator URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import re_path, include
from django.views.generic import RedirectView
from data_aggregator.views.pages import APIDocumentationView, JobAdminView, \
    JobAdminDetailView
from data_aggregator.views.api.jobs import JobView, JobRestartView, \
    JobChartDataView
from data_aggregator.views.api.analytics import AccountAssignmentView, \
    AccountParticipationView, TermAssignmentView, TermParticipationView, \
    UserView, UserAssignmentView, UserParticipationView

urlpatterns = [
    re_path(r'^$',
            RedirectView.as_view(pattern_name='api_analytics',
                                 permanent=False)),
    re_path(r'admin/$',
            RedirectView.as_view(pattern_name='admin_jobs', permanent=False)),
    re_path(r'admin/jobs/$', JobAdminView.as_view(), name="admin_jobs"),
    re_path(r'admin/jobs/(?P<pk>[-@:\d]+)/$', JobAdminDetailView.as_view()),
    re_path(r'api/internal/jobs/$', JobView.as_view()),
    re_path(r'api/internal/jobs-chart-data/', JobChartDataView.as_view()),
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
