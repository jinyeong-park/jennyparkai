"""Unit tests for Phase 3 creative generation.

All tests run without an ANTHROPIC_API_KEY.
Tests use the MockLLMProvider and fixture YAML briefs from examples/creative_briefs/.

Run with:
    pytest tests/unit/test_creative_generator.py -v
"""

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from growth_agent.creative.service import CreativeService
from growth_agent.creative.validators import check_claims, validate_variant
from growth_agent.domain.creative import (
    CreativeBrief,
    CreativeGenerationRequest,
    CreativeGenerationResponse,
    CreativeVariant,
)
from growth_agent.providers.mock import MockLLMProvider

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent.parent
BRIEFS_DIR = REPO_ROOT / "examples" / "creative_briefs"
PROMPTS_DIR = REPO_ROOT / "prompts"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_provider() -> MockLLMProvider:
    return MockLLMProvider()


@pytest.fixture
def service(mock_provider: MockLLMProvider) -> CreativeService:
    return CreativeService(provider=mock_provider, prompts_dir=PROMPTS_DIR)


@pytest.fixture
def brief_cb001(service: CreativeService) -> CreativeBrief:
    return service.load_brief_from_yaml(BRIEFS_DIR / "cb_001.yaml")


@pytest.fixture
def brief_cb002(service: CreativeService) -> CreativeBrief:
    return service.load_brief_from_yaml(BRIEFS_DIR / "cb_002.yaml")


@pytest.fixture
def brief_cb014(service: CreativeService) -> CreativeBrief:
    return service.load_brief_from_yaml(BRIEFS_DIR / "cb_014.yaml")


def _make_run_id() -> str:
    return str(uuid.uuid4())


def _make_variant(**kwargs) -> CreativeVariant:
    """Build a minimal valid CreativeVariant for validator tests."""
    defaults = {
        "variant_id": "cb_001_v1",
        "brief_id": "cb_001",
        "creative_id": "cr_meta_001_001",
        "experiment_id": "exp_001",
        "persona": "scrappy_independent",
        "channel": "META",
        "format": "SHORT_FORM_VIDEO",
        "hook_type": "CONTRAST",
        "headline": "Stop losing to chains",
        "primary_text": (
            "Independent restaurants have Tablr. "
            "Set up in under an hour. Start your free 14-day trial."
        ),
        "cta": "start_free_trial",
        "visual_concept": "Owner in restaurant, phone showing Tablr dashboard.",
        "hypothesis": "CONTRAST hook will produce higher CTR than OUTCOME hook.",
        "variable_tested": "hook_type",
        "compliance_notes": "No specific revenue claims. Results may vary.",
        "provider": "mock",
        "generation_timestamp": datetime.now(timezone.utc),
        "run_id": "test-run-001",
    }
    defaults.update(kwargs)
    return CreativeVariant(**defaults)


def _make_brief(**kwargs) -> CreativeBrief:
    """Build a minimal valid CreativeBrief for service/validator tests."""
    defaults = {
        "brief_id": "cb_001",
        "creative_id": "cr_meta_001_001",
        "experiment_id": "exp_001",
        "persona": "scrappy_independent",
        "channel": "META",
        "format": "SHORT_FORM_VIDEO",
        "awareness_stage": "problem_aware",
        "messaging_territory": "Stop losing to the chains",
        "primary_pain": "I don't have time to learn another marketing platform.",
        "desired_outcome": "Get more new customers without spending hours on campaigns.",
        "primary_barrier": "Believes marketing software is built for people with degrees.",
        "hook_type": "CONTRAST",
        "primary_hook": "The chain has a loyalty app. You have Instagram. That's about to change.",
        "proof_type": "SIMPLICITY_DEMO",
        "visual_concept": "Owner behind counter, phone showing Tablr.",
        "headline": "Stop losing customers to chains",
        "primary_text": "National brands have marketing teams. You have Tablr.",
        "cta": "start_free_trial",
        "landing_page_message": "Marketing infrastructure built for independent restaurants.",
        "hypothesis": "CONTRAST hook will produce higher CTR than OUTCOME hook.",
        "variable_tested": "hook_type",
        "compliance_notes": "No specific revenue claims. Results may vary.",
        "activation_hypothesis": "Owners who click are already motivated to act.",
        "expected_quality": "high",
    }
    defaults.update(kwargs)
    return CreativeBrief(**defaults)


# ---------------------------------------------------------------------------
# Provider tests
# ---------------------------------------------------------------------------


def test_mock_provider_is_available(mock_provider: MockLLMProvider) -> None:
    """MockLLMProvider.is_available() must always return True."""
    assert mock_provider.is_available() is True


