#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 23 11:35:50 2024

This is a script to compute the TC wind field from the ECMWF forecast tracks.
Output: climada.hazard.Hazard class in .hdf5 format

@author: Pui Man (Mannie) Kam
"""
import time
import os
import numpy as np
from pathlib import Path
from climada import CONFIG
import warnings
warnings.filterwarnings("ignore")

from climada.hazard import TropCyclone
from climada_petals.hazard import TCForecast
from climada.util.api_client import Client
client = Client()

from tc_tracks_func import filter_storm, _correct_max_sustained_wind_speed
from helpers import get_most_recent_forecast_dir

time_start = time.time()

FORECAST_DIR = get_most_recent_forecast_dir()
SAVE_WIND_DIR = FORECAST_DIR + "/wind_fields/"

N_ENSEMBLE = 51

# retrieve the Centroids from 
glob_centroids = client.get_centroids()

# retrieve the latest forecast
tr_fcast = TCForecast()
tr_fcast.fetch_ecmwf()
tr_filter = filter_storm(tr_fcast)
tr_filter.equal_timestep(1/6)
_correct_max_sustained_wind_speed(tr_filter)


if len(tr_filter.data) != 0:

    tr_name_unique = set([tr.name for tr in tr_filter.data])
    if not os.path.exists(SAVE_WIND_DIR):
        os.makedirs(SAVE_WIND_DIR)

    for tr_name in tr_name_unique:
        # select single storm and interpolate the tracks
        tr_one_storm = tr_filter.subset({'name': tr_name})

        # refine the centroids
        storm_extent = tr_one_storm.get_extent(deg_buffer=5.)
        centroids_refine = glob_centroids.select(extent=storm_extent)

        # compute the windfield for each storm
        tc_wind_one_storm = TropCyclone.from_tracks(tr_one_storm, centroids_refine,
                                                    model="H1980")
        tc_wind_one_storm.frequency = np.ones(len(tc_wind_one_storm.event_id))/N_ENSEMBLE
        tc_wind_one_storm.write_hdf5(SAVE_WIND_DIR +'tc_wind_' +tr_name +'_' +formatted_datetime +'.hdf5')

else:
    print(f"There is no active storm forecasted at {formatted_datetime}")

# record the time
time_end = time.time()

print("TC wind computation complete. Time: " +str(time_end-time_start))