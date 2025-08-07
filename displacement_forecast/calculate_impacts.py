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
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

from climada import CONFIG
from climada.hazard import Hazard
from climada.engine import ImpactCalc
from climada.util.coordinates import get_country_code, country_to_iso
from climada.util.api_client import Client
client = Client()

from displacement_forecast.impact_calc_func import (
    impf_set_exposed_pop, impf_set_displacement,
    round_to_previous_12h_utc, get_forecast_times,
    summarize_forecast,
    save_forecast_summary, save_average_impact_geospatial_points,
    save_impact_at_event
    )


WORKING_DIR = CONFIG.forecast_sandbox.dir.str()
EXPOSED_TO_WIND_THRESHOLD = 32.92 # threshold for people exposed to wind in m/s   # TODO move this to the config


def calculate_impacts(time_str=None, overwrite=False):
    FORECAST_DIR = Path(WORKING_DIR, time_str)
    WIND_DIR = Path(FORECAST_DIR, "wind_fields")
    IMPACT_DIR = Path(FORECAST_DIR, "impacts")

    if not os.path.exists(FORECAST_DIR):
        raise FileNotFoundError(f"Directory {str(FORECAST_DIR)} does not exist. Please download the forecast first and calculate wind fields.")
    if not os.path.exists(WIND_DIR):
        raise FileNotFoundError(f"Directory {str(WIND_DIR)} does not exist. Please calculate wind fields first.")
    os.makedirs(IMPACT_DIR, exist_ok=True)

    if len(os.listdir(IMPACT_DIR)) > 0 and not overwrite:
        print(f"Impacts for forecast {time_str} already computed, skipping.")
        return

    tc_wind_files = os.listdir(WIND_DIR)
    if len(tc_wind_files) == 0:
        print(f"No TC activities found at {time_str}. No impacts to calculate.")

    # Start the impact calculation for all the storms
    for tc_file in tc_wind_files:

        # extract the tc_name from the hdf file
        tc_base_file_name = os.path.basename(tc_file)
        tc_name = tc_base_file_name.split('_')[2]
        print(f"Calculating impacts for storm {tc_name}...")

        # read the hdf file
        tc_haz = Hazard.from_hdf5(Path(WIND_DIR, tc_file))

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
            print(f"   ...{country_iso3}")

            try:
                exp = client.get_exposures(
                    exposures_type='litpop',
                    properties={'country_iso3num':[str(country_code).zfill(3)],
                                'exponents':'(0,1)',
                                'fin_mode':'pop',
                                'version':'v2'
                                }
                    )
            except client.NoResult:
                print(f"there is no matching dataset in Data API. Country code: {country_code}. Skipping this calculation")
                continue

            # run impact calc for people exposed to cat. 1 wind speed or above
            impf_exposed = impf_set_exposed_pop(threshold=EXPOSED_TO_WIND_THRESHOLD)
            impact_exposed = ImpactCalc(exp, impf_exposed, tc_haz).impact()

            if impact_exposed.aai_agg == 0.: # do not save the files if impact is 0.
                print(f"No exposed population for country {country_code} with storm {tc_name}.")
            else:
                impact_exposed.write_hdf5(Path(IMPACT_DIR, f"{tc_name}_{country_iso3}_exposed_population.h5"))

            # run the same impact calc but for displacement
            impf_displacement = impf_set_displacement(country_iso3)

            impact_displacement = ImpactCalc(exp, impf_displacement, tc_haz).impact()

            if impact_displacement.aai_agg == 0.: # do not save the files if impact is 0.
                print(f"No displaced population for country {country_code} with storm {tc_name}.")
            else:
                impact_displacement.write_hdf5(Path(IMPACT_DIR, f"{tc_name}_{country_iso3}_displaced_population.h5"))
