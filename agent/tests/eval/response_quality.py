"""Local LLM-as-judge for `custom_response_quality` (see eval_config.yaml)."""

import os
import threading

from google import genai
from google.genai import types
from pydantic import BaseModel

_local = threading.local()


class _Verdict(BaseModel):
    score: int  # 1-5
    explanation: str


def _client() -> genai.Client:
    """One client per grading thread.

    The eval SDK grades cases on its own thread pool; this initialization runs once
    per thread. Avoids creating a new client for each eval case, which would re-do
    ADC and the TLS handshake every time. Each thread gets its own client, because
    google-auth freezes the SSL context after the first connection when a client
    certificate is present.
    """
    client = getattr(_local, "client", None)
    if client is None:
        # AI Studio (GEMINI_API_KEY) or Gemini platform (ADC).
        client = _local.client = genai.Client()
    return client


def _user_prompt(instance) -> str:
    """單輪案例用 prompt；多輪案例（沒有 prompt）取 agent_data 裡最後一則使用者訊息。"""
    if instance.get("prompt"):
        return str(instance["prompt"])
    last = ""
    for turn in (instance.get("agent_data") or {}).get("turns", []):
        for event in turn.get("events", []):
            if event.get("author") == "user":
                parts = (event.get("content") or {}).get("parts") or []
                last = "".join(p.get("text", "") for p in parts if isinstance(p, dict)) or last
    return last


def evaluate(instance):
    reference = instance.get("reference")
    rubric = (
        "Grade the agent's final response on a 1-5 scale (1 poor, 5 excellent) for "
        "accuracy, relevance, and clarity."
    )
    if reference:
        rubric += (
            " The response should agree with the expected answer below; penalize "
            "factual disagreement with it."
        )
    prompt = (
        f"You are an expert QA evaluator for an enterprise AI assistant. {rubric}\n"
        f"User Prompt (last user message): {_user_prompt(instance)}\n"
        f"Final Response: {instance.get('response', '')}\n"
    )
    if reference:
        prompt += f"Expected Answer (ground truth): {reference}\n"
    prompt += f"Full Agent Trace: {instance.get('agent_data', '')}\n"

    response = _client().models.generate_content(
        # 與 Agent 用同一個模型設定（AGENT_MODEL），可用 EVAL_JUDGE_MODEL 另外指定。
        model=os.environ.get("EVAL_JUDGE_MODEL") or os.environ.get("AGENT_MODEL", "gemini-3.8-flash"),
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0,  # deterministic grading
            response_mime_type="application/json",
            response_schema=_Verdict,  # guaranteed schema-valid JSON
        ),
    )
    verdict = response.parsed
    if verdict is None:  # model returned nothing usable
        return {"score": 0, "explanation": response.text or ""}
    return {"score": max(1, min(5, verdict.score)), "explanation": verdict.explanation}
