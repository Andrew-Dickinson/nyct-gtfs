import unittest
from datetime import datetime, date, timedelta

from nyct_gtfs import NYCTFeed, StopTimeUpdate
from nyct_gtfs.compiled_gtfs import gtfs_realtime_pb2, nyct_subway_pb2


class TestFeedParseADivision(unittest.TestCase):
    def setUp(self) -> None:
        with open('test_data/a_division.nyct.gtfsrt', 'rb') as f:
            self.feed = NYCTFeed('1', api_key=None, fetch_immediately=False)
            self.feed.load_gtfs_bytes(f.read())

    def test_feed_header(self):
        self.assertTrue(repr(self.feed).startswith("{NYCT_GTFS_Realtime_Feed, @2021-11-26 15:56:25, [{\"090300_1..N\", "
                                                   "IN_TRANSIT_TO 107N @15:56:17}, {"))
        self.assertEqual("NYCT Subway Feed (gtfs), generated 2021-11-26 15:56:25, containing 285 trips", str(self.feed))
        self.assertEqual('1.0', self.feed.gtfs_realtime_version)
        self.assertEqual('1.0', self.feed.nyct_subway_gtfs_version)
        self.assertEqual(datetime.fromisoformat("2021-11-26T15:56:25"), self.feed.last_generated)
        self.assertEqual(["1", "2", "3", "4", "5", "6", "7", "S"], list(self.feed.trip_replacement_periods.keys()))
        for line, trip_replacement_period in self.feed.trip_replacement_periods.items():
            self.assertEqual(datetime.fromisoformat("2021-11-26T16:26:25"), trip_replacement_period)

    def test_train_parse_underway(self):
        trip = self.feed.trips[0]

        self.assertEqual(30, trip.current_stop_sequence_index)
        self.assertEqual(datetime.fromisoformat("2021-11-26T15:03:00"), trip.departure_time)
        self.assertEqual("N", trip.direction)
        self.assertEqual(False, trip.has_delay_alert)
        self.assertEqual("Van Cortlandt Park-242 St", trip.headsign_text)
        self.assertEqual(datetime.fromisoformat("2021-11-26T15:56:17"), trip.last_position_update)
        self.assertEqual('107N', trip.location)
        self.assertEqual('IN_TRANSIT_TO', trip.location_status)
        self.assertEqual('/1 1503  SFT/242', trip.nyc_train_id)
        self.assertEqual('1', trip.route_id)
        self.assertEqual('1..N', trip.shape_id)
        self.assertEqual(date.fromisoformat("2021-11-26"), trip.start_date)
        self.assertEqual(True, trip.train_assigned)
        self.assertEqual('090300_1..N', trip.trip_id)
        self.assertEqual(True, trip.underway)

        self.assertEqual('{"090300_1..N", IN_TRANSIT_TO 107N @15:56:17}', repr(trip))
        self.assertEqual('Northbound 1 to Van Cortlandt Park-242 St, departed origin 15:03:00, Currently IN_TRANSIT_TO 215 St, '
                         'last update at 15:56:17', str(trip))

        self.assertEqual(False, trip.headed_to_stop('asdfljasd'))
        self.assertEqual(False, trip.headed_to_stop('123N'))
        self.assertEqual(False, trip.headed_to_stop('R25N'))
        self.assertEqual(True, trip.headed_to_stop('106N'))
        self.assertEqual(False, trip.headed_to_stop('106S'))
        self.assertEqual(False, trip.headed_to_stop('106'))

        remaining_stops = trip.stop_time_updates
        self.assertEqual(5, len(remaining_stops))

        self.assertEqual('107N', remaining_stops[0].stop_id)
        self.assertEqual('215 St', remaining_stops[0].stop_name)
        self.assertEqual(datetime.fromisoformat('2021-11-26T15:57:47'), remaining_stops[0].arrival)
        self.assertEqual(datetime.fromisoformat('2021-11-26T15:57:47'), remaining_stops[0].departure)
        self.assertEqual("{ID: 107N, Arr: 15:57:47, Dep: 15:57:47, Sched: T4, }", repr(remaining_stops[0]))
        self.assertEqual("215 St: Projected Arrival 15:57:47. Projected Departure 15:57:47. Scheduled to arrive on "
                         "track 4. ", str(remaining_stops[0]))

        self.assertEqual('106N', remaining_stops[1].stop_id)
        self.assertEqual('Marble Hill-225 St', remaining_stops[1].stop_name)
        self.assertEqual(datetime.fromisoformat('2021-11-26T15:59:17'), remaining_stops[1].arrival)
        self.assertEqual(datetime.fromisoformat('2021-11-26T15:59:17'), remaining_stops[1].departure)

        self.assertEqual('104N', remaining_stops[2].stop_id)
        self.assertEqual('231 St', remaining_stops[2].stop_name)
        self.assertEqual(datetime.fromisoformat('2021-11-26T16:00:47'), remaining_stops[2].arrival)
        self.assertEqual(datetime.fromisoformat('2021-11-26T16:00:47'), remaining_stops[2].departure)

        self.assertEqual('103N', remaining_stops[3].stop_id)
        self.assertEqual('238 St', remaining_stops[3].stop_name)
        self.assertEqual(datetime.fromisoformat('2021-11-26T16:02:17'), remaining_stops[3].arrival)
        self.assertEqual(datetime.fromisoformat('2021-11-26T16:02:17'), remaining_stops[3].departure)

        self.assertEqual('101N', remaining_stops[4].stop_id)
        self.assertEqual('Van Cortlandt Park-242 St', remaining_stops[4].stop_name)
        self.assertEqual(datetime.fromisoformat('2021-11-26T16:03:47'), remaining_stops[4].arrival)
        self.assertEqual(None, remaining_stops[4].departure)

        for stop in remaining_stops:
            self.assertEqual('4', stop.scheduled_track)
            self.assertEqual(False, stop.unexpected_track_arrival)


    def test_train_parse_assigned(self):
        trip = self.feed.trips[22]

        self.assertEqual(None, trip.current_stop_sequence_index)
        self.assertEqual(datetime.fromisoformat("2021-11-26T15:56:30"), trip.departure_time)
        self.assertEqual("S", trip.direction)
        self.assertEqual(False, trip.has_delay_alert)
        self.assertEqual('South Ferry', trip.headsign_text)
        self.assertEqual(None, trip.last_position_update)
        self.assertEqual(None, trip.location)
        self.assertEqual(None, trip.location_status)
        self.assertEqual('01 1556+ 242/SFT', trip.nyc_train_id)
        self.assertEqual('1', trip.route_id)
        self.assertEqual('1..S03R', trip.shape_id)
        self.assertEqual(date.fromisoformat("2021-11-26"), trip.start_date)
        self.assertEqual(True, trip.train_assigned)
        self.assertEqual('095650_1..S03R', trip.trip_id)
        self.assertEqual(False, trip.underway)

        self.assertEqual('{"095650_1..S03R", Assgn,}', repr(trip))
        self.assertEqual('Southbound 1 to South Ferry, departs origin 15:56:30 - train assigned', str(trip))

        self.assertEqual(False, trip.headed_to_stop('asdfljasd'))
        self.assertEqual(False, trip.headed_to_stop('R25N'))
        self.assertEqual(True, trip.headed_to_stop('123S'))
        self.assertEqual(False, trip.headed_to_stop('123N'))
        self.assertEqual(False, trip.headed_to_stop('123'))

        self.assertEqual(38, len(trip.stop_time_updates))

        self.assertEqual('101S', trip.stop_time_updates[0].stop_id)
        self.assertEqual('Van Cortlandt Park-242 St', trip.stop_time_updates[0].stop_name)
        self.assertEqual(None, trip.stop_time_updates[0].arrival)
        self.assertEqual("1", trip.stop_time_updates[0].actual_track)

        self.assertEqual('142S', trip.stop_time_updates[-1].stop_id)
        self.assertEqual('South Ferry', trip.stop_time_updates[-1].stop_name)

        for stop in trip.stop_time_updates:
            self.assertEqual('1', stop.scheduled_track)
            self.assertEqual(False, stop.unexpected_track_arrival)

    def test_train_parse_unassigned(self):
        trip = self.feed.trips[25]

        self.assertEqual(None, trip.current_stop_sequence_index)
        self.assertEqual(datetime.fromisoformat("2021-11-26T16:06:30"), trip.departure_time)
        self.assertEqual("S", trip.direction)
        self.assertEqual(False, trip.has_delay_alert)
        self.assertEqual("South Ferry", trip.headsign_text)
        self.assertEqual(None, trip.last_position_update)
        self.assertEqual(None, trip.location)
        self.assertEqual(None, trip.location_status)
        self.assertEqual('01 1606+ 238/SFT', trip.nyc_train_id)
        self.assertEqual('1', trip.route_id)
        self.assertEqual('1..S04R', trip.shape_id)
        self.assertEqual(date.fromisoformat("2021-11-26"), trip.start_date)
        self.assertEqual(False, trip.train_assigned)
        self.assertEqual('096650_1..S04R', trip.trip_id)
        self.assertEqual(False, trip.underway)

        self.assertEqual('{"096650_1..S04R", }', repr(trip))
        self.assertEqual('Southbound 1 to South Ferry, departs origin 16:06:30', str(trip))

        self.assertEqual(False, trip.headed_to_stop('asdfljasd'))
        self.assertEqual(False, trip.headed_to_stop('R25N'))
        self.assertEqual(True, trip.headed_to_stop('123S'))
        self.assertEqual(False, trip.headed_to_stop('123N'))
        self.assertEqual(False, trip.headed_to_stop('123'))

        self.assertEqual(37, len(trip.stop_time_updates))

        self.assertEqual('103S', trip.stop_time_updates[0].stop_id)
        self.assertEqual('238 St', trip.stop_time_updates[0].stop_name)
        self.assertEqual(None, trip.stop_time_updates[0].arrival)

        self.assertEqual('142S', trip.stop_time_updates[-1].stop_id)
        self.assertEqual('South Ferry', trip.stop_time_updates[-1].stop_name)

        for stop in trip.stop_time_updates:
            self.assertEqual('1', stop.scheduled_track)
            self.assertEqual(False, stop.unexpected_track_arrival)

    def test_stop_time_bogus_id(self):
        protobuf_stop_time = gtfs_realtime_pb2.TripUpdate.StopTimeUpdate()
        protobuf_stop_time.stop_id = "!@#$%^&"

        stop_time = StopTimeUpdate(protobuf_stop_time)

        self.assertEqual("!@#$%^&", stop_time.stop_id)
        self.assertEqual("{ID: !@#$%^&, }", repr(stop_time))
        self.assertEqual("!@#$%^&: ", str(stop_time))
        self.assertEqual(None, stop_time.stop_name)
        self.assertEqual(None, stop_time.arrival)
        self.assertEqual(None, stop_time.departure)
        self.assertEqual(None, stop_time.actual_track)
        self.assertEqual(None, stop_time.scheduled_track)
        self.assertEqual(False, stop_time.unexpected_track_arrival)

    def test_stop_time_track_mismatch(self):
        protobuf_stop_time = gtfs_realtime_pb2.TripUpdate.StopTimeUpdate()
        protobuf_stop_time.stop_id = "123S"

        stop_time = StopTimeUpdate(protobuf_stop_time)

        self.assertEqual("123S", stop_time.stop_id)
        self.assertEqual("72 St", stop_time.stop_name)
        self.assertEqual(None, stop_time.arrival)
        self.assertEqual(None, stop_time.departure)
        self.assertEqual(None, stop_time.scheduled_track)
        self.assertEqual(None, stop_time.actual_track)
        self.assertEqual(False, stop_time.unexpected_track_arrival)

        protobuf_stop_time.Extensions[nyct_subway_pb2.nyct_stop_time_update].scheduled_track = "1"
        protobuf_stop_time.Extensions[nyct_subway_pb2.nyct_stop_time_update].actual_track = "2"

        self.assertEqual("1", stop_time.scheduled_track)
        self.assertEqual("2", stop_time.actual_track)
        self.assertEqual(True, stop_time.unexpected_track_arrival)
        self.assertEqual("{ID: 123S, Sched: T1, Act: T2}", repr(stop_time))
        self.assertEqual("72 St: Scheduled to arrive on track 1. Actually arriving on track 2. ", str(stop_time))

        protobuf_stop_time.Extensions[nyct_subway_pb2.nyct_stop_time_update].ClearField('actual_track')
        self.assertEqual("1", stop_time.scheduled_track)
        self.assertEqual(None, stop_time.actual_track)
        self.assertEqual(False, stop_time.unexpected_track_arrival)

        protobuf_stop_time.Extensions[nyct_subway_pb2.nyct_stop_time_update].ClearField('scheduled_track')
        protobuf_stop_time.Extensions[nyct_subway_pb2.nyct_stop_time_update].actual_track = "2"
        self.assertEqual(None, stop_time.scheduled_track)
        self.assertEqual("2", stop_time.actual_track)
        self.assertEqual(False, stop_time.unexpected_track_arrival)


