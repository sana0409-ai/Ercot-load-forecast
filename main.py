import os
import numpy as np
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from gridstatus.ercot import Ercot
import joblib
import tensorflow as tf
from fastapi.responses import Response
import datetime
import uvicorn

app = FastAPI(
    title="ERCOT Load Forecast API",
    description="Real-time ERCOT forecast using BiLSTM + GridStatus",
)

# Allow Tableau (and other local tools) to request data from this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------
# LOAD MODEL + SCALER
# -------------------------------------
model = tf.keras.models.load_model("bilstm_univariate.h5", compile=False)
scaler = joblib.load("scaler_univariate.pkl")

FALLBACK_CSV = "last_known_load.csv"
scheduler = BackgroundScheduler()


# -------------------------------------
# CLEAN FLOATS
# -------------------------------------
def clean_array(arr):
    arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
    return arr.astype(float)


# -------------------------------------
# FETCH LAST 24 HOURS USING LATEST ENDPOINT
# -------------------------------------
def fetch_ercot_last24():
    ercot = Ercot()

    # 1) Get latest 5-minute load data (most stable endpoint)
    try:
        df = ercot.get_load("latest")
    except Exception as e:
        raise Exception(f"ERCOT latest fetch failed: {e}")

    if df is None or len(df) == 0:
        raise Exception("ERCOT returned EMPTY dataframe")

    # Convert fields
    df["Load"] = pd.to_numeric(df["Load"], errors="coerce")
    # Parse Time and force UTC to avoid tz-naive vs tz-aware comparison issues
    df["Time"] = pd.to_datetime(df["Time"], errors="coerce", utc=True)
    df = df.dropna(subset=["Load", "Time"])

    # Floor incoming timestamps to the 5-minute grid so they align with our reindex range
    df["Time"] = df["Time"].dt.floor("5min")

    # Aggregate any duplicate timestamps (take mean of Load) to ensure unique index
    df = df.groupby("Time", as_index=False).agg({"Load": "mean"})

    if len(df) < 50:
        print("[WARN] ERCOT returned fewer than 50 rows","rows=", len(df))
        print(df.head(5).to_string())
        raise Exception("Not enough valid ERCOT rows")

    # 2) Determine last 24 hours (aligned to 5-minute boundaries)
    now_utc = pd.Timestamp.now(tz='UTC')
    cutoff = now_utc - pd.Timedelta(hours=24)

    # Align cutoff and now to 5-minute grid so reindex matches the series timestamps
    cutoff_aligned = cutoff.floor('5min')
    now_aligned = now_utc.floor('5min')

    df = df[df["Time"] >= cutoff_aligned]

    if len(df) < 20:
        print("[WARN] After filtering to last-24h, too few rows","rows=", len(df))
        print(df.head(5).to_string())
        raise Exception("Latest endpoint missing too much data")

    # 3) Align measured timestamps to the 5-minute grid robustly
    # Build full 5-minute target range
    full_range = pd.date_range(start=cutoff_aligned, end=now_aligned, freq="5min", tz="UTC")

    # Create a Series from measured loads
    s = pd.Series(df["Load"].values, index=df["Time"]).sort_index()

    # Snap each target grid point to the nearest measured value within a tolerance
    # This avoids full-NaN reindexes when source timestamps have small offsets
    s_snapped = s.reindex(full_range, method="nearest", tolerance=pd.Timedelta("2min30s"))

    # Interpolate any remaining short gaps
    s_filled = s_snapped.interpolate(method="time")

    # Fill any remaining leading/trailing NaNs by forward/backward fill
    s_filled = s_filled.fillna(method="ffill").fillna(method="bfill")

    df = s_filled.to_frame(name="Load")

    if df["Load"].isna().sum() > 0:
        print("[WARN] Interpolation left NaNs:", df["Load"].isna().sum())
        raise Exception("Interpolation failed")

    # 4) Convert to hourly means
    df_hourly = df["Load"].resample("1H").mean()

    if len(df_hourly) < 24:
        print("[WARN] Hourly resample produced <24 points:", len(df_hourly))
        print(df_hourly.head(5).to_string())
        raise Exception("Not enough hourly points")

    arr = df_hourly.tail(24).values.astype(float)

    # 5) Reject bad data
    if np.all(arr == 0) or np.max(arr) < 1000:
        print("[WARN] ERCOT hourly array invalid. min,max:", np.min(arr), np.max(arr))
        raise Exception("Invalid ERCOT load (zeros or nonsense)")

    return clean_array(arr)


# -------------------------------------
# FALLBACK LOADER
# -------------------------------------
def load_fallback_last24():
    if not os.path.exists(FALLBACK_CSV):
        print("[WARN] Creating first fallback file...")
        dummy = np.ones(24) * 50000
        pd.DataFrame({"ercot": dummy}).to_csv(FALLBACK_CSV, index=False)

    df = pd.read_csv(FALLBACK_CSV)
    vals = df["ercot"].astype(float).values[-24:]

    # If the fallback file contains invalid values (all zeros or unrealistically low),
    # attempt a one-time refresh from ERCOT before falling back to a safe default.
    if np.all(vals == 0) or np.max(vals) < 1000:
        try:
            print("[WARN] Fallback appears invalid — attempting one-time refresh from ERCOT...")
            refresh_fallback_job()
            df = pd.read_csv(FALLBACK_CSV)
            vals = df["ercot"].astype(float).values[-24:]
        except Exception as e:
            print("[WARN] One-time refresh failed:", e)

    # Final safety: if values are still invalid, replace with a safe default and persist it.
    if np.all(vals == 0) or np.max(vals) < 1000:
        print("[WARN] Final fallback invalid — writing safe default values.")
        vals = np.ones(24) * 50000
        pd.DataFrame({"ercot": vals}).to_csv(FALLBACK_CSV, index=False)

    return clean_array(vals)


