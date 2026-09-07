"""
Agent State — TypedDict defining the data flowing through the LangGraph pipeline.

This is the "memory" of the agent: each node reads from and writes to this state.
"""

from typing import TypedDict


class AgentState(TypedDict):
    """
    State flowing through the self-healing Text-to-SQL pipeline.

    Attributes:
        question:   The user's natural language question.
        schema:     The database schema formatted as text.
        sql:        The generated SQL query.
        result:     The query result (list of dicts) or error description.
        error:      The last error message (empty string if no error).
        attempts:   How many SQL generation attempts have been made.
        is_success: Whether the final query execution succeeded.
    """

    question: str
    schema: str
    sql: str
    result: str
    error: str
    attempts: int
    is_success: bool
