from langchain.chat_models import init_chat_model
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
import os


class State(TypedDict):
    messages: Annotated[list, add_messages]

SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are a personal finance assistant with access to tools that can read PDFs and summarize data. "
        "If the user asks about transactions, money received, or summaries from account statements, "
        "you should use the tools like `get_data_dir_files_tool`, `pdf_parser_tool`, and `local_llm_tool` "
        "to extract and analyze data from the files. "
        "If a question does not require file or data access, respond directly."
        "You have to use the tools aggressively to find the relevant information."
    )
}


class ChatbotAgent:
    def __init__(self, name:str , tools:list):
        self.name = name
        self.llm = init_chat_model("google_genai:gemini-2.0-flash", temperature=0)
        self.llm_with_tools = self.llm.bind_tools(tools)
        self.tools = tools

        self.init_bot("default_user")

        ### dialogue state
        self.dialogue_state = None

    def init_bot(self , username:str):
        self.connect_nodes()
        self.dialogue_config = { 'configurable': { 'thread_id' : username} }
        self.dialogue_state = None

    def connect_nodes(self):
        self._pg_context = PostgresSaver.from_conn_string(os.getenv("DATABASE_URL"))
        self._pg_store = PostgresStore.from_conn_string(os.getenv("DATABASE_URL"))

        self.checkpointer = self._pg_context.__enter__()
        self.store = self._pg_store.__enter__()

        self.checkpointer.setup()
        self.store.setup()

        self.builder = StateGraph(State)
        self.builder.add_node("chatbot", self.chatbot)
        self.builder.add_node("tools", ToolNode(tools=self.tools))
        self.builder.add_edge(START, "chatbot")
        self.builder.add_conditional_edges("chatbot" , tools_condition)
        self.builder.add_edge("tools", "chatbot")
        self.builder.add_edge("chatbot", END)
        self.graph = self.builder.compile(checkpointer=self.checkpointer , store=self.store)


    def chatbot(self , state: State) -> State:
        return {"messages": [self.llm_with_tools.invoke(state["messages"])]}
    

    def dialogue(self, query:str) -> str:
        user_message = {"role": "user", "content": query}
        if self.dialogue_state is None:
            self.dialogue_state = self.graph.invoke(
                {"messages": [SYSTEM_PROMPT, user_message]},
                config=self.dialogue_config
            )
            return self.dialogue_state["messages"][-1].content
        else:
            self.dialogue_state = self.graph.invoke(
                {"messages": self.dialogue_state["messages"] + [user_message]},
                config=self.dialogue_config
            )
            return self.dialogue_state["messages"][-1].content
