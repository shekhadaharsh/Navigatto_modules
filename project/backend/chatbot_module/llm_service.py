"""
llm_service.py — centralizes all asynchronous LLM operations using Groq client.
Loads prompts from prompts.py.
"""

import os
from typing import List, Dict, Any, Optional
from groq import AsyncGroq

from chatbot_module.prompts import (
    QUERY_REWRITE_PROMPT,
    RELEVANCE_CHECK_PROMPT,
    SQL_GENERATION_PROMPT,
    SQL_FIX_PROMPT,
    ANSWER_GENERATION_PROMPT,
    SQL_GENERATOR_SYSTEM_MSG,
    SQL_FIXER_SYSTEM_MSG,
    ANALYST_SYSTEM_MSG,
)

# Settings
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
_client: Optional[AsyncGroq] = None


def get_client() -> AsyncGroq:
    """Lazily initialize the AsyncGroq client to avoid startup crashes if API key is missing."""
    global _client
    if _client is not None:
        return _client

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is not set in the environment or .env file. "
            "Please configure it to enable the chatbot."
        )

    _client = AsyncGroq(api_key=api_key)
    return _client


async def rewrite_query_with_history(query: str, history: List[Dict[str, str]]) -> str:
    """
    Uses LLM to resolve pronouns and context from history, producing a standalone query.
    """
    if not history:
        return query

    # Format history for the LLM
    history_str = ""
    for msg in history[-4:]:  # Last 4 messages (2 turns) for context
        role = "User" if msg.get("role") == "user" else "Assistant"
        history_str += f"{role}: {msg.get('content')}\n"

    prompt = QUERY_REWRITE_PROMPT.format(history=history_str, query=query)
    
    try:
        client = get_client()
        response = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=150
        )
        rewritten = response.choices[0].message.content.strip()
        return rewritten if rewritten else query
    except Exception as e:
        print(f"[LLMService] Error during query rewrite: {e}")
        return query


async def is_sql_relevant(query: str) -> bool:
    """
    Checks whether the user's question is related to the database/SQL or not.
    Returns True if the question is relevant, False if it is out-of-scope.
    """
    prompt = RELEVANCE_CHECK_PROMPT.format(query=query)
    
    try:
        client = get_client()
        response = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=5
        )
        answer = response.choices[0].message.content.strip().upper()
        return answer.startswith("YES")
    except Exception as e:
        print(f"[LLMService] Error checking SQL relevance: {e}")
        # Default to True so we try to generate SQL rather than blocking on API error
        return True


async def generate_sql(query: str, schema_context: str) -> str:
    """
    Generates T-SQL based on the user question and relevant schema context.
    """
    prompt = SQL_GENERATION_PROMPT.format(query=query, schema=schema_context)
    
    client = get_client()
    response = await client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SQL_GENERATOR_SYSTEM_MSG},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )
    
    return response.choices[0].message.content.strip()


async def fix_sql(query: str, failed_sql: str, error: str, schema_context: str) -> str:
    """
    Self-healing: given a SQL query that failed at execution, asks LLM to fix it.
    """
    prompt = SQL_FIX_PROMPT.format(
        query=query,
        failed_sql=failed_sql,
        error=error,
        schema=schema_context
    )
    
    client = get_client()
    response = await client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SQL_FIXER_SYSTEM_MSG},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0
    )
    
    return response.choices[0].message.content.strip()


async def generate_answer(query: str, columns: List[str], rows: List[List[Any]], schema_context: str = "") -> str:
    """
    Converts raw database results into a natural language answer to the user's question.
    """
    row_count = len(rows)
    if not rows:
        data_str = "[EMPTY RESULT] The database returned 0 rows for this query."
    else:
        # Format results as plain text for the LLM (cap at 10 rows to stay within token limits)
        header = " | ".join(str(c) for c in columns)
        data_rows = "\n".join(
            " | ".join(str(v) if v is not None else "NULL" for v in row)
            for row in rows[:10]
        )
        data_str = f"Columns: {header}\nData (First 10 rows):\n{data_rows}\nTotal Results Found: {row_count}"

    schema_instruction = ""
    if schema_context:
        schema_instruction = (
            f"\n\nAvailable Schema Context:\n{schema_context}\n\n"
            "**STRICT SUGGESTION RULE**: Your follow-up questions MUST ONLY use tables and columns "
            "listed in the 'Available Schema Context' above. Do not suggest anything that cannot "
            "be answered with these tables."
        )

    prompt = ANSWER_GENERATION_PROMPT.format(
        query=query,
        data=f"{data_str}{schema_instruction}"
    )
    
    client = get_client()
    response = await client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": ANALYST_SYSTEM_MSG},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    
    return response.choices[0].message.content.strip()