class TestParseCustomStaticFiles(unittest.TestCase):
    def setUp(self) -> None:
        with open('test_data/a_division.nyct.gtfsrt', 'rb') as f:
            with open('../nyct_gtfs/gtfs_static/stops.txt', 'r') as stops:
                with open('../nyct_gtfs/gtfs_static/trips.txt', 'r') as trips:
                    self.feed = NYCTFeed('1', api_key=None, fetch_immediately=False, stops_txt=stops, trips_txt=trips)
                    self.feed.load_gtfs_bytes(f.read())

    def test_read_from_trips(self):
        trip = self.feed.trips[25]
        self.assertEqual('Southbound 1 to South Ferry, departs origin 16:06:30', str(trip))

    def test_read_from_stops(self):
        trip = self.feed.trips[25]
        self.assertEqual('238 St', trip.stop_time_updates[0].stop_name)


class TestFeedConstructor(unittest.TestCase):
    def test_feed_constructor_bogus_feed(self):
        self.assertRaises(ValueError, NYCTFeed, "alskfjdk", api_key=None, fetch_immediately=False)

    def test_feed_constructor_ace(self):
        ace_feed = NYCTFeed("A", api_key=None, fetch_immediately=False)
        self.assertEqual("https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace", ace_feed._feed_url)

    def test_feed_constructor_ace_link(self):
        ace_feed = NYCTFeed("https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace", api_key=None,
                            fetch_immediately=False)
        self.assertEqual("https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace", ace_feed._feed_url)


