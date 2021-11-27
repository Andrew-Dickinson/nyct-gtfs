import datetime
from urllib.parse import urlparse, unquote

import requests

from nyct_gtfs.compiled_gtfs import nyct_subway_pb2, gtfs_realtime_pb2
from nyct_gtfs.gtfs_static_types import TripShapes, Stations
from nyct_gtfs.trip import Trip


class NYCTFeed:
    """
    Provides an interface for querying the NYCT GTFS-realtime data feeds. Provides some metadata from the feed headers
    such as version and update time information. Also provides the `get_trips` method, which gives access to the main
    data from the feed - real time NYCT subway trip data.
    """
    _train_to_url = {
        "1": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
        "2": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
        "3": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
        "4": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
        "5": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
        "6": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
        "7": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
        "S": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
        "GS": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
        "A": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace",
        "C": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace",
        "E": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace",
        "H": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace",
        "FS": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace",
        "SF": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace",
        "SR": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace",
        "B": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm",
        "D": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm",
        "F": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm",
        "M": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm",
        "G": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-g",
        "J": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-jz",
        "Z": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-jz",
        "N": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw",
        "Q": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw",
        "R": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw",
        "W": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw",
        "L": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-l",
        "SI": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-si",
        "SS": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-si",
        "SIR": "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-si"
    }

    def __init__(self, feed_specifier, api_key, fetch_immediately=True, trips_txt=None, stops_txt=None):
        """
        Creates NYCTFeed object

        :param feed_specifier: Either a subway line identifier (e.g. "1", "Q", etc.) or a `api.mta.info` datafeed URL
        :param api_key: An API key obtained from https://api.mta.info/
        :param fetch_immediately: False disables auto fetch. You'll need to call refresh() before using this object
        :param trips_txt: A file or file path to a NYCT subway GTFS-static trips.txt file (to override built-in copy)
        :param stops_txt: A file or file path to a NYCT subway GTFS-static stops.txt file (to override built-in copy)
        """
        self._feed = None
        self._api_key = api_key
        self._trip_shapes = TripShapes(trips_txt)
        self._stops = Stations(stops_txt)

        if feed_specifier in self._train_to_url:
            self._feed_url = self._train_to_url[feed_specifier]
        else:
            parsed_url = urlparse(feed_specifier)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError(f"Invalid feed specifier: {feed_specifier}, must be a valid feed URL or one of: "
                                 f"{self._train_to_url.keys()}")
            self._feed_url = feed_specifier

        if fetch_immediately:
            self.refresh()

    @property
    def last_generated(self):
        """A datetime.datetime object representing when this feed was generated by the MTA server"""
        return datetime.datetime.fromtimestamp(self._feed.header.timestamp)

    @property
    def gtfs_realtime_version(self):
        """The version of the GTFS-realtime specification that this feed conforms to"""
        return self._feed.header.gtfs_realtime_version

    @property
    def nyct_subway_gtfs_version(self):
        """The version of the NYCT GTFS-realtime specification extension that this feed conforms to"""
        return self._feed.header.Extensions[nyct_subway_pb2.nyct_feed_header].nyct_subway_version

    @property
    def trip_replacement_periods(self):
        """
        A dictionary with a datetime.datetime representing the end of the replacement period for each line

        From the NYCT GTFS-realtime spec:
        ```
            For the NYCT Subway, the GTFS-realtime feed replaces any scheduled trip within the
            trip_replacement_period.

            This feed is a full dataset, it contains all trips starting in the trip_replacement_period. If a trip from
            the static GTFS is not found in the GTFS-realtime feed, it should be considered as cancelled.

            The replacement period can be different for each route, so we supply a list of the routes where the trips
            in the feed replace all scheduled trips within the replacement period. This is 30 minutes for all routes
            currently implemented.
        ```
        """
        periods = {}
        raw_periods = self._feed.header.Extensions[nyct_subway_pb2.nyct_feed_header].trip_replacement_period
        for trip_replacement_period in raw_periods:
            end_time = datetime.datetime.fromtimestamp(trip_replacement_period.replacement_period.end)
            periods[trip_replacement_period.route_id] = end_time
        return periods

    def refresh(self):
        """Reload this object's feed information from the MTA API"""
        response = requests.get(self._feed_url, headers={'x-api-key': self._api_key})
        self.load_gtfs_bytes(response.content)

    def load_gtfs_bytes(self, gtfs_bytes):
        """
        Load this object's feed information from a binary GTFS string, useful for testing or analyzing stored feed data
        """
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(gtfs_bytes)
        self._feed = feed

    @staticmethod
    def _trip_identifier(trip):
        return trip.trip_id + " " + trip.Extensions[nyct_subway_pb2.nyct_trip_descriptor].train_id[-7:]

    @property
    def trips(self):
        """Get the list of subway trips from the GTFS-realtime feed. Returns a list of `Trip` objects"""
        trip_updates = {}
        vehicle_updates = {}
        alerts = {}
        for entity in self._feed.entity:
            if entity.HasField('trip_update'):
                trip_updates[self._trip_identifier(entity.trip_update.trip)] = entity.trip_update
            elif entity.HasField('vehicle'):
                vehicle_updates[self._trip_identifier(entity.vehicle.trip)] = entity.vehicle
            elif entity.HasField('alert'):
                for informed_entity in entity.alert.informed_entity:
                    if self._trip_identifier(informed_entity.trip) not in alerts:
                        alerts[self._trip_identifier(informed_entity.trip)] = []
                    alerts[self._trip_identifier(informed_entity.trip)].append(entity.alert)

        trips = []
        for trip_id, trip_update in trip_updates.items():
            vehicle_update = None
            applicable_alerts = None
            if trip_id in vehicle_updates:
                vehicle_update = vehicle_updates[trip_id]
            if trip_id in alerts:
                applicable_alerts = alerts[trip_id]

            trip = Trip(
                trip_update,
                vehicle_update=vehicle_update,
                applicable_alerts=applicable_alerts,
                trip_shapes=self._trip_shapes,
                stops=self._stops,
                feed_datetime=self.last_generated
            )
            trips.append(trip)

        return trips

    def filter_trips(self, line_id=None, travel_direction=None, train_assigned=None, underway=None, shape_id=None,
                  headed_for_stop_id=None, updated_after=None, has_delay_alert=None):
        """
        Get the list of subway trips from the GTFS-realtime feed, optionally filtering based on one or more parameters.

        If more than one filter is specified, only trips that match all filters will be returned.

        :param line_id: A line identifier str (or list of strs)  such as "1", "A", "GS", or "FS"
        :param travel_direction: A travel direction str, either "N" for North or "S" for South (see `Trip.direction`)
        :param train_assigned: A boolean that is True iff a train has been assigned to this trip
        :param underway: A boolean that is True iff a train has begun this trip
        :param shape_id: A str (or list of strs) representing the shape id (i.e. "1..S03R") (see `Trip.shape_id`)
        :param headed_for_stop_id: A str (or list of strs) representing a stop id(s) that this trip must be heading to
        :param updated_after: A datetime.datetime, trips whose most recent update is before this time are excluded
                              (note, specifying this option always excludes trains not underway - since only trains
                              that are underway provide position updates)
        :param has_delay_alert: A boolean that is True iff a train currently has a delay alert published
        :return: A list of `Trip` objects
        """
        trips = []
        for trip in self.trips:
            # Filter based on method parameters
            if line_id is not None:
                if isinstance(line_id, str):
                    if trip.route_id != line_id:
                        continue
                elif isinstance(line_id, list):
                    if trip.route_id not in line_id:
                        continue
                else:
                    raise ValueError(f"Valid value for line_id: {line_id}. Must be str or list")

            if travel_direction is not None:
                if trip.direction != travel_direction:
                    continue

            if train_assigned is not None:
                if trip.train_assigned != train_assigned:
                    continue

            if underway is not None:
                if trip.underway != underway:
                    continue

            if shape_id is not None:
                if isinstance(shape_id, str):
                    if trip.shape_id != shape_id:
                        continue
                elif isinstance(shape_id, list):
                    if trip.shape_id not in shape_id:
                        continue
                else:
                    raise ValueError(f"Valid value for shape_id: {shape_id}. Must be str or list")

            if headed_for_stop_id is not None:
                if isinstance(headed_for_stop_id, str):
                    if not trip.headed_to_stop(headed_for_stop_id):
                        continue
                elif isinstance(headed_for_stop_id, list):
                    headed_for_stops = [trip.headed_to_stop(stop_id) for stop_id in headed_for_stop_id]
                    if sum(headed_for_stops) == 0:
                        # This means that none of the stops requested by the caller are in this train's future path
                        continue

            if updated_after is not None:
                if not trip.underway:
                    continue
                if trip.last_position_update < updated_after:
                    continue

            if has_delay_alert is not None:
                if trip.has_delay_alert != has_delay_alert:
                    continue

            trips.append(trip)

        return trips

    def __repr__(self):
        return f"{{NYCT_GTFS_Realtime_Feed, @{self.last_generated.strftime('%Y-%m-%d %H:%M:%S')}, {str(self.trips)}}}"

    def __str__(self):
        path = unquote(urlparse(self._feed_url).path)
        feed_id = path.split('/')[-1]
        return f"NYCT Subway Feed ({feed_id}), generated {self.last_generated.strftime('%Y-%m-%d %H:%M:%S')}, " \
               f"containing {len(self.trips)} trips"
