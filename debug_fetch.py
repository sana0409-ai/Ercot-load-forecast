from gridstatus.ercot import Ercot
import pandas as pd
import numpy as np
import datetime

ercot = Ercot()
try:
    df = ercot.get_load('latest')
    print('initial rows:', len(df))
    print(df.head(5).to_string())
    df['Load'] = pd.to_numeric(df['Load'], errors='coerce')
    df['Time'] = pd.to_datetime(df['Time'], errors='coerce', utc=True)
    print('\nAfter parsing Time and Load types:')
    print(df.head(5).to_string())
    print('Time dtype:', df['Time'].dtype)
    print('Load nulls before dropna:', df['Load'].isna().sum())
    df = df.dropna(subset=['Load','Time'])
    print('after dropna rows:', len(df))
    print(df.head(5).to_string())
    now_utc = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    cutoff = now_utc - datetime.timedelta(hours=24)
    df_recent = df[df['Time'] >= cutoff]
    print('\nafter cutoff rows:', len(df_recent))
    print(df_recent.head(5).to_string())
    df_set = df_recent.set_index('Time')
    print('\nIndex tzinfo:', df_set.index.tz)
    print('non-null Load before reindex:', df_set['Load'].notna().sum())
    full_range = pd.date_range(start=cutoff, end=now_utc, freq='5min', tz='UTC')
    df_re = df_set.reindex(full_range)
    print('\nafter reindex rows:', len(df_re))
    print('non-null Load after reindex:', df_re['Load'].notna().sum())
    print('sample after reindex:')
    print(df_re.head(20).to_string())
    df_re['Load'] = df_re['Load'].interpolate(method='time')
    print('\nAfter interpolation non-nulls:', df_re['Load'].notna().sum())
    df_hourly = df_re['Load'].resample('1H').mean()
    print('\nHourly len:', len(df_hourly))
    print(df_hourly.to_string())
except Exception as e:
    print('Exception:', e)