# -------------------------------------
# FORECAST
# -------------------------------------
def forecast_from_last24(last24):
    last24 = clean_array(last24)

    scaled = scaler.transform(last24.reshape(-1, 1))
    x = scaled.reshape(1, 24, 1)

    pred = model.predict(x)[0]
    pred = scaler.inverse_transform(pred.reshape(-1, 1)).flatten()

    return clean_array(pred)


# -------------------------------------
# REFRESH FALLBACK JOB
# -------------------------------------
def refresh_fallback_job():
    try:
        print("[INFO] Updating fallback CSV...")
        last24 = fetch_ercot_last24()
        pd.DataFrame({"ercot": last24}).to_csv(FALLBACK_CSV, index=False)
        print("[INFO] Updated fallback CSV.")
    except Exception as e:
        print("[WARN] Could not refresh fallback CSV:", e)


# -------------------------------------
# STARTUP / SHUTDOWN
# -------------------------------------
@app.on_event("startup")
def on_startup():
    scheduler.add_job(refresh_fallback_job, "interval", minutes=10)
    scheduler.start()
    print("[INFO] Scheduler started.")


@app.on_event("shutdown")
def on_shutdown():
    scheduler.shutdown()
    print("[INFO] Scheduler stopped.")


# -------------------------------------
# FORECAST ENDPOINT
# -------------------------------------
@app.get("/forecast_realtime")
def forecast_realtime():
    try:
        last24 = fetch_ercot_last24()
        source = "live"

        # Save fresh fallback
        pd.DataFrame({"ercot": last24}).to_csv(FALLBACK_CSV, index=False)

    except Exception as e:
        print("[WARN] Live fetch failed -> using fallback:", e)
        last24 = load_fallback_last24()
        source = "fallback"

    pred = forecast_from_last24(last24)

    return {
        "status": "success",
        "source": source,
        "last_24_values": last24.tolist(),
        "forecast_MW": pred.tolist(),
    }


# -------------------------------------
# TEST ENDPOINT
# -------------------------------------
@app.get("/ercot_test")
def ercot_test():
    ercot = Ercot()
    df = ercot.get_load("latest")
    df["Load"] = pd.to_numeric(df["Load"], errors="coerce")
    return df.tail(10).to_dict(orient="records")


# -------------------------------------
# TABLEAU FEED
# -------------------------------------
@app.get("/tableau_feed")
def tableau_feed():
    try:
        last24 = fetch_ercot_last24()
    except:
        last24 = load_fallback_last24()

    pred = forecast_from_last24(last24)

    now = datetime.datetime.utcnow()

    df_actual = pd.DataFrame({
        "timestamp": [(now - datetime.timedelta(hours=24 - i)).isoformat() for i in range(24)],
        "value": last24,
        "type": "actual"
    })

    df_pred = pd.DataFrame({
        "timestamp": [(now + datetime.timedelta(hours=i+1)).isoformat() for i in range(len(pred))],
        "value": pred,
        "type": "forecast"
    })

    df_out = pd.concat([df_actual, df_pred], ignore_index=True)
    return Response(df_out.to_csv(index=False), media_type="text/csv")


# -------------------------------------
# TABLEAU WDC + JSON DATA ENDPOINT
# -------------------------------------
@app.get("/wdc")
def wdc_page():
    # Serve the local WDC HTML file used by Tableau (if present)
    path = "tableau_wdc.html"
    if os.path.exists(path):
        return FileResponse(path, media_type="text/html")
    return JSONResponse({"error": "wdc file not found"}, status_code=404)


@app.get("/tableau_data")
def tableau_data():
    # Return JSON list of records containing actuals (last 24) and forecasts
    try:
        last24 = fetch_ercot_last24()
        source = "live"
    except Exception:
        last24 = load_fallback_last24()
        source = "fallback"

    pred = forecast_from_last24(last24)

    now = datetime.datetime.utcnow()

    actual_rows = []
    for i in range(24):
        ts = (now - datetime.timedelta(hours=24 - i)).isoformat()
        actual_rows.append({"timestamp": ts, "value": float(last24[i]), "type": "actual"})

    pred_rows = []
    for i in range(len(pred)):
        ts = (now + datetime.timedelta(hours=i + 1)).isoformat()
        pred_rows.append({"timestamp": ts, "value": float(pred[i]), "type": "forecast"})

    out = actual_rows + pred_rows
    return JSONResponse(out)


# -------------------------------------
# MAIN
# -------------------------------------
if __name__ == "__main__":
    # Allow runtime configuration via environment variables so the
    # helper scripts or container orchestration can choose host/port.
    port = int(os.getenv("PORT", "8001"))
    host = os.getenv("HOST", "0.0.0.0")
    reload_flag = os.getenv("DEV_RELOAD", "false").lower() in ("1", "true", "yes")

    print(f"[INFO] Starting uvicorn on http://{host}:{port} (reload={reload_flag})")
    uvicorn.run(app, host=host, port=port, reload=reload_flag)
