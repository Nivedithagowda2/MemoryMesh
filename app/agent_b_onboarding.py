"""
Agent B: a completely different agent (developer-onboarding assistant).
Hits a problem worded differently from Agent A's incident, but rooted in
the same underlying cause. Checks the SHARED MemoryMesh before reasoning.
"""
import time

from . import memory_store

AGENT_NAME = "onboarding-agent"
AGENT_TYPE = "onboarding"

NEW_QUESTION = (
    "New hire's container won't start on our EKS cluster, image pull keeps failing "
    "with a permissions error from the container registry"
)

FRESH_REASONING_SECONDS = 8.0


def run() -> dict:
    print(f"[{AGENT_NAME}] New question: {NEW_QUESTION}")
    print(f"[{AGENT_NAME}] Checking shared MemoryMesh before reasoning from scratch...")

    agent_id = memory_store.ensure_agent(AGENT_NAME, AGENT_TYPE)

    start = time.time()
    results = memory_store.recall(
        query_text=NEW_QUESTION,
        recalling_agent_id=agent_id,
        top_k=3,
        assumed_fresh_reasoning_seconds=FRESH_REASONING_SECONDS,
    )
    elapsed = time.time() - start

    if results:
        best = results[0]
        print(
            f"[{AGENT_NAME}] Found a matching memory from '{best['source_agent']}' "
            f"(similarity {best['similarity']}) in {elapsed:.2f}s:"
        )
        print(f"[{AGENT_NAME}]   -> {best['resolution']}")
        print(
            f"[{AGENT_NAME}] Instant fix applied. Estimated time saved: "
            f"~{FRESH_REASONING_SECONDS - elapsed:.1f}s vs. reasoning from scratch.\n"
        )
    else:
        print(f"[{AGENT_NAME}] No relevant memory found — would reason from scratch here.\n")

    return {
        "agent": AGENT_NAME,
        "query": NEW_QUESTION,
        "recall_seconds": elapsed,
        "results": results,
    }


if __name__ == "__main__":
    run()
