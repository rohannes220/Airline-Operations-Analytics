"""Create synthetic flight records to smoke-test the modeling pipeline.

These records are simulated and MUST NOT be reported as DOT/BTS data.
"""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from sqlalchemy import create_engine

AIRPORTS = np.array(['ATL', 'BOS', 'ORD', 'DFW', 'LAX', 'JFK', 'SFO', 'DEN', 'MIA', 'SEA', 'PHX', 'EWR'])
AIRLINES = np.array(['AA', 'DL', 'UA', 'WN', 'B6', 'AS'])

def generate(n=75000, seed=42):
    rng = np.random.default_rng(seed)
    dates = pd.Timestamp('2025-01-01') + pd.to_timedelta(rng.integers(0, 365, n), unit='D')
    origin = rng.choice(AIRPORTS, n)
    destination = rng.choice(AIRPORTS, n)
    destination = np.where(destination == origin, np.roll(destination, 1), destination)
    destination = np.where(destination == origin, 'ATL', destination)
    airline = rng.choice(AIRLINES, n)
    hour = rng.integers(5, 24, n)
    distance = rng.uniform(200, 2600, n).round(0)
    day_of_week = dates.dayofweek.to_numpy() + 1
    weekend = (day_of_week >= 6).astype(int)
    month = dates.month.to_numpy()
    elapsed = (45 + distance / 8.2 + rng.normal(0, 12, n)).clip(40).round(0)
    score = (-2.1 + 0.055 * (hour - 12)
             + 0.32 * np.isin(origin, ['ORD', 'EWR', 'JFK'])
             + 0.30 * np.isin(month, [6, 7, 8, 12])
             + 0.23 * np.isin(airline, ['B6', 'UA'])
             + 0.00017 * distance + 0.12 * weekend
             + 0.28 * np.sin(distance / 500))
    probability = 1 / (1 + np.exp(-score))
    delayed = rng.binomial(1, probability)
    return pd.DataFrame({
        'flight_date': dates.strftime('%Y-%m-%d'),
        'airline': airline, 'origin': origin, 'destination': destination,
        'month': month, 'day_of_week': day_of_week, 'departure_hour': hour,
        'distance': distance, 'is_weekend': weekend,
        'scheduled_elapsed_time': elapsed, 'arrival_delayed_15': delayed,
        'cancelled': np.zeros(n, dtype=int), 'diverted': np.zeros(n, dtype=int)
    })

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rows', type=int, default=75000)
    parser.add_argument('--output', default='data/synthetic_airline_ops.db')
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    df = generate(args.rows)
    df.to_sql('fact_flights', create_engine(f'sqlite:///{output.resolve()}'),
              if_exists='replace', index=False)
    print(f'SYNTHETIC DATA: {len(df)} flights; delay rate {df.arrival_delayed_15.mean():.3f}; saved {output}')

if __name__ == '__main__':
    main()
