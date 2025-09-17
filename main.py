import config
import llms
import os
from langchain.agents import initialize_agent
from langgraph.graph import START , END , StateGraph
from agents import common_tools
from llms import init_llm





# 8) Example usage
if __name__ == "__main__":
    init_llm()


    graph = StateGraph(common_tools.AgentState)
    graph.add_node("planner", common_tools.planner_node)
    graph.add_node("executor", common_tools.executor_node)
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "executor")
    graph.add_edge("executor", END)
    app = graph.compile()
    initial = {"question": "Can you write biography of Indian prime minister Narendra Modi?"}
    final_state = app.invoke(initial)
    print("Plan (parsed):", final_state.get("plan"))
    print("Step results:", final_state.get("step_results"))
    print("Final answer:", final_state.get("final_answer"))





    
