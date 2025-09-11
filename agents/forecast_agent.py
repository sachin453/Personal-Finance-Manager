# agents/forecast_agent.py
from prophet import Prophet
import pandas as pd

class ForecastAgent:
    def __init__(self):
        self.model = Prophet()

    def train(self, df):
        # Prepare data for Prophet
        forecast_df = df.groupby('date')['amount'].sum().reset_index()
        forecast_df.columns = ['ds', 'y']
        self.model.fit(forecast_df)

    def predict_future(self, days=30):
        future = self.model.make_future_dataframe(periods=days)
        forecast = self.model.predict(future)
        return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