class TestFeedParseBDivision(unittest.TestCase):
    def setUp(self) -> None:
        with open('test_data/b_division.nyct.gtfsrt', 'rb') as f:
            self.feed = NYCTFeed('1', api_key=None, fetch_immediately=False)
            self.feed.load_gtfs_bytes(f.read())

    def test_fake_underway(self):
        self.assertIsNotNone(self.feed.trips[19]._vehicle_update)
        self.assertEqual(False, self.feed.trips[19].underway)

    def test_feed_filtering(self):
        self.assertEqual(
            20,
            len(self.feed.filter_trips(line_id="A", updated_after=self.feed.last_generated - timedelta(minutes=5)))
        )

    def test_automatic_headsign_gen(self):
        self.assertEqual('Inwood-207 St', self.feed.trips[0].headsign_text)
        self.assertEqual('A..N', self.feed.trips[0].shape_id)

class TestFeedParseDelayAlerts(unittest.TestCase):
    def setUp(self) -> None:
        with open('test_data/2_delay.nyct.gtfsrt', 'rb') as f:
            self.feed = NYCTFeed('2', api_key=None, fetch_immediately=False)
            self.feed.load_gtfs_bytes(f.read())

    def test_feed_filtering(self):
        self.assertEqual(
            1,
            len(self.feed.filter_trips(line_id="2", has_delay_alert=True))
        )

        delayed_trip = self.feed.filter_trips(line_id="2", has_delay_alert=True)[0]
        self.assertEqual('{"120700_2..N01R", DELAY, IN_TRANSIT_TO 201N @21:42:41}', repr(delayed_trip))
        self.assertEqual('DELAYED Northbound 2 to Wakefield-241 St, departed origin 20:07:00, '
                         'Currently IN_TRANSIT_TO Wakefield-241 St, last update at 21:42:41', str(delayed_trip))


