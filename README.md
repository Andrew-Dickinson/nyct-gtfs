<div id="top"></div>

<br />
<div>
  <a href="https://github.com/Andrew-Dickinson/nyct-gtfs">
    <img src="img/img.png" alt="Train Icons" width="400">
  </a>
  <br/>
  <br/>
</div>


# NYCT-GTFS - Real-time NYC subway data parsing for humans
<!-- PROJECT SHIELDS -->
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
>>> feed = NYCTFeed("1", api_key="YOUR_MTA_API_KEY_GOES_HERE")

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

See `trip.py` and `stop_time_update.py` for more information about the fields available

### Built With

This section should list any major frameworks/libraries used to bootstrap your project. Leave any add-ons/plugins for the acknowledgements section. Here are a few examples.

* [Requests](https://docs.python-requests.org/)
* [Protocol Buffers](https://developers.google.com/protocol-buffers/)
* [MTA GTFS-realtime Data Feeds](https://api.mta.info/)

<!-- GETTING STARTED -->
## Installation

1. Get a free MTA API Key at [https://api.mta.info/](https://api.mta.info/#/signup)
2. Install nyct-gtfs
   ```sh
   pip install nyct-gtfs
   ```
3. Load the data feed
    ```python
    from nyct_gtfs import NYCTFeed
    
    # Load the realtime feed from the MTA site
    feed = NYCTFeed("1", api_key="YOUR_MTA_API_KEY_GOES_HERE")
    ```
    
    
    
<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request




<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.


<!-- CONTACT -->
## Contact

Andrew Dickinson - andrew.dickinson.0216@gmail.com

Project Link: [https://github.com/Andrew-Dickinson/nyct-gtfs](https://github.com/Andrew-Dickinson/nyct-gtfs)


<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* [Choose an Open Source License](https://choosealicense.com)
* [MTA Developer Resources](http://web.mta.info/developers/)
* [MTA Developer Google Group](https://groups.google.com/g/mtadeveloperresources)

## Disclaimer
This project is not endorsed by, directly affiliated with, maintained, authorized, or sponsored by any transit agency. 
All names and marks are the registered trademarks of their original owners. The use of any trade name or trademark is 
for identification and reference purposes only and does not imply any association with the trademark holder or their 
brand.

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
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