-- Logical warehouse schema. ETL creates equivalent tables automatically.
CREATE TABLE dim_airline (
  airline VARCHAR(10) PRIMARY KEY
);
CREATE TABLE dim_airport (
  airport_code VARCHAR(3) PRIMARY KEY,
  city VARCHAR(100), state VARCHAR(2)
);
CREATE TABLE dim_date (
  flight_date DATE PRIMARY KEY,
  year INT, month INT, month_name VARCHAR(12), day INT,
  day_of_week INT, day_name VARCHAR(12), is_weekend INT
);
CREATE TABLE dim_route (
  route VARCHAR(7) PRIMARY KEY,
  origin VARCHAR(3), destination VARCHAR(3), distance NUMERIC
);
-- fact_flights is generated from BTS fields by src/etl.py.
