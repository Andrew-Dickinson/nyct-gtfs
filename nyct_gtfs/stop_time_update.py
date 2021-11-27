import datetime

from nyct_gtfs.gtfs_static_types import Stations
from nyct_gtfs.compiled_gtfs import nyct_subway_pb2


class StopTimeUpdate:
    """
    Represents a predicted future stop at a specific location for a trip. Includes the arrival/departure times and
    scheduled/actual track the train will arrive on.

    From the NYCT GTFS-realtime spec:
    ```
        For most stops along the trip path, NYC subway schedules define a transit time. Departure times are
        supplied for the Origin Terminal, arrival times for the Destination Terminal. Transit times are provided
        at all in-between stops except at those locations where there are “scheduled holds”. At those locations
        both arrival and departure times are given.
        Note that the predicted times are not updated when the train is not moving. Feed consumers can detect
        this condition using the timestamp in the VehiclePosition message.
    ```
    """
    def __init__(self, stop_time_update, stops=None):
        self._stop_time_update = stop_time_update

        if stops is None:
            stops = Stations()

        self._stops = stops

    @property
    def stop_id(self):
        """
        The GTFS stop ID str for that this stop update corresponds to, including direction indicator (i.e. "N" or "S")

        From the NYCT GTFS-realtime spec:
        ```
            parent_station (from stops.txt) and the direction the train is moving to (‘N’
            or ‘S’). For example, a northbound trip Hunts Point Ave stop is 613N.
        ```
        """
        return self._stop_time_update.stop_id

    @property
    def arrival(self):
        """
        A datetime.datetime object corresponding to the predicted arrival/transit time for this update or None
        if this field is not available in the data feed

        From the NYCT GTFS-realtime spec:
        ```
            Predicted arrival time when there is a scheduled arrival time, predicted
            transit time if there is a scheduled transit time, not used otherwise.
        ```
        """
        if not self._stop_time_update.HasField('arrival'):
            return None

        return datetime.datetime.fromtimestamp(self._stop_time_update.arrival.time)

    @property
    def departure(self):
        """
        A datetime.datetime object corresponding to the predicted departure/transit time for this update or None
        if this field is not available in the data feed

        From the NYCT GTFS-realtime spec:
        ```
            Predicted departure time when there is a scheduled departure time,
            predicted transit time if there is a scheduled transit time, not used
            otherwise
        ```
        """
        if not self._stop_time_update.HasField('departure'):
            return None

        return datetime.datetime.fromtimestamp(self._stop_time_update.departure.time)

    @property
    def scheduled_track(self):
        """
        A 1-character string representing the track that the train is scheduled to arrive at for this stop event
        (or None if this information is not provided).

        From the NYCT GTFS-realtime spec:
        ```
            This is an NYCT Subway extension. It provides
            the scheduled station arrival track. This may
            change enroute during automated rerouting
            operations. The following is the Manhattan track
            configurations:
            1: southbound local
            2: southbound express
            3: northbound express
            4: northbound local
            In the Bronx (except Dyre Ave line)
            M: bi-directional express (in the AM express to
            Manhattan, in the PM express away).
            The Dyre Ave line is configured:
            1: southbound
            2: northbound
            3: bi-directional
        ```
        """
        if not self._stop_time_update.Extensions[nyct_subway_pb2.nyct_stop_time_update].HasField('scheduled_track'):
            return None

        return self._stop_time_update.Extensions[nyct_subway_pb2.nyct_stop_time_update].scheduled_track

    @property
    def actual_track(self):
        """
        A 1-character string representing the track that the train is actually going to arrive at for this stop event
        (or None if this information is not provided). See `StopTimeUpdate.scheduled_track`

        From the NYCT GTFS-realtime spec:
        ```
            This is the actual track that the train is operating
            on and can be used to determine if a train is
            operating according to its current schedule
            (plan).
            The actual track is not known before the train
            leaves the previous station. Therefore, the
            NYCT feed sets this field only for the first station
            of the remaining trip.
        ```
        """
        if not self._stop_time_update.Extensions[nyct_subway_pb2.nyct_stop_time_update].HasField('actual_track'):
            return None

        return self._stop_time_update.Extensions[nyct_subway_pb2.nyct_stop_time_update].actual_track

    @property
    def unexpected_track_arrival(self):
        """
        Checks if this train will be arriving on an unexpected track. This can only be true if we have received both an
        `actual_track` and `scheduled_track` from the feed. Per the NYCT GTFS-realtime spec, this is generally only true
        for the next stop for each train, and is not guaranteed to be provided.

        Therefore, this function is conservative. That is, when this function returns `True`, you can be quite confident
        that the train this update corresponds to is running on an unexpected track (and therefore you may want to
        change your display logic per the note below). However, when this function returns `False`, that does not
        necessarily guarantee that the train is running on the expected tracks. You may need to check an earlier
        StopTimeUpdate, or the `actual_track` may not have been determined yet or may not be available.

        From the NYCT GTFS-realtime spec:
        ```
            For a train enroute, the actual track may differ from the scheduled track. This could be
            the result of manually rerouting the train from its scheduled track. When this occurs, prediction data
            may become unreliable since the train is no longer operating in accordance to its schedule. The rules
            engine for the “countdown” clocks will remove this train from all scheduled station signage. It is highly
            probable that the train will be rerouted back to its schedule track at some future point. When this
            happens train prediction for this train will return to the “countdown” clocks.
            It is not unusual for the schedule/actual track numbers to differ at the origin and destination terminals.
        ```
        """
        if self.scheduled_track is None or self.actual_track is None:
            return False

        return self.scheduled_track != self.actual_track

    @property
    def stop_name(self):
        """
        Look up `StopTimeUpdate.stop_id` in `stops.txt` to determine the human-readable name for the stop in this
        update. If `StopTimeUpdate.stop_id` is not found in `stops.txt`, returns None
        """
        try:
            return self._stops.get_station_name(self.stop_id)
        except ValueError:
            return None

    def __repr__(self):
        string = f"{{ID: {self.stop_id}, "

        if self.arrival:
            string += f"Arr: {self.arrival.strftime('%H:%M:%S')}, "

        if self.departure:
            string += f"Dep: {self.departure.strftime('%H:%M:%S')}, "

        if self.scheduled_track:
            string += f"Sched: T{self.scheduled_track}, "

        if self.actual_track:
            string += f"Act: T{self.actual_track}"

        string += "}"

        return string

    def __str__(self):
        if self.stop_name is not None:
            stop_name = self.stop_name
        else:
            stop_name = self.stop_id

        string = f"{stop_name}: "

        if self.arrival:
            string += f"Projected Arrival {self.arrival.strftime('%H:%M:%S')}. "

        if self.departure:
            string += f"Projected Departure {self.arrival.strftime('%H:%M:%S')}. "

        if self.scheduled_track:
            string += f"Scheduled to arrive on track {self.scheduled_track}. "

        if self.actual_track:
            string += f"Actually arriving on track {self.actual_track}. "

        return string


