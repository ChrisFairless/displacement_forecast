import os
from pathlib import Path
from climada import CONFIG

from displacement_forecast import (
    download_tracks,
    analyse_tracks,
    calculate_windfields,
    # analyse_windfields,
    calculate_impacts,
    analyse_impacts,
    build_report
)

WORKING_DIR = CONFIG.forecast_sandbox.dir.str()

def get_forecast_times():
    forecast_time_list = os.listdir(WORKING_DIR)
    forecast_time_list = [p for p in forecast_time_list if p[0].isdigit() and len(p) == 14]
    print(f"There are {len(forecast_time_list)} forecast times available locally.")
    return forecast_time_list
    

def regenerate(func):
    print(f"Regenerating with {func.__name__}...")
    forecast_time_list = get_forecast_times()

    for time_str in forecast_time_list:
        print("FORECAST TIME: " + time_str)
        try:
            func(time_str, overwrite=True)
        except Exception as e:
            print(f"Error processing {time_str}: {e}")
            continue


def regenerate_all_forecasts():
    regenerate(download_tracks.download_and_process_forecast)

def regenerate_all_track_analyses():
    regenerate(analyse_tracks.analyse_tracks)

def regenerate_all_windfields():
    regenerate(calculate_windfields.calculate_windfields)

def regenerate_all_impacts():
    regenerate(calculate_impacts.calculate_impacts)

def regenerate_all_impact_analyses():
    regenerate(analyse_impacts.analyse_impacts)

def regenerate_all_reports():
    regenerate(build_report.build_report)



if __name__ == "__main__":
    regenerate_all_reports()