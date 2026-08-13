# MemoryMesh

A shared, distributed memory layer for AI agents, backed by **CockroachDB**,
deployable on **AWS**.

## The idea in one paragraph

AI agents normally forget everything between runs, and agents built for
different purposes never share what they learn. MemoryMesh gives every
agent one shared memory: when Agent A solves a problem, it writes what it
learned into CockroachDB. When Agent B later hits something similar — even
worded completely differently — it searches that shared memory (via
CockroachDB's vector index) and gets the answer instantly instead of
reasoning from scratch.

---

## 🎥 Demo Video

Watch the MemoryMesh demo to see the complete system in action:

▶️ https://memorymesh-3hee.onrender.com

▶️ https://youtu.be/uqlHhuhQl70


The demo shows:
-  AI agent interaction
-  Persistent memory with CockroachDB
-  Amazon S3 integration
-  Memory storage and retrieval
-  FastAPI backend workflow


## Architecture

```
Agent A (DevOps)          Agent B (Onboarding)
      |                          |
      |  remember()              |  recall()
      v                          v
        CockroachDB (shared memory layer)
         - structured memory table
         - VECTOR column + vector index (semantic search)
         - memory_recalls audit log (proves cross-agent reuse)
      |
      v
FastAPI app  --(Mangum)-->  AWS Lambda / API Gateway
      |
      v
Amazon Bedrock (optional) — Titan embeddings for real semantic search
```

**CockroachDB tools used:**
1. **Distributed Vector Indexing** — the `memories` table's `embedding`
   column + `memories_embedding_idx`, queried with the `<->` operator.
2. **CockroachDB Cloud Managed MCP Server** — point Claude Code / Cursor at
   your cluster via MCP during development to inspect memory tables live.

**AWS service used:** AWS Lambda (serverless execution via
`lambda/lambda_handler.py`), optionally Amazon Bedrock for real embeddings.

---

## 1. Set up CockroachDB Cloud (free tier works)

1. Go to https://cockroachlabs.cloud/ and create a free Serverless cluster.
2. In the console, click **Connect**, copy the connection string.
3. Run the schema against it (easiest: paste the contents of `db/schema.sql`
   into the **SQL Shell** in the CockroachDB Cloud console).

## 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and paste your real `DATABASE_URL` (with your actual password).
Use `sslmode=require` unless you've specifically set up certificate
verification — `require` still fully encrypts the connection, it just
skips the extra identity-check step, which is fine for development.

Leave `USE_BEDROCK=false` for now — the app uses a local embedding fallback
so everything works without AWS credentials yet.

## 3. Install dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 4. Run the demo

```bash
python demo.py
```

Agent A works through an incident and writes a memory, then Agent B finds
that memory and solves a differently-worded problem instantly, followed by
a time-saved comparison and shared-memory stats. **This is the exact
script to screen-record for your submission video.**

## 5. Run the live API (for your "demo app URL")

```bash
 python -m uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs`, or:
```bash
curl -X POST http://localhost:8000/demo/run
curl http://localhost:8000/stats
```

## 6. Enable real Bedrock embeddings (optional, recommended for submission)

1. In AWS Console, enable model access for **Titan Embeddings** in Bedrock.
2. In `.env`, set:
   ```
   USE_BEDROCK=true
   AWS_ACCESS_KEY_ID=...
   AWS_SECRET_ACCESS_KEY=...
   AWS_REGION=us-east-1
   ```
3. Re-run `python demo.py`.

## 7. Deploy to AWS Lambda

```bash
pip install mangum
mkdir -p package
pip install -r requirements.txt -t package/
pip install mangum -t package/
cp -r app package/
cp lambda/lambda_handler.py package/
cd package && zip -r ../memorymesh_lambda.zip . && cd ..
```

In AWS Console: create a Lambda function (Python 3.12), upload the zip,
set handler to `lambda_handler.handler`, add your env vars, and enable a
**Function URL** for a public HTTPS endpoint.

## Using the CockroachDB MCP Server (dev-time tool)

CockroachDB Cloud Console → your cluster → **Connect** → **MCP Server** tab
gives you a config snippet for Claude Code / Cursor. This lets you inspect
the `memories` table and audit recalls directly from your coding assistant
— mention this as your second CockroachDB tool in your submission.

---

## Troubleshooting

**"root certificate file does not exist" / SSL errors on Windows:**
The simplest fix is using `sslmode=require` instead of `sslmode=verify-full`
in your `DATABASE_URL` — this still encrypts everything, it just skips
certificate identity verification. Fine for hackathon/dev use.

**Editing `.env` and changes don't seem to take effect:**
On Windows, Notepad can silently fail to save in some setups. Rewrite the
file directly from PowerShell instead:
```powershell
@"
DATABASE_URL=postgresql://user:password@host:26257/defaultdb?sslmode=require
AWS_REGION=us-east-1
USE_BEDROCK=false
"@ | Set-Content -Path .env -Encoding utf8
```

**Agent B doesn't find Agent A's memory (recall returns nothing):**
This was a real bug in earlier versions of this code — `memory_store.py`
was converting CockroachDB's `<->` operator (raw Euclidean/L2 distance)
into a similarity score with the wrong formula (`1 - distance`), which
badly underestimates similarity. Since embeddings here are unit-normalized,
the correct conversion is `similarity = 1 - (distance ** 2) / 2`. This is
already fixed in `app/memory_store.py` — if you see this issue again,
check that formula first.

---

## Project structure

```
memorymesh/
├── app/
│   ├── config.py
│   ├── embeddings.py          # Bedrock + local embedding fallback
│   ├── memory_store.py        # core remember()/recall() logic
│   ├── agent_a_devops.py      # Agent A: hits an incident, stores memory
│   ├── agent_b_onboarding.py  # Agent B: recalls Agent A's memory
│   └── main.py                # FastAPI app (live demo API)
├── db/
│   └── schema.sql
├── lambda/
│   └── lambda_handler.py
├── demo.py                    # end-to-end demo script (record this!)
├── requirements.txt
├── .env.example
└── README.md
```

## What to say in your submission narrative

- **CockroachDB tools:** Distributed Vector Indexing (semantic memory
  search across agents) + MCP Server (dev-time cluster inspection).
- **AWS services:** Lambda (serverless agent execution), optionally Bedrock.
- **What makes this "agentic memory," not just a database:** memory is
  written by one agent and consumed by a *different* agent it was never
  designed to talk to — the `memory_recalls` table is a real audit log
  proving cross-agent reuse happened, with measured time saved.
