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
from data_aggregator.views.pages import HomeView
from data_aggregator.views.api.data import JobFilter, JobReset

urlpatterns = [
    re_path(r'^$', HomeView.as_view()),
    re_path(r'^api/filterjobs/$', JobFilter.as_view()),
    re_path(r'^api/resetjobs/$', JobReset.as_view()),
    re_path(r'^saml/', include('uw_saml.urls')),
]