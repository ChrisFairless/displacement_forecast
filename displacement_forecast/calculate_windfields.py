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
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

from climada import CONFIG
from climada.hazard import TropCyclone
from climada_petals.hazard import TCForecast
from climada.util.api_client import Client
client = Client()

from displacement_forecast.tc_tracks_func import filter_storm, _correct_max_sustained_wind_speed
from displacement_forecast.download_tracks import get_forecast_tracks

WORKING_DIR = CONFIG.forecast_sandbox.dir.str()
N_ENSEMBLE = 51


def calculate_windfields(time_str, overwrite=False):

    time_start = time.time()

    FORECAST_DIR = Path(WORKING_DIR, time_str)
    WIND_DIR = Path(FORECAST_DIR, "wind_fields")

    if not os.path.exists(FORECAST_DIR):
        raise FileNotFoundError(f"Directory {str(FORECAST_DIR)} does not exist. Please download the forecast first.")   
    os.makedirs(WIND_DIR, exist_ok=True)

    if len(os.listdir(WIND_DIR)) > 0 and not overwrite:
        print(f"Wind fields for forecast {time_str} already computed, skipping.")
        return

    # retrieve the forecast (already downloaded)
    tr_filter = get_forecast_tracks(time_str)
    forecast_time = datetime.strptime(time_str, '%Y%m%d%H0000')
    formatted_datetime = forecast_time.strftime('%Y-%m-%d %H:%M UTC')

    if len(tr_filter.data) != 0:
        tr_name_unique = set([tr.name for tr in tr_filter.data])

        # retrieve the Centroids
        glob_centroids = client.get_centroids()

        for tr_name in tr_name_unique:
            print(f"Computing wind fields for storm {tr_name}")

            # select single storm and interpolate the tracks
            tr_one_storm = tr_filter.subset({'name': tr_name})

            # refine the centroids
            storm_extent = tr_one_storm.get_extent(deg_buffer=5.)
            centroids_refine = glob_centroids.select(extent=storm_extent)

            # compute the windfield for each storm
            tc_wind_one_storm = TropCyclone.from_tracks(tr_one_storm, centroids_refine,
                                                        model="H1980")
            tc_wind_one_storm.frequency = np.ones(len(tc_wind_one_storm.event_id))/N_ENSEMBLE
            tc_wind_one_storm.write_hdf5(Path(WIND_DIR, f'tc_wind_{tr_name}_{time_str}.hdf5'))
    else:
        print(f"There is no active storm forecasted at {formatted_datetime}")

    # record the time
    time_end = time.time()

    print("TC wind computation complete. Time: " +str(time_end-time_start))


