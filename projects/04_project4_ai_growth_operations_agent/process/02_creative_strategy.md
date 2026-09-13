# Phase 2 — Creative Strategy

## Purpose

Translate audience hypotheses into structured creative briefs that can be tested systematically — one variable at a time.

## Personas

| Persona | Core motivation | Primary barrier |
|---|---|---|
| Scrappy Independent | Survive without big-chain resources | Skeptical of tools that cost money without clear ROI |
| Growth-Minded | Scale to multiple locations | Needs proof from peers, not just promises |
| New Owner | Get first customers fast | Overwhelmed, doesn't know where to start |
| Delivery-Heavy | Reduce third-party commission dependency | Locked into Uber Eats / DoorDash, unsure how to escape |
| Community-Focused | Build loyal local customer base | Doesn't want to feel like a faceless corporate chain |

## Hook Taxonomy

| Hook Type | Core mechanic | Best for |
|---|---|---|
| CONTRAST | Before/after, us vs them | Scrappy Independent (skeptic) |
| OUTCOME | Revenue, growth numbers | Growth-Minded |
| SOCIAL_PROOF | Peer restaurant success | Growth-Minded, Community-Focused |
| DEMONSTRATION | Product walkthrough | New Owner |
| FEAR_OF_MISSING_OUT | Competitors already using it | Delivery-Heavy |

## Creative Briefs

16 briefs in `examples/creative_briefs/` (cb_001.yaml through cb_016.yaml).

Coverage:
- **Channels**: META ×9, TikTok ×3, Google Search ×1, LinkedIn ×3
- **Personas**: all 5 represented
- **Hook types**: all 5 represented
- **Each brief defines**: hypothesis, single primary variable tested, pain point, desired outcome, compliance notes

## Key Design Principle

Every brief identifies one and only one `variable_tested`. This makes it possible to attribute performance differences to a specific creative decision — not a mix of headline, format, and audience changes.

## Artifacts

| File | Purpose |
|---|---|
| `config/personas.yaml` | Structured persona definitions |
| `config/brand.yaml` | Brand voice, tone, prohibited claims |
| `config/channels.yaml` | Channel-specific format and copy constraints |
| `docs/message_map.md` | Pain → barrier → value prop → proof matrix |
| `docs/hook_taxonomy.md` | Hook definitions with examples |
| `docs/creative_testing_matrix.md` | Which briefs test which variable per channel |
| `docs/creative_qc_checklist.md` | Review checklist before brief approval |
