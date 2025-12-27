from gridstatus.ercot import Ercot
import pandas as pd
import numpy as np
import datetime

ercot = Ercot()
try:
    df = ercot.get_load('latest')
    df['Load'] = pd.to_numeric(df['Load'], errors='coerce')
    df['Time'] = pd.to_datetime(df['Time'], errors='coerce', utc=True)
    df = df.dropna(subset=['Load','Time'])
    df['Time'] = df['Time'].dt.floor('5min')
    df = df.groupby('Time', as_index=False).agg({'Load':'mean'})
    print('after groupby rows:', len(df))
    now_utc = pd.Timestamp.now(tz='UTC')
    cutoff = now_utc - pd.Timedelta(hours=24)
    cutoff_aligned = cutoff.floor('5min')
    now_aligned = now_utc.floor('5min')
    full_range = pd.date_range(start=cutoff_aligned, end=now_aligned, freq='5min', tz='UTC')
    s = pd.Series(df['Load'].values, index=df['Time']).sort_index()
    print('s index sample:', s.index[:5])
    s_snapped = s.reindex(full_range, method='nearest', tolerance=pd.Timedelta('2min30s'))
    print('snapped non-null:', s_snapped.notna().sum())
    s_filled = s_snapped.interpolate(method='time')
    print('filled non-null:', s_filled.notna().sum())
    hourly = s_filled.resample('1H').mean()
    print('hourly len, non-null count:', len(hourly), hourly.notna().sum())
    print('hourly sample:', hourly.head(10).to_string())
except Exception as e:
    print('Exception:', e)
