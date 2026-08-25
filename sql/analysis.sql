-- 1) Portfolio KPIs
SELECT COUNT(*) AS flights,
       ROUND(100.0 * AVG(on_time), 2) AS on_time_pct,
       ROUND(AVG(arrival_delay), 2) AS avg_arrival_delay,
       ROUND(100.0 * AVG(cancelled), 2) AS cancellation_pct
FROM fact_flights;

-- 2) Carrier benchmark
SELECT airline, COUNT(*) AS flights,
       ROUND(100.0 * AVG(on_time), 2) AS on_time_pct,
       ROUND(AVG(arrival_delay), 2) AS avg_arrival_delay,
       ROUND(100.0 * AVG(cancelled), 2) AS cancellation_pct
FROM fact_flights
GROUP BY airline
HAVING COUNT(*) >= 100
ORDER BY on_time_pct DESC;

-- 3) Monthly airline ranking using CTE + window function
WITH carrier_month AS (
  SELECT month, airline, COUNT(*) AS flights,
         100.0 * AVG(on_time) AS on_time_pct
  FROM fact_flights
  GROUP BY month, airline
  HAVING COUNT(*) >= 50
), ranked AS (
  SELECT *, RANK() OVER (PARTITION BY month ORDER BY on_time_pct DESC) AS on_time_rank
  FROM carrier_month
)
SELECT month, airline, flights, ROUND(on_time_pct, 2) AS on_time_pct, on_time_rank
FROM ranked
ORDER BY month, on_time_rank;

-- 4) Worst origin airports with meaningful volume
SELECT origin, COUNT(*) AS flights,
       ROUND(AVG(arrival_delay), 2) AS avg_arrival_delay,
       ROUND(100.0 * AVG(on_time), 2) AS on_time_pct
FROM fact_flights
WHERE cancelled = 0
GROUP BY origin
HAVING COUNT(*) >= 200
ORDER BY avg_arrival_delay DESC
LIMIT 15;

-- 5) Route performance
SELECT route, COUNT(*) AS flights,
       ROUND(AVG(arrival_delay), 2) AS avg_arrival_delay,
       ROUND(100.0 * AVG(on_time), 2) AS on_time_pct
FROM fact_flights
WHERE cancelled = 0
GROUP BY route
HAVING COUNT(*) >= 50
ORDER BY avg_arrival_delay DESC
LIMIT 20;

-- 6) Departure-hour pattern
SELECT departure_hour, COUNT(*) AS flights,
       ROUND(AVG(arrival_delay), 2) AS avg_arrival_delay,
       ROUND(100.0 * AVG(on_time), 2) AS on_time_pct
FROM fact_flights
WHERE cancelled = 0
GROUP BY departure_hour
ORDER BY departure_hour;

-- 7) Delay-cause minutes by airline
SELECT airline,
       ROUND(SUM(carrier_delay),0) AS carrier_minutes,
       ROUND(SUM(weather_delay),0) AS weather_minutes,
       ROUND(SUM(nas_delay),0) AS nas_minutes,
       ROUND(SUM(security_delay),0) AS security_minutes,
       ROUND(SUM(late_aircraft_delay),0) AS late_aircraft_minutes
FROM fact_flights
GROUP BY airline
ORDER BY (SUM(carrier_delay)+SUM(weather_delay)+SUM(nas_delay)+SUM(security_delay)+SUM(late_aircraft_delay)) DESC;
