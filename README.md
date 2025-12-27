 Project Overview

This project develops a real-time short-term electricity load forecasting system for the Texas power grid (ERCOT). The goal is to accurately predict next-2-hour electricity demand using deep learning models and deploy the solution as a live, continuously updating analytics pipeline.

Unlike traditional forecasting projects, this work goes beyond offline model evaluation by implementing a production-style architecture that connects live grid data, machine learning inference, APIs, and interactive dashboards.

 Problem Statement

Accurate short-term load forecasting is critical for grid reliability, cost control, and blackout prevention. Even small forecasting errors can lead to expensive emergency power purchases or system overloads. This project addresses that challenge by identifying the most effective RNN-based model for near-term forecasting and operational deployment.

Data Source (Real-Time + Historical)

ERCOT Electricity Load Data (2020–2025)

Hourly system-wide and regional load data

Live operational data retrieved using ERCOT / GridStatus APIs

Machine Learning Models

The following RNN architectures were implemented and compared:

Vanilla RNN

LSTM

Bidirectional LSTM

GRU

Each model was trained in:

Univariate mode (total ERCOT load only)

Multivariate mode (regional loads + time features)

Best Model:

Bidirectional LSTM (after hyperparameter tuning)

Achieved the lowest RMSE and MAPE for next-2-hour forecasts

 Model Pipeline

Sliding window: past 24 hours → predict next 2 hours

MinMax scaling (training-only fit)

Hyperparameter tuning using Optuna

Evaluation using RMSE, MAE, and MAPE

 Deployment Architecture

FastAPI backend:

Fetches live ERCOT data

Applies preprocessing + trained BiLSTM model

Generates real-time forecasts via API endpoints

Tableau Web Data Connector (WDC):

Pulls live actual + forecast data on refresh

Enables automated dashboard updates

 Visualization (Tableau Dashboard)

The Tableau dashboard provides:

Current ERCOT load

Next-hour forecast

Model accuracy (MAPE rating)

Actual vs forecast load trends

Average load by hour of day

The dashboard refreshes dynamically as new grid data arrives, enabling real-time monitoring and evaluation.

 Key Insights

Multivariate BiLSTM and GRU models performed best after tuning

Adding regional features significantly improved accuracy

Vanilla RNN underperformed for long temporal dependencies

A complete ML + API + BI pipeline is feasible for live grid operations

 Tech Stack

Python, TensorFlow / Keras

FastAPI

Optuna

Tableau

ERCOT / GridStatus APIs

 Impact

This project demonstrates how machine learning can support:

Grid operators (reliability & cost reduction)

Renewable energy planning

Smart grid & IoT systems

Real-world ML deployment workflows

 Live Dashboard:
https://public.tableau.com/views/Ercotenergydashboard/Dashboard1

##  Model Development

All model training, experimentation, and evaluation were conducted in a Colab notebook:

- `notebooks/ercot_load_forecasting_models.ipynb`

This notebook includes data preprocessing, feature engineering, model training, and performance evaluation used in the real-time forecasting pipeline.


