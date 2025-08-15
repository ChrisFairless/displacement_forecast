#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import warnings
warnings.filterwarnings("ignore")

import os
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

from climada import CONFIG
from climada.hazard import Hazard
from climada.engine import ImpactCalc, Impact
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
from displacement_forecast.plot_func import (
    plot_imp_map_exposed,
    plot_imp_map_displacement,
    plot_histogram,
    make_save_map_file_name,
    make_save_histogram_file_name
)

WORKING_DIR = CONFIG.forecast_sandbox.dir.str()


def analyse_impacts(time_str=None, overwrite=False):

    FORECAST_DIR = Path(WORKING_DIR, time_str)
    IMPACT_DIR = Path(FORECAST_DIR, "impacts")
    IMPACT_ANALYSIS_DIR = Path(FORECAST_DIR, "analysis_impacts")

    if not os.path.exists(FORECAST_DIR):
        raise FileNotFoundError(f"Directory {str(FORECAST_DIR)} does not exist. Please download the forecast first and calculate wind fields and impacts.")
    if not os.path.exists(IMPACT_DIR):
        raise FileNotFoundError(f"Directory {str(IMPACT_DIR)} does not exist. Please calculate impacts first.")
    os.makedirs(IMPACT_ANALYSIS_DIR, exist_ok=True)

    if len(os.listdir(IMPACT_ANALYSIS_DIR)) > 0 and not overwrite:
        print(f"Analyses for forecast {time_str} already computed, skipping.")
        return

    impact_files = os.listdir(IMPACT_DIR)
    if len(impact_files) == 0:
        print(f"No impacts found at {time_str}. No impacts to analyse.")

    # Start the impact calculation for all the storms
    for impact_file in impact_files:

        # extract tc_name and country from the hdf file
        tc_base_file_name = os.path.basename(impact_file)
        tc_name = tc_base_file_name.split('_')[0]
        country_iso3 = tc_base_file_name.split('_')[1]
        impact_type = tc_base_file_name.split('_')[2]
        print(f"Analysing impacts for storm {tc_name} in country {country_iso3} for {impact_type} population...")

        forecast_time = datetime.strptime(time_str, '%Y%m%d%H0000')
        formatted_datetime = forecast_time.strftime('%Y-%m-%d_%HUTC')

        # read the hdf file
        impact = Impact.from_hdf5(Path(IMPACT_DIR, impact_file))

        imp_summary = summarize_forecast(
            country_iso3=country_iso3,
            forecast_time=formatted_datetime,
            impact_type=impact_type,
            tc_name=tc_name,
            impact=impact)

        save_forecast_summary(
            IMPACT_ANALYSIS_DIR,
            imp_summary)
        save_average_impact_geospatial_points(
            IMPACT_ANALYSIS_DIR,
            imp_summary,
            impact)
        save_impact_at_event(
            IMPACT_ANALYSIS_DIR,
            imp_summary,
            impact)
        
        if impact_type == "exposed":
            # create impact maps
            ax_map_exposed = plot_imp_map_exposed(imp_summary, impact)
            ax_map_exposed.figure.savefig(Path(IMPACT_ANALYSIS_DIR, make_save_map_file_name(imp_summary)))

            # create histogram
            ax_hist_exposed = plot_histogram(imp_summary, impact)
            ax_hist_exposed.figure.savefig(Path(IMPACT_ANALYSIS_DIR, make_save_histogram_file_name(imp_summary)))

        if impact_type == "displacement":
            # create impact maps
            ax_map_displacement = plot_imp_map_displacement(imp_summary, impact)
            ax_map_displacement.figure.savefig(Path(IMPACT_ANALYSIS_DIR, make_save_map_file_name(imp_summary)))

            # create histogram
            ax_hist_displacement = plot_histogram(imp_summary, impact)
            ax_hist_displacement.figure.savefig(Path(IMPACT_ANALYSIS_DIR, make_save_histogram_file_name(imp_summary)))