"""
Agent Nodes — the individual steps in the self-healing pipeline.

Each function takes an AgentState dict, performs work, and returns
a partial state update dict that gets merged back into the state.

Nodes:
1. load_schema   — Fetch DB schema
2. generate_sql  — Ask Gemini to write SQL
3. validate_sql  — Safety check (read-only enforcement)
4. execute_sql   — Run the SQL against the database
5. handle_error  — Prepare error context for retry
"""

import json
import re

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import settings
from app.database.connection import get_schema_as_text, execute_query
from app.prompts.templates import (
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
    RETRY_PROMPT_TEMPLATE,
)
from app.agent.state import AgentState


# ── LLM Instance ────────────────────────────────────────────────────────────

def get_llm():
    """Create a Gemini LLM instance."""
    return ChatGoogleGenerativeAI(
        model=settings.LLM_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0,  # Deterministic SQL generation
    )


# ── Node Functions ──────────────────────────────────────────────────────────


def load_schema(state: AgentState) -> dict:
    """
    Node 1: Load the database schema.

    Reads the database schema via SQLAlchemy introspection and
    formats it as human-readable text for the LLM prompt.
    """
    print("📋 Loading database schema...")
    schema_text = get_schema_as_text()
    return {"schema": schema_text}


def generate_sql(state: AgentState) -> dict:
    """
    Node 2: Generate SQL from the natural language question.

    On first attempt, uses the standard prompt.
    On retries, includes the previous error for self-healing.
    """
    attempt_num = state.get("attempts", 0) + 1
    print(f"🤖 Generating SQL (attempt {attempt_num})...")

    llm = get_llm()

    # Build the prompt based on whether this is a retry
    if state.get("error") and attempt_num > 1:
        # Self-healing: include the error context
        user_content = RETRY_PROMPT_TEMPLATE.format(
            schema=state["schema"],
            question=state["question"],
            previous_sql=state.get("sql", ""),
            error=state["error"],
        )
    else:
        # First attempt
        user_content = USER_PROMPT_TEMPLATE.format(
            schema=state["schema"],
            question=state["question"],
        )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ]

    response = llm.invoke(messages)
    
    # Handle response.content being either a string or a list of content parts
    raw_content = response.content
    if isinstance(raw_content, list):
        # Extract text from content parts
        text_parts = []
        for part in raw_content:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict) and "text" in part:
                text_parts.append(part["text"])
        raw_response = " ".join(text_parts).strip()
    else:
        raw_response = raw_content.strip()

    # Extract SQL from the response (handle markdown code blocks)
    sql = extract_sql(raw_response)

    print(f"   📝 Generated SQL: {sql}")
    return {"sql": sql, "attempts": attempt_num}


def validate_sql(state: AgentState) -> dict:
    """
    Node 3: Validate the SQL for safety.

    Blocks any destructive operations (DROP, DELETE, UPDATE, INSERT, etc.)
    to ensure the agent only runs read-only SELECT queries.
    """
    print("🛡️  Validating SQL safety...")
    sql = state.get("sql", "").strip()

    if not sql:
        return {
            "error": "No SQL query was generated. The LLM returned an empty response.",
            "is_success": False,
        }

    # Check for destructive SQL operations
    BLOCKED_KEYWORDS = [
        r"\bDROP\b",
        r"\bDELETE\b",
        r"\bUPDATE\b",
        r"\bINSERT\b",
        r"\bALTER\b",
        r"\bTRUNCATE\b",
        r"\bCREATE\b",
        r"\bGRANT\b",
        r"\bREVOKE\b",
        r"\bEXEC\b",
    ]

    sql_upper = sql.upper()
    for pattern in BLOCKED_KEYWORDS:
        if re.search(pattern, sql_upper):
            keyword = re.search(pattern, sql_upper).group()
            return {
                "error": (
                    f"Safety violation: SQL contains blocked operation '{keyword}'. "
                    "Only SELECT queries are allowed."
                ),
                "is_success": False,
            }

    return {}  # No error — validation passed


def execute_sql(state: AgentState) -> dict:
    """
    Node 4: Execute the SQL query against the database.

    If execution succeeds, sets result and is_success=True.
    If it fails, captures the error message for self-healing.
    """
    # If validation already set an error, skip execution
    if state.get("error") and not state.get("is_success", True):
        return {}

    sql = state["sql"]
    print(f"⚡ Executing SQL: {sql}")

    try:
        rows = execute_query(sql)
        result_str = json.dumps(rows, default=str, indent=2)
        print(f"   ✅ Success — {len(rows)} rows returned.")
        return {
            "result": result_str,
            "is_success": True,
            "error": "",
        }
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"   ❌ SQL execution failed: {error_msg}")
        return {
            "error": error_msg,
            "is_success": False,
            "result": "",
        }


def handle_error(state: AgentState) -> dict:
    """
    Node 5: Prepare error context for the retry loop.

    This node is reached when SQL execution fails and there are
    retries remaining. It preserves the error context so the
    generate_sql node can self-heal.
    """
    attempt = state.get("attempts", 1)
    error = state.get("error", "Unknown error")
    print(f"🔄 Self-healing: attempt {attempt} failed — preparing retry...")
    print(f"   Error: {error}")

    # The error and sql are already in state; generate_sql will use them
    return {}


# ── Helpers ─────────────────────────────────────────────────────────────────


def extract_sql(raw_response: str) -> str:
    """
    Extract a SQL query from the LLM's raw response.

    Handles cases where the LLM wraps SQL in markdown code blocks:
      ```sql
      SELECT * FROM ...
      ```
    """
    # Try to extract from markdown code block
    code_block_match = re.search(
        r"```(?:sql)?\s*\n?(.*?)```", raw_response, re.DOTALL | re.IGNORECASE
    )
    if code_block_match:
        return code_block_match.group(1).strip()

    # If no code block, try to find a SELECT statement
    select_match = re.search(
        r"(SELECT\s+.+)", raw_response, re.DOTALL | re.IGNORECASE
    )
    if select_match:
        return select_match.group(1).strip().rstrip(";") + ";"

    # Fall back to the raw response
    return raw_response.strip()
