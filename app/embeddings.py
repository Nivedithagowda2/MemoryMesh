"""
Turns text into a vector so CockroachDB can do semantic similarity search.

Two modes:
  - USE_BEDROCK=true  -> calls Amazon Bedrock Titan Embeddings (real AWS usage)
  - USE_BEDROCK=false -> local deterministic fallback (no AWS needed)
"""
import hashlib
import json
import numpy as np

from . import config

_bedrock_client = None


def _get_bedrock_client():
    global _bedrock_client
    if _bedrock_client is None:
        import boto3
        _bedrock_client = boto3.client("bedrock-runtime", region_name=config.AWS_REGION)
    return _bedrock_client


# Small synonym map so the offline fallback groups related terms into the
# same hash buckets (a real embedding model does this automatically).
_SYNONYMS = {
    "accessdenied": "permission", "unauthorized": "permission",
    "authorized": "permission", "permissions": "permission", "denied": "permission",
    "ecr": "registry", "registry": "registry",
    "image": "container", "pod": "container", "container": "container",
    "pull": "pull", "pulling": "pull", "imagepullbackoff": "pull",
    "eks": "cluster", "kubernetes": "cluster", "k8s": "cluster", "cluster": "cluster",
    "iam": "role", "role": "role",
    "fail": "fail", "failing": "fail", "failed": "fail", "error": "fail",
}


def _local_embedding(text: str) -> list[float]:
    """
    Deterministic offline embedding using a hashing trick, with synonym
    normalization so related terms land in the same buckets. Not a real
    semantic model, but good enough to prove the pipeline end-to-end.
    Vectors are unit-normalized (length 1).
    """
    dim = config.EMBEDDING_DIM
    vec = np.zeros(dim, dtype=np.float32)
    raw_tokens = text.lower().replace("/", " ").replace("-", " ").replace("_", " ").replace(":", " ").replace(".", " ").split()
    tokens = [_SYNONYMS.get(tok, tok) for tok in raw_tokens]
    for tok in tokens:
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if (h // dim) % 2 == 0 else -1.0
        vec[idx] += sign
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.tolist()


def _bedrock_embedding(text: str) -> list[float]:
    client = _get_bedrock_client()
    body = json.dumps({"inputText": text})
    response = client.invoke_model(
        modelId=config.BEDROCK_EMBED_MODEL_ID,
        body=body,
        contentType="application/json",
        accept="application/json",
    )
    result = json.loads(response["body"].read())
    embedding = result["embedding"]
    dim = config.EMBEDDING_DIM
    if len(embedding) > dim:
        embedding = embedding[:dim]
    elif len(embedding) < dim:
        embedding = embedding + [0.0] * (dim - len(embedding))
    # normalize so distance math stays consistent with the local fallback
    arr = np.array(embedding, dtype=np.float32)
    norm = np.linalg.norm(arr)
    if norm > 0:
        arr = arr / norm
    return arr.tolist()


def embed_text(text: str) -> list[float]:
    if config.USE_BEDROCK:
        return _bedrock_embedding(text)
    return _local_embedding(text)
