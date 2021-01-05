from datetime import date, datetime


def split_course_file(course_file, chunk_size=10):
    """Yield successive n-sized chunks from lst."""
    with open(course_file, mode="r") as cf:
        chunks = []
        courses = cf.read().strip("\n").split("\n")
        for i in range(0, len(courses), chunk_size):
            chunks.append(courses[i:i + chunk_size])
    return chunks


def read_courses(course_file):
    """Yield successive n-sized chunks from lst."""
    with open(course_file, mode="r") as cf:
        return cf.read().strip("\n").split("\n")


def get_week_of_term(first_day_quarter, cmp_dt=None):
    if cmp_dt is None:
        cmp_dt = datetime.now()
    if isinstance(first_day_quarter, date):
        first_day_quarter = datetime.combine(first_day_quarter,
                                             datetime.min.time())
    days = (cmp_dt - first_day_quarter).days
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
        raise ValueError("Quarter name {} not found. Options are "
                         "WINTER, SPRING, SUMMER, and AUTUMN."
                         .format(quarter_name))
