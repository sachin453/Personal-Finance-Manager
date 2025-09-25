from datetime import datetime
from typing import TypedDict , Optional, List, Dict, Any , Annotated
import re
import json
from agents import google_search_agents
import llms
from llms import init_llm
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    question: str
    plan: List[Dict[str, Any]]
    plan_raw: str
    plan_parse_error: str
    step_results: List[Dict[str, Any]]
    final_answer: str
    retries: int
    failed: bool
    failed_step: Optional[int]
    messages:Annotated[List , add_messages]

def parse_json_from_text(text: str):
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        # try to find first [...] or {...}
        m = re.search(r'(\[.*\])', text, re.S)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass
        m2 = re.search(r'(\{.*\})', text, re.S)
        if m2:
            try:
                return json.loads(m2.group(1))
            except Exception:
                pass
    raise ValueError("Could not parse JSON from LLM output")





def planner_node(state: AgentState) -> AgentState:
    question = state.get("question", "")
    planner_prompt = (
        "You are a strict planner AI.\n"
        "Given the user's QUESTION, return ONLY a JSON array of ordered steps.\n"
        "You have access to the following tools:\n"
        "- Date: returns today's date.\n"
        "- Calculator: evaluates math expressions safely\n"
        "- LLM: answers general knowledge questions\n"
        "- Google Search: Use it for getting information about future events.\n"
        "Each step must be an object with exactly two fields:\n"
        '  "action": one of ["Date", "Calculator", "LLM", "Google Search"]\n'
        '  "input": string to pass to that tool\n\n'
        "STRICT RULES:\n"
        "- Do NOT include any text before or after the JSON.\n"
        "- No explanations, no reasoning, no commentary.\n"
        "- Output must start with [ and end with ].\n\n"
        "Example:\n"
        '[{"action": "Date", "input": "today"}, {"action": "Google Search", "input": "latest cricket news"}]\n\n'
        f"QUESTION: {question}\n"
    )
    planner_llm = init_llm()
    resp_text = planner_llm.generate_response_with_params(planner_prompt)
    cleaned = re.sub(r"<think>.*?</think>", "", resp_text, flags=re.S).strip()
    state["plan_raw"] = cleaned
    try:
        plan = parse_json_from_text(resp_text)
        if not isinstance(plan, list):
            raise ValueError("Planner JSON is not a list")
        # basic validation: each step must contain action+input
        sanitized = []
        for step in plan:
            if not isinstance(step, dict) or "action" not in step or "input" not in step:
                raise ValueError("Planner returned invalid step: " + str(step))
            sanitized.append({"action": step["action"].strip(), "input": str(step["input"]).strip()})
        state["plan"] = sanitized
    except Exception as e:
        state["plan_parse_error"] = str(e)
        state["plan"] = []
    return state











def executor_node(state: AgentState) -> AgentState:
    plan = state.get("plan", []) or []
    step_results: List[Dict[str, Any]] = []
    state["failed"] = False
    state.setdefault("retries", 0)
    MAX_RETRIES = 2  # example: allow planner -> executor retry cycles if necessary

    # A small helper to call tools
    def run_tool(action: str, input_text: str):
        action = action.lower()
        if action == "date":
            # common_tools.date_tool expects a question-like input ("today", "day after tomorrow", or full)
            return date_tool(input_text)
        if action == "calculator":
            # our calculator expects either an expression string or state key; pass expression directly
            return calculator_tool(input_text)
        if action == "google search":
            # use your GoogleSearchAgent wrapper
            return google_search_agents.GoogleSearchAgent().answer_from_search_with_gemini(input_text)
        if action == "llm":
            return init_llm().generate_response_with_params(input_text)
        return f"Unknown action: {action}"

    # Execute the plan (single pass). If a step errors, mark failed.
    for i, step in enumerate(plan):
        action = step.get("action")
        input_text = step.get("input", "")
        try:
            result = run_tool(action, input_text)
        except Exception as e:
            result = f"Error executing {action}: {e}"
        step_results.append({
            "index": i,
            "action": action,
            "input": input_text,
            "result": result
        })

        # simple failure detection
        if isinstance(result, str) and (result.lower().startswith("error") or "error" in result.lower()):
            state["failed"] = True
            state["failed_step"] = i
            break

    state["step_results"] = step_results

    # 5) If failed, ask the planner to revise (simple retry loop inside executor)
    if state["failed"] and state["retries"] < MAX_RETRIES:
        state["retries"] += 1
        # generate replan prompt that includes failure context
        fail_idx = state.get("failed_step")
        fail_info = step_results[fail_idx] if fail_idx is not None and fail_idx < len(step_results) else {}
        replan_prompt = (
            "A previous plan failed at step index {idx}. The failing step: {fail}.\n"
            "User question: {q}\n"
            "Existing plan (raw): {raw}\n"
            "Please return a revised JSON plan that avoids the failure. Strictly return JSON array.\n"
        ).format(idx=fail_idx, fail=json.dumps(fail_info, ensure_ascii=False), q=state.get("question", ""), raw=state.get("plan_raw", ""))
        planner_llm = init_llm()
        repl_text = planner_llm.generate_response_with_params(replan_prompt)
        state["plan_raw"] = repl_text
        try:
            new_plan = parse_json_from_text(repl_text)
            if isinstance(new_plan, list):
                state["plan"] = [{"action": s["action"].strip(), "input": str(s["input"]).strip()} for s in new_plan]
                # re-run execution recursively (simple approach)
                return executor_node(state)
            else:
                state["plan_parse_error"] = "Replan did not return list"
        except Exception as e:
            state["plan_parse_error"] = str(e)

    # 6) Synthesize final answer from results using the LLM (concise final answer only)
    synth_prompt = (
        "You are a concise synthesizer. Given the user question and the step execution results (JSON),\n"
        "produce a short final answer (one or two sentences) that directly answers the user's question.\n"
        "Return FINAL ANSWER ONLY (no reasoning). Question: {q}\nResults: {res}\n"
    ).format(q=state.get("question", ""), res=json.dumps(step_results, ensure_ascii=False))
    
    synth_resp = init_llm().generate_response_with_params(synth_prompt)
    state["final_answer"] = synth_resp.strip()
    return state









def calculator_tool(expression:str) -> str:
    print(">>> CALCULATOR TOOL CALLED <<<")
    print(f"Evaluating expression: {expression}")
    try:
        result = eval(expression, {"__builtins__": None}, {})
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {e}"

    

def date_tool(query:str) -> str:
    print(">>> DATE TOOL CALLED <<<")
    today = datetime.today()
    return today.strftime("%Y-%m-%d")
