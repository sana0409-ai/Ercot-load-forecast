Real-Time ERCOT Load Forecasting Dashboard
 Problem Statement

Accurate short-term electricity load forecasting is critical for grid reliability and operational planning. Traditional dashboards often rely on static or delayed data, limiting their usefulness for real-time decision-making. This project addresses the need for near real-time load monitoring and forecast evaluation using live grid data.

 Real-Time Data Source

The system ingests live electricity demand data from the ERCOT Grid Status API via the GridStatus Python library. This ensures access to up-to-date operational load values published by ERCOT, reflecting current grid conditions.

 Machine Learning Model

A time-series forecasting model is used to generate next-hour load predictions based on the most recent 24 hours of observed demand. The model is trained offline and applied in real time for inference, enabling continuous forecast updates as new data arrives.

 FastAPI Backend

A FastAPI service acts as the real-time inference and data-serving layer. It:

Fetches the latest ERCOT load data

Preprocesses and aggregates data to an hourly level

Runs the forecasting model

Exposes actual and forecasted load values through REST endpoints

These endpoints are designed for direct consumption by analytics and visualization tools.

 Tableau Visualization Layer

An interactive Tableau dashboard serves as the frontend for the system. It visualizes:

Actual vs forecasted load over time

Current system load

Next-hour forecast

Forecast accuracy using MAPE and qualitative ratings

Tableau consumes data from the FastAPI endpoints through a Web Data Connector (WDC).

Auto-Refresh Behavior

The dashboard updates dynamically whenever the data source is refreshed. Each refresh triggers a new API call to the FastAPI backend, which retrieves fresh ERCOT data and generates updated forecasts. This enables near real-time monitoring, with refresh frequency controlled by the user or scheduling environment.
