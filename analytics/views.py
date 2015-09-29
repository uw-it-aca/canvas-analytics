from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.template import RequestContext
from django.core.urlresolvers import reverse
from analytics.models import WeeklyDataTimePeriod, WeeklyDataDataPoint
import StringIO
import csv
import codecs
import cStringIO

def home(request):
    term_names = WeeklyDataTimePeriod.objects.values('term').distinct()

    terms = []
    for item in term_names:
        term = item["term"]
        terms.append({
            "name": term,
            "url": reverse('week_list', kwargs={"term": term }),
        })

    return render_to_response("term_list.html", { "terms": terms}, RequestContext(request))

def weeks(request, term):
    periods = WeeklyDataTimePeriod.objects.filter(term=term).order_by('start_date')

    weeks = []
    for period in periods:
        weeks.append({
            "start": period.start_date,
            "end": period.end_date,
            "url": reverse("courses_list", kwargs={"term": term, "week_id": period.id}),
        })

    return render_to_response("weeks.html", {"weeks": weeks}, RequestContext(request))

def courses(request, term, week_id):
    period = WeeklyDataTimePeriod.objects.get(id=week_id)

    course_ids = WeeklyDataDataPoint.objects.filter(time_period=period).values("course_id").distinct()

    courses = []
    for course in course_ids:
        course_id = course["course_id"]
        courses.append({
            "name": course_id,
            "url": reverse("course_data", kwargs={"term":term, "week_id": week_id, "course_id": course_id }),
        })


    return render_to_response("courses_list.html", {"courses": courses}, RequestContext(request))

def data(request, term, week_id, course_id):
    period = WeeklyDataTimePeriod.objects.get(id=week_id)

    data_points = WeeklyDataDataPoint.objects.filter(time_period=period, course_id=course_id)

    keys = {}
    by_person_course_data = {}

    for item in data_points:
        keys[item.key] = True

        if not item.login_name in by_person_course_data:
            by_person_course_data[item.login_name] = {}

        by_person_course_data[item.login_name][item.key] = item.value

    data_keys = keys.keys()
    data_keys.sort()


    csv_file = StringIO.StringIO()

    csv_writer = UnicodeWriter(csv_file, dialect=csv.excel)
    csv_writer.writerow(["login name"] + data_keys)

    for login_name in by_person_course_data.keys():
        csv_values = [login_name]

        for key in data_keys:
            if key in by_person_course_data[login_name]:
                csv_values.append(by_person_course_data[login_name][key])
            else:
                csv_values.append("")

        csv_writer.writerow(csv_values)

    # With text/csv excel wants to open it - but it doesn't parse as csv
    # on my computer :(
    return HttpResponse(csv_file.getvalue(), content_type="text/plain")


# From the csv documentation:

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        # Uglying up their code a bit, cause we sometimes have null values:
        #self.writer.writerow([s.encode("utf-8") for s in row])
        self.writer.writerow([s.encode("utf-8") if s is not None else "" for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

