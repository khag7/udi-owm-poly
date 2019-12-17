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
from nodes import owm
from nodes import owm_daily

LOGGER = polyinterface.LOGGER

if __name__ == "__main__":
    try:
        polyglot = polyinterface.Interface('OWM')
        polyglot.start()
        control = owm.Controller(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
        