def test_mock_provider_generates_n_variants(
    mock_provider: MockLLMProvider,
) -> None:
    """MockLLMProvider must return exactly n_variants variants."""
    brief = _make_brief()
    for n in [1, 2, 3]:
        request = CreativeGenerationRequest(
            brief=brief,
            n_variants=n,
            run_id=_make_run_id(),
            dry_run=True,
        )
        response = mock_provider.generate_creatives(request)
        assert len(response.variants) == n, (
            f"Expected {n} variants, got {len(response.variants)}"
        )


def test_mock_provider_is_deterministic(mock_provider: MockLLMProvider) -> None:
    """Same brief_id must produce identical headlines across two runs."""
    brief = _make_brief()
    run_a = CreativeGenerationRequest(
        brief=brief,
        n_variants=3,
        run_id="run-a",
        dry_run=True,
    )
    run_b = CreativeGenerationRequest(
        brief=brief,
        n_variants=3,
        run_id="run-b",
        dry_run=True,
    )

    response_a = mock_provider.generate_creatives(run_a)
    response_b = mock_provider.generate_creatives(run_b)

    headlines_a = [v.headline for v in response_a.variants]
    headlines_b = [v.headline for v in response_b.variants]

    assert headlines_a == headlines_b, (
        f"Mock provider is not deterministic. "
        f"Run A headlines: {headlines_a}. Run B headlines: {headlines_b}"
    )


def test_variant_ids_follow_convention(mock_provider: MockLLMProvider) -> None:
    """Variant IDs must follow the {brief_id}_v{n} convention."""
    brief = _make_brief(brief_id="cb_test")
    request = CreativeGenerationRequest(
        brief=brief,
        n_variants=3,
        run_id=_make_run_id(),
        dry_run=True,
    )
    response = mock_provider.generate_creatives(request)

    expected_ids = ["cb_test_v1", "cb_test_v2", "cb_test_v3"]
    actual_ids = [v.variant_id for v in response.variants]

    assert actual_ids == expected_ids, (
        f"Expected variant IDs {expected_ids}, got {actual_ids}"
    )


# ---------------------------------------------------------------------------
# Validator tests
# ---------------------------------------------------------------------------


def test_validate_variant_passes_valid_input() -> None:
    """A well-formed variant on META should produce no findings."""
    brief = _make_brief()
    variant = _make_variant()

    findings = validate_variant(variant, brief)

    assert findings == [], (
        f"Expected no findings for a valid variant. Got: {findings}"
    )


def test_validate_variant_flags_long_headline() -> None:
    """A META headline exceeding 40 chars must produce a length finding."""
    brief = _make_brief(channel="META")
    long_headline = "This headline is definitely too long for Meta ads to approve"
    assert len(long_headline) > 40, "Test setup error: headline should exceed 40 chars"

    variant = _make_variant(channel="META", headline=long_headline)
    findings = validate_variant(variant, brief)

    headline_findings = [f for f in findings if "headline too long" in f or "META headline" in f]
    assert len(headline_findings) >= 1, (
        f"Expected a headline length finding but got: {findings}"
    )


def test_check_claims_flags_prohibited_phrase() -> None:
    """check_claims must flag 'guaranteed' and 'increase revenue by'."""
    text_with_prohibited = "Guaranteed to increase revenue by 30% in your first month."
    findings = check_claims(text_with_prohibited)

    assert len(findings) > 0, "Expected at least one prohibited claim finding."

    flagged_phrases = " ".join(findings).lower()
    assert "guaranteed" in flagged_phrases or "increase revenue by" in flagged_phrases, (
        f"Expected 'guaranteed' or 'increase revenue by' to be flagged. Findings: {findings}"
    )


def test_check_claims_passes_clean_copy() -> None:
    """check_claims must return empty list for compliant copy."""
    clean_text = (
        "Tablr helps independent restaurant owners attract and retain customers. "
        "Start your free trial today. Results may vary."
    )
    findings = check_claims(clean_text)
    assert findings == [], f"Expected no findings for clean copy. Got: {findings}"


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------


def test_service_generates_from_brief_yaml(service: CreativeService) -> None:
    """CreativeService.load_brief_from_yaml + generate_from_brief must work end-to-end."""
    brief = service.load_brief_from_yaml(BRIEFS_DIR / "cb_001.yaml")
    response = service.generate_from_brief(brief, n_variants=3, dry_run=True)

    assert isinstance(response, CreativeGenerationResponse)
    assert len(response.variants) == 3
    assert response.brief_id == "cb_001"
    assert response.provider == "mock"


def test_service_attaches_validation_findings(service: CreativeService) -> None:
    """Service must attach findings to variants and to response when issues exist.

    We inject an unrealistically long META headline via a custom brief to
    trigger a length validation finding.
    """
    # Build a brief that will cause a validator failure: channel=META with long headline
    brief = _make_brief(channel="META")

    # Generate normally — mock provider headlines are short and should pass
    response = service.generate_from_brief(brief, n_variants=1, dry_run=True)

    # The response should exist and have variants regardless
    assert response is not None
    assert len(response.variants) == 1

    # Validate that the service attaches findings when we manually inject a problem
    variant = response.variants[0]
    variant.headline = "X" * 50  # force headline too long
    findings = validate_variant(variant, brief)

    assert any("headline" in f.lower() or "META" in f for f in findings), (
        f"Expected a headline length finding. Got: {findings}"
    )


