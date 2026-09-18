# Phase 3 — AI Creative Generation

## Purpose

Generate structured ad copy from approved creative briefs using an LLM, with validation that prevents non-compliant output from reaching downstream campaign objects.

## Flow

```text
CreativeBrief (YAML)
  → CreativeService
  → LLMProvider (Mock or Anthropic)
  → CreativeVariant (headline, primary_text, cta, visual_concept)
  → validators (length, CTA allowlist, prohibited phrases)
  → CreativeGenerationResponse (variants + findings)
```

## Provider Abstraction

Two providers implement the same `LLMProvider` Protocol:

| Provider | When to use | API key needed |
|---|---|---|
| `MockLLMProvider` | Tests, CI, development | No |
| `AnthropicProvider` | Live generation | Yes (claude-haiku-4-5) |

Switching providers requires only a config change — no code changes.

## Validation Rules

| Check | Rule |
|---|---|
| META headline length | ≤ 40 characters |
| TikTok caption length | ≤ 150 characters |
| Google Search headline | ≤ 30 characters |
| LinkedIn intro text | ≤ 150 characters |
| CTA | Must be in approved list (4 values) |
| Prohibited phrases | "guaranteed", "100% proven", "increase revenue by", "#1 restaurant", "best restaurant marketing", "results guaranteed" |
| Brief ID consistency | variant.brief_id must match brief.brief_id |
| Hypothesis preserved | Must be carried forward from brief |

## Evaluation Dataset

`docs/evals/creative_generation_cases.yaml` — 16 cases covering:
- Valid generation (expected to pass)
- Prohibited claim detection (expected to flag)
- Headline too long (expected to flag)
- CTA not on approved list (expected to flag)

## Tests

16 unit tests in `tests/unit/test_creative_generator.py` — all pass without an API key using MockLLMProvider.

## Key Design Decision

Valid JSON output from the LLM is not enough. A creative variant must pass structural validation (length, CTA), claim checking (prohibited phrases), and brief-ID consistency before it is considered acceptable. Rejected variants are returned with `review_status="pending"` and a list of findings — they are never silently dropped.
