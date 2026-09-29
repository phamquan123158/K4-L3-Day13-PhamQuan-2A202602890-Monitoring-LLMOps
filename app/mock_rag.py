from __future__ import annotations

import time

from .incidents import STATE
from .pii import summarize_text
from .tracing import get_langfuse_client, observe

CORPUS = {
    "refund": ["Refunds are available within 7 days with proof of purchase."],
    "monitoring": ["Metrics detect incidents, logs identify affected requests, traces localize the root cause."],
    "policy": ["Do not expose PII in logs. Use sanitized summaries only."],
}


@observe(name="rag-retrieve", as_type="retriever", capture_input=False, capture_output=False)
def retrieve(message: str) -> list[str]:
    if STATE["tool_fail"]:
        raise RuntimeError("Vector store timeout")
    if STATE["rag_slow"]:
        time.sleep(2.5)
    lowered = message.lower()
    docs: list[str]
    for key, candidate_docs in CORPUS.items():
        if key in lowered:
            docs = candidate_docs
            break
    else:
        docs = ["No domain document matched. Use general fallback answer."]

    get_langfuse_client().update_current_span(
        metadata={
            "query_preview": summarize_text(message),
            "doc_count": len(docs),
            "retrieval_mode": "keyword",
        }
    )
    return docs
