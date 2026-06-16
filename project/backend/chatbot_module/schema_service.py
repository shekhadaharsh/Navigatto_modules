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
from typing import List, Dict, Optional, Any
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

# ── Path to the schema JSON ──────────────────────────────────────────────────
SCHEMA_PATH = Path(__file__).parent / "navigatto_schema_nl2sql.json"

# ── In-memory schema store and search indexes ────────────────────────────────
_schema_entries: List[Dict] = []
_qdrant_client: Optional[QdrantClient] = None
_encoder: Optional[SentenceTransformer] = None
_bm25: Optional[BM25Okapi] = None


def load_schema() -> None:
    """Load the JSON schema file into memory and build hybrid search indexes."""
    global _schema_entries, _qdrant_client, _encoder, _bm25
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(
            f"Schema file not found: {SCHEMA_PATH}\n"
            "Place navigatto_schema_nl2sql.json in the chatbot_module/ directory."
        )
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        _schema_entries = json.load(f)
    print(f"[SchemaService] Loaded {len(_schema_entries)} tables from schema JSON.")

    # 1. Initialize Qdrant Client in memory
    print("[SchemaService] Initializing Qdrant In-Memory client...")
    _qdrant_client = QdrantClient(":memory:")
    
    # 2. Initialize sentence transformer model (MiniLM is fast and works locally on CPU)
    print("[SchemaService] Loading SentenceTransformer 'all-MiniLM-L6-v2'...")
    _encoder = SentenceTransformer("all-MiniLM-L6-v2")
    
    # 3. Create schema collection
    collection_name = "schema_collection"
    if _qdrant_client.collection_exists(collection_name):
        _qdrant_client.delete_collection(collection_name)
    _qdrant_client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )
    
    # 4. Generate embeddings and upsert to Qdrant
    points = []
    documents_for_bm25 = []
    
    for idx, entry in enumerate(_schema_entries):
        table_id = entry["id"]
        text = entry["text"]
        
        # Combine table name and text to form a complete searchable document
        doc_text = f"Table: {table_id}. Description: {text}"
        documents_for_bm25.append(doc_text.lower())
        
        # Encode dense semantic vector
        vector = _encoder.encode(doc_text, convert_to_numpy=True).tolist()
        
        points.append(PointStruct(
            id=idx,
            vector=vector,
            payload={
                "id": table_id,
                "text": text
            }
        ))
        
    _qdrant_client.upsert(collection_name=collection_name, points=points)
    print(f"[SchemaService] Indexed {len(points)} tables in Qdrant collection.")
    
    # 5. Build BM25 sparse index
    tokenized_docs = [doc.split() for doc in documents_for_bm25]
    _bm25 = BM25Okapi(tokenized_docs)
    print("[SchemaService] Successfully initialized BM25 sparse index.")


def get_all_table_names() -> List[str]:
    """Return a list of all table IDs (names) in the schema."""
    return [entry["id"] for entry in _schema_entries]


def get_relevant_tables(query: str, top_k: int = 8) -> List[Dict]:
    """
    Select the most relevant tables for a given user query using Hybrid Search (BM25 + Qdrant vectors) and RRF.
    """
    global _schema_entries, _qdrant_client, _encoder, _bm25
    if not _schema_entries:
        load_schema()

    if not _qdrant_client or not _encoder or not _bm25:
        print("[SchemaService] Search indexes not initialized, falling back to all tables.")
        return _schema_entries

    query_lower = query.lower()
    
    # ────────────────────────────────────────────────────────
    # 1. Sparse search (BM25)
    # ────────────────────────────────────────────────────────
    # Tokenize query words
    q_words = re.findall(r'\b[a-z]{3,}\b', query_lower)
    if not q_words:
        q_words = query_lower.split()
    bm25_scores = _bm25.get_scores(q_words)
    # Get table indices sorted by BM25 score descending
    bm25_ranks = np.argsort(bm25_scores)[::-1]
    
    # ────────────────────────────────────────────────────────
    # 2. Dense search (Qdrant Vector Cosine Similarity)
    # ────────────────────────────────────────────────────────
    query_vector = _encoder.encode(query, convert_to_numpy=True).tolist()
    vector_results = _qdrant_client.query_points(
        collection_name="schema_collection",
        query=query_vector,
        limit=len(_schema_entries)
    ).points
    
    # Map vector results to their index in _schema_entries
    vector_rank_map = {}
    for rank_idx, hit in enumerate(vector_results):
        vector_rank_map[hit.payload["id"]] = rank_idx

    # ────────────────────────────────────────────────────────
    # 3. Reciprocal Rank Fusion (RRF)
    # ────────────────────────────────────────────────────────
    rrf_scores = {}
    for idx, entry in enumerate(_schema_entries):
        table_name = entry["id"]
        
        # BM25 rank position
        bm25_pos = list(bm25_ranks).index(idx)
        
        # Vector rank position
        vector_pos = vector_rank_map.get(table_name, len(_schema_entries))
        
        # Calculate reciprocal rank score (using k = 60 constant)
        score = (1.0 / (60.0 + bm25_pos + 1)) + (1.0 / (60.0 + vector_pos + 1))
        
        # Table name matching bonus to guarantee exact matches
        if table_name.lower() in query_lower:
            score += 1.5
            
        rrf_scores[table_name] = (score, entry)

    # Sort tables by final RRF score descending
    sorted_entries = sorted(rrf_scores.values(), key=lambda x: x[0], reverse=True)

    # Ensure core tables are always present
    core_tables = {"journeys", "drivers", "vehicles", "journey_scores"}
    selected_ids = set()
    selected = []

    # Select top K tables based on score
    for score, entry in sorted_entries[:top_k]:
        selected.append(entry)
        selected_ids.add(entry["id"])

    # Ensure core tables are included
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
