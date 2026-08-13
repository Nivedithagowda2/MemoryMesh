"""
The shared memory layer that every agent reads from and writes to,
backed by CockroachDB.
"""
import json
import time
import uuid

import psycopg

from . import config
from .embeddings import embed_text


def get_connection():
    if not config.DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not set. Copy .env.example to .env and fill in "
            "your CockroachDB Cloud connection string."
        )
    return psycopg.connect(config.DATABASE_URL, autocommit=True)


def ensure_agent(agent_name: str, agent_type: str) -> str:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT agent_id FROM agents WHERE agent_name = %s", (agent_name,)
            )
            row = cur.fetchone()
            if row:
                return str(row[0])
            cur.execute(
                """
                INSERT INTO agents (agent_id, agent_name, agent_type)
                VALUES (%s, %s, %s)
                RETURNING agent_id
                """,
                (str(uuid.uuid4()), agent_name, agent_type),
            )
            return str(cur.fetchone()[0])


def remember(
    agent_id: str,
    memory_type: str,
    task_summary: str,
    context: str,
    resolution: str,
    confidence: float = 0.85,
) -> str:
    embedding = embed_text(f"{task_summary} {context}")
    memory_id = str(uuid.uuid4())
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO memories
                    (memory_id, agent_id, memory_type, task_summary, context,
                     resolution, confidence, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    memory_id,
                    agent_id,
                    memory_type,
                    task_summary,
                    context,
                    resolution,
                    confidence,
                    json.dumps(embedding),
                ),
            )
    return memory_id


def recall(
    query_text: str,
    recalling_agent_id: str,
    top_k: int = 3,
    similarity_threshold: float = 0.35,
    assumed_fresh_reasoning_seconds: float = 600.0,
) -> list[dict]:
    """
    Searches the SHARED memory (written by any agent) for anything similar
    to the current query, using CockroachDB's vector distance operator.

    IMPORTANT: `embedding <-> query` returns the raw L2 (Euclidean)
    distance, NOT a similarity score. Our embeddings are unit-normalized
    (length 1), so for unit vectors the relationship between L2 distance
    and cosine similarity is exactly:

        cosine_similarity = 1 - (L2_distance ** 2) / 2

    Using "1 - L2_distance" directly (a common mistake) badly
    underestimates similarity and can make real matches fall below the
    threshold, which is why we convert it properly below.
    """
    query_embedding = embed_text(query_text)
    start = time.time()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    m.memory_id,
                    m.agent_id,
                    a.agent_name,
                    m.memory_type,
                    m.task_summary,
                    m.context,
                    m.resolution,
                    m.confidence,
                    m.embedding <-> %s AS distance
                FROM memories m
                JOIN agents a ON a.agent_id = m.agent_id
                ORDER BY m.embedding <-> %s
                LIMIT %s
                """,
                (json.dumps(query_embedding), json.dumps(query_embedding), top_k),
            )
            rows = cur.fetchall()

    results = []
    for row in rows:
        (memory_id, agent_id, agent_name, memory_type, task_summary,
         context, resolution, confidence, distance) = row
        distance = float(distance)
        # Correct conversion from L2 distance -> cosine similarity for
        # unit-normalized vectors (see docstring above).
        similarity = 1 - (distance ** 2) / 2
        if similarity < similarity_threshold:
            continue
        results.append({
            "memory_id": str(memory_id),
            "source_agent": agent_name,
            "memory_type": memory_type,
            "task_summary": task_summary,
            "context": context,
            "resolution": resolution,
            "confidence": float(confidence),
            "similarity": round(similarity, 3),
        })

    elapsed = time.time() - start

    if results:
        with get_connection() as conn:
            with conn.cursor() as cur:
                for r in results:
                    cur.execute(
                        """
                        INSERT INTO memory_recalls
                            (recall_id, memory_id, recalling_agent_id, query_text,
                             similarity_score, time_saved_seconds)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            str(uuid.uuid4()),
                            r["memory_id"],
                            recalling_agent_id,
                            query_text,
                            r["similarity"],
                            assumed_fresh_reasoning_seconds - elapsed,
                        ),
                    )
                    cur.execute(
                        "UPDATE memories SET times_reused = times_reused + 1 WHERE memory_id = %s",
                        (r["memory_id"],),
                    )

    return results


def get_stats() -> dict:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM agents")
            agent_count = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM memories")
            memory_count = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM memory_recalls")
            recall_count = cur.fetchone()[0]
            cur.execute("SELECT coalesce(sum(time_saved_seconds), 0) FROM memory_recalls")
            time_saved = cur.fetchone()[0]
    return {
        "agents": agent_count,
        "memories_stored": memory_count,
        "cross_agent_recalls": recall_count,
        "estimated_seconds_saved": float(time_saved),
    }
