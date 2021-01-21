import json
from data_aggregator.models import Job
from data_aggregator.views.api import RESTDispatch
from django.db.models import F, BooleanField, Value


class JobFilter(RESTDispatch):

    def post(self, request, *args, **kwargs):
        filters = json.loads(request.body.decode('utf-8'))
        jobs = (Job.objects
                .annotate(
                    job_type=F('type__type'),
                    selected=Value(False, BooleanField())
                ))

        if 'date_range' in filters:
            jobs = jobs.filter(
                target_date_start__lte=filters["date_range"]["endDate"])
            jobs = jobs.filter(
                target_date_end__gte=filters["date_range"]["startDate"])

        jobs = jobs.values("id", "context", "job_type", "pid",
                           "start", "end", "message", "created",
                           "selected")
        return self.json_response(content={"jobs": list(jobs)})


class JobReset(RESTDispatch):

    def post(self, request, *args, **kwargs):
        data = json.loads(request.body.decode('utf-8'))
        job_ids = data["job_ids"]
        for job_id in job_ids:
            job = Job.objects.get(id=job_id)
            job.pid = None
            job.start = None
            job.end = None
            job.message = ""
            job.save()
        return self.json_response(content={"reset": True})
