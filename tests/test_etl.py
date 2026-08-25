import pandas as pd
from src.etl import transform

def test_transform_keeps_multiple_airlines_and_builds_features():
    raw = pd.DataFrame({
        'FlightDate':['2026-06-01','2026-06-01'],
        'Reporting_Airline':['DL','UA'],
        'Flight_Number_Reporting_Airline':[1,2],
        'Origin':['BOS','EWR'],'OriginCityName':['Boston, MA','Newark, NJ'],'OriginState':['MA','NJ'],
        'Dest':['ATL','ORD'],'DestCityName':['Atlanta, GA','Chicago, IL'],'DestState':['GA','IL'],
        'CRSDepTime':[900,1300],'DepTime':[905,1310],'DepDelay':[5,10],
        'CRSArrTime':[1200,1500],'ArrTime':[1205,1520],'ArrDelay':[5,20],'ArrDel15':[0,1],
        'Cancelled':[0,0],'Diverted':[0,0],'Distance':[946,719],'DayOfWeek':[1,1]
    })
    out = transform(raw)
    assert set(out.airline) == {'DL','UA'}
    assert set(out.route) == {'BOS-ATL','EWR-ORD'}
    assert list(out.arrival_delayed_15) == [0,1]
