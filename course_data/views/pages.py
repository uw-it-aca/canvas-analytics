from django.views.generic import TemplateView
from uw_saml.utils import get_user
from django.conf import settings
from course_data.models import Week, JobType


class PageView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['netid'] = get_user(self.request)
        context['ga_key'] = getattr(settings, "GA_KEY", None)
        return context


class HomeView(PageView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = {}
        weeks = (Week.objects.all().values())
        jobtypes = (JobType.objects.all().values())
        context['weeks'] = list(weeks)
        context['jobtypes'] = list(jobtypes)
        context['debug'] = settings.DEBUG
        return context
