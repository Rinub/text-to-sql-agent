"""
API routes — the Swagger-facing endpoints.

POST /api/v1/query   → Natural language query → SQL → Result
GET  /api/v1/schema  → Inspect database schema
GET  /api/v1/health  → Health check
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agent.graph import run_agent
from app.database.connection import get_db_schema

router = APIRouter()


# ── Request / Response Schemas ──────────────────────────────────────────────


class QueryRequest(BaseModel):
    """User's natural language question."""

    question: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Your question in plain English, e.g. 'Show me the top 5 customers by spending'",
        json_schema_extra={
            "examples": ["What are the total sales by product category?"]
        },
    )


class QueryResponse(BaseModel):
    """Response containing the generated SQL, result, and metadata."""

    question: str = Field(description="The original question")
    sql: str = Field(description="Generated SQL query")
    result: object = Field(description="Query result (list of rows)")
    attempts: int = Field(description="Number of attempts (1 = first try succeeded)")
    is_success: bool = Field(description="Whether the query succeeded")
    error: str | None = Field(default=None, description="Error message if failed")


class SchemaResponse(BaseModel):
    """Database schema information."""

    tables: list[dict] = Field(description="List of tables with columns")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str


# ── Endpoints ───────────────────────────────────────────────────────────────


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Ask a question in plain English",
    description=(
        "Submit a natural language question about your data. "
        "The agent will generate SQL, execute it, and return the results. "
        "If the SQL fails, the agent self-heals by fixing the query and retrying."
    ),
    tags=["Query"],
)
async def query_database(request: QueryRequest):
    """
    Convert a natural language question to SQL, execute it, and return results.

    The self-healing pipeline will:
    1. Load the database schema
    2. Generate SQL using Gemini LLM
    3. Validate the SQL for safety (read-only)
    4. Execute the query
    5. If it fails, feed the error back to the LLM and retry (up to 3 times)
    """
    try:
        result = await run_agent(request.question)
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/schema",
    response_model=SchemaResponse,
    summary="Get database schema",
    description="Returns the current database schema (tables, columns, and types).",
    tags=["Database"],
)
async def get_schema():
    """Return the database schema for inspection."""
    try:
        schema_info = get_db_schema()
        return SchemaResponse(tables=schema_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    tags=["System"],
)
async def health_check():
    """Simple health check endpoint."""
    from app.config import settings

    return HealthResponse(status="healthy", version=settings.APP_VERSION)
