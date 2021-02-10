import json
from data_aggregator.models import Job
from data_aggregator.views.api import RESTDispatch
from django.db.models import F, Q, BooleanField, Value


class JobView(RESTDispatch):
    '''
    API endpoint returning a list of job dictionaries

    /api/internal/jobs/

    HTTP POST accepts the following dictionary paramters:
    * filters: dictionary of request filters
    '''

    def post(self, request, *args, **kwargs):
        filters = json.loads(request.body.decode('utf-8'))
        jobs = (Job.objects
                .annotate(
                    job_type=F('type__type'),
                    selected=Value(False, BooleanField())
                ))

        activeDateRange = filters.get('activeDateRange')
        if activeDateRange:
            jobs = jobs.filter(
                target_date_start__lte=activeDateRange["endDate"]
            )
            jobs = jobs.filter(
                target_date_end__gte=activeDateRange["startDate"]
            )

        jobDateRange = filters.get('jobDateRange')
        if jobDateRange.get("startDate") and \
                jobDateRange.get("endDate"):
            jobs = jobs.filter(
                Q(start__lte=jobDateRange["endDate"]) |
                Q(start__isnull=True)
            )
            jobs = jobs.filter(
                Q(end__gte=jobDateRange["startDate"]) |
                Q(end__isnull=True)
            )

        if filters.get('jobType'):
            jobs = jobs.filter(
                type__type__in=filters["jobType"])

        total_jobs = 0
        job_dicts = []
        for job in jobs:
            jd = {}
            jd["id"] = job.id
            jd["context"] = job.context
            jd["job_type"] = job.job_type
            jd["pid"] = job.pid
            jd["start"] = job.start.isoformat() if job.start else None
            jd["end"] = job.end.isoformat() if job.end else None
            jd["message"] = job.message
            jd["created"] = job.created.isoformat() if job.created else None
            jd["status"] = job.status
            jd["selected"] = job.selected
            if filters.get('jobStatus'):
                if job.status in filters["jobStatus"]:
                    job_dicts.append(jd)
                    total_jobs += 1
            else:
                job_dicts.append(jd)
                total_jobs += 1

        # sort in code since the django doesn't support sorting by properties
        sort_by = filters.get("sortBy")
        if sort_by:
            sort_desc = True if filters.get("sortDesc") else False
            job_dicts = sorted(job_dicts,
                               key=lambda job: ("" if job[sort_by] is None
                                                else job[sort_by]),
                               reverse=sort_desc)

        # calculate pagination
        currPage = filters["currPage"]
        perPage = filters["perPage"]
        page_start = (currPage - 1) * perPage
        page_end = (currPage * perPage) - 1

        # get current page
        job_dicts = job_dicts[page_start:page_end]

        return self.json_response(content={"jobs": job_dicts,
                                           "total_jobs": total_jobs})


class JobRestartView(RESTDispatch):
    '''
    API endpoint to restart a job

    /api/internal/jobs/restart/

    HTTP POST accepts the following dictionary paramters:
    * job_ids: list of job ids to restart
    '''

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