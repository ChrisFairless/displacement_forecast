import warnings
warnings.filterwarnings("ignore")

import os
import glob
import json
import numpy as np
import pandas as pd
from pathlib import Path
import subprocess
import shutil
from datetime import datetime, timedelta

from climada import CONFIG
from climada.hazard import Hazard
from climada.util.coordinates import get_country_code, country_to_iso
from climada.util.api_client import Client
client = Client()

from displacement_forecast.impact_calc_func import (
    round_to_previous_12h_utc, get_forecast_times,
    summarize_forecast
    )
from displacement_forecast.plot_func import (
    make_save_map_file_name, make_save_histogram_file_name
)

WORKING_DIR = CONFIG.forecast_sandbox.dir.str()
TEMPLATE_DIR = Path(Path(__file__).parent.parent, 'reporting_templates', 'report')


def build_report(time_str, overwrite=False):

    # Plotting directories
    FORECAST_DIR = Path(WORKING_DIR, time_str)
    TRACKS_DIR = Path(FORECAST_DIR, "tracks")
    TRACK_ANALYSIS_DIR = Path(FORECAST_DIR, "analysis_tracks")
    WIND_DIR = Path(FORECAST_DIR, "wind_fields")
    IMPACT_DIR = Path(FORECAST_DIR, "impacts")
    IMPACT_ANALYSIS_DIR = Path(FORECAST_DIR, "analysis_impacts")
    REPORT_DIR = Path(FORECAST_DIR, "report")

    summary_stats = {}

    if not os.path.exists(FORECAST_DIR):
        raise FileNotFoundError(f"Directory {str(FORECAST_DIR)} does not exist. Please download the forecast first and calculate wind fields and impacts.")
    os.makedirs(REPORT_DIR, exist_ok=True)
    os.makedirs(LATEST_DIR, exist_ok=True)

    if os.path.exists(Path(REPORT_DIR, 'report.md')) and not overwrite:
        print(f"Report for forecast {time_str} already built, skipping.")
        return

    index_file = Path(TEMPLATE_DIR, 'index.md')
    report_components = [index_file]
    find_replace = {}

    # load data
    forecast_time = datetime.strptime(time_str, '%Y%m%d%H0000')
    forecast_time_str = forecast_time.strftime('%Y-%m-%d %H:%M UTC')
    tc_wind_files = os.listdir(WIND_DIR)
    find_replace['XX_date_XX'] = forecast_time_str
    find_replace['XX_number_active_XX'] = str(len(tc_wind_files))

    summary_stats['forecast_time'] = forecast_time_str
    summary_stats['number_active'] = len(tc_wind_files)
    summary_stats['storm_names'] = []
    summary_stats['number_affecting_people'] = 0
    summary_stats['number_displacing_people'] = 0

    track_plot_filename = f"ECMWF_TC_tracks_{time_str}.png"
    track_plot_path = Path(TRACK_ANALYSIS_DIR, track_plot_filename)
    shutil.copy(track_plot_path, Path(REPORT_DIR, track_plot_filename))
    find_replace['XX_tracks_plot_XX'] = track_plot_filename

    print("Adding overview")
    overview_file = Path(REPORT_DIR, 'tracks_overview.md')
    shutil.copy(Path(TEMPLATE_DIR, 'tracks_overview.md'), overview_file)
    find_replace_in_file(overview_file, find_replace)
    report_components.append(overview_file)


    # This section was for the interactive map plot. Not using that for now, going static instead.

    # tracks_plot_src = Path(TRACKS_DIR, f"ECMWF_TC_tracks_interactive_map_{forecast_time_str}.html")
    # tracks_plot_dst = Path(REPORT_DIR, f"interactive_map.html")
    # shutil.copy(tracks_plot_src, tracks_plot_dst)

    # Old: when the <head> tag was included in the HTML file
    # with open(tracks_plot_src, 'r', encoding='utf-8') as file:
    #     lines = file.readlines()

    # with open(tracks_plot_dst, 'w', encoding='utf-8') as file:
    #     file.write('<div>')
    #     for line in lines[3:-1]:  # Skip the first two lines which are the <head> tag
    #         file.write(line)
    #     file.write('</div>')

    # report_components.append(tracks_plot_dst)


    # Gather the impact calculation for all the storms
    for tc_file in tc_wind_files:
        print("...working on storm file:", tc_file)

        # extract the tc_name from the hdf file
        tc_base_file_name = os.path.basename(tc_file)
        tc_name = tc_base_file_name.split('_')[2]
        find_replace['XX_name_XX'] = tc_name
        summary_stats['storm_names'].append(tc_name)

        impact_files = os.listdir(IMPACT_DIR)
        impact_files = [f for f in impact_files if f.startswith(tc_name)]
        country_code_all = [f.split('_')[1] for f in impact_files]
        country_code_unique = np.unique(country_code_all)

        if len(country_code_unique) == 0:
            print(f"No affected countries found for storm {tc_name}.")
            shutil.copy(Path(TEMPLATE_DIR, 'exposed_none.md'), Path(REPORT_DIR, 'exposed_none.md'))
            shutil.copy(Path(TEMPLATE_DIR, 'displacement_none.md'), Path(REPORT_DIR, 'displacement_none.md'))
            find_replace_in_file(Path(REPORT_DIR, 'exposed_none.md'), find_replace)
            find_replace_in_file(Path(REPORT_DIR, 'displacement_none.md'), find_replace)
            report_components.append(Path(REPORT_DIR, 'exposed_none.md'))
            report_components.append(Path(REPORT_DIR, 'displacement_none.md'))
            continue


        for country_code in country_code_unique:
            print("Working on country code:", country_code)

            country_iso3 = country_to_iso(country_code, "alpha3")

            storm_dict = {
                "eventName": tc_name,
                "countryISO3": country_iso3,
                "initializationTime": time_str,
                "impactType": "exposed_population_32.92ms",
            }
            exposed_map_filename = make_save_map_file_name(storm_dict)
            exposed_hist_filename = make_save_histogram_file_name(storm_dict)
            exposed_map_path = Path(IMPACT_ANALYSIS_DIR, exposed_map_filename)
            exposed_hist_path = Path(IMPACT_ANALYSIS_DIR, exposed_hist_filename)
            find_replace['XX_exposed_map_path_XX'] = exposed_map_filename
            find_replace['XX_exposed_hist_path_XX'] = exposed_hist_filename
            exposed_file = Path(REPORT_DIR, f"exposed_{tc_name}_{country_iso3}.md")

            if os.path.exists(exposed_map_path):
                print("processing " + str(exposed_map_path))
                shutil.copy(Path(TEMPLATE_DIR, 'exposed.md'), exposed_file)
                shutil.copy(exposed_map_path, Path(REPORT_DIR, exposed_map_filename))
                shutil.copy(exposed_hist_path, Path(REPORT_DIR, exposed_hist_filename))
                summary_stats['number_affecting_people'] += 1
            else:
                print("No exposed population found at " + str(exposed_map_path))
                shutil.copy(Path(TEMPLATE_DIR, 'exposed_none.md'), exposed_file)
            find_replace_in_file(exposed_file, find_replace)
            report_components.append(exposed_file)


            storm_dict["impactType"] = "displacement"
            displacement_map_filename = make_save_map_file_name(storm_dict)
            displacement_hist_filename = make_save_histogram_file_name(storm_dict)
            displacement_map_path = Path(IMPACT_ANALYSIS_DIR, displacement_map_filename)
            displacement_hist_path = Path(IMPACT_ANALYSIS_DIR, displacement_hist_filename)
            find_replace['XX_displacement_map_path_XX'] = displacement_map_filename
            find_replace['XX_displacement_hist_path_XX'] = displacement_hist_filename
            displacement_file = Path(REPORT_DIR, f"displacement_{tc_name}_{country_iso3}.md")

            if os.path.exists(displacement_map_path):
                print("processing " + str(displacement_map_path))
                shutil.copy(Path(TEMPLATE_DIR, 'displacement.md'), displacement_file)
                shutil.copy(displacement_map_path, Path(REPORT_DIR, displacement_map_filename))
                shutil.copy(displacement_hist_path, Path(REPORT_DIR, displacement_hist_filename))
                summary_stats['number_displacing_people'] += 1
            else:
                print("No displaced population found at " + str(displacement_map_path))
                shutil.copy(Path(TEMPLATE_DIR, 'displacement_none.md'), displacement_file)
            find_replace_in_file(displacement_file, find_replace)
            report_components.append(displacement_file)

    json.dump(summary_stats, open(Path(REPORT_DIR, 'summary_stats.json'), 'w', encoding='utf-8'))

    print("Combining report components")

    # List of input files to combine
    report_components = [str(f) for f in report_components]
    output_file = Path(REPORT_DIR, 'report.md')

    with open(output_file, 'w', encoding='utf-8') as outfile:
        for fname in report_components:
            with open(fname, 'r', encoding='utf-8') as infile:
                outfile.write(infile.read())
                outfile.write('\n')

    # Build the pandoc command
    # cmd = ['pandoc', *report_components, '-o', output_file]

    # Build the pandoc command
    output_html = Path(REPORT_DIR, 'report.html')
    cmd = ['pandoc', output_file, '-o', output_html]

    # Run the command
    subprocess.run(cmd, check=True)


def find_replace_in_file(file_path, find_replace_dict):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    for key, value in find_replace_dict.items():
        content = content.replace(key, value)

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
