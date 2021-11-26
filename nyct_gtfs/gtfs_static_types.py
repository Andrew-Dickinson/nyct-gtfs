import csv
import io
import os
import pathlib


class TripShapes:
    """
    Stores the trip shape information from the `trips.txt` static GTFS file,
    currently just `shape_id` and `trip_headsign` for each trip shape
    """
    def load_from_file(self, fp):
        reader = csv.reader(fp)
        for i, row in enumerate(reader):
            if i != 0:
                shape_id_implicit = row[2].split('_')[2]
                shape_id_explicit = ""
                if len(row) >= 7:
                    shape_id_explicit = row[6]
                headsign_text = row[3]
                if shape_id_explicit:
                    assert shape_id_implicit == shape_id_explicit

                if shape_id_implicit not in self.trip_shapes:
                    self.trip_shapes[shape_id_implicit] = {
                        'trip_headsign': headsign_text
                    }
                else:
                    assert self.trip_shapes[shape_id_implicit]['trip_headsign'] == headsign_text

    def __init__(self, trips_txt=None):
        if trips_txt is None:
            trips_txt = os.path.join(pathlib.Path(__file__).parent.resolve(), "gtfs_static", "trips.txt")

        self.trip_shapes = {}
        if isinstance(trips_txt, str):
            with open(trips_txt, 'r') as fp:
                self.load_from_file(fp)
        elif isinstance(trips_txt, io.IOBase):
            self.load_from_file(trips_txt)

    def get_headsign_text(self, shape_id):
        """
        Finds the "headsign text" for a given GTFS trip shape id, which is usually the name of the terminal station,
        e.g. "Wakefield-241 St"

        :raises: ValueError if the given shape_id is not found in the `trips.txt` dataset
        """
        if shape_id not in self.trip_shapes:
            raise ValueError(f"Invalid shape_id: {shape_id}, not found in trips.txt file")
        return self.trip_shapes[shape_id]['trip_headsign']


class Stations:
    """
    Stores information about every platform and station complex, loaded from the `stops.txt` static GTFS file
    """
    def load_from_file(self, fp):
        reader = csv.reader(fp)
        headings = []
        for i, row in enumerate(reader):
            if i == 0:
                headings = row
            else:
                stop_id = row[0]
                stop = {}
                for heading, value in zip(headings, row):
                    stop[heading] = value
                self.stops[stop_id] = stop

    def __init__(self, stops_txt=None):
        if stops_txt is None:
            stops_txt = os.path.join(pathlib.Path(__file__).parent.resolve(), "gtfs_static", "stops.txt")

        self.stops = {}
        if isinstance(stops_txt, str):
            with open(stops_txt, 'r') as fp:
                self.load_from_file(fp)
        elif isinstance(stops_txt, io.IOBase):
            self.load_from_file(stops_txt)

    def get_station_name(self, stop_id):
        """
        Finds the human-readable stop name for a given GTFS stop id, e.g. Stop ID 127 is "Times Sq-42 St"

        :raises: ValueError if the given stop_id is not found in the `stops.txt` dataset
        """
        if stop_id not in self.stops:
            raise ValueError(f"Invalid stop_id: {stop_id}, not found in stops.txt file")
        return self.stops[stop_id]['stop_name']

