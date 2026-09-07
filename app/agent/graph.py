"""
LangGraph Graph — wires the agent nodes into a self-healing pipeline.

Graph flow:
    START → load_schema → generate_sql → validate_sql → execute_sql
                                                           ↓
                                                 [success] → END
                                                 [error + retries left] → handle_error → generate_sql
                                                 [error + max retries] → END (with error)
"""

import asyncio
import json
from langgraph.graph import StateGraph, START, END

from app.config import settings
from app.agent.state import AgentState
from app.agent.nodes import (
    load_schema,
    generate_sql,
    validate_sql,
    execute_sql,
    handle_error,
)


def should_retry(state: AgentState) -> str:
    """
    Conditional edge: decide whether to retry or finish.

    Returns:
        "handle_error"  — if there's an error and retries remain
        "end"           — if success OR max retries exhausted
    """
    is_success = state.get("is_success", False)
    attempts = state.get("attempts", 0)
    has_error = bool(state.get("error"))

    if is_success:
        return "end"

    if has_error and attempts < settings.MAX_RETRIES:
        return "handle_error"

    return "end"


def build_graph() -> StateGraph:
    """
    Build and compile the LangGraph StateGraph for the Text-to-SQL agent.

    Returns a compiled graph ready to be invoked.
    """
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("load_schema", load_schema)
    graph.add_node("generate_sql", generate_sql)
    graph.add_node("validate_sql", validate_sql)
    graph.add_node("execute_sql", execute_sql)
    graph.add_node("handle_error", handle_error)

    # Add edges
    graph.add_edge(START, "load_schema")
    graph.add_edge("load_schema", "generate_sql")
    graph.add_edge("generate_sql", "validate_sql")
    graph.add_edge("validate_sql", "execute_sql")

    # Conditional edge after execution
    graph.add_conditional_edges(
        "execute_sql",
        should_retry,
        {
            "handle_error": "handle_error",
            "end": END,
        },
    )

    # After error handling, retry SQL generation
    graph.add_edge("handle_error", "generate_sql")

    return graph.compile()


# Compiled graph singleton
agent_graph = build_graph()


async def run_agent(question: str) -> dict:
    """
    Run the self-healing Text-to-SQL agent.

    Args:
        question: The user's natural language question.

    Returns:
        Dict with keys: question, sql, result, attempts, is_success, error
    """
    print(f"\n{'='*60}")
    print(f"🧠 Agent invoked with question: {question}")
    print(f"{'='*60}")

    initial_state: AgentState = {
        "question": question,
        "schema": "",
        "sql": "",
        "result": "",
        "error": "",
        "attempts": 0,
        "is_success": False,
    }

    # Run the graph asynchronously in worker thread
    final_state = await asyncio.to_thread(agent_graph.invoke, initial_state)

    # Parse result back from JSON string if successful
    result_data = final_state.get("result", "")
    if result_data and final_state.get("is_success"):
        try:
            result_data = json.loads(result_data)
        except json.JSONDecodeError:
            pass  # Keep as string if not valid JSON

    return {
        "question": final_state["question"],
        "sql": final_state.get("sql", ""),
        "result": result_data,
        "attempts": final_state.get("attempts", 0),
        "is_success": final_state.get("is_success", False),
        "error": final_state.get("error", "") or None,
    }
