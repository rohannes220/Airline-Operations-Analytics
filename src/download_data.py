"""Download monthly BTS Reporting Carrier On-Time Performance ZIP files.

Example:
    python -m src.download_data --year 2025 --months 1 2 3
"""
import argparse
from pathlib import Path
import requests
from src.config import RAW_DIR

BASE = "https://transtats.bts.gov/PREZIP/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{year}_{month}.zip"

def download(year: int, month: int, out_dir: Path = RAW_DIR) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    url = BASE.format(year=year, month=month)
    path = out_dir / f"bts_{year}_{month:02d}.zip"
    if path.exists():
        print(f"Exists: {path}")
        return path
    print(f"Downloading {url}")
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with path.open('wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
    print(f"Saved: {path}")
    return path

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--year', type=int, required=True)
    p.add_argument('--months', type=int, nargs='+', required=True)
    args = p.parse_args()
    for m in args.months:
        if not 1 <= m <= 12:
            raise ValueError('Month must be 1-12')
        download(args.year, m)