class TestFeedFiltering(unittest.TestCase):
    def setUp(self) -> None:
        with open('test_data/a_division.nyct.gtfsrt', 'rb') as f:
            self.feed = NYCTFeed('1', api_key=None, fetch_immediately=False)
            self.feed.load_gtfs_bytes(f.read())

    def test_feed_filtering(self):
        self.assertEqual(36, len(self.feed.filter_trips(line_id="1")))
        self.assertRaises(TypeError, self.feed.filter_trips, line_id=1)
        self.assertEqual(17, len(self.feed.filter_trips(line_id="1", travel_direction="N")))
        self.assertEqual(12, len(self.feed.filter_trips(line_id="1", travel_direction="N", headed_for_stop_id="123N")))
        self.assertEqual(12, len(self.feed.filter_trips(line_id="1", headed_for_stop_id="123N")))
        self.assertEqual(12, len(self.feed.filter_trips(line_id="1", headed_for_stop_id=["123N"])))
        self.assertEqual(26, len(self.feed.filter_trips(line_id="1", headed_for_stop_id=["123N", "123S"])))
        self.assertRaises(TypeError, self.feed.filter_trips, headed_for_stop_id=137123)
        self.assertEqual(9, len(self.feed.filter_trips(line_id="2", underway=False)))
        self.assertEqual(11, len(self.feed.filter_trips(line_id="3", underway=False, train_assigned=False)))
        self.assertEqual(2, len(self.feed.filter_trips(line_id="3", underway=False, train_assigned=True)))
        self.assertEqual(16, len(self.feed.filter_trips(shape_id="1..S03R")))
        self.assertEqual(16, len(self.feed.filter_trips(shape_id=["1..S03R"])))
        self.assertEqual(19, len(self.feed.filter_trips(shape_id=["1..S03R", "1..S04R"])))
        self.assertRaises(TypeError, self.feed.filter_trips, shape_id=137123)

        self.assertEqual(
            23,
            len(self.feed.filter_trips(line_id="4", updated_after=self.feed.last_generated - timedelta(minutes=5)))
        )

        self.assertEqual(
            21,
            len(
                self.feed.filter_trips(
                    line_id=["7", "7X"],
                    updated_after=self.feed.last_generated - timedelta(minutes=5)
                )
            )
        )

        self.assertEqual(
            16,
            len(
                self.feed.filter_trips(
                    line_id=["7"],
                    updated_after=self.feed.last_generated - timedelta(minutes=5)
                )
            )
        )


class TestBadTripShape(unittest.TestCase):
    def setUp(self) -> None:
        with open('test_data/2_train_with_0_shape.nyct.gtfsrt', 'rb') as f:
            self.feed = NYCTFeed('1', api_key=None, fetch_immediately=False)
            self.feed.load_gtfs_bytes(f.read())

    def test_bad_trip_shape_doesnt_cause_exception(self):
        for trip in self.feed.trips:
            assert trip.direction in ["N", "S", None]

    def test_none_as_valid_trip_shape(self):
        assert self.feed.trips[76].shape_id == '0'
        assert self.feed.trips[76].direction is None


if __name__ == '__main__':
    unittest.main()