"""
schema_service.py — Loads and queries the JSON schema file.

Responsibilities:
  - Load navigatto_schema_nl2sql.json once at startup
  - Select only the relevant tables for a given user query (keyword matching)
  - Format schema into compact TableName(Col:type, ...) string for LLM
"""

import json
import os
import re
from pathlib import Path
from typing import List, Dict

# ── Path to the schema JSON ──────────────────────────────────────────────────
SCHEMA_PATH = Path(__file__).parent / "navigatto_schema_nl2sql.json"

# ── In-memory schema store (loaded once at module import) ────────────────────
_schema_entries: List[Dict] = []


def load_schema() -> None:
    """Load the JSON schema file into memory. Called at app startup."""
    global _schema_entries
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Schema file not found: {SCHEMA_PATH}\n"
            "Place navigatto_schema_nl2sql.json in the chatbot_module/ directory."
        )
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        _schema_entries = json.load(f)
    print(f"[SchemaService] Loaded {len(_schema_entries)} tables from schema JSON.")


def get_all_table_names() -> List[str]:
    """Return a list of all table IDs (names) in the schema."""
    return [entry["id"] for entry in _schema_entries]


def get_relevant_tables(query: str, top_k: int = 8) -> List[Dict]:
    """
    Select the most relevant tables for a given user query using keyword matching.

    Strategy:
    1. Extract meaningful words from the query (skip stop-words).
    2. For each schema entry, count keyword overlaps between query words and the
       table's 'Keywords' section + table name.
    3. Return the top_k highest-scoring entries (always include journeys, drivers, vehicles).

    Args:
        query: The user's (rewritten) question.
        top_k: Maximum number of tables to return. Default 8.

    Returns:
        List of schema entry dicts (each has 'id' and 'text').
    """
    if not _schema_entries:
        load_schema()

    # Normalize query
    q_lower = query.lower()
    q_words = set(re.findall(r'\b[a-z]{3,}\b', q_lower))  # words ≥ 3 chars

    # Stop-words to ignore during matching
    stop_words = {
        'the', 'and', 'for', 'are', 'was', 'were', 'has', 'have', 'had',
        'how', 'many', 'show', 'give', 'list', 'get', 'what', 'which',
        'that', 'this', 'with', 'from', 'all', 'last', 'most', 'more',
        'than', 'each', 'per', 'any', 'did', 'does', 'been', 'their',
        'its', 'our', 'top', 'can', 'not', 'also', 'only',
    }
    q_words -= stop_words

    scored = []
    for entry in _schema_entries:
        table_name = entry["id"].lower()
        text_lower = entry["text"].lower()

        score = 0

        # Table name match is weighted 3x
        if table_name in q_lower:
            score += 10
        for word in q_words:
            if word in table_name:
                score += 3

        # Keyword section match
        kw_match = re.search(r'keywords:\n(.*)', text_lower)
        if kw_match:
            kw_string = kw_match.group(1)
            for word in q_words:
                if word in kw_string:
                    score += 2

        # Full text match (description + columns)
        for word in q_words:
            if word in text_lower:
                score += 1

        scored.append((score, entry))

    # Sort by score descending
    scored.sort(key=lambda x: x[0], reverse=True)

    # Always include core tables (journeys, drivers, vehicles) if they scored > 0
    core_tables = {"journeys", "drivers", "vehicles", "journey_scores"}
    selected_ids = set()
    selected = []

    # First pass: top_k results
    for score, entry in scored[:top_k]:
        if score > 0:
            selected.append(entry)
            selected_ids.add(entry["id"])

    # Second pass: ensure core tables are included if not already selected
    for entry in _schema_entries:
        if entry["id"] in core_tables and entry["id"] not in selected_ids:
            selected.append(entry)
            selected_ids.add(entry["id"])
            if len(selected) >= top_k + len(core_tables):
                break

    return selected


def format_schema_for_llm(entries: List[Dict]) -> str:
    """
    Convert schema entries to compact TableName(Col:type, ...) | Relationships: [...] format.
    This saves tokens while preserving all essential type and relationship information.

    Example output:
        journeys(trip_id:nvarchar, vehicle_id:uniqueidentifier, distance_km:float, ...)
        | Relationships: [vehicle_id → vehicles.id, driver_id → drivers.driver_id]
    """
    lines = []
    for entry in entries:
        text = entry["text"]
        table_name = entry["id"]
        cols = []
        relationships = []

        in_cols = False
        in_rels = False
        for line in text.split("\n"):
            stripped = line.strip()
            if stripped.lower().startswith("columns:"):
                in_cols = True
                in_rels = False
                continue
            elif stripped.lower().startswith("relationships:"):
                in_rels = True
                in_cols = False
                continue
            elif stripped.lower().startswith("description:") or stripped.lower().startswith("keywords:"):
                in_cols = False
                in_rels = False
                continue
            elif stripped.lower().startswith("table:"):
                continue

            if in_cols and stripped.startswith("-"):
                # Format: "- col_name: type (nullable)"
                col_part = stripped.lstrip("- ").split("(")[0].strip()
                # Extract just name and base type
                if ":" in col_part:
                    col_name, col_type = col_part.split(":", 1)
                    col_type = col_type.strip().split("(")[0].strip()  # remove precision
                    cols.append(f"{col_name.strip()}:{col_type}")

            if in_rels and stripped.startswith("-"):
                rel = stripped.lstrip("- ").strip()
                if rel and rel != "None":
                    relationships.append(rel)

        compact = f"{table_name}({', '.join(cols)})"
        if relationships:
            compact += f" | Relationships: [{', '.join(relationships)}]"
        lines.append(compact)

    return "\n".join(lines)


def get_schema_context(query: str, top_k: int = 8) -> str:
    """
    Convenience function: select relevant tables and format them for the LLM.
    This is the main function called by the pipeline.

    Returns:
        Compact schema string ready to be injected into the SQL generation prompt.
    """
    relevant = get_relevant_tables(query, top_k=top_k)
    return format_schema_for_llm(relevant)


def get_schema_summary() -> Dict:
    """Returns a summary dict for the /health endpoint."""
    return {
        "schema_file": str(SCHEMA_PATH),
        "tables_loaded": len(_schema_entries),
        "table_names": get_all_table_names(),
    }
