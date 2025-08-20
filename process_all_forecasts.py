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
    

def process_all_forecasts(overwrite=False):

    print("Processing all forecasts...")

    print("Fetching forecast data from ECMWF...")
    forecast_time_list = download_tracks.get_available_forecast_times()
    print(f"There are {str(len(forecast_time_list))} forecast times available.")

    for time_str in forecast_time_list:
        print("\n---------------------")
        print("FORECAST TIME: " + time_str)
        print("---------------------\n")

        print("--- STEP 1: Downloading ---")
        download_tracks.download_and_process_forecast(time_str, overwrite=overwrite)
        if download_tracks.count_named_storms(time_str) == 0:
            print(f"No named storms found in forecast {time_str}. Finished.")
            continue

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
    process_all_forecasts()