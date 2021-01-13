import json
from course_data.models import Job
from course_data.views.api import RESTDispatch
from django.db.models import F, Value, BooleanField


class JobFilter(RESTDispatch):

    def post(self, request, *args, **kwargs):
        filters = json.loads(request.body.decode('utf-8'))
        print(filters)
        jobs = (Job.objects
                .select_related('course')
                .annotate(
                    course_year=F('course__term__year'),
                    course_quarter=F('course__term__quarter'),
                    course_week=F('week'),
                    course_code=F('course__course_id'),
                    job_type=F('type__type'),
                    show=Value(True, BooleanField())
                ))

        if 'week' in filters:
            jobs = jobs.filter(week=filters["week"])
        if 'term' in filters:
            jobs = (jobs.filter(course_year=filters["term"]["year"])
                        .filter(course_quarter=filters["term"]["quarter"]))

        jobs = jobs.values("id", "course_year", "course_quarter",
                           "course_week", "course_code", "job_type", "pid",
                           "start", "end", "message", "created", "show")
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
