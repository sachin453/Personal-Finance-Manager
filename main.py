import config
import llms
import os

from agents import ingestion_agent
from agents import categorization_agent
from agents import forecast_agent
from agents import decision_agent




def __main__():
    IngestionAgent = ingestion_agent.IngestionAgent()
    IngestionAgent.process_expense_files()


## run the main function
if __name__ == "__main__":
    __main__()
        