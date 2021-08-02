# Copyright 2021 UW-IT, University of Washington
# SPDX-License-Identifier: Apache-2.0

from django.views.generic import TemplateView, DetailView
from uw_saml.utils import get_user
from uw_saml.decorators import group_required
from django.utils.decorators import method_decorator
from django.conf import settings
from data_aggregator.models import AnalyticTypes, Assignment, Participation, \
    Term, JobType, Job
from data_aggregator.utilities import get_sortable_term_id
from django.db import models
from django.db.models.functions import Cast


@method_decorator(group_required(settings.DATA_AGGREGATOR_ACCESS_GROUP),
                  name='dispatch')
class PageView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['netid'] = get_user(self.request)
        context['ga_key'] = getattr(settings, "GA_KEY", None)
        return context


class JobAdminView(PageView):

    template_name = "admin/jobs.html"

    def get_context_data(self, **kwargs):
        terms = Term.objects.values()
        jobtypes = JobType.objects.values()
        job_ranges = Job.objects.annotate(
            target_day_start=Cast('target_date_start', models.DateField()),
            target_day_end=Cast('target_date_end', models.DateField()),
        ).values('target_day_start', 'target_day_end').distinct()
        context = {}
        context['terms'] = \
            sorted(terms,
                   key=lambda term: get_sortable_term_id(term['sis_term_id']))
        context['jobtypes'] = [jt["type"] for jt in jobtypes]
        context['job_ranges'] = list(job_ranges)
        return context


class JobAdminDetailView(DetailView):

    model = Job
    template_name = "admin/job_detail.html"

    def get_object(self, queryset=None):
        job = super(JobAdminDetailView, self).get_object(queryset=queryset)
        return job.to_dict()

    def get_related_objects(self):
        job = self.get_object()
        related_objects = []
        if job["type"] == AnalyticTypes.assignment:
            related_objects = \
                Assignment.objects.filter(job__id=job["id"]).values()
        elif job["type"] == AnalyticTypes.participation:
            related_objects = \
                Participation.objects.filter(job__id=job["id"]).values()
        return list(related_objects)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['netid'] = get_user(self.request)
        context['ga_key'] = getattr(settings, "GA_KEY", None)
        context['related_objects'] = self.get_related_objects()
        return context


class MetadataFileAdminView(PageView):

    template_name = "admin/metadata.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['netid'] = get_user(self.request)
        context['ga_key'] = getattr(settings, "GA_KEY", None)
        terms = Term.objects.all().values_list('sis_term_id')
        context['terms'] = \
            sorted(terms,
                   key=lambda term: get_sortable_term_id(term[0]))
        return context


class APIDocumentationView(PageView):

    template_name = "api/analytics.html"
