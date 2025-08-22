from displacement_forecast import (
    download_tracks,
    analyse_tracks,
    calculate_windfields,
    # analyse_windfields,
    calculate_impacts,
    analyse_impacts,
    build_report,
    build_index_page
)
import os
import sys
from pathlib import Path
from traceback import print_tb
import pandas as pd
from climada import CONFIG

WORKING_DIR = CONFIG.forecast_sandbox.dir.str()



def check_outputs_complete(fix=False):
    forecasts = []

    # Download list of current forecasts
    forecast_time_list_ftp = download_tracks.get_available_forecast_times()
    print(f"There are {len(forecast_time_list_ftp)} forecast times available.")

    forecast_time_list_local = os.listdir(WORKING_DIR)
    forecast_time_list_local = [p for p in forecast_time_list_local if os.path.isdir(Path(WORKING_DIR, p))]
    forecast_time_list_local = [p for p in forecast_time_list_local if p[0].isdigit() and len(p) == 14]
    print(f"There are {len(forecast_time_list_local)} forecast times available locally.")

    all_times = set(forecast_time_list_ftp) | set(forecast_time_list_local)
    forecast_dict = {}

    for time_str in all_times:
        print("\n---------------------")
        print("FORECAST TIME: " + time_str)
        print("---------------------\n")

        forecast = {}
        FORECAST_DIR = Path(WORKING_DIR, time_str)

        forecast['time_str'] = time_str
        forecast['dir'] = {
            'root': FORECAST_DIR,
            'bufr': Path(FORECAST_DIR, "bufr"),
            'tracks': Path(FORECAST_DIR, "tracks"),
            'tracks_analysis': Path(FORECAST_DIR, "analysis_tracks"),
            'wind_fields': Path(FORECAST_DIR, "wind_fields"),
            'impacts': Path(FORECAST_DIR, "impacts"),
            'analysis_impacts': Path(FORECAST_DIR, "analysis_impacts"),
            'report': Path(FORECAST_DIR, "report")
        }
        forecast['exists_local'] = True if forecast['time_str'] in forecast_time_list_local else False
        forecast['exists_ftp'] = True if forecast['time_str'] in forecast_time_list_ftp else False
        forecast['success_download'] = False
        forecast['success_write_tracks'] = False
        forecast['success_track_plots'] = False
        forecast['success_wind_fields'] = False
        forecast['success_impacts'] = False
        forecast['success_impact_plots'] = False
        forecast['success_report'] = False
        forecast['final_step'] = None
        forecast['errors'] = []

        print("--- STEP 1: Downloads ---")
        try:
            forecast = check_downloads(forecast, fix=fix)
        except Exception as e:
            print(f"Error checking downloads for {time_str}: {str(sys.exc_info())}")
            print_tb(sys.exc_info()[2])
            forecast['errors'].append(f"Error checking downloads: {str(sys.exc_info())}")
            continue

        print("--- STEP 2: Analysing forecast tracks ---")
        try:
            forecast = check_track_plots(forecast, fix=fix)
        except Exception as e:
            print(f"Error checking track plots for {time_str}: {str(sys.exc_info())}")
            print_tb(sys.exc_info()[2])
            forecast['errors'].append(f"Error checking track plots: {str(sys.exc_info())}")
            continue

        print("--- STEP 3: Generating wind fields ---")
        try:
            forecast = check_wind_fields(forecast, fix=fix)
        except Exception as e:
            print(f"Error checking wind fields for {time_str}: {str(sys.exc_info())}")
            print_tb(sys.exc_info()[2])
            forecast['errors'].append(f"Error checking wind fields: {str(sys.exc_info())}")
            continue

        print("--- STEP 4: Calculating impacts ---")
        try:
            forecast = check_impacts(forecast, fix=fix)
        except Exception as e:
            print(f"Error checking impacts for {time_str}: {str(sys.exc_info())}")
            print_tb(sys.exc_info()[2])
            forecast['errors'].append(f"Error checking impacts: {str(sys.exc_info())}")
            continue

        print("--- STEP 5: Analysing impacts ---")
        try:
            forecast = check_impact_plots(forecast, fix=fix)
        except Exception as e:
            print(f"Error checking impact plots for {time_str}: {str(sys.exc_info())}")
            print_tb(sys.exc_info()[2])
            forecast['errors'].append(f"Error checking impact plots: {str(sys.exc_info())}")
            continue

        print("--- STEP 6: Building report ---")
        try:
            forecast = check_report(forecast, fix=fix)
        except Exception as e:
            print(f"Error checking report for {time_str}: {str(sys.exc_info())}")
            print_tb(sys.exc_info()[2])
            forecast['errors'].append(f"Error checking report: {str(sys.exc_info())}")
            continue

        forecast_dict[time_str] = forecast

    if fix:
        print("--- STEP 7: Rebuilding index page ---")
        try:
            build_index_page.build_index_page()
        except Exception as e:
            print(f"Error updating index page: {str(sys.exc_info())}")
            print_tb(sys.exc_info()[2])

    print("Writing output")
    output_path = Path(WORKING_DIR, 'check_outputs.csv')
    print(output_path)
    out = pd.DataFrame(forecast_dict).T
    print(out)
    out.to_csv(output_path, index=False)



