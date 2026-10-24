"""Read-only access to the EZStore OKF (Open Knowledge Format v0.2) bundle used by the advisor."""

import os
import re
from pathlib import Path

import yaml

DEFAULT_BUNDLE = Path(__file__).resolve().parent.parent / "knowledge" / "ezstore"
RESERVED = {"index.md", "log.md"}
_FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?(.*)\Z", re.S)


def bundle_dir() -> Path:
    return Path(os.environ.get("OKF_BUNDLE") or DEFAULT_BUNDLE)


def load_concepts() -> dict[str, dict]:
    """Concept ID (path without .md) -> {"meta": frontmatter dict, "body": markdown text}."""
    root = bundle_dir()
    concepts = {}
    for path in sorted(root.rglob("*.md")):
        if path.name in RESERVED:
            continue
        match = _FRONTMATTER.match(path.read_text(encoding="utf-8"))
        if not match:
            continue
        meta = yaml.safe_load(match.group(1)) or {}
        concept_id = path.relative_to(root).with_suffix("").as_posix()
        concepts[concept_id] = {"meta": meta, "body": match.group(2).strip()}
    return concepts


def trust_tier(meta: dict) -> str:
    """OKF trust tier: unverified / machine-confirmed / human-reviewed (spec section 5.3)."""
    verified = meta.get("verified")
    if not verified:
        return "unverified"
    entries = verified if isinstance(verified, list) else [verified]
    if any(str(e.get("by", "")).startswith("human:") for e in entries if isinstance(e, dict)):
        return "human-reviewed"
    return "machine-confirmed"


def list_knowledge() -> str:
    """List every concept in the EZStore knowledge bundle: concept ID, title and one-line description."""
    lines = []
    for concept_id, c in load_concepts().items():
        meta = c["meta"]
        lines.append(f"- {concept_id} | {meta.get('title', concept_id)} | {meta.get('description', '')}")
    return "\n".join(lines)


def search_knowledge(query: str) -> str:
    """Search the knowledge bundle for concepts about a topic (customer levels, pricing, a product name or number...).

    Args:
        query: words to look for, in Chinese or English, for example "VIP 報價因子" or "SP-001".
    """
    terms = [t.lower() for t in re.split(r"[\s,，、]+", query) if t]
    scored = []
    for concept_id, c in load_concepts().items():
        meta = c["meta"]
        head = f"{concept_id} {meta.get('title', '')} {meta.get('description', '')} {' '.join(meta.get('tags') or [])}".lower()
        body = c["body"].lower()
        score = sum(3 * head.count(t) + body.count(t) for t in terms)
        if score:
            scored.append((score, concept_id, meta))
    scored.sort(key=lambda s: (-s[0], s[1]))
    if not scored:
        return "No concept matches. Call list_knowledge to see every concept."
    return "\n".join(
        f"- {cid} | {meta.get('title', cid)} | {meta.get('description', '')}" for _, cid, meta in scored[:6]
    )


def read_concepts(concept_ids: list[str]) -> str:
    """Read several concepts in full in one call, each with its sources and trust tier.

    Args:
        concept_ids: concept IDs from the knowledge index, for example ["policies/quotation-lifecycle", "policies/copy-on-write"].
    """
    return "\n\n=====\n\n".join(read_concept(cid) for cid in concept_ids[:6])


def read_concept(concept_id: str) -> str:
    """Read one concept in full, with its sources and trust tier.

    Args:
        concept_id: the concept ID from list_knowledge or search_knowledge, for example "policies/customer-levels".
    """
    concepts = load_concepts()
    c = concepts.get(concept_id.strip().removesuffix(".md").lstrip("/"))
    if c is None:
        return f"Concept '{concept_id}' does not exist. Call search_knowledge or list_knowledge first."
    meta = c["meta"]
    sources = ", ".join(str(s.get("resource")) for s in meta.get("sources") or [] if isinstance(s, dict))
    return (
        f"Concept: {concept_id}\nType: {meta.get('type')}\nTitle: {meta.get('title', concept_id)}\n"
        f"Trust tier: {trust_tier(meta)}\nSources: {sources or 'none'}\n\n{c['body']}"
    )
