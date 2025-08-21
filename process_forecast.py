from datetime import datetime

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


def process_forecast(
    time_str=None,
    overwrite=False,
    redownload=False
    ):

    # Identify and process latest forecast
    if time_str is None:
        print("Processing latest forecast...")
        time_str = download_tracks.get_most_recent_forecast_time()
        print("Most recent forecast time:", time_str)

        print("--- STEP 1: Downloading ---")
        try:
            download_tracks.download_and_process_forecast(time_str, overwrite=redownload)
        except FileNotFoundError as e:
            print(f"Failed to download forecast for {time_str}: most likely it has not been processed and uploaded yet: {e}")
            print("Downloading previous forecast instead...")
            forecast_time = datetime.strptime(time_str, '%Y%m%d%H0000')
            previous_forecast_time = forecast_time - pd.Timedelta(hours=12)
            time_str = previous_forecast_time.strftime('%Y%m%d%H0000')
            download_tracks.download_and_process_forecast(time_str, overwrite=redownload)

    else:
        print("--- STEP 1: Downloading ---")
        download_tracks.download_and_process_forecast(time_str, overwrite=redownload)
        if download_tracks.count_named_storms(time_str) == 0:
            print(f"No named storms found in forecast {time_str}. Finished.")
            return

    print("--- STEP 2: Analysing forecast tracks ---")
    analyse_tracks.analyse_tracks(time_str, overwrite=overwrite)

    print("--- STEP 3: Generating wind fields ---")
    calculate_windfields.calculate_windfields(time_str, overwrite=overwrite)

    # print("Analysing wind fields...")
    # analyse_windfields.analyse_windfields(time_Str, overwrite=overwrite)

    print("--- STEP 4: Calculating impacts ---")
    calculate_impacts.calculate_impacts(time_str, overwrite=overwrite)

    print("--- STEP 5: Analysing impacts ---")
    analyse_impacts.analyse_impacts(time_str, overwrite=overwrite)

    print("--- STEP 6: Building report ---")
    build_report.build_report(time_str, overwrite=overwrite)

    print("--- STEP 7: Rebuilding index page ---")
    build_index_page.build_index_page()



if __name__ == "__main__":
    # process_forecast('20250811000000', overwrite=True, redownload=False)
    # process_forecast(time_str=None, overwrite=True, redownload=False)
    process_forecast()