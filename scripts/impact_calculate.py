#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 2 10:45:50 2024

Impact calculation for TC impact on people.
Output: Impact forecast summary.
        Aggregated impact for eact ensemble member and histogram plot.
        Averaged impact for each grid point and map plot.

@author: Pui Man (Mannie) Kam
"""
import warnings
warnings.filterwarnings("ignore")

import os
import glob
import numpy as np
import pandas as pd
from pathlib import Path

from climada import CONFIG
from climada.hazard import Hazard
from climada.engine import ImpactCalc
from climada.util.coordinates import get_country_code, country_to_iso
from climada.util.api_client import Client
client = Client()

from impact_calc_func import (
    impf_set_exposed_pop, impf_set_displacement,
    round_to_previous_12h_utc, get_forecast_times,
    get_tc_wind_files, summarize_forecast,
    save_forecast_summary, save_average_impact_geospatial_points,
    save_impact_at_event
    )
from plot_func import (
    plot_imp_map_exposed, plot_imp_map_displacement,
    plot_histogram,
    make_save_map_file_name, make_save_histogram_file_name
)

# Save directories
SAVE_DIR = str(Path(CONFIG.forecast_sandbox.dir.str())) + "/{forecast_time}/impacts/"

# get the wind files
TC_WIND_DIR = str(Path(CONFIG.forecast_sandbox.dir.str())) + "/{forecast_time}/wind_fields/"

EXPOSED_TO_WIND_THRESHOLD = 32.92 # threshold for people exposed to wind in m/s

# Get the current timestamp
current_timestamp = pd.Timestamp.now().tz_localize('UTC')

forecast_time, previous_forecast_time = get_forecast_times(current_timestamp)
forecast_time_str = forecast_time.strftime('%Y-%m-%d_%HUTC')
TC_WIND_DIR = TC_WIND_DIR.format(forecast_time=forecast_time_str)

forecast_time_str, tc_wind_files = get_tc_wind_files(forecast_time, previous_forecast_time, TC_WIND_DIR)

# stop running if there is no active storm.
if not tc_wind_files:
    print(f"No TC activities at {forecast_time.strftime('%Y-%m-%d_%HUTC')}.")
    print("End impact calculation script")
    exit()

SAVE_DIR = SAVE_DIR.format(forecast_time_str=forecast_time_str)

# Now start the impact calculation for all the storms
for tc_file in tc_wind_files:

    # extract the tc_name from the hdf file
    tc_base_file_name = os.path.basename(tc_file)
    tc_name = tc_base_file_name.split('_')[2]

    # read the hdf file
    tc_haz = Hazard.from_hdf5(tc_file)

    # get the country code where the wind speed >0
    idx_non_zero_wind = tc_haz.intensity.max(axis=0).nonzero()[1]
    country_code_all = get_country_code(
                            tc_haz.centroids.lat[idx_non_zero_wind], 
                            tc_haz.centroids.lon[idx_non_zero_wind]
                        )
    country_code_unique = np.trim_zeros(np.unique(country_code_all))

    # now run impact for each country
    for country_code in country_code_unique:

        country_iso3 = country_to_iso(country_code, "alpha3")
        try:
            exp = client.get_exposures(exposures_type='litpop',
                                    properties={'country_iso3num':[str(country_code).zfill(3)],
                                                'exponents':'(0,1)',
                                                'fin_mode':'pop',
                                                'version':'v2'
                                                }
                                    )
        except client.NoResult:
            print(f"there is no matching dataset in Data API. Country code: {country_code}")
            continue

        # run impact calc for people exposed to cat. 1 wind speed or above
        impf_exposed = impf_set_exposed_pop(threshold=EXPOSED_TO_WIND_THRESHOLD)

        impact_exposed = ImpactCalc(exp, impf_exposed, tc_haz).impact()

        if impact_exposed.aai_agg == 0.: # do not save the files if impact is 0.
            continue

        imp_exposed_summary = summarize_forecast(country_iso3=country_to_iso(country_code, 
                                                                     "alpha3"),
                                        forecast_time=forecast_time.strftime('%Y-%m-%d_%HUTC'),
                                        impact_type="exposed_population_32.92ms",
                                        tc_haz=tc_haz,
                                        tc_name=tc_name,
                                        impact=impact_exposed)
 
        save_forecast_summary(
            SAVE_DIR.format(forecast_time_str=forecast_time_str),
            imp_exposed_summary)
        save_average_impact_geospatial_points(
            SAVE_DIR.format(forecast_time_str=forecast_time_str),
            imp_exposed_summary,
            impact_exposed)
        save_impact_at_event(
            SAVE_DIR.format(forecast_time_str=forecast_time_str),
            imp_exposed_summary,
            impact_exposed)
        
        # save the impact map
        ax_map_exposed = plot_imp_map_exposed(imp_exposed_summary, impact_exposed)
        ax_map_exposed.figure.savefig(SAVE_DIR.format(forecast_time_str=forecast_time_str) +make_save_map_file_name(imp_exposed_summary))

        # save the histogram
        ax_hist_exposed = plot_histogram(imp_exposed_summary, impact_exposed)
        ax_hist_exposed.figure.savefig(SAVE_DIR.format(forecast_time_str=forecast_time_str) +make_save_histogram_file_name(imp_exposed_summary))

        # run the same impact calc but for displacement
        impf_displacement = impf_set_displacement(country_iso3)

        impact_displacement = ImpactCalc(exp, impf_displacement, tc_haz).impact()

        if impact_displacement.aai_agg == 0.: # do not save the files if impact is 0.
            continue
        imp_displacement_summary = summarize_forecast(country_iso3=country_to_iso(country_code, 
                                                                     "alpha3"),
                                                    forecast_time=forecast_time.strftime('%Y-%m-%d_%HUTC'),
                                                    impact_type="displacement",
                                                    tc_haz=tc_haz,
                                                    tc_name=tc_name,
                                                    impact=impact_displacement)

        save_forecast_summary(
            SAVE_DIR.format(forecast_time_str=forecast_time_str),
            imp_displacement_summary)
        
        save_average_impact_geospatial_points(
            SAVE_DIR.format(forecast_time_str=forecast_time_str),
            imp_displacement_summary,
            impact_displacement)
        save_impact_at_event(
            SAVE_DIR.format(forecast_time_str=forecast_time_str),
            imp_displacement_summary,
            impact_displacement)
        
        # save the impact map
        ax_map_displacement = plot_imp_map_displacement(imp_displacement_summary, impact_displacement)
        ax_map_displacement.figure.savefig(SAVE_DIR.format(forecast_time_str=forecast_time_str) +make_save_map_file_name(imp_displacement_summary))

        # save the histogram
        ax_hist_displacement = plot_histogram(imp_displacement_summary, impact_displacement)
        ax_hist_displacement.figure.savefig(SAVE_DIR.format(forecast_time_str=forecast_time_str) +make_save_histogram_file_name(imp_displacement_summary))