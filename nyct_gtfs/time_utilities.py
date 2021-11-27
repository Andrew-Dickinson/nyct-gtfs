import datetime
from typing import Optional


def parse_timestamp(timestamp, feed_datetime: Optional[datetime.datetime] = None):
    """
    Parse a datetime.datetime object from a POSIX timestamp. This the the format generated by the NYCT GTFS-realtime
    data feed.

    For some (undocumented) reason, some position update timestamps are in the future by an hour. This likely has
    something to do with time zones or daylight savings (maybe someone at the MTA hardcoded server timezones to be
    UTC-4 regardless of time of the year?).

    If a feed_datetime is specified, this will be used to determine if the position update timestamp is reasonable,
    i.e. it makes no sense for a train's last most recent position update to be timestamped more than 30 minutes into
    the future. If a timestamp is considered unreasonable, an hour is subtracted manually to make it make sense.

    This is EXTREMELY hacky and will likely break in the future. It also doesn't work for times that are SUPPOSED to
    be in the future, such as scheduled trips that have yet to depart. Since this off-by-one-hour timestamp phenomenon
    is inconsistent, I can't see a way to correct these timestamps.
    """
    raw_datetime = datetime.datetime.fromtimestamp(timestamp)

    if feed_datetime is None:
        return raw_datetime

    # This is SUPER hacky. But the only way that I can think of to correct the MTA's bogus time data
    if raw_datetime > (feed_datetime + datetime.timedelta(minutes=30)):
        return raw_datetime - datetime.timedelta(minutes=60)
    else:
        return raw_datetime