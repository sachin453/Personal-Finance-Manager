# agents/ingestion_agent.py
import pandas as pd
from pathlib import Path

class IngestionAgent:
    def __init__(self, data_path):
        self.data_path = Path(data_path)

    def load_transactions(self):
        if not self.data_path.exists():
            raise FileNotFoundError(f"CSV not found: {self.data_path}")
        df = pd.read_csv(self.data_path)
        df['date'] = pd.to_datetime(df['date'])
        return df