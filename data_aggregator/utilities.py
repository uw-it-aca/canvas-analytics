from django.utils import timezone
from datetime import date, datetime, timedelta


def datestring_to_datetime(date_str):
    """
    Converts an iso8601 date string to a datetime.datetime object
    :param: date_str
    :type: str
    :returns: datetime equivalent to string
    :type: datetime
    """
    if isinstance(date_str, (str)):
        fmts = ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S")
        for fmt in fmts:
            try:
                dt = timezone.make_aware(
                    datetime.strptime(date_str, fmt), timezone=timezone.utc)
                if dt.year < 1900:
                    err_msg = (f"Date {date_str} is out of range. "
                               f"Year must be year >= 1900.")
                    raise ValueError(err_msg)
                return dt
            except ValueError:
                pass
        err_msg = f"Unsupported date format. {date_str}"
        raise ValueError(err_msg)
    elif isinstance(date_str, datetime):
        return date_str  # already a date
    else:
        raise ValueError(f"Got {date_str} expected str.")

def get_relative_week(relative_date, cmp_dt=None):
    """
    Returns week number relative to supplied relative_date. If cmp_dt is
    supplied, then returns number of weeks between supplied relative_date and
    cmp_dt. If cmp_dt is not supplied, then returns number of weeks between
    supplied relative_date and the current utc date.
    """
    if cmp_dt is None:
        cmp_dt = timezone.now()
    if isinstance(relative_date, date):
        relative_date = timezone.make_aware(
            datetime.combine(relative_date, datetime.min.time()),
            timezone=timezone.utc)
    days = (cmp_dt - relative_date).days
    if days >= 0:
        return (days // 7) + 1
    return (days // 7)


def get_term_number(quarter_name):
    """
    Returns quarter info for the specified code.

    :param quarter_name: name of the quarter
    :type value: str
    """
    quarter_definitions = {
        "WINTER": 1,
        "SPRING": 2,
        "SUMMER": 3,
        "AUTUMN": 4,
    }
    try:
        return quarter_definitions[quarter_name.upper()]
    except KeyError:
        raise ValueError(f"Quarter name {quarter_name} not found. Options are "
                         f"WINTER, SPRING, SUMMER, and AUTUMN.")


def get_view_name(sis_term_id, week, label):
    sis_term_id = sis_term_id.replace("-", "_")
    view_name = f"{sis_term_id}_week_{week}_{label}"
    return view_name


def get_default_target_start():
    return timezone.now()


def get_default_target_end():
    now = timezone.now()
    tomorrow = now + timedelta(days=1)
    return tomorrow


def chunk_list(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))
