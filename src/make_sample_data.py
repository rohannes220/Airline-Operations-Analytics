"""Create BTS-shaped sample data so the full project can run without a large download."""
import numpy as np
import pandas as pd
from src.config import RAW_DIR

def make(n=5000, seed=42):
    rng=np.random.default_rng(seed)
    airports=np.array(['ATL','BOS','JFK','LGA','DTW','MSP','SLC','SEA','LAX','MCO'])
    dates=pd.date_range('2025-01-01','2025-03-31')
    origin=rng.choice(airports,n); dest=rng.choice(airports,n)
    same=origin==dest
    while same.any(): dest[same]=rng.choice(airports,same.sum()); same=origin==dest
    sched_dep=rng.integers(5,23,n)*100+rng.choice([0,15,30,45],n)
    distance=rng.integers(200,2600,n)
    dep_delay=np.maximum(-15, rng.normal(8,25,n))
    weather=(rng.random(n)<.05)*rng.gamma(2,12,n)
    late=(rng.random(n)<.15)*rng.gamma(2,15,n)
    nas=(rng.random(n)<.12)*rng.gamma(2,10,n)
    carrier=(rng.random(n)<.10)*rng.gamma(2,9,n)
    security=(rng.random(n)<.003)*rng.gamma(2,5,n)
    arr_delay=dep_delay*.65+weather+late+nas+carrier+security+rng.normal(-4,12,n)
    cancelled=(rng.random(n)<.015).astype(int); diverted=(rng.random(n)<.003).astype(int)
    flight_date=rng.choice(dates,n)
    df=pd.DataFrame({
      'FlightDate':flight_date,'Reporting_Airline':rng.choice(np.array(['AA','AS','B6','DL','F9','G4','HA','NK','UA','WN','OO','YX','9E','OH']), n),'Flight_Number_Reporting_Airline':rng.integers(100,2999,n),
      'Origin':origin,'OriginCityName':origin+' City','OriginState':'NA','Dest':dest,'DestCityName':dest+' City','DestState':'NA',
      'CRSDepTime':sched_dep,'DepTime':sched_dep+dep_delay,'DepDelay':dep_delay,'CRSArrTime':(sched_dep+200)%2400,
      'ArrTime':(sched_dep+200+arr_delay)%2400,'ArrDelay':arr_delay,'ArrDel15':(arr_delay>=15).astype(int),
      'Cancelled':cancelled,'CancellationCode':np.where(cancelled==1,'B',None),'Diverted':diverted,
      'CRSElapsedTime':distance/7+45,'ActualElapsedTime':distance/7+45+arr_delay-dep_delay,'AirTime':distance/7,
      'Distance':distance,'CarrierDelay':carrier,'WeatherDelay':weather,'NASDelay':nas,'SecurityDelay':security,
      'LateAircraftDelay':late,'TaxiOut':rng.normal(18,5,n),'TaxiIn':rng.normal(8,3,n),
      'DayOfWeek':pd.to_datetime(flight_date).dayofweek+1})
    RAW_DIR.mkdir(parents=True,exist_ok=True)
    path=RAW_DIR/'sample_bts_all_airlines.csv'; df.to_csv(path,index=False); print(path)
if __name__=='__main__': make()
