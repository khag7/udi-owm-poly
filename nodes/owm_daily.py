# Node definition for a daily forecast node

try:
    import polyinterface
except ImportError:
    import pgc_interface as polyinterface

import json
import time
import datetime
from nodes import et3
from nodes import uom
import node_funcs

LOGGER = polyinterface.LOGGER

@node_funcs.add_functions_as_methods(node_funcs.functions)
class DailyNode(polyinterface.Node):
    id = 'daily'
    drivers = [
            {'driver': 'GV19', 'value': 0, 'uom': 25},     # day of week
            {'driver': 'GV0', 'value': 0, 'uom': 4},       # high temp
            {'driver': 'GV1', 'value': 0, 'uom': 4},       # low temp
            {'driver': 'CLIHUM', 'value': 0, 'uom': 22},   # humidity
            {'driver': 'BARPRES', 'value': 0, 'uom': 118}, # pressure
            {'driver': 'GV13', 'value': 0, 'uom': 25},     # conditions
            {'driver': 'GV14', 'value': 0, 'uom': 22},     # clouds
            {'driver': 'GV4', 'value': 0, 'uom': 49},      # wind speed
            {'driver': 'UV', 'value': 0, 'uom': 71},       # UV index
            {'driver': 'GV20', 'value': 0, 'uom': 106},    # mm/day
            ]
    uom = {'GV19': 25,
            'GV0': 4,
            'GV1': 4,
            'CLIHUM': 22,
            'BARPRES': 118,
            'GV13': 25,
            'GV14': 22,
            'GV4': 49,
            'UV': 71,
            'GV20': 107,
            }

    def set_driver_uom(self, units):
        if units == 'metric':
            self.uom = uom.get_uom(units)
            self.units = units

    def mm2inch(self, mm):
        return mm/25.4

    def update_forecast(self, forecast, latitude, elevation, plant_type, units):

        epoch = int(forecast['dt'])
        dow = time.strftime("%w", time.gmtime(epoch))
        LOGGER.info('Day of week = ' + dow)

        humidity = (forecast['Hmin'] + forecast['Hmax']) / 2
        self.update_driver('CLIHUM', round(humidity, 0))
        self.update_driver('BARPRES', round(forecast['pressure'], 1))
        self.update_driver('GV0', round(forecast['temp_max'], 1))
        self.update_driver('GV1', round(forecast['temp_min'], 1))
        self.update_driver('GV14', round(forecast['clouds'], 0))
        self.update_driver('GV4', round(forecast['speed'], 1))

        self.update_driver('GV19', int(dow))
        self.update_driver('GV13', forecast['weather'])
        self.update_driver('UV', round(forecast['uv'], 1))

        # Calculate ETo
        #  Temp is in degree C and windspeed is in m/s, we may need to
        #  convert these.
        J = datetime.datetime.fromtimestamp(epoch).timetuple().tm_yday

        Tmin = forecast['temp_min']
        Tmax = forecast['temp_max']
        Ws = forecast['speed']
        if units != 'si':
            LOGGER.info('Conversion of temperature/wind speed required')
            Tmin = et3.FtoC(Tmin)
            Tmax = et3.FtoC(Tmax)
            Ws = et3.mph2ms(Ws)

        et0 = et3.evapotranspriation(Tmax, Tmin, None, Ws, float(elevation), forecast['Hmax'], forecast['Hmin'], latitude, float(plant_type), J)
        self.update_driver('GV20', round(et0, 2))
        LOGGER.info("ETo = %f %f" % (et0, self.mm2inch(et0)))


