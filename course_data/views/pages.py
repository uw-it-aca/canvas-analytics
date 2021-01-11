from django.views.generic import TemplateView
from uw_saml.utils import get_user
from django.conf import settings
from course_data.models import JobType, Job, Course


class PageView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['netid'] = get_user(self.request)
        context['ga_key'] = getattr(settings, "GA_KEY", None)
        return context


class HomeView(PageView):
    template_name = "home.html"

    def get_weeks_for_term(self, term):
        weeks = list(Job.objects
                     .filter(course__year=term["year"])
                     .filter(course__quarter=term["quarter"])
                     .values('week')
                     .distinct())
        print("weeks = %s" % weeks)
        return weeks

    def get_context_data(self, **kwargs):
        terms = (Course.objects.values('year', 'quarter').distinct())
        default_term = terms.first()
        weeks = (Job.objects
                 .filter(course__year=default_term["year"])
                 .filter(course__quarter=default_term["quarter"])
                 .values('week')
                 .distinct())
        jobtypes = (JobType.objects.all().values())

        context = {}
        context['terms'] = list(terms)
        context['weeks'] = list(weeks)
        context['jobtypes'] = list(jobtypes)
        context['debug'] = settings.DEBUG
        return context
