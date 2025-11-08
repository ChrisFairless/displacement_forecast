#!/bin/sh

# Clear up intermediate files to save space
# As is, this will delete everything except the raw bufr files downloaded from 
# ECMWF, and the output report files

# Choose a subset of outputs to remove: make this string longer or shorter 
# to remove a year/month/day/individual forecast
OUTPUT_ROOT='/Users/chrisfairless/Data/UNU/idmc/displacement_forecast/output/20'

echo "Deleting intermediate files"

# Delete the CLIMADA Track files created from the downloaded bufrs
rm -v ${OUTPUT_ROOT}*/tracks/*.h5

# Delete the tracks plot (it's copied to the report folder)
rm -v ${OUTPUT_ROOT}*/analysis_tracks/*.png

# Delete the wind fields
rm -v ${OUTPUT_ROOT}*/wind_fields/*.hdf5

# Delete the Impact objects
rm -v ${OUTPUT_ROOT}*/impacts/*.h5

# Delete the Impact plots and summary stats
rm -v ${OUTPUT_ROOT}*/analysis_impacts/*.png
rm -v ${OUTPUT_ROOT}*/analysis_impacts/*.csv
rm -v ${OUTPUT_ROOT}*/analysis_impacts/*.json
