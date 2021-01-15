from django.views.generic import TemplateView
from uw_saml.utils import get_user
from django.conf import settings
from course_data.models import Term, JobType, Job
from django.db import models
from django.db.models.functions import Cast


class PageView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['netid'] = get_user(self.request)
        context['ga_key'] = getattr(settings, "GA_KEY", None)
        return context


class HomeView(PageView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        terms = Term.objects.values()
        jobtypes = (JobType.objects.all().values())
        job_ranges = Job.objects.annotate(
            target_day_start=Cast('target_date_start', models.DateField()),
            target_day_end=Cast('target_date_end', models.DateField()),
        ).values('target_day_start', 'target_day_end').distinct()
        context = {}
        context['terms'] = list(terms)
        context['jobtypes'] = list(jobtypes)
        context['job_ranges'] = list(job_ranges)
        context['debug'] = settings.DEBUG
        return context
