"""Knowledge tools over the real OKF bundle (no LLM, no network)."""

from sales_advisor.knowledge import list_knowledge, load_concepts, read_concept, search_knowledge, trust_tier


def test_bundle_loads_every_concept_with_a_type():
    concepts = load_concepts()
    assert len(concepts) == 26
    assert all(c["meta"].get("type") for c in concepts.values())


def test_list_knowledge_has_one_line_per_concept():
    assert len(list_knowledge().splitlines()) == 26


def test_search_finds_customer_levels_first():
    assert search_knowledge("VIP 報價因子").splitlines()[0].startswith("- policies/customer-levels")


def test_search_by_product_number():
    assert search_knowledge("SP-001").splitlines()[0].startswith("- products/SP-001")


def test_read_concept_includes_sources_and_trust_tier():
    text = read_concept("policies/customer-levels")
    assert "Trust tier: unverified" in text
    assert "backend/models/customer.go" in text
    assert "0.80" in text


def test_read_unknown_concept_says_so():
    assert "does not exist" in read_concept("policies/nope")


def test_trust_tiers():
    assert trust_tier({}) == "unverified"
    assert trust_tier({"verified": {"by": "okf-checker/1", "at": "2026-10-24T00:00:00Z"}}) == "machine-confirmed"
    assert trust_tier({"verified": [{"by": "human:yabes", "at": "2026-10-24T00:00:00Z"}]}) == "human-reviewed"
