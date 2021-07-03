from django.conf import settings
from django.utils.importlib import import_module
from datetime import datetime
from analytics.models import WeeklyDataTimePeriod, WeeklyDataDataPoint
from uw_canvas.courses import Courses
import traceback
import sys


def build_data():
    start_time = datetime.now()
    data_gather_modules = \
        getattr(settings, 'ANALYTICS_DATA_GATHERING_MODULE_LIST',
                ['analytics.gatherers.assignments',
                 'analytics.gatherers.assignment_due_dates',
                 'analytics.gatherers.assignment_submission_counts',
                 'analytics.gatherers.conversations',
                 'analytics.gatherers.discussions',
                 'analytics.gatherers.logins',
                 'analytics.gatherers.page_edits',
                 'analytics.gatherers.quiz',
                 'analytics.gatherers.user_page_views', ])

    period, term = get_time_period()

    course_modules = []
    person_modules = []
    for module in data_gather_modules:
        mod = import_module(module)
        if hasattr(mod, "collect_analytics_for_sis_course_id"):
            course_modules.append(mod)
        if hasattr(mod, "collect_analytics_for_sis_person_id"):
            person_modules.append(mod)

    course_ids = build_data_by_course(course_modules, start_time, period, term)
    build_data_by_person(person_modules, start_time, course_ids, period, term)


def build_data_by_course(gatherers, start_time, time_period, term):
    course_module = getattr(settings, 'ANALYTICS_COURSE_LIST_MODULE',
                            'analytics.data_source.course_list')
    mod = import_module(course_module)

    count = 0
    all_ids = mod.get_all_course_sis_ids()
    total = len(all_ids)
    for course_id in all_ids:
        count = count + 1
        print("On course {} of {}, time: {}".format(
            count, total, (datetime.now() - start_time).__str__()))
        for gatherer in gatherers:
            try:
                data = \
                    gatherer.collect_analytics_for_sis_course_id(course_id,
                                                                 time_period)
                for entry in data:
                    try:
                        login_name = entry["login_name"]
                        key = entry["type"]
                        value = entry["value"]

                        WeeklyDataDataPoint.objects.create(
                            time_period=time_period,
                            course_id=course_id,
                            login_name=login_name,
                            key=key,
                            value=value
                        )
                    except Exception as ex:
                        print("Error: {}".format(ex))
            except Exception as ex:
                print("Error: {}".format(ex))
                traceback.print_exc(file=sys.stdout)
                # XXX - handle these later
                pass
#            Oops - Error saving data:  too many SQL variables
#            try:
#                WeeklyDataDataPoint.objects.bulk_create(gatherer_data)
#            except Exception as ex:
#                print("Error saving data: {}".format(ex))
    return all_ids


def build_data_by_person(gatherers, start_time, course_ids, time_period, term):
    person_module = getattr(settings, 'ANALYTICS_PERSON_LIST_MODULE',
                            'analytics.data_source.person_list')
    mod = import_module(person_module)

    all_ids = mod.get_all_person_sis_ids(course_ids)
    total = len(all_ids)
    count = 0

    # Some gatherers can only get us the canvas course id - so build up a
    # reverse loopup as needed
    sis_course_lookup = {}

    for person_id in all_ids:
        count = count + 1
        print("On person {} of {}, time: {}".format(
            count, total, (datetime.now() - start_time).__str__()))
        for gatherer in gatherers:
            try:
                data = \
                    gatherer.collect_analytics_for_sis_person_id(person_id,
                                                                 time_period)
                for entry in data:
                    try:
                        course_id = None
                        if "course_canvas_id" in entry:
                            canvas_id = entry["course_canvas_id"]
                            if canvas_id not in sis_course_lookup:
                                course = Courses().get_course(canvas_id)
                                sis_course_lookup[canvas_id] = \
                                    course.sis_course_id
                            course_id = sis_course_lookup[canvas_id]
                        if "course_id" in entry:
                            course_id = entry["course_id"]
                        key = entry["type"]
                        value = entry["value"]

                        WeeklyDataDataPoint.objects.create(
                            time_period=time_period,
                            course_id=course_id,
                            login_name=person_id,
                            key=key,
                            value=value
                        )
                    except Exception as ex:
                        print("Error {}: {}".format(entry, ex))

            except Exception as ex:
                # XXX - handle these later
                print("Error: {}".format(ex))
                pass

    for gatherer in gatherers:
        try:
            data = gatherer.post_process(course_ids)
            for entry in data:
                try:
                    course_id = None
                    if "course_id" in entry:
                        course_id = entry["course_id"]
                    person_id = entry["login_name"]
                    key = entry["type"]
                    value = entry["value"]

                    # gatherer_data.append(WeeklyDataDataPoint(
                    WeeklyDataDataPoint.objects.create(
                        time_period=time_period,
                        course_id=course_id,
                        login_name=person_id,
                        key=key,
                        value=value
                    )
                except Exception as ex:
                    print("Error {}: {}".format(entry, ex))

        except AttributeError:
            pass
        except Exception as ex:
            print("Error: {}".format(ex))
            traceback.print_exc(file=sys.stdout)


def get_time_period():
    term_module = getattr(settings, 'ANALYTICS_CURRENT_TERM_MODULE',
                          'analytics.data_source.managed_term')
    mod = import_module(term_module)

    current_term = mod.get_term()
    current_sis_id = current_term.sis_term_id

    start_date = current_term.get_start_date()
    end_date = datetime.now()

    new_period = WeeklyDataTimePeriod.objects.create(term=current_sis_id,
                                                     start_date=start_date,
                                                     end_date=end_date)

    return new_period, current_term
