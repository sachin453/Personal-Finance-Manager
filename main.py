import config
import llms
import os
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType

from agents import ingestion_agent
from agents import categorization_agent
from agents import forecast_agent
from agents import decision_agent
from agents import google_search_agents



class brain:
    def __init__(self):
        self.GoogleSearchAgent = google_search_agents.GoogleSearchAgent()
        self.LLMAgent = llms.qwen()
        self.llm = llms.CustomLLM()
        self.tools = [
            Tool(
                name="Google Search",
                func=self.GoogleSearchAgent.answer_from_search_with_gemini,
                description="Useful for when you need to answer questions about future events. Input should be a fully formed question."
            ),
            Tool(
                name="LLM",
                func=self.LLMAgent.generate_response_with_params,
                description="Useful for when you need to answer questions or generate text. Input should be a fully formed question or prompt."
            )
        ]
        self.agent = initialize_agent(
            self.tools,
            self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True,
            agent_kwargs={
                "prefix": (
                    "You are an AI assistant that strictly follows the ReAct format.\n"
                    "When you need to use a tool, always respond with:\n"
                    "Action: <tool name>\n"
                    "Action Input: <input for the tool>\n\n"
                    "When you have the final answer, respond only with:\n"
                    "Final Answer: <your final answer>\n\n"
                    "Do NOT mix Final Answer with Action in the same step."
                )
            }
        )

    def answer(self, question: str) -> str:
        return self.agent.run(question)
        # return self.GoogleSearchAgent.answer_from_search_with_gemini(question)

    



temp = brain()
print(temp.answer("What is today's date?"))

    
