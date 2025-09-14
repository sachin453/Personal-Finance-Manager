import pandas as pd
from pathlib import Path
import os
import json
from agents import categorization_agent

# --------- CONFIGURATION ---------
CSV_FOLDER = "./data/"
PROCESSED_DATA_JSON = "./cache/processed_data.json"
PROCESSED_FILES_JSON = "./cache/processed_files.json"

class IngestionAgent:
    def __init__(self):
        self.CategorizationAgent = categorization_agent.CategorizationAgent()

    def load_transactions(self , data_path):
        if not Path(data_path).exists():
            raise FileNotFoundError(f"CSV not found: {data_path}")
        df = pd.read_csv(data_path)
        df['date'] = pd.to_datetime(df['date'])
        return df

    # --------- LOAD TRACKED FILES ---------
    def load_processed_files(self):
        if os.path.exists(PROCESSED_FILES_JSON):
            with open(PROCESSED_FILES_JSON, "r") as f:
                return set(json.load(f))
        return set()
    
    # --------- SAVE TRACKED FILES ---------
    def save_processed_files(self,processed_files):
        with open(PROCESSED_FILES_JSON, "w") as f:
            json.dump(list(processed_files), f, indent=2)

    # --------- LOAD EXISTING DATA ---------
    def load_existing_data(self):
        if os.path.exists(PROCESSED_DATA_JSON):
            with open(PROCESSED_DATA_JSON, "r") as f:
                return pd.DataFrame(json.load(f))
        return pd.DataFrame(columns=["date", "description", "amount", "category"])
    
    # --------- MAIN PROCESS ---------
    def process_expense_files(self):
        processed_files = self.load_processed_files()
        existing_data = self.load_existing_data()

        new_dataframes = []
        current_files = set()

        for filename in os.listdir(CSV_FOLDER):
            if filename.endswith(".csv"):
                filepath = os.path.join(CSV_FOLDER, filename)
                current_files.add(filename)

                if filename not in processed_files:
                    print(f"Processing new file: {filename}")
                    df = pd.read_csv(filepath)

                    # Ensure correct columns
                    df.columns = [col.strip().lower() for col in df.columns]
                    if not {"date", "description", "amount"}.issubset(df.columns):
                        raise ValueError(f"File {filename} does not have required columns!")

                    # Add category column
                    df["category"] = df["description"].apply(self.CategorizationAgent.classify_transaction)

                    new_dataframes.append(df)
                    processed_files.add(filename)
                else:
                    print(f"Skipping already processed file: {filename}")

        # Combine all data
        if new_dataframes:
            combined_new_data = pd.concat(new_dataframes, ignore_index=True)
            final_data = pd.concat([existing_data, combined_new_data], ignore_index=True)
        else:
            final_data = existing_data

        # Save final data to JSON
        final_data.to_json(PROCESSED_DATA_JSON, orient="records", indent=2)

        # Save updated processed files
        self.save_processed_files(processed_files)

        print(f"Processed data JSON updated at {PROCESSED_DATA_JSON}")
        print(f"Tracked processed files at {PROCESSED_FILES_JSON}")