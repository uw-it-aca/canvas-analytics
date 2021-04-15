from uw_canvas.models import CanvasTerm
from analytics.models import ManagedCurrentTerm


def get_term():
    # Hopefully there's only one!
    managed = ManagedCurrentTerm.objects.all()[0]
    term = CanvasTerm()
    term.sis_term_id = "%s-%s" % (managed.year, managed.quarter)
    term.name = "%s %s" % (managed.quarter, managed.year)
    term._start_date = managed.start_date
    term._end_date = managed.end_date

    return term
