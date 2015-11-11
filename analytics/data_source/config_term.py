from restclients.models.canvas import CanvasTerm
from django.conf import settings
from dateutil import parser

# Just kidding, it's winter
def get_term():
    term = CanvasTerm()
    term.sis_term_id = settings.ANALYTICS_TERM_SIS_ID
    term.name = getattr(settings, "ANALYTICS_TERM_NAME", "Current Term")
    term._start_date = parser.parse(settings.ANALYTICS_TERM_START_DATE)
    term._end_date = parser.parse(settings.ANALYTICS_TERM_END_DATE)

    return term
