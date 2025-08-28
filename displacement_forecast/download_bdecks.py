
import os
import requests
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup
from io import StringIO
from datetime import datetime

# Constants
year = datetime.utcnow().year
BASE_URL = f"https://hurricanes.ral.ucar.edu/repository/data/bdecks_open/{year}/"
LOCAL_DIR = f"/Users/chrisfairless/Projects/UNU/idmc/forecast/displacement_forecast/displacement_forecast/docs/bdecks/{year}/"


def download_bdecks():
    # Ensure local directory exists
    os.makedirs(LOCAL_DIR, exist_ok=True)

    # Get list of existing local files
    local_files = [
        {
            'filename': f,
            'modified': os.path.getmtime(os.path.join(LOCAL_DIR, f))
        } for f in os.listdir(LOCAL_DIR)
    ]
    local_df = pd.DataFrame(local_files, columns=['filename', 'modified'])

    # Fetch the directory listing from the UCAR repository
    response = requests.get(BASE_URL)
    soup = BeautifulSoup(response.text, "html.parser")

    # Find the table
    table = soup.find("table")
    remote_df = pd.read_html(StringIO(str(table)))[0]
    remote_df = remote_df[['Name', 'Last modified']].rename(columns={'Name': 'filename', 'Last modified': 'modified'}).dropna()
    remote_df['modified'] = [datetime.strptime(s, '%Y-%m-%d %H:%M') for s in remote_df['modified']]

    df = remote_df.merge(local_df, on='filename', how='left', suffixes=('_remote', '_local'))

    print('Reading remote files and updating local data')
    for _, row in df.iterrows():
        print(f"{row['filename']}: {row['modified_remote']}")
        download_file = False

        if pd.isna(row['modified_local']):
            download_file = True
            print('   ...downloading new track')

        if abs(row['modified_remote'].timestamp() - row['modified_local']) > 60:
            download_file = True
            print('   ...downloading updated file')

        if not download_file:
            print('   ...up to date: skipping')
            continue

        file_url = BASE_URL + row['filename']
        try:
            r = requests.get(file_url)
            local_path = Path(LOCAL_DIR, row['filename'])
            with open(local_path, 'wb') as f:
                f.write(r.content)
            
            # Modify the file's timestamp to match the remote file's last modified time
            ts = row['modified_remote'].timestamp()
            os.utime(local_path, (ts, ts))
        except Exception as e:
            print(f"Failed to download {filename}: {e}")



if __name__ == "__main__":
    download_bdecks()