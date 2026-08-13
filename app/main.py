import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from . import memory_store
from . import agent_a_devops, agent_b_onboarding

app = FastAPI(
    title="MemoryMesh",
    description="A distributed shared memory layer for AI agents, backed by CockroachDB.",
    version="0.1.0",
)

_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


class RememberRequest(BaseModel):
    agent_type: str
    memory_type: str
    task_summary: str
    context: str = ""
    resolution: str = ""
    confidence: float = 0.85


class RecallRequest(BaseModel):
    agent_type: str
    query_text: str
    top_k: int = 3


@app.get("/", response_class=HTMLResponse)
def root():
    """Visual dashboard — click 'Run Demo' to see Agent A -> Agent B live."""
    with open(os.path.join(_STATIC_DIR, "dashboard.html"), encoding="utf-8") as f:
        return f.read()


@app.get("/api")
def api_info():
    return {
        "service": "MemoryMesh",
        "description": "Shared memory layer for AI agents on CockroachDB",
        "endpoints": ["/agents/{agent_name}/remember", "/agents/{agent_name}/recall",
                      "/stats", "/demo/run", "/docs"],
    }


@app.post("/agents/{agent_name}/remember")
def remember(agent_name: str, req: RememberRequest):
    try:
        agent_id = memory_store.ensure_agent(agent_name, req.agent_type)
        memory_id = memory_store.remember(
            agent_id=agent_id,
            memory_type=req.memory_type,
            task_summary=req.task_summary,
            context=req.context,
            resolution=req.resolution,
            confidence=req.confidence,
        )
        return {"status": "stored", "memory_id": memory_id, "agent_id": agent_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/{agent_name}/recall")
def recall(agent_name: str, req: RecallRequest):
    try:
        agent_id = memory_store.ensure_agent(agent_name, req.agent_type)
        results = memory_store.recall(
            query_text=req.query_text,
            recalling_agent_id=agent_id,
            top_k=req.top_k,
        )
        return {"query": req.query_text, "results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
def stats():
    try:
        return memory_store.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/demo/run")
def run_demo():
    try:
        # Use the same 8s baseline as demo.py so the speedup comparison is
        # meaningful and not skewed by real network latency to CockroachDB
        # Cloud (which can itself take a couple of seconds).
        result_a = agent_a_devops.run(reasoning_seconds=8.0)
        result_b = agent_b_onboarding.run()
        return {"agent_a": result_a, "agent_b": result_b, "stats": memory_store.get_stats()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
