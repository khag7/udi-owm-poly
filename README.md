
# OpenWeatherMaps

This is a node server to pull weather data from OpenWeatherMaps and make it available to a [Universal Devices ISY994i](https://www.universal-devices.com/residential/ISY) [Polyglot interface](http://www.universal-devices.com/developers/polyglot/docs/) with  [Polyglot V2](https://github.com/Einstein42/udi-polyglotv2)

OpenWeatherMaps requires you to create an API key that you will need to access the data via their API.  See [OpenWeatherMap](http://openweathermap.org/api)

(c) 2018 Robert Paauwe
MIT license.


## Installation

1. Backup Your ISY in case of problems!
   * Really, do the backup, please
2. Go to the Polyglot Store in the UI and install.
3. Add NodeServer in Polyglot Web
   * After the install completes, Polyglot will reboot your ISY, you can watch the status in the main polyglot log.
4. Once your ISY is back up open the Admin Console.
5. Configure the node server per configuration section below.

### Node Settings
The settings for this node are:

#### Short Poll
   * Not used
#### Long Poll
   * How often to poll the OpenWeatherMap weather service. Note that the data is only updated every 10 minutes. Setting this to less may result in exceeding the free service rate limit.


## Requirements

1. Polyglot V2 itself should be run on Raspian Stretch.
  To check your version, ```cat /etc/os-release``` and the first line should look like
  ```PRETTY_NAME="Raspbian GNU/Linux 9 (stretch)"```. It is possible to upgrade from Jessie to
  Stretch, but I would recommend just re-imaging the SD card.  Some helpful links:
   * https://www.raspberrypi.org/blog/raspbian-stretch/
   * https://linuxconfig.org/raspbian-gnu-linux-upgrade-from-jessie-to-raspbian-stretch-9
2. This has only been tested with ISY 5.0.14 so it is not guaranteed to work with any other version.

# Upgrading

Open the Polyglot web page, go to nodeserver store and click "Update" for "WeatherFlow".

For Polyglot 2.0.35, hit "Cancel" in the update window so the profile will not be updated and ISY rebooted.  The install procedure will properly handle this for you.  This will change with 2.0.36, for that version you will always say "No" and let the install procedure handle it for you as well.

Then restart the nodeserver by selecting it in the Polyglot dashboard and select Control -> Restart, then watch the log to make sure everything goes well.

The nodeserver keeps track of the version number and when a profile rebuild is necessary.  The profile/version.txt will contain the profile_version which is updated in server.json when the profile should be rebuilt.

# Release Notes

- 1.2.8 11/25/2019
   - Trap failures in http requests.
- 1.2.7 09/15/2019
   - Fix use of uninitalized uv data when no uv data exist.
- 1.2.6 09/06/2019
   - Trap no dat return from uv query.
- 1.2.5 08/27/2019
   - Fix use of uninitialized uv data.
- 1.2.4 08/20/2019
   - Add error check on location data.
- 1.2.3 08/19/2019
   - Add error check on forecast UV data.
- 1.2.2 08/15/2019
   - Improve error checkin, specifically for wind direction.
- 1.2.1 08/03/2019
   - Allow zipcode without country code for backwards compatibility
- 1.2.0 08/03/2019
   - Add some additional error checking to queried values
   - Allow for city, lat/long location specifiers in configuration
- 1.1.1 07/30/2019
   - Fix condition codes editor entry and NSL entries.
- 1.1.0 07/17/2019
   - Rewrite editor profile and node server code to make use of multi-uom
     editors.  This seems to be a better way to handle switching between
     imperial and metric units.
- 1.0.1 07/12/2019
   - Fix errors in editor profile file
- 1.0.0 03/05/2019
   - Initial version published to github
