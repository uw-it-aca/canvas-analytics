from django.conf import settings
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from uw_saml.decorators import group_required
from analytics.models import SubaccountActivity


@method_decorator(group_required(settings.CANVAS_ANALYTICS_GROUP),
                  name='dispatch')
class ActivityReports(View):
    template_name = 'analytics/activity_reports.html'

    def get(self, request, *args, **kwargs):
        params = {
            'reports': SubaccountActivity.objects.all(),
        }
        return render(request, self.template_name, params)
