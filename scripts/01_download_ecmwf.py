#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adapted from Mannie's work at https://github.com/manniepmkam/TC_impact_forecast_sandbox

This is a script to download the global TC tracks forecast from ECMWF daily.

@author: Pui Man (Mannie) Kam
@author: Chris Fairless
"""

import warnings
warnings.filterwarnings("ignore")

import os
import pandas as pd
import numpy as np

from climada_petals.hazard import TCForecast
from climada import CONFIG
from tc_tracks_func import filter_storm, _correct_max_sustained_wind_speed


WORKING_DIR = CONFIG.forecast_sandbox.dir.str()
SAVE_TRACK_DIR = WORKING_DIR + "/{forecast_time}/tracks/"

tr_fcast = TCForecast()
tr_fcast.fetch_ecmwf()
tr_filter = filter_storm(tr_fcast)
tr_filter.equal_timestep(3.)
_correct_max_sustained_wind_speed(tr_filter)

# extract datetime information
run_datetime = tr_fcast.data[0].run_datetime
datetime_temp = run_datetime.astype('datetime64[s]').astype(str)
formatted_datetime = datetime_temp.replace('T', '_')[:-6] + 'UTC'

# create directory to store the figure
if not os.path.exists(SAVE_TRACK_DIR.format(forecast_time=formatted_datetime)):
    os.makedirs(SAVE_TRACK_DIR.format(forecast_time=formatted_datetime))

tr_filter.write_hdf5(SAVE_TRACK_DIR.format(forecast_time='latest') + "ECMWF_TC_tracks.h5")