def check_downloads(forecast, fix=False):    
    if fix and not forecast['exists_local']:
        if forecast['exists_ftp']:
            print(f"Missing download: downloading forecast {forecast['time_str']}...")
            download_tracks.download_and_process_forecast(forecast['time_str'], overwrite=True)      

    if not os.path.exists(forecast['dir']['bufr']):
        forecast['errors'].append(f"No downloaded data found")
        return forecast

    downloaded_files = os.listdir(forecast['dir']['bufr'])

    for file in downloaded_files:
        if not file.endswith('.bin'):
            forecast['errors'].append(f"Unexpected non .bin download: {file}")
        if forecast['time_str'] not in str(file):
            forecast['errors'].append(f"Downloaded filename does not contain the expected time string {forecast['time_str']}:  {file}")    
        if 'tropical_cyclone_track' not in str(file):
            forecast['errors'].append(f"Downloaded filename does not contain the string 'tropical_cyclone': {file}")

    forecast['storm_ids'] = [s.split('_')[8] for s in downloaded_files]
    forecast['named_storms'] = [s for s in forecast['storm_ids'] if not s[0].isdigit()]
    forecast['number_storms'] = len(forecast['named_storms'])
    forecast['success_download'] = len(downloaded_files) > 0
    if forecast['number_storms'] == 0:
        forecast['final_step'] = 'download_tracks'
        return forecast
    
    if forecast['number_storms'] == 0:
        forecast['final_step'] = 'download_tracks'
        return forecast

    if fix and not os.path.exists(forecast['dir']['tracks']):
        print(f"Missing tracks folder: reprocessing forecast {forecast['time_str']}...")
        download_tracks.process_bufr(forecast['time_str'], overwrite=True)
    
    tracks_path = Path(forecast['dir']['tracks'], "ECMWF_TC_tracks.h5")
    if fix and not os.path.exists(tracks_path):
        print(f"Missing tracks file: reprocessing forecast {forecast['time_str']}...")
        download_tracks.process_bufr(forecast['time_str'], overwrite=True)

    if not os.path.exists(tracks_path):
        forecast['errors'].append(f"No tracks file found at {tracks_path}.")
        return forecast

    forecast['success_write_tracks'] = True
    return forecast


def check_track_plots(forecast, fix=False):
    if not forecast['success_write_tracks']:
        return forecast

    if fix and not os.path.exists(forecast['dir']['tracks_analysis']):
        analyse_tracks.analyse_tracks(forecast['time_str'], overwrite=True)
    if fix and len(os.listdir(forecast['dir']['tracks_analysis'])) == 0:
        analyse_tracks.analyse_tracks(forecast['time_str'], overwrite=True)

    track_plots = os.listdir(forecast['dir']['tracks_analysis'])
    if len(track_plots) == 0:
        forecast['errors'].append("No track plots found.")
        return forecast

    forecast['success_track_plots'] = True
    return forecast


def check_wind_fields(forecast, fix=False):
    if not forecast['success_write_tracks']:
        return forecast

    if fix and not os.path.exists(forecast['dir']['wind_fields']):
        calculate_windfields.calculate_windfields(forecast['time_str'], overwrite=True)
    if fix and len(os.listdir(forecast['dir']['wind_fields'])) == 0:
        calculate_windfields.calculate_windfields(forecast['time_str'], overwrite=True)

    if len(os.listdir(forecast['dir']['wind_fields'])) == 0:
        forecast['errors'].append(f"No wind fields calculated despite names storms")
        return forecast

    forecast['success_wind_fields'] = True
    return forecast


def check_impacts(forecast, fix=False):
    if not forecast['success_wind_fields']:
        return forecast
    
    if fix and not os.path.exists(forecast['dir']['impacts']):
        calculate_impacts.calculate_impacts(forecast['time_str'], overwrite=True)
    
    impact_files = os.listdir(forecast['dir']['impacts'])
    forecast['has_impacts'] = False
    forecast['has_affected'] = False
    forecast['has_displaced'] = False

    if len(impact_files) == 0:
        forecast['final_step'] = 'calculate_windfields'
        return forecast

    for impact_file in impact_files:
        if 'affected' in impact_file:
            forecast['has_impacts'] = True
            forecast['has_affected'] = True
        if 'displaced' in impact_file:
            forecast['has_displaced'] = True
            break

    forecast['success_impacts'] = True
    forecast['final_step'] = 'calculate_impact'
    return forecast


def check_impact_plots(forecast, fix=False):
    if not forecast['success_impacts']:
        return forecast

    if fix and not os.path.exists(forecast['dir']['analysis_impacts']):
        analyse_impacts.analyse_impacts(forecast['time_str'], overwrite=True)
    if fix and len(os.listdir(forecast['dir']['analysis_impacts'])) == 0:
        analyse_impacts.analyse_impacts(forecast['time_str'], overwrite=True)
    
    impact_plots = os.listdir(forecast['dir']['analysis_impacts'])
    if len(impact_plots) == 0:
        forecast['errors'].append("No impact plots found.")
        return forecast
    
    forecast['success_impact_plots'] = True
    return forecast


def check_report(forecast, fix=False):
    if not forecast['success_download']:
        return forecast

    report_path = Path(forecast['dir']['report'], 'report.html')

    if fix and not os.path.exists(forecast['dir']['report']):
        build_report.build_report(forecast['time_str'], overwrite=True)
    if fix and not os.path.exists(report_path):
        build_report.build_report(forecast['time_str'], overwrite=True)

    if not os.path.exists(report_path):
        forecast['errors'].append("No report files found.")
        return forecast
    
    forecast['success_report'] = True
    return forecast


if __name__ == "__main__":
    check_outputs_complete(fix=False)
