import pandas as pd
import streamlit as st
import plotly.express as px
from sqlalchemy import create_engine
from src.config import DATABASE_URL

st.set_page_config(page_title='U.S. Airline Operations Analytics', layout='wide')
st.title('U.S. Airline Operations Analytics')
engine = create_engine(DATABASE_URL)
df = pd.read_sql('SELECT * FROM fact_flights', engine)
df['flight_date'] = pd.to_datetime(df['flight_date'])

carriers = sorted(df['airline'].dropna().unique())
selected = st.sidebar.multiselect('Airlines', carriers, default=carriers)
view = df[df['airline'].isin(selected)] if selected else df.iloc[0:0]

c1,c2,c3,c4 = st.columns(4)
c1.metric('Flights', f'{len(view):,}')
c2.metric('On-time %', f"{100*view['on_time'].mean():.1f}%" if len(view) else '—')
c3.metric('Avg arrival delay', f"{view['arrival_delay'].mean():.1f} min" if len(view) else '—')
c4.metric('Cancellation %', f"{100*view['cancelled'].mean():.1f}%" if len(view) else '—')

carrier = view.groupby('airline', as_index=False).agg(flights=('airline','size'), on_time_pct=('on_time','mean'), avg_delay=('arrival_delay','mean'))
carrier['on_time_pct'] *= 100
st.plotly_chart(px.bar(carrier.sort_values('on_time_pct', ascending=False), x='airline', y='on_time_pct', hover_data=['flights','avg_delay'], title='On-time Performance by Airline'), use_container_width=True)

hourly = view[view.cancelled.eq(0)].groupby('departure_hour', as_index=False).arrival_delay.mean()
st.plotly_chart(px.line(hourly, x='departure_hour', y='arrival_delay', markers=True, title='Average Arrival Delay by Scheduled Departure Hour'), use_container_width=True)

airport = view[view.cancelled.eq(0)].groupby('origin').agg(flights=('origin','size'), avg_delay=('arrival_delay','mean')).reset_index()
airport = airport[airport.flights >= 100].nlargest(15, 'avg_delay')
st.plotly_chart(px.bar(airport, x='origin', y='avg_delay', hover_data=['flights'], title='Highest-delay Origin Airports'), use_container_width=True)

routes = view[view.cancelled.eq(0)].groupby('route').agg(flights=('route','size'), avg_delay=('arrival_delay','mean'), on_time_pct=('on_time','mean')).reset_index()
routes['on_time_pct'] *= 100
st.dataframe(routes[routes.flights >= 25].sort_values('avg_delay', ascending=False).head(25), use_container_width=True)
