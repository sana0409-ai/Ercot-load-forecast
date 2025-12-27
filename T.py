from fastapi import FastAPI, Response
import datetime
import pandas as pd 
from apscheduler.schedulers.background import BackgroundScheduler
import uvicorn

app = FastAPI()
# read_csv function to read the CSV file
def read_csv(file_path):
    df = pd.read_csv(file_path)
    return df
def tableau_feed():
    # Read the last known load data from CSV
    df = pd.read_csv("last_known_load.csv")
    return df.to_dict(orient="records")

@app.get("/tableau_feed")
def get_tableau_feed():
    return tableau_feed()

if __name__ == "__main__":
    # print("Starting FastAPI server...")
    df = read_csv("last_known_load.csv")
    print(df.head())
# feed df to tableau_feed data source tableau_tj.twb



    # uvicorn.run(app, host="0.0.0.0", port=8000)

