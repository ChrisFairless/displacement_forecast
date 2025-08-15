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
    

def process_forecast(time_str=None, overwrite=False):

    if time_str is None:
        print("Processing latest forecast...")
        time_str = download_tracks.get_most_recent_forecast_time()
        print("Most recent forecast time:", time_str)
    
    print("--- STEP 1: Downloading ---")
    download_tracks.download_and_process_forecast(time_str, overwrite=overwrite)

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
    build_report.build_report(time_str, overwrite=True)

    print("--- STEP 7: Rebuilding index page ---")
    build_index_page.build_index_page()



if __name__ == "__main__":
    # process_forecast('20250812120000', overwrite=True)
    process_forecast()