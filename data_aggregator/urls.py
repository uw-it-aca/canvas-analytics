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
from data_aggregator.views.pages import AdminView, APIDocumentationView
from data_aggregator.views.api.jobs import JobView, JobRestartView, \
    JobChartDataView, JobClearView
from data_aggregator.views.api.analytics import AccountAssignmentView, \
    AccountParticipationView, TermAssignmentView, TermParticipationView, \
    UserView, UserAssignmentView, UserParticipationView

urlpatterns = [
    re_path(r'admin/$', AdminView.as_view()),
    re_path(r'api/internal/jobs/$', JobView.as_view()),
    re_path(r'api/internal/jobs-chart-data/', JobChartDataView.as_view()),
    re_path(r'api/internal/jobs/restart/$', JobRestartView.as_view()),
    re_path(r'api/internal/jobs/clear/$', JobClearView.as_view()),
    re_path(r'api/$', APIDocumentationView.as_view()),
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
    re_path(r'^saml/', include('uw_saml.urls')),
]
