from gridstatus.ercot import Ercot
import pandas as pd
import numpy as np
import datetime

ercot = Ercot()
try:
    df = ercot.get_load('latest')
    print('df rows:', len(df))
    df['Load'] = pd.to_numeric(df['Load'], errors='coerce')
    df['Time'] = pd.to_datetime(df['Time'], errors='coerce', utc=True)
    print('Time dtype:', df['Time'].dtype)
    df = df.dropna(subset=['Load','Time'])
    print('after dropna rows:', len(df))
    if len(df) < 50:
        print('FAILED: len < 50 ->', len(df))
    now_utc = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    cutoff = now_utc - datetime.timedelta(hours=24)
    df = df[df['Time'] >= cutoff]
    print('after cutoff rows:', len(df))
    df = df.set_index('Time')
    full_range = pd.date_range(start=cutoff, end=now_utc, freq='5min', tz='UTC')
    df = df.reindex(full_range)
    print('after reindex rows:', len(df))
    df['Load'] = df['Load'].interpolate(method='time')
    print('nans after interp:', df['Load'].isna().sum())
    df_hourly = df['Load'].resample('1H').mean()
    print('hourly len:', len(df_hourly))
    arr = df_hourly.tail(24).values.astype(float)
    print('arr min max:', np.min(arr), np.max(arr))
except Exception as e:
    print('Exception:', e)
