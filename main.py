import config
import llms
import os

from agents import ingestion_agent
from agents import categorization_agent
from agents import forecast_agent
from agents import decision_agent
from agents import google_search_agents


import requests



def __main__():
    # IngestionAgent = ingestion_agent.IngestionAgent()
    # IngestionAgent.process_expense_files()
    temp = google_search_agents.GoogleSearchAgent()
    xx = temp.answer_from_search_with_gemini("Is Babar Azam playing Asia Cup T20 2025?")
    print(xx)

    # llm = llms.qwen()
    # llm.generate_response("Who is Virat Kohli?")


# run the main function
if __name__ == "__main__":
    __main__()
    
