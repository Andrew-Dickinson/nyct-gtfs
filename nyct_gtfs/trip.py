import datetime

from nyct_gtfs.stop_time_update import StopTimeUpdate
from nyct_gtfs.compiled_gtfs import nyct_subway_pb2, gtfs_realtime_pb2
from nyct_gtfs.gtfs_static_types import TripShapes, Stations


class Trip:
    """
    Represents the abstract idea of a "trip", which is usually (but not always) served by exactly one train. A trip is
    created by the feed before departing the origin station (usually 30 minutes before). Then, prior to departure
    (usually only a few minutes prior), the trip will be assigned to a specific train, which will then execute the trip
    for the entirety of the route. Finally, once the train departs the origin station, the trip is considered to be
    "underway" and updates to the train's location become available.

    Implemented as a wrapper around the GTFS-realtime objects of a `TripUpdate` message and (optionally) a
    corresponding `VehiclePosition` message. Links the data from the vehicle update and the trip update into a single
    object, and provides helper functions to query the raw GTFS-realtime data for higher level questions.

    See TripUpdate and VehiclePosition in the NYCT GTFS-realtime specification for more details
    """

    def __init__(self, trip_update, vehicle_update=None, applicable_alerts=None, trip_shapes=None, stops=None,
                 feed_datetime=None):
        self._trip_update = trip_update
        self._vehicle_update = vehicle_update

        self._feed_datetime = feed_datetime

        if applicable_alerts is None:
            applicable_alerts = []

        if trip_shapes is None:
            trip_shapes = TripShapes()
        if stops is None:
            stops = Stations()

        self._trip_shapes = trip_shapes
        self._stops = stops

        self._applicable_alerts = applicable_alerts

    @property
    def underway(self):
        """
        Returns `True` if the trip is underway (or will be shortly), `False` otherwise

        This is determined based on whether or not the `vehicle` field is provided by the GTFS feed and whether the
        timestamp for that field is future dated.

        It appears that on the A division lines (and the L), the presence of a VehiclePosition message is appropriate to
        conclude the train has departed its origin station. However, on the B division lines, a VehiclePosition message
        is provided prior to departure from the origin station. This message is future dated for the scheduled departure
        time of the train. Therefore we will only consider a train to be underway when it both has a VehiclePosition
        message and the timestamp associated with that message is in the past/present.
        """
        if self._vehicle_update is None:
            return False

        last_update = datetime.datetime.fromtimestamp(self._vehicle_update.timestamp)

        # Only trips whose most recent update is not future-dated are considered to be underway
        buffer_to_account_for_clock_desync = datetime.timedelta(minutes=1)
        if last_update <= self._feed_datetime + buffer_to_account_for_clock_desync:
            return True
        else:
            return False

    @property
    def train_assigned(self):
        """
        Returns `True` if this trip has been assigned a train, `False` otherwise

        This assignment usually happens at the origin station within 30 minutes of departure. Once a trip is underway
        it will typically continue to be assigned until it reaches its terminal
        """
        return True if self._trip_update.trip.Extensions[nyct_subway_pb2.nyct_trip_descriptor].is_assigned else False

    @property
    def trip_id(self):
        """
        Returns the GTFS trip ID string corresponding to this trip

        NOTE that per the discussion in: https://groups.google.com/g/mtadeveloperresources/c/RI2JB5DzIls/m/XJlIOvFQAgAJ
        this field is not sufficient to uniquely identify a trip in all cases. Notably, during the 1 hour "repeat" in
        the first hour of daylight savings time each Spring.

        e.g. 090850_1..N03R

        090850 - Number of 1/100ths of a minute past midnight that this train was scheduled to depart its origin station
        1 - route_id
        N - Northbound train (or Grand Central bound shuttle).
            Could also be S for southbound trains and Times Square bound shuttles
        03R - Internal code to identify this stopping pattern (i.e. express/local, day/weekend/late night service, etc.)
        """
        return self._trip_update.trip.trip_id

    @property
    def nyc_train_id(self):
        """
        The internal NYC train ID that will be used to represent the train on this trip

        e.g. 01 1508+ SFT/242

        From the NYCT GTFS-realtime specification:
        ```
            This field is meant for internal use only. It provides
            an easy way to associated GTFS-RT trip identifiers
            with NYCT rail operations identifier
            The ATS office system assigns unique train
            identification (Train ID) to each train operating
            within or ready to enter the mainline of the
            monitored territory. An example of this is 06 0123+ PEL/BBR
            and is decoded as follows:

            The first character represents the trip type
            designator. 0 identifies a scheduled revenue trip.
            Other revenue trip values that are a result of a
            change to the base schedule include; [= reroute], [/
            skip stop], [$ turn train] also known as shortly lined
            service.

            The second character 6 represents the trip line i.e.
            number 6 train

            The third set of characters identify the decoded
            origin time. The last character may be blank “on
            the whole minute” or + “30 seconds”
            Note: Origin times will not change when there is a
            trip type change.
            This is followed by a three character “Origin
            Location” / “Destination Location”
        ```
        """
        return self._trip_update.trip.Extensions[nyct_subway_pb2.nyct_trip_descriptor].train_id

    @property
    def route_id(self):
        """
        Returns the GTFS route ID string corresponding to this trip, usually this corresponds to the train
        letter/number (e.g. "1", "A", "F", etc.). However, for some trains, this might be slightly different to the
        publicly used identifier (e.g. the Grand Central shuttle is identified as "GS", the Franklin Av shuttle
         is identified as "FS"). See static GTFS file, `trips.txt` for a complete listing.
        """
        return self._trip_update.trip.route_id

    @property
    def start_date(self):
        """
        A datetime.date object corresponding to the date on which this trip started. Note that since trips take time to
        complete it's possible for a trip to have started before the current date.
        """
        return datetime.datetime.strptime(self._trip_update.trip.start_date, "%Y%m%d").date()

    @property
    def last_position_update(self):
        """
        A datetime.datetime object (or None) which represents the last time that this train gave a position update.
        This is important when determining a stalled train condition. This field is only available after the train gets
        underway. If this field is accessed before `Train.underway` is True, None is returned

        From the NYCT GTFS-realtime spec:
        ```
            The motivation to include VehiclePosition is to provide the timestamp field. This is the time of the last
            detected movement of the train. This allows feed consumers to detect the situation when a train stops
            moving (aka stalled). The platform countdown clocks only count down when trains are moving
            otherwise they persist the last published arrival time for that train. If one wants to mimic this
            behavioryou must first determine the absence of movement (stalled train condition) ), then the
            countdown must be stopped.

            As an example, a countdown could be stopped for a trip when the difference between the timestamp in
            the VehiclePosition and the timestamp in the field header is greater than, 90 seconds.
            Note: since VehiclePosition information is not provided until the train starts moving, it is recommended
            that feed consumers use the origin terminal departure to determine a train stalled condition.
        ```
        """
        if not self.underway:
            return None

        return datetime.datetime.fromtimestamp(self._vehicle_update.timestamp)

    @property
    def location(self):
        """
        Returns the GTFS stop ID str for the next stop that this train will visit, or the current stop that the train is
        stopped at. This value is updated immediately upon departure from the prior station. This field is only
        available after the train gets underway. If this field is accessed before `Train.underway` is True,
        None is returned
        """
        if not self.underway:
            return None

        return self._vehicle_update.stop_id

    @property
    def location_status(self):
        """
        This train's relationship to the value provided by `Trip.location`. This field is only available after the train
        gets underway. If this field is accessed before `Train.underway` is True, None is returned

        Provided as a string, which will be one of: "INCOMING_AT", "STOPPED_AT", and "IN_TRANSIT_TO"

        From the GTFS-realtime spec:
        ```
            INCOMING_AT	    The vehicle is just about to arrive at the stop (on a stop display, the vehicle symbol
                            typically flashes).
            STOPPED_AT	    The vehicle is standing at the stop.
            IN_TRANSIT_TO	The vehicle has departed the previous stop and is in transit.
        ```
        """
        if not self.underway:
            return None

        str_translation = {
            gtfs_realtime_pb2.VehiclePosition.VehicleStopStatus.INCOMING_AT: "INCOMING_AT",
            gtfs_realtime_pb2.VehiclePosition.VehicleStopStatus.STOPPED_AT: "STOPPED_AT",
            gtfs_realtime_pb2.VehiclePosition.VehicleStopStatus.IN_TRANSIT_TO: "IN_TRANSIT_TO"
        }
        return str_translation[self._vehicle_update.current_status]

    @property
    def current_stop_sequence_index(self):
        """
        An integer indicating the index of the stop represented by `Trip.location` along the route of the train. This
        field is only available after the train gets underway. If this field is accessed before `Train.underway` is
        `True, None is returned

        From the GTFS-realtime specification:
        ```
            The stop sequence index of the current stop. The meaning of current_stop_sequence (i.e., the stop that it
            refers to) is determined by current_status. If current_status is missing IN_TRANSIT_TO is assumed.
        ```
        """
        if not self.underway:
            return None

        return self._vehicle_update.current_stop_sequence

    @property
    def stop_time_updates(self):
        """
        Returns a list of `StopTimeUpdate` objects corresponding to the remaining stops (including the current stop if
        the train is at a station) on this trip, with up-to-date estimates of arrival and departure times for each stop,
        as well as scheduled and actual track number information. See `StopTimeUpdate` for more details

        From the NYCT GTFS-realtime specification:
        ```
            This includes all future Stop Times for the trip but StopTimes from the past
            are omitted. The first StopTime in the sequence is the stop the train is
            currently approaching, stopped at or about to leave. A stop is dropped from
            the sequence when the train departs the station.
        ```
        """
        return [
            StopTimeUpdate(stop_time_update, stops=self._stops)
            for stop_time_update in self._trip_update.stop_time_update
        ]

    @property
    def shape_id(self):
        """
        Parses the `Trip.trip_id` field to determine the GTFS shape ID string for this trip. This identifies the train
        line, direction of travel, and stopping pattern (i.e. express/local, day/weekend/late night service, etc.) and
        corresponds to the "shape_id" column in `trips.txt` from the static GTFS data feed.

        For example, a Southbound 1 train might have a shape ID of: "1..S03R"
        """
        return self.trip_id.split('_')[1]

    @property
    def direction(self):
        """
        Parses the `Trip.shape_id` field to determine direction of travel

        Returns either "N" for northbound trains (and Grand Central bound shuttles) or "S" for southbound trains
        (and Times Square bound shuttles)
        """
        return self.shape_id.split('..')[1][0] if '..' in self.trip_id else self.shape_id.split('.')[1][0]

    @property
    def departure_time(self):
        """
        Pareses the `Trip.trip_id` field to determine scheduled departure time from origin station

        Returns a datetime.datetime object
        """
        minutes_past_midnight = float(self.trip_id.split('_')[0]) / 100
        midnight_on_start_date = datetime.datetime.combine(self.start_date, datetime.time.min)
        return midnight_on_start_date + datetime.timedelta(minutes=minutes_past_midnight)

    @property
    def headsign_text(self):
        """
        Finds the "headsign text" for this trip, which is usually the name of the terminal station,
        e.g. "Wakefield-241 St"

        If trip shape information is unavailable or the trip shape ID doesn't match anything in the static GTFS
        schedule, this function attempts to identify this trip's terminal station by the real-time stop schedule,
        and if available, returns the name of the terminal station

        Returns a string representing the headsign text
        """
        try:
            return self._trip_shapes.get_headsign_text(self.shape_id)
        except ValueError:
            if len(self.stop_time_updates) > 0 and self.stop_time_updates[-1].stop_name is not None:
                return self.stop_time_updates[-1].stop_name
            return None

    @property
    def has_delay_alert(self):
        """
        Check if this trip has a published delay alert. Per the NYCT GTFS-realtime spec, all alerts in this feed are
        for train delays, so this field simply reflects the binary presence of one or more alerts corresponding
        to this trip in the GTFS-realtime feed.

        NOTE: that this not a necessary condition for a delayed train. That is, it is possible for a train to
        be delayed (particularly in the B division), without this function returning true.

        From the NYCT GTFS-realtime spec:
        ```
            The only alerts included in the NYCT Subway GTFS-realtime feed are notifications about delayed trains
            therefore the entity is always a trip. In general, when a train is shown as ‘delayed’ on the station
            countdown clocks, an Alert is generated for that trip in the feed.
        ```
        """
        return len(self._applicable_alerts) > 0

    def headed_to_stop(self, stop_id):
        """
        Check if this trip is heading for a given stop_id. Note: this check does not include past stops, but does
        include the current stop if the train has not yet departed

        :param stop_id The ID of the stop to check (e.g. "123S")
        :return True iff this trip is going to visit (or is present at) the provided stop id
        """
        return stop_id in (stop.stop_id for stop in self.stop_time_updates)

    def __str__(self):
        string = ""

        if self.has_delay_alert:
            string += "DELAYED "

        string += f"{'Southbound' if self.direction == 'S' else 'Northbound'} {self.route_id}"

        headsign_text = self.headsign_text
        if headsign_text:
            string += f" to {headsign_text}"
        else:
            string += f" ({self.shape_id})"

        string += f", {'departed origin' if self.underway else 'departs origin'} " \
                  f"{self.departure_time.strftime('%H:%M:%S')}"

        if self.train_assigned and not self.underway:
            string += ' - train assigned'

        if self.underway:
            string += f", Currently {self.location_status} {self._stops.get_station_name(self.location)}, " \
                      f"last update at {self.last_position_update.strftime('%H:%M:%S')}"

        return string

    def __repr__(self):
        string = f"{{\"{self.trip_id}\", {'Assgn,' if self.train_assigned and not self.underway else ''}"
        if self.has_delay_alert:
            string += "DELAY, "
        if self.underway:
            string += f"{self.location_status} {self.location} @{self.last_position_update.strftime('%H:%M:%S')}"
        string += "}"
        return string
