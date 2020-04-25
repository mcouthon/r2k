from datetime import datetime
from typing import Union

from dateutil.parser import parse as parse_date


def get_pretty_date_str(date: Union[str, datetime], show_time: bool = False, short_date: bool = False) -> str:
    """Return a nice representation of a date"""
    if isinstance(date, str):
        date = parse_date(date)

    # Only day and Month
    template = "%d %B"

    # Add the Year
    if not short_date:
        template = f"{template}, %Y"

    # Add the time
    if show_time:
        template = f"%H:%M {template}"
    return date.strftime(template)
