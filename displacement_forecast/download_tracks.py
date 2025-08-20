import os
from pathlib import Path
import ftplib
import pandas as pd

from climada import CONFIG
from climada_petals.hazard.tc_tracks_forecast import TCForecast

from climada.hazard import TropCyclone, TCTracks
from climada_petals.hazard import TCForecast
from climada.util.api_client import Client

from displacement_forecast.tc_tracks_func import filter_storm, _correct_max_sustained_wind_speed

client = Client()
ECMWF_FTP = CONFIG.hazard.tc_tracks_forecast.resources.ecmwf
WORKING_DIR = CONFIG.forecast_sandbox.dir.str()


def get_forecast_tracks(time_str):
    # Forecast time string must be in the format '%Y%m%d%H0000'
    
    FORECAST_DIR = Path(WORKING_DIR, time_str)
    TRACKS_DIR = Path(FORECAST_DIR, "tracks")

    if not os.path.exists(TRACKS_DIR):
        raise FileNotFoundError(f"Directory {str(TRACKS_DIR)} does not exist. Please download the forecast first.")
    
    return TCTracks.from_hdf5(Path(TRACKS_DIR, "ECMWF_TC_tracks.h5"))


def download_and_process_forecast(time_str, overwrite=False):
    download_forecast(time_str, overwrite=overwrite)
    process_bufr(time_str, overwrite=overwrite)


def download_forecast(time_str, overwrite=False):

    # Forecast time string must be in the format '%Y%m%d%H0000'

    # Download forecast
    FORECAST_DIR = Path(WORKING_DIR, time_str)
    os.makedirs(FORECAST_DIR, exist_ok=True)

    BUFR_DIR = Path(FORECAST_DIR, "bufr")
    os.makedirs(BUFR_DIR, exist_ok=True)

    local_files = os.listdir(BUFR_DIR)
    if len(local_files) > 0 and not overwrite:
        print(f"Forecast {time_str} already downloaded, skipping.")
    else:
        TCForecast.fetch_bufr_ftp(target_dir=BUFR_DIR, remote_dir=time_str)



def process_bufr(time_str, overwrite=False):    
    FORECAST_DIR = Path(WORKING_DIR, time_str)
    BUFR_DIR = Path(FORECAST_DIR, "bufr")
    TRACKS_DIR = Path(FORECAST_DIR, "tracks")

    if not os.path.exists(FORECAST_DIR) or not os.path.exists(BUFR_DIR):
        raise FileNotFoundError(f"Directory {str(FORECAST_DIR)} does not exist. Please download the forecast first.")    
    os.makedirs(TRACKS_DIR, exist_ok=True)

    if len(os.listdir(TRACKS_DIR)) > 0 and not overwrite:
        print(f"Tracks for forecast {time_str} already exist, skipping.")
        return

    # read forecast
    tr_fcast = TCForecast()
    tr_fcast.fetch_ecmwf(path=BUFR_DIR)

    # filter to named storms
    tr_filter = filter_storm(tr_fcast)

    # interpolate to 10-minute timesteps
    tr_filter.equal_timestep(1/6)

    # apply wind correction
    _correct_max_sustained_wind_speed(tr_filter)

    # write tracks to file
    tr_filter.write_hdf5(Path(TRACKS_DIR, "ECMWF_TC_tracks.h5"))



def download_and_process_latest_forecast(overwrite=False):
    latest_time = get_latest_forecast_time()
    download_forecast(latest_time, overwrite=overwrite)
    process_bufr(latest_time, overwrite=overwrite)


def get_available_forecast_times():
    con = ftplib.FTP(host=ECMWF_FTP.host.str(),
                        user=ECMWF_FTP.user.str(),
                        passwd=ECMWF_FTP.passwd.str())
    try:
        # Read list of directories on the FTP server
        remote = pd.Series(con.nlst())
        # Identify directories with forecasts initialised as 00 or 12 UTC
        remote = remote[remote.str.contains('120000|000000$')]
        # Select the most recent directory (names are formatted yyyymmddhhmmss)
        remote = remote.sort_values(ascending=False)

    except ftplib.all_errors as err:
        con.quit()
        raise type(err)('Error while downloading BUFR TC tracks: ' + str(err)) from err

    _ = con.quit()
    return remote


def get_most_recent_forecast_time():
    remote = get_available_forecast_times()
    return remote.iloc[0]



if __name__ == "__main__":
    print("Available forecast times:")
    forecast_times = get_available_forecast_times()
    print(forecast_times)
    print("Most recent forecast time:")
    most_recent_time = forecast_times.iloc[0]
    print(most_recent_time)
    print("Downloading latest forecast...")
    download_and_process_latest_forecast(time_str=most_recent_time, overwrite=False)
