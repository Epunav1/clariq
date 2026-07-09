from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ai.nl_to_sql import question_to_sql, generate_answer
from db.snowflake_client import run_query, test_connection

router = APIRouter()


class QuestionRequest(BaseModel):
    question: str


@router.post("/ask")
async def ask_clariq(request: QuestionRequest):
    """Human-friendly endpoint — returns a plain English answer. Used by the dashboard."""
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        # Convert question to SQL
        sql = question_to_sql(request.question)
        
        # Execute the SQL
        result = run_query(sql)
        
        # Generate human-readable answer
        answer = generate_answer(
            request.question,
            result.get("columns", []),
            result.get("rows", [])
        )
        # Better confidence heuristic and provenance
        if result.get("error"):
            confidence = 0.0
            sample_rows = []
        else:
            rows = result.get("rows", []) or []
            cols = result.get("columns", []) or []
            sample_rows = rows[:5]
            # Heuristic: more rows and more columns -> higher confidence
            if len(rows) >= 5 and len(cols) >= 2:
                confidence = 0.95
            elif len(rows) > 0:
                confidence = 0.75
            else:
                confidence = 0.4

        return {
            "question": request.question,
            "answer": answer,
            "sql": sql,
            "provenance": {"sql": sql, "columns": result.get("columns", []), "sample_rows": sample_rows},
            "confidence": confidence,
            "data": result.get("rows", []),
            "columns": result.get("columns", [])
        }
    except Exception as e:
        return {
            "question": request.question,
            "answer": "Something went wrong while processing your question. Please try again.",
            "error": str(e)
        }


@router.post("/query")
async def query_data(request: QuestionRequest):
    """Raw query endpoint — returns SQL + raw data. Used by developer tools."""
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        # Convert question to SQL
        sql = question_to_sql(request.question)
        
        # Execute the SQL
        result = run_query(sql)
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result.get("error"))

        rows = result.get("rows", []) or []
        cols = result.get("columns", []) or []
        sample_rows = rows[:5]
        if len(rows) >= 5 and len(cols) >= 2:
            confidence = 0.95
        elif len(rows) > 0:
            confidence = 0.75
        else:
            confidence = 0.4

        return {
            "question": request.question,
            "sql": sql,
            "provenance": {"sql": sql, "columns": cols, "sample_rows": sample_rows},
            "confidence": confidence,
            "data": result.get("rows", []),
            "columns": cols
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test Snowflake connection
        test_connection()
        return {
            "api": "healthy",
            "snowflake": "connected"
        }
    except Exception as e:
        return {
            "api": "healthy",
            "snowflake": f"disconnected: {str(e)}"
        }