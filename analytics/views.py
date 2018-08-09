from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from uw_saml.decorators import group_required
from analytics.models import (
    WeeklyDataTimePeriod, WeeklyDataDataPoint, ManagedCurrentTerm,
    ManagedCourseSISIDs)
from dateutil import parser
import StringIO
import csv
import codecs
import cStringIO


@group_required(settings.CANVAS_ANALYTICS_GROUP)
def home(request):
    term_names = WeeklyDataTimePeriod.objects.values('term').distinct()

    terms = []
    for item in term_names:
        term = item["term"]
        terms.append({
            "name": term,
            "url": reverse('week_list', kwargs={"term": term}),
        })
    return render(request, "term_list.html", {"terms": terms})


@group_required(settings.CANVAS_ANALYTICS_GROUP)
def weeks(request, term):
    periods = WeeklyDataTimePeriod.objects.filter(
        term=term).order_by('start_date')

    weeks = []
    for period in periods:
        weeks.append({
            "start": period.start_date,
            "end": period.end_date,
            "url": reverse("courses_list", kwargs={
                "term": term, "week_id": period.id}),
        })
    return render(request, "weeks.html", {"weeks": weeks})


@group_required(settings.CANVAS_ANALYTICS_GROUP)
def courses(request, term, week_id):
    period = WeeklyDataTimePeriod.objects.get(id=week_id)

    course_ids = WeeklyDataDataPoint.objects.filter(
        time_period=period).values("course_id").distinct()

    courses = []
    for course in course_ids:
        course_id = course["course_id"]
        courses.append({
            "name": course_id,
            "url": reverse("course_data", kwargs={
                "term": term, "week_id": week_id, "course_id": course_id}),
        })
    return render(request, "courses_list.html", {"courses": courses})


@group_required(settings.CANVAS_ANALYTICS_GROUP)
def data(request, term, week_id, course_id):
    period = WeeklyDataTimePeriod.objects.get(id=week_id)

    data_points = WeeklyDataDataPoint.objects.filter(
        time_period=period, course_id=course_id)

    keys = {}
    by_person_course_data = {}

    for item in data_points:
        keys[item.key] = True

        if item.login_name not in by_person_course_data:
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


@group_required(settings.CANVAS_ANALYTICS_GROUP)
def manage(request):
    error = None
    if "POST" == request.META['REQUEST_METHOD']:
        if "term" == request.POST["change"]:
            try:
                year = request.POST["year"]
                quarter = request.POST["term_quarter"]
                start = parser.parse(request.POST["start_date"])
                end = parser.parse(request.POST["end_date"])

                obj = ManagedCurrentTerm()
                obj.year = year
                obj.quarter = quarter
                obj.start_date = start
                obj.end_date = end
                # Try to save first, so if that fails for some reasonable
                # reason, we didn't just delete everything
                obj.save()
                ManagedCurrentTerm.objects.all().delete()
                obj.save()

            except Exception as ex:
                error = str(ex)

        if "courses" == request.POST["change"]:
            ManagedCourseSISIDs.objects.all().delete()
            seen = {}
            values = request.POST["new_list"]

            for sis_id in values.splitlines():
                plain = sis_id.strip()
                if plain not in seen:
                    if plain:
                        seen[plain] = True
                        ManagedCourseSISIDs.objects.create(sis_id=plain)

    data = {
        "error": error,
    }

    try:
        current_term = ManagedCurrentTerm.objects.all()[0]
        data["term_year"] = current_term.year
        data["term_quarter"] = current_term.quarter
        data["term_start"] = current_term.start_date.strftime("%m/%d/%Y")
        data["term_end"] = current_term.end_date.strftime("%m/%d/%Y")
    except Exception as ex:
        pass

    data["course_ids"] = []
    all_course_sis_ids = ManagedCourseSISIDs.objects.all()
    for val in sorted(all_course_sis_ids, key=lambda x: x.sis_id):
        data["course_ids"].append(val.sis_id)

    return render(request, "manage_everything.html", data)


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
        # self.writer.writerow([s.encode("utf-8") for s in row])
        self.writer.writerow([s.encode("utf-8") if (
            s is not None) else "" for s in row])
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
