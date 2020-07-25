from datetime import datetime
from typing import Union

import arrow
import yaml

DATE_FORMATS = [arrow.FORMAT_RSS, arrow.FORMAT_ATOM, "ddd, DD MMM YYYY HH:mm:ss ZZZ"]


def get_pretty_date_str(
    date: Union[str, datetime, arrow.Arrow], show_time: bool = False, show_year: bool = True
) -> str:
    """Return a nice representation of a date"""
    date = parse_date(date)

    # Only day and Month
    template = "%d %B"

    if show_year:
        template = f"{template}, %Y"

    # Add the time
    if show_time:
        template = f"%H:%M {template}"

    return date.strftime(template)


def parse_date(date: Union[str, datetime, arrow.Arrow]) -> arrow.Arrow:
    """Return a standardized UTC Arrow object"""
    _date = None
    if isinstance(date, str):
        try:
            _date = arrow.get(date)
        except arrow.ParserError:
            pass

        if not _date:
            parser = arrow.parser.DateTimeParser()
            for fmt in DATE_FORMATS:
                try:
                    _date = parser.parse(date, fmt=fmt)
                except arrow.ParserError:
                    continue
        if not _date:
            raise arrow.ParserError()

    elif isinstance(date, datetime):
        _date = arrow.Arrow.fromdatetime(date)
    else:
        _date = date

    return _date.astimezone(tz=arrow.utcnow().tzinfo)


def now() -> arrow.Arrow:
    """Convenience function for getting the current UTC DateTime"""
    return arrow.utcnow()


def arrow_representer(dumper: yaml.Dumper, data: arrow.Arrow) -> str:
    """
    Represent an `arrow.arrow.Arrow` object as a scalar in ISO format.

    ! '2013-05-07T04:24:24+00:00'
    """
    return dumper.represent_scalar("!", data.isoformat("T"))


yaml.add_representer(arrow.Arrow, arrow_representer)
yaml.SafeDumper.add_representer(arrow.Arrow, arrow_representer)
