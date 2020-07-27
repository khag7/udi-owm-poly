#!/usr/bin/env python3
"""
Polyglot v2 node server OpenWeatherMap weather data
Copyright (C) 2018,2019 Robert Paauwe
"""

try:
    import polyinterface
except ImportError:
    import pgc_interface as polyinterface
import sys
import time
import datetime
import requests
import socket
import math
import re
import json
import node_funcs
from nodes import owm_daily
from nodes import uom

LOGGER = polyinterface.LOGGER

@node_funcs.add_functions_as_methods(node_funcs.functions)
class Controller(polyinterface.Controller):
    id = 'weather'
    #id = 'controller'
    #hint = [0,0,0,0]
    def __init__(self, polyglot):
        super(Controller, self).__init__(polyglot)
        self.name = 'OpenWeatherMap'
        self.address = 'weather'
        self.primary = self.address
        self.configured = False
        self.discovery = False
        self.start_finished = False

        self.params = node_funcs.NSParameters([{
            'name': 'APIkey',
            'default': 'set me',
            'isRequired': True,
            'notice': 'OpenWeatherMap API key must be set',
            },
            {
            'name': 'Location',
            'default': 'set me',
            'isRequired': True,
            'notice': 'OpenWeatherMap location must be set',
            },
            {
            'name': 'Units',
            'default': 'imperial',
            'isRequired': False,
            'notice': '',
            },
            {
            'name': 'Forecast Days',
            'default': '0',
            'isRequired': False,
            'notice': '',
            },
            {
            'name': 'Elevation',
            'default': '0',
            'isRequired': False,
            'notice': '',
            },
            {
            'name': 'Plant Type',
            'default': '0.23',
            'isRequired': False,
            'notice': '',
            },
            ])

        self.poly.onConfig(self.process_config)

    # Process changes to customParameters
    def process_config(self, config):
        (valid, changed) = self.params.update_from_polyglot(config)
        if changed and not valid:
            LOGGER.debug('-- configuration not yet valid')
            self.removeNoticesAll()
            self.params.send_notices(self)
        elif changed and valid:
            LOGGER.debug('-- configuration is valid')
            self.removeNoticesAll()
            self.configured = True
            if self.params.isChanged('Forecast Days'):
                if self.start_finished:
                    LOGGER.info('calling discover because forecast days set and ' + str(self.start_finished))
                    self.discover()
                    self.initialize()
        elif valid:
            LOGGER.debug('-- configuration not changed, but is valid')

    def start(self):
        LOGGER.info('Starting node server')
        self.check_params()
        self.discover()
        LOGGER.info('Node server started')

        # Do an initial query to get filled in as soon as possible
        if self.configured:
            self.initialize()

        self.start_finished = True

    def initialize(self):
        time.sleep(2)  # give things some time to settle
        self.query_conditions()
        self.query_forecast()

    def longPoll(self):
        self.query_forecast()

    def shortPoll(self):
        self.query_conditions()

    # extra = weather or forecast or uvi
    def get_weather_data(self, extra, lat=None, lon=None):
        request = 'http://api.openweathermap.org/data/2.5/' + extra + '?'
        if 'uvi' in extra:
            request += 'lat=' + str(lat)
            request += '&lon=' + str(lon)
        else:
            # if location looks like a zip code, treat it as such for backwards
            # compatibility
            if re.fullmatch(r'\d\d\d\d\d,..', self.params.get('Location')) != None:
                request += 'zip=' + self.params.get('Location')
            elif re.fullmatch(r'\d\d\d\d\d', self.params.get('Location')) != None:
                request += 'zip=' + self.params.get('Location')
            else:
                request += self.params.get('Location')
            request += '&units=' + self.params.get('Units')

        request += '&appid=' + self.params.get('APIkey')

        LOGGER.debug('request = %s' % request)
        try:
            c = requests.get(request)
            jdata = c.json()
            c.close()
            LOGGER.debug(jdata)
        except:
            LOGGER.error('HTTP request failed for api.openweathermap.org')
            jdata = None

        return jdata


    def query_conditions(self, force=False):
        # Query for the current conditions. We can do this fairly
        # frequently, probably as often as once a minute.
        #
        # By default JSON is returned
        # http://api.openweathermap.org/data/2.5/weather?

        if not self.configured:
            LOGGER.info('Skipping connection because we aren\'t configured yet.')
            return

        try:
            jdata = self.get_weather_data('weather')

            if jdata == None:
                LOGGER.error('Query returned no data')
                return

            self.latitude = jdata['coord']['lat']
            self.longitude = jdata['coord']['lon']

            try:
                uv_data = self.get_weather_data('uvi', self.latitude, self.longitude)
                if uv_data != None:
                    LOGGER.debug('UV index = %f' % uv_data['value'])
                    self.update_driver('UV', uv_data['value'], force)
                else:
                    LOGGER.error('UV query returned no data')
            except:
                LOGGER.error('Failed to query for UV data')


            # TODO: Query for pollution data
        except:
            LOGGER.error('Weather data query failed')
            return

        # Assume we always get the main section with data
        self.update_driver('CLITEMP', jdata['main']['temp'], force)
        self.update_driver('CLIHUM', jdata['main']['humidity'], force)
        self.update_driver('BARPRES', jdata['main']['pressure'], force)
        self.update_driver('GV0', jdata['main']['temp_max'], force)
        self.update_driver('GV1', jdata['main']['temp_min'], force)
        if 'wind' in jdata:
            # Wind data is apparently flaky so check to make sure it exist.
            if 'speed' in jdata['wind']:
                self.update_driver('GV4', jdata['wind']['speed'], force)
            if 'gust' in jdata['wind']:
                self.update_driver('GV5', jdata['wind']['gust'], force)
            if 'deg' in jdata['wind']:
                self.update_driver('WINDDIR', jdata['wind']['deg'], force)
        if 'visibility' in jdata:
            # always reported in meters convert to either km or miles
            if self.params.get('Units') == 'metric':
                vis = float(jdata['visibility']) / 1000
            else:
                vis = float(jdata['visibility']) * 0.000621371
            self.update_driver('DISTANC', round(vis,1), force)

        rain = self.parse_precipitation(jdata, 'rain')
        self.update_driver('GV6', round(rain, 2), force)

        snow = self.parse_precipitation(jdata, 'snow')
        self.update_driver('GV7', round(snow, 2), force)

        if 'clouds' in jdata:
            self.update_driver('GV14', jdata['clouds']['all'], force)
        if 'weather' in jdata:
            self.update_driver('GV13', jdata['weather'][0]['id'], force)
        

    # parse rain/snow values from data
    def parse_precipitation(self, data, tag):
        if tag in data:
            if '3h' in data[tag]:
                snow = float(data[tag]['3h'])
            elif '1h' in data[tag]:
                snow = float(data[tag]['1h'])
            else:
                snow = 0
            LOGGER.debug('Found ' + tag + ' value = ' + str(snow))

            # this is reported in mm, need to convert to inches
            if self.params.get('Units') == 'imperial':
                snow *= 0.0393701
        else:
            snow = 0

        return snow

    def query_forecast(self):
        # Three hour forecast for 5 days (or about 30 entries). This
        # is probably too much data to send to the ISY and there isn't
        # really a good way to deal with this. Would it make sense
        # to pick one of the entries for the day and just use that?

        if not self.configured:
            LOGGER.info('Skipping connection because we aren\'t configured yet.')
            return

        try:
            jdata = self.get_weather_data('forecast')

            if jdata == None:
                LOGGER.error('Query returned no data')
                return

            uv_data = self.get_weather_data('uvi/forecast', self.latitude, self.longitude)
            LOGGER.info('Found ' + str(len(uv_data)) + ' UV forecasts')
            # what if we have no UV data?  below we assume it's there and
            # crash if it's not.
        except:
            LOGGER.error('Foreast query failed.')
            return

        # Free accounts only give us a 3hr/5day forecast so the first step
        # is to map into days with min/max values.
        fcast = []
        LOGGER.info('Forecast has ' + str(jdata['cnt']) + ' lines of data')
        day = 0
        fcast.append({})
        count = 0
        temp_max = 0
        temp_min = 200
        Hmax = 0
        Hmin = 100
        pressure = 0
        weather = 0
        speed = 0
        winddir = 0
        clouds = 0
        dt = 0
        uv = 0
        rain = 0
        snow = 0
        dow = -1

        if 'list' in jdata:
            for forecast in jdata['list']:
                dt_txt = forecast['dt_txt'].split(' ')
                LOGGER.info('Day = ' + str(day) + ' - Forecast dt = ' + str(forecast['dt']) + ' ' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(forecast['dt'])))
                # Forecast may optionally have rain or snow data. Should
                # parse that.
                rain = self.parse_precipitation(forecast, 'rain')
                snow = self.parse_precipitation(forecast, 'snow')

                # We should convert 'dt' to local time and use that to determine day breaks.
                hour = time.strftime('%H', time.localtime(forecast['dt']))
                LOGGER.info('day = ' + str(dow) + ' hour = ' + hour)

                if dow != time.strftime("%w", time.localtime(forecast['dt'])):
                    if count != 0:
                        fcast.append({})
                        fcast[day] = {
                            'temp_max': temp_max,
                            'temp_min': temp_min,
                            'Hmax': Hmax,
                            'Hmin': Hmin,
                            'pressure': pressure / count,
                            'weather': weather,
                            'speed': speed / count,
                            'winddir': winddir / count,
                            'clouds': clouds / count,
                            'dt': dt,
                            'uv': uv,
                            'rain': rain,
                            'snow': snow,
                            'count': count,
                            }
                        day += 1

                    temp_max = 0
                    temp_min = 200
                    Hmax = 0
                    Hmin = 100
                    pressure = 0
                    weather = 0
                    speed = 0
                    winddir = 0
                    clouds = 0
                    dt = 0
                    uv = 0
                    rain = 0
                    snow = 0
                    count = 0
                    dow = time.strftime("%w", time.localtime(forecast['dt']))

                if 0 <= day < len(uv_data):
                    uv = float(uv_data[day]['value'])
                else:
                    uv = 0.0

                # Build daily forecast data
                if float(forecast['main']['temp']) > temp_max:
                    temp_max = float(forecast['main']['temp'])
                if float(forecast['main']['temp']) < temp_min:
                    temp_min = float(forecast['main']['temp'])
                if float(forecast['main']['humidity']) > Hmax:
                    Hmax = float(forecast['main']['humidity'])
                if float(forecast['main']['humidity']) < Hmin:
                    Hmin = float(forecast['main']['humidity'])
                pressure += float(forecast['main']['pressure'])
                weather = float(forecast['weather'][0]['id'])
                speed += float(forecast['wind']['speed'])
                winddir += float(forecast['wind']['deg'])
                clouds += float(forecast['clouds']['all'])
                dt = forecast['dt']
                uv = uv
                rain += rain
                snow += snow
                count += 1

                
            LOGGER.info('Created ' + str(day) +' days forecast.')

            try:
                self.removeNotice('noData')
            except Exception as e:
                LOGGER.error(e)

            for f in range(0,int(self.params.get('Forecast Days'))):
                address = 'forecast_' + str(f)
                if f < len(fcast) and fcast[f] != {}:
                    if fcast[f]['count'] == 8:
                        self.nodes[address].update_forecast(fcast[f], self.latitude, self.params.get('Elevation'), self.params.get('Plant Type'), self.params.get('Units'))
                    else:
                        LOGGER.debug('Skipping update for ' + address + ' because it lacks 8 records.')
                        try:
                            self.addNotice('Insufficient data for forecast ' + address, 'noData')
                        except:
                            self.addNotice({'noData': 'Insufficient data for forecast ' + address})
                else:
                    LOGGER.warning('No forecast information available for day ' + str(f))

    def query(self):
        LOGGER.info("In Query...")
        for node in self.nodes:
            self.nodes[node].reportDrivers()

    def discover(self, *args, **kwargs):
        if self.discovery:
            LOGGER.info('Discover already running.')
            return

        self.discovery = True
        LOGGER.info("In Discovery...")

        # Create any additional nodes here
        num_days = int(self.params.get('Forecast Days'))
        if num_days < 5:
            # delete any extra days
            for day in range(num_days, 5):
                address = 'forecast_' + str(day)
                try:
                    self.delNode(address)
                except:
                    LOGGER.debug('Failed to delete node ' + address)

        for day in range(0,num_days):
            address = 'forecast_' + str(day)
            title = 'Forecast ' + str(day)
            try:
                node = owm_daily.DailyNode(self, self.address, address, title, self.params.get('Units'))
                self.addNode(node)
            except Exception as e:
                LOGGER.error('Failed to create forecast node ' + title)
                LOGGER.error(str(e))

        # Set the uom dictionary based on current user units preference
        LOGGER.info('New Configure driver units to ' + self.params.get('Units'))
        self.uom = uom.get_uom(self.params.get('Units'))
        self.discovery = False

    # Delete the node server from Polyglot
    def delete(self):
        LOGGER.info('Removing node server')

    def stop(self):
        LOGGER.info('Stopping node server')

    def update_profile(self, command):
        st = self.poly.installprofile()
        return st

    def check_params(self):
        self.removeNoticesAll()

        if self.params.get_from_polyglot(self):
            LOGGER.debug('All required parameters are set!')
            self.configured = True
            if int(self.params.get('Forecast Days')) > 5:
                self.addNotice('Number of days of forecast data is limited to 5 days', 'forecast')
                self.params.set('Forecast Days', 5)
        else:
            LOGGER.debug('Configuration required.')
            LOGGER.debug('APIkey = ' + self.params.get('APIkey'))
            LOGGER.debug('Location = ' + self.params.get('Location'))
            self.params.send_notices(self)

    def remove_notices_all(self, command):
        self.removeNoticesAll()

    def set_logging_level(self, level=None):
        if level is None:
            try:
                level = self.get_saved_log_level()
            except:
                LOGGER.error('set_logging_level: get saved log level failed.')

            if level is None:
                level = 30

            level = int(level)
        else:
            level = int(level['value'])

        self.save_log_level(level)
        LOGGER.info('set_logging_level: Setting log level to %d' % level)
        LOGGER.setLevel(level)



    commands = {
            'DISCOVER': discover,
            'UPDATE_PROFILE': update_profile,
            'REMOVE_NOTICES_ALL': remove_notices_all,
            'DEBUG': set_logging_level,
            }

    # For this node server, all of the info is available in the single
    # controller node.
    #
    # TODO: Do we want to try and do evapotranspiration calculations? 
    #       maybe later as an enhancement.
    # TODO: Add forecast data
    drivers = [
            {'driver': 'ST', 'value': 1, 'uom': 2},   # node server status
            {'driver': 'CLITEMP', 'value': 0, 'uom': 4},   # temperature
            {'driver': 'CLIHUM', 'value': 0, 'uom': 22},   # humidity
            {'driver': 'BARPRES', 'value': 0, 'uom': 118}, # pressure
            {'driver': 'WINDDIR', 'value': 0, 'uom': 76},  # direction
            {'driver': 'GV0', 'value': 0, 'uom': 4},       # max temp
            {'driver': 'GV1', 'value': 0, 'uom': 4},       # min temp
            {'driver': 'GV4', 'value': 0, 'uom': 49},      # wind speed
            {'driver': 'GV5', 'value': 0, 'uom': 49},      # gust speed
            {'driver': 'GV6', 'value': 0, 'uom': 82},      # rain
            {'driver': 'GV7', 'value': 0, 'uom': 82},      # snow
            {'driver': 'GV13', 'value': 0, 'uom': 25},     # climate conditions
            {'driver': 'GV14', 'value': 0, 'uom': 22},     # cloud conditions
            {'driver': 'DISTANC', 'value': 0, 'uom': 83},  # visibility
            {'driver': 'UV', 'value': 0, 'uom': 71},       # UV index
            ]

