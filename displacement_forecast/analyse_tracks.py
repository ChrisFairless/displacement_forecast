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
from datetime import datetime
from pathlib import Path

# import plotly.graph_objects as go
import matplotlib as mpl
import matplotlib.cm as cm_mp
from matplotlib.colors import BoundaryNorm, ListedColormap

from climada_petals.hazard import TCForecast
from climada.hazard import TCTracks
from climada import CONFIG
from displacement_forecast.tc_tracks_func import filter_storm, _correct_max_sustained_wind_speed
from displacement_forecast.plot_func import (
    plot_global_tracks, plot_empty_base_map, 
    plot_interactive_map, plot_empty_interactive_map
)
from displacement_forecast.calculate_windfields import get_forecast_tracks

WORKING_DIR = CONFIG.forecast_sandbox.dir.str()


def analyse_tracks(time_str, overwrite=False):

    FORECAST_DIR = Path(WORKING_DIR, time_str)
    TRACKS_DIR = Path(FORECAST_DIR, "tracks")
    TRACK_ANALYSIS_DIR = Path(FORECAST_DIR, "analysis_tracks")

    if not os.path.exists(FORECAST_DIR):
        raise FileNotFoundError(f"Directory {str(FORECAST_DIR)} does not exist. Please download the forecast first.")    
    if not os.path.exists(TRACKS_DIR):
        raise FileNotFoundError(f"Directory {str(TRACKS_DIR)} does not exist. Please download the forecast first.")    
    os.makedirs(TRACK_ANALYSIS_DIR, exist_ok=True)

    if len(os.listdir(TRACK_ANALYSIS_DIR)) > 0 and not overwrite:
        print(f"Forecast track analysis for {time_str} already computed, skipping.")
        return

    # retrieve the forecast (already downloaded)
    tr_filter = get_forecast_tracks(time_str)
    forecast_time = datetime.strptime(time_str, '%Y%m%d%H0000')
    formatted_datetime = forecast_time.strftime('%Y-%m-%d %H:%M UTC')

    # plotting the global overview in .png
    if len(tr_filter.data)==0:
        print("No named storms. Generating empty plot.")
        axis_png = plot_empty_base_map()
        axis_png.set_title(
            f"Forecast time: {formatted_datetime}\n"
            f"Current number of active storms: 0",
            fontdict={"fontsize": 14})
    else:
        print(f"Plotting {len(tr_filter.data)} named storms.")
        tr_unique_storm_id = [tr.sid for tr in tr_filter.data]
        tr_storm_id_list = list(set(tr_unique_storm_id))

        axis_png = plot_global_tracks(tr_filter)
        axis_png.set_title(
            f"Forecast time: {formatted_datetime}\n"
            f"Current number of active storms: {str(len(tr_storm_id_list))}",
            fontdict={"fontsize": 14})

    axis_png.figure.savefig(Path(TRACK_ANALYSIS_DIR, f"ECMWF_TC_tracks_{time_str}.png"))

    # plotting the global overview in interactive map
    print("Skipping interactive map for now...")
    # if len(tr_filter.data)==0:
    #     fig_interactive = plot_empty_interactive_map()
    # else:
    #     fig_interactive = plot_interactive_map(tr_filter)

    # fig_interactive.write_html(
    #     Path(TRACK_ANALYSIS_DIR, f"ECMWF_TC_tracks_interactive_map_{formatted_datetime}.html"),
    #     full_html=False,  # for embedding in other HTML files
    #     include_plotlyjs='cdn'
    # )