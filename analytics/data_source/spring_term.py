from restclients.models.canvas import CanvasTerm
from dateutil import parser

# Just kidding, it's winter
def get_term():
    term = CanvasTerm()
    term.sis_term_id = "2015-winter"
    term.name = "Winter 2014"
    term._start_date = parser.parse("2015-01-05")
    term._end_date = parser.parse("2015-03-20")

    return term
