import os
from climada import CONFIG

WORKING_DIR = CONFIG.forecast_sandbox.dir.str()

def get_most_recent_forecast_dir() -> TCForecast:
    dir_list = os.listdir(WORKING_DIR)[-1]