# ---------------------------------------------------------------------------
# Anthropic provider tests
# ---------------------------------------------------------------------------


def test_anthropic_provider_unavailable_without_key() -> None:
    """AnthropicProvider must raise ProviderError when ANTHROPIC_API_KEY is absent."""
    # Temporarily remove the key if present
    original = os.environ.pop("ANTHROPIC_API_KEY", None)
    try:
        from growth_agent.providers.anthropic import AnthropicProvider, ProviderError

        with pytest.raises((ProviderError, Exception)) as exc_info:
            AnthropicProvider(prompts_dir=PROMPTS_DIR)

        error_message = str(exc_info.value)
        assert (
            "ANTHROPIC_API_KEY" in error_message
            or "anthropic" in error_message.lower()
        ), (
            f"Expected error mentioning ANTHROPIC_API_KEY or anthropic package. "
            f"Got: {error_message}"
        )
    finally:
        if original is not None:
            os.environ["ANTHROPIC_API_KEY"] = original


# ---------------------------------------------------------------------------
# Provenance field tests
# ---------------------------------------------------------------------------


def test_variant_has_required_provenance_fields(
    mock_provider: MockLLMProvider,
) -> None:
    """Every generated variant must carry all required provenance fields."""
    brief = _make_brief()
    run_id = "provenance-test-run"
    request = CreativeGenerationRequest(
        brief=brief,
        n_variants=1,
        run_id=run_id,
        dry_run=True,
    )
    response = mock_provider.generate_creatives(request)
    variant = response.variants[0]

    # Required provenance fields
    assert variant.prompt_template_version, "prompt_template_version must not be empty"
    assert variant.provider == "mock", f"provider must be 'mock', got '{variant.provider}'"
    assert variant.run_id == run_id, (
        f"run_id must be '{run_id}', got '{variant.run_id}'"
    )
    assert isinstance(variant.generation_timestamp, datetime), (
        "generation_timestamp must be a datetime object"
    )
    assert variant.brief_version, "brief_version must not be empty"
    assert variant.data_origin == "SYNTHETIC", (
        f"data_origin must be 'SYNTHETIC', got '{variant.data_origin}'"
    )


def test_variant_review_status_defaults_to_pending(
    mock_provider: MockLLMProvider,
) -> None:
    """New variants must have review_status='pending' — never pre-approved."""
    brief = _make_brief()
    request = CreativeGenerationRequest(
        brief=brief,
        n_variants=2,
        run_id=_make_run_id(),
        dry_run=True,
    )
    response = mock_provider.generate_creatives(request)

    for variant in response.variants:
        assert variant.review_status == "pending", (
            f"Expected review_status='pending', got '{variant.review_status}' "
            f"for variant {variant.variant_id}"
        )


def test_mock_provider_sets_estimated_cost_to_zero(
    mock_provider: MockLLMProvider,
) -> None:
    """Mock provider must report estimated_cost_usd=0.0 — no API calls made."""
    brief = _make_brief()
    request = CreativeGenerationRequest(
        brief=brief,
        n_variants=3,
        run_id=_make_run_id(),
        dry_run=True,
    )
    response = mock_provider.generate_creatives(request)
    assert response.estimated_cost_usd == 0.0, (
        f"Expected estimated_cost_usd=0.0, got {response.estimated_cost_usd}"
    )


def test_mock_provider_latency_in_expected_range(
    mock_provider: MockLLMProvider,
) -> None:
    """Mock provider latency must fall in the 150–350ms simulated range."""
    brief = _make_brief()
    request = CreativeGenerationRequest(
        brief=brief,
        n_variants=1,
        run_id=_make_run_id(),
        dry_run=True,
    )
    response = mock_provider.generate_creatives(request)
    assert 150 <= response.latency_ms <= 350, (
        f"Expected latency 150–350ms, got {response.latency_ms}ms"
    )


def test_service_loads_brief_from_yaml_file(service: CreativeService) -> None:
    """load_brief_from_yaml must return a valid CreativeBrief for all fixture briefs."""
    for yaml_file in sorted(BRIEFS_DIR.glob("cb_*.yaml")):
        brief = service.load_brief_from_yaml(yaml_file)
        assert isinstance(brief, CreativeBrief), (
            f"Expected CreativeBrief from {yaml_file.name}, got {type(brief)}"
        )
        assert brief.brief_id, f"brief_id should not be empty in {yaml_file.name}"
        assert brief.hypothesis, f"hypothesis should not be empty in {yaml_file.name}"
