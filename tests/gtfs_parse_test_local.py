import os
from datetime import datetime, timedelta

from nyct_gtfs import NYCTFeed


def main():
    feed = NYCTFeed("2", api_key=None, fetch_immediately=False)
    with open('test_data/2_delay.nyct.gtfsrt', 'rb') as f:
        feed.load_gtfs_bytes(f.read())
    trips = feed.filter_trips(line_id=["2"], travel_direction="N", has_delay_alert=True)
    print(trips[0])


if __name__ == '__main__':
    main()
