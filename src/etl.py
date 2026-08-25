"""ETL for U.S. reporting-carrier flight operations data from BTS files."""
from __future__ import annotations
import argparse
from pathlib import Path
import zipfile
import pandas as pd
from sqlalchemy import create_engine
from src.config import RAW_DIR, PROCESSED_DIR, DATABASE_URL, TARGET_SAMPLE_SIZE, RANDOM_SEED

COLUMN_MAP = {
    'FlightDate': 'flight_date', 'Reporting_Airline': 'airline',
    'Flight_Number_Reporting_Airline': 'flight_number', 'Origin': 'origin',
    'OriginCityName': 'origin_city', 'OriginState': 'origin_state',
    'Dest': 'destination', 'DestCityName': 'destination_city', 'DestState': 'destination_state',
    'CRSDepTime': 'scheduled_departure', 'DepTime': 'actual_departure', 'DepDelay': 'departure_delay',
    'CRSArrTime': 'scheduled_arrival', 'ArrTime': 'actual_arrival', 'ArrDelay': 'arrival_delay',
    'ArrDel15': 'arrival_delayed_15', 'Cancelled': 'cancelled', 'CancellationCode': 'cancellation_code',
    'Diverted': 'diverted', 'CRSElapsedTime': 'scheduled_elapsed_time',
    'ActualElapsedTime': 'actual_elapsed_time', 'AirTime': 'air_time', 'Distance': 'distance',
    'CarrierDelay': 'carrier_delay', 'WeatherDelay': 'weather_delay', 'NASDelay': 'nas_delay',
    'SecurityDelay': 'security_delay', 'LateAircraftDelay': 'late_aircraft_delay',
    'TaxiOut': 'taxi_out', 'TaxiIn': 'taxi_in', 'DayOfWeek': 'day_of_week',
}

def _read_one(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == '.zip':
        with zipfile.ZipFile(path) as z:
            csv_name = next(n for n in z.namelist() if n.lower().endswith('.csv'))
            with z.open(csv_name) as f:
                return pd.read_csv(f, low_memory=False)
    return pd.read_csv(path, low_memory=False)

def transform(df: pd.DataFrame) -> pd.DataFrame:
    available = [c for c in COLUMN_MAP if c in df.columns]
    df = df.loc[:, available].rename(columns=COLUMN_MAP).copy()
    df['flight_date'] = pd.to_datetime(df['flight_date'], errors='coerce')
    numeric = [c for c in df.columns if c not in {'flight_date','airline','origin','origin_city','origin_state','destination','destination_city','destination_state','cancellation_code'}]
    for c in numeric:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    for c in ['cancelled','diverted','arrival_delayed_15']:
        if c in df:
            df[c] = df[c].fillna(0).astype(int)
    df['route'] = df['origin'].astype(str) + '-' + df['destination'].astype(str)
    df['month'] = df['flight_date'].dt.month
    df['day_of_month'] = df['flight_date'].dt.day
    df['departure_hour'] = (df['scheduled_departure'].fillna(0).astype(int) // 100).clip(0, 23)
    df['is_weekend'] = df['day_of_week'].isin([6, 7]).astype(int)
    df['on_time'] = ((df['arrival_delay'].fillna(0) < 15) & (df['cancelled'] == 0)).astype(int)
    delay_cols = ['carrier_delay','weather_delay','nas_delay','security_delay','late_aircraft_delay']
    for c in delay_cols:
        if c not in df: df[c] = 0.0
        df[c] = df[c].fillna(0)
    df['primary_delay_cause'] = df[delay_cols].idxmax(axis=1).str.replace('_delay','', regex=False)
    df.loc[df[delay_cols].sum(axis=1).eq(0), 'primary_delay_cause'] = 'none'
    return df.dropna(subset=['flight_date','origin','destination'])

def build_dimensions(flights: pd.DataFrame):
    airports_o = flights[['origin','origin_city','origin_state']].rename(columns={'origin':'airport_code','origin_city':'city','origin_state':'state'})
    airports_d = flights[['destination','destination_city','destination_state']].rename(columns={'destination':'airport_code','destination_city':'city','destination_state':'state'})
    dim_airport = pd.concat([airports_o, airports_d]).drop_duplicates('airport_code').sort_values('airport_code')
    dim_date = pd.DataFrame({'flight_date': sorted(flights['flight_date'].dropna().unique())})
    dim_date['flight_date'] = pd.to_datetime(dim_date['flight_date'])
    dim_date['year'] = dim_date.flight_date.dt.year
    dim_date['month'] = dim_date.flight_date.dt.month
    dim_date['month_name'] = dim_date.flight_date.dt.month_name()
    dim_date['day'] = dim_date.flight_date.dt.day
    dim_date['day_of_week'] = dim_date.flight_date.dt.dayofweek + 1
    dim_date['day_name'] = dim_date.flight_date.dt.day_name()
    dim_date['is_weekend'] = (dim_date.flight_date.dt.dayofweek >= 5).astype(int)
    dim_route = flights[['route','origin','destination','distance']].drop_duplicates('route').sort_values('route')
    dim_airline = flights[['airline']].drop_duplicates().sort_values('airline')
    return dim_airport, dim_date, dim_route, dim_airline

def run(input_dir: Path = RAW_DIR, database_url: str = DATABASE_URL):
    paths = sorted([*input_dir.glob('*.zip'), *input_dir.glob('*.csv')])
    if not paths:
        raise FileNotFoundError(f'No ZIP/CSV files in {input_dir}. Run download_data.py first.')
    chunks = []
    for p in paths:
        print(f'Reading {p.name}')
        t = transform(_read_one(p))
        if not t.empty: chunks.append(t)
    if not chunks:
        raise ValueError('No usable airline rows found in supplied files.')
    flights = pd.concat(chunks, ignore_index=True).drop_duplicates()
    if len(flights) > TARGET_SAMPLE_SIZE:
        flights = flights.sample(n=TARGET_SAMPLE_SIZE, random_state=RANDOM_SEED).sort_values('flight_date').reset_index(drop=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    flights.to_csv(PROCESSED_DIR / 'us_airline_flights_75k.csv', index=False)
    dim_airport, dim_date, dim_route, dim_airline = build_dimensions(flights)
    engine = create_engine(database_url)
    flights.to_sql('fact_flights', engine, if_exists='replace', index=False, chunksize=5000)
    dim_airport.to_sql('dim_airport', engine, if_exists='replace', index=False)
    dim_date.to_sql('dim_date', engine, if_exists='replace', index=False)
    dim_route.to_sql('dim_route', engine, if_exists='replace', index=False)
    dim_airline.to_sql('dim_airline', engine, if_exists='replace', index=False)
    print(f'Loaded {len(flights):,} U.S. reporting-carrier flights into {database_url}')
    return flights

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--input-dir', type=Path, default=RAW_DIR)
    args = p.parse_args()
    run(args.input_dir)
