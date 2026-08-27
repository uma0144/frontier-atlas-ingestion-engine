"""
Unit tests for deterministic entity resolution and canonicalization.
"""

from src.resolver.entity_resolver import EntityResolver


def test_seed_entity_resolution():
    resolver = EntityResolver()

    # Test cases mentioned in specification: OpenAI, OpenAI, Inc., Open AI -> OpenAI
    canonical1, conf1, m1 = resolver.resolve("OpenAI, Inc.")
    assert canonical1 == "OpenAI"
    assert conf1 >= 0.95

    canonical2, conf2, m2 = resolver.resolve("Open AI")
    assert canonical2 == "OpenAI"
    assert conf2 >= 0.95

    canonical3, conf3, m3 = resolver.resolve("OpenAI LLC")
    assert canonical3 == "OpenAI"

    # Test Anthropic variants
    canonical4, conf4, m4 = resolver.resolve("Anthropic PBC")
    assert canonical4 == "Anthropic"

    # Test Mistral variants
    canonical5, conf5, m5 = resolver.resolve("Mistral.ai")
    assert canonical5 == "Mistral AI"

    # Test Hugging Face
    canonical6, conf6, m6 = resolver.resolve("HuggingFace Inc")
    assert canonical6 == "Hugging Face"


def test_rule_based_legal_suffix_cleaning():
    resolver = EntityResolver()

    canonical, conf, method = resolver.resolve("Synthetix Technologies Inc.")
    assert "Inc" not in canonical
    assert "Technologies" not in canonical
    assert "Synthetix" in canonical


def test_mapping_log_recording():
    resolver = EntityResolver()
    resolver.resolve("Scale AI, Inc.", entity_type="STARTUP")
    resolver.resolve("Groq Inc", entity_type="STARTUP")

    logs = resolver.get_audit_logs()
    assert len(logs) >= 2
    raw_names = [l.raw_name for l in logs]
    assert "Scale AI, Inc." in raw_names
    assert "Groq Inc" in raw_names
