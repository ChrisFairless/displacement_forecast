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


WORKING_DIR = CONFIG.forecast_sandbox.dir.str()
TEMPLATE_DIR = Path(Path(__file__).parent.parent, 'reporting_templates', 'home')


def build_index_page():
    print("Building home page...")
    os.makedirs(WORKING_DIR, exist_ok=True)

    forecast_dir_list = [p for p in os.listdir(WORKING_DIR) if os.path.isdir(Path(WORKING_DIR, p))]
    forecast_dir_list = [p for p in forecast_dir_list if os.path.exists(Path(WORKING_DIR, p, 'report', 'report.md'))]
    forecast_dir_list = [p for p in forecast_dir_list if os.path.exists(Path(WORKING_DIR, p, 'report', 'summary_stats.json'))]
    results_dir_list = [Path(WORKING_DIR, p, 'report') for p in forecast_dir_list]

    summary_stats = pd.DataFrame(load_json(Path(p, 'summary_stats.json')) for p in results_dir_list)
    summary_stats['url'] = [str(Path(p, 'report', 'report.html')) for p in forecast_dir_list]
    summary_stats['link_markdown'] = [f'[{p["forecast_time"]}]({p["url"]})' for _, p in summary_stats.iterrows()]
    summary_stats['storm_names_str'] = summary_stats['storm_names'].apply(lambda x: '\n'.join(x))

    output_stats = pd.DataFrame({
        'Forecast Time': summary_stats['link_markdown'],
        'Number of Named Storms': summary_stats['number_active'],
        'Storms': summary_stats['storm_names_str'],
        'Number Affecting People': summary_stats['number_affecting_people'],
        'Number Displacing People': summary_stats['number_displacing_people']
    })

    index_file = Path(WORKING_DIR, 'home.md')
    shutil.copy(Path(TEMPLATE_DIR, 'home.md'), index_file)

    index_components = [index_file]

    summary_file = Path(WORKING_DIR, 'summary_of_forecasts.md')
    shutil.copy(Path(TEMPLATE_DIR, 'summary_of_forecasts.md'), summary_file)
    with open(summary_file, "a") as f:
        output_stats.to_markdown(f, index=False, tablefmt="pipe", floatfmt=".2f")
    index_components.append(summary_file)
 
    # List of input files to combine
    index_components = [str(f) for f in index_components]
    output_file = Path(WORKING_DIR, 'index.md')

    with open(output_file, 'w', encoding='utf-8') as outfile:
        for fname in index_components:
            with open(fname, 'r', encoding='utf-8') as infile:
                outfile.write(infile.read())
                outfile.write('\n')

    # Build the pandoc command
    output_html = Path(WORKING_DIR, 'index.html')
    cmd = ['pandoc', output_file, '-o', output_html]

    # Run the command
    subprocess.run(cmd, check=True)

    # Remove intermediate files
    for f in index_components:
        os.remove(f)


def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

if __name__ == "__main__":
    build_index_page()
