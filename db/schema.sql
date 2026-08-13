-- MemoryMesh schema
-- This is the shared memory layer that every agent reads from and writes to.

CREATE TABLE IF NOT EXISTS agents (
    agent_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name    STRING NOT NULL UNIQUE,
    agent_type    STRING NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS memories (
    memory_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id        UUID NOT NULL REFERENCES agents(agent_id),
    memory_type     STRING NOT NULL,
    task_summary    STRING NOT NULL,
    context         STRING,
    resolution      STRING,
    confidence      FLOAT NOT NULL DEFAULT 0.8,
    embedding       VECTOR(384) NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    times_reused    INT NOT NULL DEFAULT 0
);

CREATE VECTOR INDEX IF NOT EXISTS memories_embedding_idx
    ON memories (embedding);

CREATE TABLE IF NOT EXISTS memory_recalls (
    recall_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id         UUID NOT NULL REFERENCES memories(memory_id),
    recalling_agent_id UUID NOT NULL REFERENCES agents(agent_id),
    query_text        STRING NOT NULL,
    similarity_score  FLOAT NOT NULL,
    time_saved_seconds FLOAT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
