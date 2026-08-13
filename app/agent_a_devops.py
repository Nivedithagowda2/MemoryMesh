"""
Agent A: a DevOps agent. Hits a deployment failure, solves it, and writes
what it learned into the SHARED memory.
"""
import time

from . import memory_store

AGENT_NAME = "devops-agent"
AGENT_TYPE = "devops"

INCIDENT = {
    "task_summary": "EKS deployment failing with AccessDenied on ECR pull",
    "context": (
        "Pod stuck in ImagePullBackOff. kubectl describe pod shows: "
        "'Failed to pull image: AccessDenied: User is not authorized to "
        "perform ecr:GetAuthorizationToken'. Node IAM role is missing the "
        "ECR read policy."
    ),
    "resolution": (
        "Attach the AmazonEC2ContainerRegistryReadOnly managed policy to the "
        "EKS node IAM role, then rollout restart the deployment."
    ),
}


def run(reasoning_seconds: float = 8.0) -> dict:
    print(f"[{AGENT_NAME}] New incident: {INCIDENT['task_summary']}")
    print(f"[{AGENT_NAME}] Reasoning from scratch (no relevant memory exists yet)...")

    start = time.time()
    time.sleep(reasoning_seconds)
    elapsed = time.time() - start

    print(f"[{AGENT_NAME}] Root cause found in {elapsed:.1f}s: {INCIDENT['resolution']}")

    agent_id = memory_store.ensure_agent(AGENT_NAME, AGENT_TYPE)
    memory_id = memory_store.remember(
        agent_id=agent_id,
        memory_type="failure",
        task_summary=INCIDENT["task_summary"],
        context=INCIDENT["context"],
        resolution=INCIDENT["resolution"],
        confidence=0.9,
    )

    print(f"[{AGENT_NAME}] Wrote memory {memory_id} to shared MemoryMesh.\n")
    return {
        "agent": AGENT_NAME,
        "memory_id": memory_id,
        "reasoning_seconds": elapsed,
        "incident": INCIDENT,
    }


if __name__ == "__main__":
    run()
