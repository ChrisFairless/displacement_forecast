!#!/bin/sh
python scripts/01_download_ecmwf.py
python scripts/02_plot_tracks.py
python scripts/03_calculate_windfields.py