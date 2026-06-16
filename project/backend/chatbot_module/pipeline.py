"""
pipeline.py — Main orchestration pipeline for the Text-to-SQL AI Chatbot.
Covers:
  1. Context rewriter (resolves conversational history)
  2. Relevance checking (scope guard)
  3. Schema context retrieval
  4. SQL generation (with safety validation)
  5. Safe execution + self-healing retry loop
  6. Final answer formatting + follow-up suggestions
"""

import re
from typing import List, Dict, Any, Optional
from chatbot_module import llm_service
from chatbot_module import schema_service
from chatbot_module import db_executor


def log_chatbot_transaction(
    query: str,
    rewritten: str,
    sql: Optional[str],
    status: str,
    error_msg: Optional[str],
    rows_count: int
):
    import datetime
    import os
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_content = f"""
======================================================================
[{timestamp}] Chatbot Transaction Log
----------------------------------------------------------------------
QUESTION: {query}
STANDALONE REWRITE: {rewritten}
GENERATED T-SQL: {sql if sql else "N/A"}
STATUS: {status}
ROWS RETURNED: {rows_count}
"""
    if error_msg:
        log_content += f"ERROR/TRACEBACK: {error_msg}\n"
    log_content += "======================================================================\n"
    
    try:
        log_path = os.path.join(os.path.dirname(__file__), "..", "chatbot.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(log_content)
    except Exception as e:
        print(f"[ChatbotLogger] Failed to write log: {e}")


async def process_query(
    query: str,
    history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Main entry point for processing a user's natural language question.
    
    Args:
        query: The user's question.
        history: Optional list of previous chat messages (e.g. [{"role": "user", "content": "..."}]).
        
    Returns:
        A dict containing status, message, sql, columns, rows, and suggestions.
    """
    if history is None:
        history = []

    print(f"[ChatbotPipeline] Received query: '{query}'")

    # Stage 1: Context Rewrite using History
    rewritten_query = await llm_service.rewrite_query_with_history(query, history)
    if rewritten_query != query:
        print(f"[ChatbotPipeline] Rewritten query: '{rewritten_query}'")

    def log_and_return(res: Dict[str, Any]) -> Dict[str, Any]:
        log_chatbot_transaction(
            query=query,
            rewritten=rewritten_query,
            sql=res.get("sql"),
            status=res.get("status"),
            error_msg=res.get("message") if res.get("status") in ["db_error", "schema_error", "error", "blocked"] else None,
            rows_count=len(res.get("rows", [])) if res.get("rows") else 0
        )
        return res

    # Stage 2: Scope Guard (Relevance Check)
    is_relevant = await llm_service.is_sql_relevant(rewritten_query)
    if not is_relevant:
        print(f"[ChatbotPipeline] Query out of scope: '{rewritten_query}'")
        return log_and_return({
            "status": "out_of_scope",
            "message": "I can only answer questions about fleet details, drivers, vehicles, journeys, wear events, and maintenance metrics. Please ask a database-related question.",
            "sql": None,
            "columns": [],
            "rows": [],
            "suggestions": [],
            "rewritten_query": rewritten_query
        })

    # Stage 3: Schema Selector
    # Select most relevant tables and format them into a compact schema context for the LLM
    try:
        schema_context = schema_service.get_schema_context(rewritten_query, top_k=8)
    except Exception as e:
        print(f"[ChatbotPipeline] Error loading schema: {e}")
        return log_and_return({
            "status": "schema_error",
            "message": f"Error loading database schema: {str(e)}",
            "sql": None,
            "columns": [],
            "rows": [],
            "suggestions": [],
            "rewritten_query": rewritten_query
        })

    # Stage 4: SQL Generation
    sql = await llm_service.generate_sql(rewritten_query, schema_context)
    # Strip any markdown or code blocks the LLM might have wrapped the query in
    sql = clean_sql_query(sql)
    print(f"[ChatbotPipeline] Generated SQL: {sql}")

    if sql.upper() == "CANNOT_GENERATE":
        return log_and_return({
            "status": "cannot_generate",
            "message": "I could not find a way to answer your question with the available database structure.",
            "sql": None,
            "columns": [],
            "rows": [],
            "suggestions": [],
            "rewritten_query": rewritten_query
        })

    # Stage 5: Execution + Healing Loop (Max 3 attempts)
    db_result = None
    MAX_RETRIES = 3
    final_sql = sql

    for attempt in range(1, MAX_RETRIES + 1):
        print(f"[ChatbotPipeline] SQL execution attempt {attempt}...")
        
        # Pre-flight security validation
        is_safe, blocked_word = db_executor.validate_sql_safety(final_sql)
        if not is_safe:
            print(f"[ChatbotPipeline] Security block: '{blocked_word}' in query '{final_sql}'")
            return log_and_return({
                "status": "blocked",
                "message": f"Security Alert: Blocked keyword '{blocked_word}' detected in generated query.",
                "sql": final_sql,
                "columns": [],
                "rows": [],
                "suggestions": [],
                "rewritten_query": rewritten_query
            })

        # Execute query
        db_result = await db_executor.execute_query(final_sql)
        
        if db_result["success"]:
            print(f"[ChatbotPipeline] SQL executed successfully. Returned {db_result['row_count']} rows.")
            break
            
        # If execution failed, try self-healing SQL fix
        print(f"[ChatbotPipeline] SQL failed on attempt {attempt}: {db_result['error']}")
        if attempt < MAX_RETRIES:
            fixed = await llm_service.fix_sql(
                rewritten_query,
                final_sql,
                db_result["error"],
                schema_context
            )
            final_sql = clean_sql_query(fixed)
            print(f"[ChatbotPipeline] Fixed SQL for retry: {final_sql}")
            if final_sql.upper() == "CANNOT_GENERATE":
                break

    # If all execution attempts failed
    if not db_result or not db_result["success"]:
        error_msg = db_result.get("error", "Unknown database error") if db_result else "No result returned"
        return log_and_return({
            "status": "db_error",
            "message": f"Sorry, I encountered a database error while executing the query: {error_msg}",
            "sql": final_sql,
            "columns": [],
            "rows": [],
            "suggestions": [],
            "rewritten_query": rewritten_query
        })

    # Stage 6: Natural Language Answer Generation
    print("[ChatbotPipeline] Generating natural language answer...")
    answer_text = await llm_service.generate_answer(
        rewritten_query,
        db_result["columns"],
        db_result["rows"],
        schema_context
    )

    # Parse follow-up suggestions from answer text
    suggestions = []
    if "QUESTIONS:" in answer_text:
        parts = answer_text.split("QUESTIONS:")
        answer_text = parts[0].strip()
        suggestions_raw = parts[1].strip().split("\n")
        for sug in suggestions_raw:
            sug_clean = sug.strip("- *•").replace("*", "").strip()
            if sug_clean:
                suggestions.append(sug_clean)

    return log_and_return({
        "status": "success",
        "message": answer_text,
        "sql": final_sql,
        "columns": db_result["columns"],
        "rows": db_result["rows"],
        "suggestions": suggestions[:2],
        "rewritten_query": rewritten_query
    })


def clean_sql_query(sql: str) -> str:
    """Helper to strip markdown, backticks, and whitespace from LLM-generated SQL."""
    # Strip markdown code formatting like ```sql ... ```
    sql_clean = re.sub(r"```(sql)?", "", sql, flags=re.IGNORECASE)
    # Strip backticks
    sql_clean = sql_clean.replace("`", "")
    return sql_clean.strip()
