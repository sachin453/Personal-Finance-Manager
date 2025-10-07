from langchain.chat_models import init_chat_model
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

import requests , os
from dotenv import load_dotenv
load_dotenv()


memory = MemorySaver()
class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]

from agents.common_tools import tools

llm = init_chat_model("google_genai:gemini-2.0-flash", temperature=0)
llm_with_tools = llm.bind_tools(tools)


def chatbot(state: State) -> State:
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

builder = StateGraph(State)

builder.add_node("chatbot", chatbot)
builder.add_node("tools", ToolNode(tools=tools))

builder.add_edge(START, "chatbot")
builder.add_conditional_edges("chatbot" , tools_condition)
builder.add_edge("tools", "chatbot")
# builder.add_edge("chatbot", "chatbot")

builder.add_edge("chatbot", END)


graph = builder.compile(checkpointer=memory)

from IPython.display import Image, display

# display(Image(graph.get_graph().draw_mermaid_png()))

config = { 'configurable': { 'thread_id' : '1'} }


state = graph.invoke({"messages": [{"role": "user", "content": "Who won mens aisa cup cricket 2025?"}]} , config=config)
print(state["messages"][-1].content)

state = graph.invoke({"messages": [{"role": "user", "content": "And What is Rohit Sharma's?"}]} , config=config)
print(state["messages"][-1].content)

print("Chat history:")
print(state)