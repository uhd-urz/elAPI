from datetime import datetime
from typing import Iterator, Tuple


def get_billing_dates(
    start_date: datetime, end_date: datetime
) -> Iterator[Tuple[int, int]]:
    from dateutil import rrule

    for date in rrule.rrule(
        dtstart=start_date, until=end_date, freq=rrule.MONTHLY, bymonthday=1
    ):
        yield date.year, date.month
