
# NYCT-GTFS - Real-time NYC subway data parsing for humans
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]

This python library provides a human-friendly, native python interface
for dealing with the [NYCT Subway data published by the MTA](https://api.mta.info/). By default,
this data is provided in a [protobuf-encoded](https://developers.google.com/protocol-buffers/) format called [GTFS-realtime](https://developers.google.com/transit/gtfs-realtime/), which further
has [NYCT-specific customization](https://web.archive.org/web/20191221213849/http://datamine.mta.info/sites/all/files/pdfs/GTFS-Realtime-NYC-Subway%20version%201%20dated%207%20Sep.pdf). 
This is quite difficult to parse, and requires a lot of boilerplate to do even very simple queries. 

However, with NYCT-GTFS, you can access and query this data in just a few lines of Python:

```python
>>> from nyct_gtfs import NYCTFeed

# Load the realtime feed from the MTA site
>>> feed = NYCTFeed("1")

# Get all 123 trains currently underway to Times Sq-42 St
>>> trains = feed.filter_trips(line_id=["1", "2", "3"], headed_for_stop_id=["127N", "127S"], underway=True)

# Let's look closer at the first train included in the filter above:
>>> str(trains[0])
'Northbound 1 to Van Cortlandt Park-242 St, departed origin 22:20:00, Currently INCOMING_AT 34 St-Penn Station, last update at 22:34:11'

# We can extract each of these details programatically as well,
# to get arrival time information for the next station (which in this case is 34th St-Penn Station):
>>> trains[0].stop_time_updates[0].arrival
datetime.datetime(2021, 11, 26, 22, 34, 51)

# What about the next stop after that? Should be Times Square
>>> trains[0].stop_time_updates[1].stop_name
'Times Sq-42 St'

# And what time will it get there?
>>> trains[0].stop_time_updates[1].arrival
datetime.datetime(2021, 11, 26, 22, 36, 21)
```

See "Usage Examples" below for more examples of the data available.

### Built With

* [Requests](https://docs.python-requests.org/)
* [Protocol Buffers](https://developers.google.com/protocol-buffers/)
* [MTA GTFS-realtime Data Feeds](https://api.mta.info/)

## Installation
*Update Version 2.0.0: API keys are no longer required to access MTA GTFS feeds. [Learn more.](https://api.mta.info/#/)*
1. Install nyct-gtfs
   ```sh
   pip install nyct-gtfs
   ```
2. Load the data feed
    ```python
    from nyct_gtfs import NYCTFeed
    
    # Load the realtime feed from the MTA site
    feed = NYCTFeed("1")
    ```

## Usage Examples

### Get All Trip Data from the Feed
```python
>>> from nyct_gtfs import NYCTFeed
>>> feed = NYCTFeed("B")

# Read all trip (train) information published to the BDFM feed 
>>> trains = feed.trips

>>> len(trains)
70
```

### Filter Only Certain Trip Data from the Feed
```python
>>> from nyct_gtfs import NYCTFeed
>>> feed = NYCTFeed("B")

# Read only D train information from the BDFM feed 
>>> trains = feed.filter_trips(line_id="D")
>>> len(trains)
26

# Read only D and M train information from the BDFM feed
>>> trains = feed.filter_trips(line_id=["D", "M"])
>>> len(trains)
43

# TODO
```

See `NYCTFeed.filter_trips()` for a complete listing of the filtering options available. 


### Read Trip/Train Metadata
```python
>>> from nyct_gtfs import NYCTFeed
>>> feed = NYCTFeed("N")

# Read the first train from the feed
>>> train = feed.trips[0]

# Get human-readable summary of the train's status
>>> str(train)
"Southbound N to Coney Island-Stillwell Av, departed origin 15:12:00, Currently STOPPED_AT 20 Av, last update at 16:22:14"

# Get each piece of this information separately:
>>> train.direction
"S"

>>> train.route_id
"N"

>>> train.headsign_text
"Coney Island-Stillwell Av"

>>> train.departure_time
datetime.datetime(2021, 11, 27, 15, 21, 00)

>>> train.location
"N06S" # This is the stop ID corresponding to the southbound platform at 20 Av

>>> train.location_status
"STOPPED_AT"

>>> train.last_position_update
datetime.datetime(2021, 11, 27, 16, 22, 14)
```

See `Trip` for a full list of train metadata fields.

### Read Remaining Stops
Each trip in the feed has a complete listing of all of its remaining stops. Stops are removed from this listing upon 
departure from the station listed. Therefore our southbound N train from the previous example still has 20 Av listed 
in its scheduled stops list:
```python
>>> from nyct_gtfs import NYCTFeed
>>> feed = NYCTFeed("N")

# Read the first train from the feed
>>> train = feed.trips[0]
>>> str(train)
"Southbound N to Coney Island-Stillwell Av, departed origin 15:12:00, Currently STOPPED_AT 20 Av, last update at 16:22:14"

>>> train.stop_time_updates[0].stop_name
"20 Av"

# We can identify the number of stops this train has left using len()
>>> len(train.stop_time_updates)
6

# We can also identify the last scheduled stop for this train using a negative list index
>>> train.stop_time_updates[-1].stop_name
"Coney Island-Stillwell Av"
```

#### Read stop details
```python
>>> from nyct_gtfs import NYCTFeed
>>> feed = NYCTFeed("N")

# Read the first train from the feed
>>> train = feed.trips[0]
>>> str(train)
"Southbound N to Coney Island-Stillwell Av, departed origin 15:12:00, Currently STOPPED_AT 20 Av, last update at 16:22:14"

>>> train.stop_time_updates[4].stop_name
"86 St"

>>> train.stop_time_updates[4].stop_id
"N10S"

# Get the estimated arrival time at this stop
>>> train.stop_time_updates[4].arrival
datetime.datetime(2021, 11, 27, 16, 31, 31)
```

For full details about stop time fields see `StopTimeUpdate`

### Read Feed Metadata

```python
>>> from nyct_gtfs import NYCTFeed
>>> feed = NYCTFeed("A")

# Get the timestamp the GTFS feed was generated at
>>> feed.last_generated
datetime.datetime(2021, 11, 26, 22, 33, 15)

# Get the GTFS-realtime specification version this feed was derived from
>>> feed.gtfs_realtime_version
"1.0"

# Get the version of the NYCT extension of the GTFS-realtime specification that this feed is derived from
# Full specification is available here:
# https://web.archive.org/web/20191221213849/http://datamine.mta.info/sites/all/files/pdfs/GTFS-Realtime-NYC-Subway%20version%201%20dated%207%20Sep.pdf
>>> feed.nyct_subway_gtfs_version
"1.0"

# Identify the trip replacement period at the time of generation for this feed
# This is the period in time that this feed covers (i.e. it "replaces" the prior published schedule for all trips 
# between the feed generation time and the time listed here). The length of this period can vary by line, but currently
# it is 30 minutes for all subway lines
>>> feed.trip_replacement_periods
{
   'A': datetime.datetime(2021, 11, 26, 23, 03, 15), 
   'C': datetime.datetime(2021, 11, 26, 23, 03, 15), 
   'E': datetime.datetime(2021, 11, 26, 23, 03, 15),
   'H': datetime.datetime(2021, 11, 26, 23, 03, 15),
   'FS': datetime.datetime(2021, 11, 26, 23, 03, 15)
}

# Trip replacement periods is also useful to get a list of which subway lines are contained within this feed
>>> feed.trip_replacement_periods.keys()
dict_keys(['A', 'C', 'E', 'H', 'FS'])
```

### Refresh Feed Data
```python
>>> from nyct_gtfs import NYCTFeed
>>> feed = NYCTFeed("A")

# Pick a train to get details from
>>> train = feed.trips[0]
>>> train.direction
"N"

# To pull new data, use the refresh() method
>>> feed.refresh()

# You must also update references to the trains list, existing objects are not modified by refresh()
>>> train = feed.trips[0]

# Note that feed.trips does not necessarily have a stable index across refresh() calls, i.e it is 
# possible for feed.trips[0] to have changed to represent a different train as a result of the refresh() operation:
>>> train.direction
"S"
```

## Feed Groupings

NYCT Subway feeds are grouped by color for all of the B division (lettered) lines. All A division lines
are grouped into a single feed. When you initialize an `NYCTFeed` object, you can specify a line or feed URL, e.g:
```python
>>> from nyct_gtfs import NYCTFeed
>>> feed1 = NYCTFeed("A")

>>> feed2 = NYCTFeed("C")

>>> feed3 = NYCTFeed("https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace")

>>> feed1.trip_replacement_periods.keys()
dict_keys(['A', 'C', 'E', 'H', 'FS'])

>>> feed2.trip_replacement_periods.keys()
dict_keys(['A', 'C', 'E', 'H', 'FS'])

>>> feed3.trip_replacement_periods.keys()
dict_keys(['A', 'C', 'E', 'H', 'FS'])
```

In this example, `feed1`, `feed2`, and `feed3` all pull from the same source, the ACE feed. Provided an update isn't
published between any of the calls above, they will all contain exactly the same data. Here is a table of the groupings
as of November 2021. An up-to-date listing can be found [here](https://api.mta.info/#/subwayRealTimeFeeds) (login required).

| Trains        | Feed URL |
|---------------|-------|
|  A C E <br/> H ([Rockaway Park Shuttle](https://en.wikipedia.org/wiki/Rockaway_Park_Shuttle)) <br/> FS ([Franklin Av Shuttle](https://en.wikipedia.org/wiki/Franklin_Avenue_Shuttle)) | https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace |
| B D F M | https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm |
| G | https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-g |
| J Z | https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-jz |
| N Q R W | https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw |
| L |  https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-l |
| 1 2 3 4 5 6 7 S | https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs |
| SIR ([Staten Island Railway](https://en.wikipedia.org/wiki/Staten_Island_Railway)) | https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-si |


## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

## Contact

Andrew Dickinson - andrew.dickinson.0216@gmail.com

Project Link: [https://github.com/Andrew-Dickinson/nyct-gtfs](https://github.com/Andrew-Dickinson/nyct-gtfs)

## Acknowledgments

* [Choose an Open Source License](https://choosealicense.com)
* [MTA Developer Resources](http://web.mta.info/developers/)
* [MTA Developer Google Group](https://groups.google.com/g/mtadeveloperresources)

## Disclaimer
This project is not endorsed by, directly affiliated with, maintained, authorized, or sponsored by any transit agency. 
All names and marks are the registered trademarks of their original owners. The use of any trade name or trademark is 
for identification and reference purposes only and does not imply any association with the trademark holder or their 
brand.


[contributors-shield]: https://img.shields.io/github/contributors/Andrew-Dickinson/nyct-gtfs.svg?style=for-the-badge
[contributors-url]: https://github.com/Andrew-Dickinson/nyct-gtfs/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/Andrew-Dickinson/nyct-gtfs.svg?style=for-the-badge
[forks-url]: https://github.com/Andrew-Dickinson/nyct-gtfs/network/members
[stars-shield]: https://img.shields.io/github/stars/Andrew-Dickinson/nyct-gtfs.svg?style=for-the-badge
[stars-url]: https://github.com/Andrew-Dickinson/nyct-gtfs/stargazers
[issues-shield]: https://img.shields.io/github/issues/Andrew-Dickinson/nyct-gtfs.svg?style=for-the-badge
[issues-url]: https://github.com/Andrew-Dickinson/nyct-gtfs/issues
[license-shield]: https://img.shields.io/github/license/Andrew-Dickinson/nyct-gtfs.svg?style=for-the-badge
[license-url]: https://github.com/Andrew-Dickinson/nyct-gtfs/blob/master/LICENSE.txt