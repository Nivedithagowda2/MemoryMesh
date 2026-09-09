"""
MemoryMesh end-to-end demo. Run after setting up .env (see README.md).
This is the exact script to screen-record for your submission video.
"""
from app import agent_a_devops, agent_b_onboarding, memory_store  


def main():        
    print("=" * 70) 
    print("MEMORYMESH DEMO — shared memory across two independent AI agents")
    print("=" * 70)
    print()

    print("STEP 1: Agent A (DevOps) hits a real incident for the first time.\n")
    result_a = agent_a_devops.run(reasoning_seconds=8.0)

    print("-" * 70)
    print("STEP 2: Agent B (Onboarding) — a totally different agent, different")
    print("purpose — hits a similar problem, worded differently.\n")
    result_b = agent_b_onboarding.run()

    print("-" * 70)
    print("RESULT")
    print(f"  Agent A reasoning time (no memory available):  {result_a['reasoning_seconds']:.1f}s")
    if result_b["results"]:
        print(f"  Agent B recall time (memory available):         {result_b['recall_seconds']:.2f}s")
        speedup = result_a["reasoning_seconds"] / max(result_b["recall_seconds"], 0.001)
        print(f"  Speedup from shared memory:                     ~{speedup:.0f}x faster")
    else:
        print("  Agent B found no memory (check DB connection / data).")

    print()
    print("-" * 70)
    print("MEMORYMESH STATS (shared CockroachDB memory layer)")
    stats = memory_store.get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print("=" * 70)


if __name__ == "__main__":
    main()
