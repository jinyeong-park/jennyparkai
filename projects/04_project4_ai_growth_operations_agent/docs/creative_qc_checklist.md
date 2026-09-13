# Creative QC Checklist

**Document status:** Synthetic portfolio simulation. This checklist applies to the Tablr growth operations simulation only.

**Purpose:** A practical, checkpoint-by-checkpoint checklist for reviewing Tablr creative briefs, production assets, and live ads before launch and after performance review. Use this checklist for every new creative that enters the experiment pipeline.

**Platform copy limits (quick reference):**

| Platform | Element | Recommended | Hard limit |
|---|---|---|---|
| Meta | Primary text | 125 chars | 500 chars |
| Meta | Headline | 27 chars | 40 chars |
| Meta | Description | 27 chars | 30 chars |
| TikTok | Caption | 150 chars | 2,200 chars |
| LinkedIn | Intro text | 150 chars | 600 chars |
| LinkedIn | Headline | 70 chars | 200 chars |
| Google Search | Headline | 30 chars max | 30 chars |
| Google Search | Description | 90 chars max | 90 chars |

---

## Before Brief Approval

### Strategic Alignment

- [ ] **Persona is defined** — The brief names exactly one `persona_id` from `data/config/personas.yaml`. Multi-persona briefs are not permitted without explicit split-testing structure.
- [ ] **Awareness stage is matched** — The creative approach (hook type, messaging territory, proof type) matches where this persona is in their decision journey (unaware / problem_aware / solution_aware / product_aware).
- [ ] **One hypothesis is stated** — The brief includes a specific, falsifiable hypothesis that predicts the outcome and explains the reasoning.
- [ ] **One variable is isolated** — If this brief is part of a controlled experiment, only one creative element changes vs. the control. All other elements are held constant.
- [ ] **Experiment ID is assigned** — The `experiment_id` field links to a row in `creative_testing_matrix.md`. Exploratory concepts without an experiment ID are labeled as such.
- [ ] **Control brief is identified** — If this is a variant, `control_id` references the control brief YAML. If this is the control, `control_id: null` is set explicitly.
- [ ] **Primary variable matches the experiment** — The `variable_tested` field in the brief is consistent with the corresponding experiment row in the testing matrix.
- [ ] **Messaging territory is declared** — One of the five Tablr territories is identified. Brief copy is evaluated against that territory's watch-outs in `docs/message_map.md`.
- [ ] **Activation hypothesis is included** — The brief explicitly explains why this hook will attract owners who will activate the product, not just owners who will click.

### Brand Compliance

- [ ] **Tone check** — Copy reads as direct, confident, empathetic, and practical. Does not use corporate jargon, marketing-speak, or condescending language toward owners.
- [ ] **No prohibited claims** — Copy does not include guaranteed results, specific revenue increase percentages, "#1 platform" superlatives, or unverified customer count claims.
- [ ] **No real competitor brand names** — Copy refers to "national brands," "the big chains," or "third-party delivery apps" — not DoorDash, Uber Eats, Yelp, or named restaurant chains.
- [ ] **Outcome claims are qualified** — Any claim that implies a specific result includes "results may vary" or is framed as hypothetical/example ("owners like you have seen...").
- [ ] **Approved claims only** — All advertising claims align with the approved claims list in `data/config/brand.yaml`.
- [ ] **Visual identity noted** — If a visual direction is specified, it aligns with Tablr's clean, modern, warm visual identity. Cold tech aesthetic, stock photo chains, and overly polished "enterprise SaaS" visuals are flagged.

---

## Before Creative Production

### Channel Spec Checks

- [ ] **Format is valid for the channel** — The `format` field in the brief is in the approved formats list for the specified channel in `data/config/channels.yaml`.
  - Meta: SHORT_FORM_VIDEO, STATIC_IMAGE, CAROUSEL, UGC_VIDEO, PRODUCT_DEMO
  - TikTok: SHORT_FORM_VIDEO, UGC_VIDEO, PRODUCT_DEMO
  - Google Search: Text-based (headline + description — no visual format field applies)
  - LinkedIn: STATIC_IMAGE, CAROUSEL, PRODUCT_DEMO
- [ ] **Primary text length** — For Meta: primary_text is within 500 chars (recommended: 125). For TikTok: caption within 2,200 chars (recommended: 150). For LinkedIn: intro text within 600 chars (recommended: 150).
- [ ] **Headline length** — For Meta: headline within 40 chars (recommended: 27). For LinkedIn: headline within 200 chars. For Google Search: every headline within 30 chars hard limit.
- [ ] **Google Search description** — Every description line within 90 chars hard limit. Count characters including spaces before finalizing.
- [ ] **Video length is appropriate** — Meta short-form: 15–30 seconds ideal. TikTok: 15–60 seconds. LinkedIn: 15–30 seconds. YouTube demo: 60–180 seconds.
- [ ] **Opening 3 seconds is specified** — Video briefs include a concrete description of what the viewer sees and hears in the first 3 seconds. "Hook, then brand" order — do not open with logo.
- [ ] **Visual concept is producer-actionable** — The `visual_concept` field is specific enough that a video producer or designer can execute without a follow-up brief. Vague descriptions ("show something exciting") are returned for revision.
- [ ] **CTA is in the approved list** — `cta` is one of: `start_free_trial`, `see_how_it_works`, `get_your_first_100_customers`, `learn_more`. Non-standard CTAs require approval.

### Message Match Check

- [ ] **Ad message → landing page message is aligned** — The primary hook and messaging territory of the ad match the primary headline and value proposition on the destination landing page. Owners who click a "stop losing to the chains" ad should land on a page that speaks to the same pain.
- [ ] **Landing page message is specified** — The `landing_page_message` field in the brief is completed. It states the primary message the owner sees when they arrive.
- [ ] **CTA matches funnel stage** — "Start free trial" is appropriate for product_aware or warm audiences. "See how it works" is appropriate for solution_aware or problem_aware audiences. "Get your first 100 customers" is appropriate for new_owner-specific messaging.

---

## Before Launch

### Claims Review

- [ ] **No unsubstantiated results in copy** — Every outcome reference in the copy is qualified or framed as a possibility, not a guarantee. "Owners like you have set up loyalty programs in under an hour" is acceptable. "You will get 100 new customers" is not.
- [ ] **No false urgency based on fabricated data** — FOMO hooks must not claim specific competitor behavior unless it is framed as hypothetical ("restaurant owners in your area may already be...").
- [ ] **No real people without consent** — No creative uses a real person's name, face, or story without authorization. In the simulation, all "owners" are explicitly hypothetical.
- [ ] **No competitor disparagement** — Copy does not directly attack or demean named competitors. Comparative claims ("unlike delivery apps that take 28%...") must be framed factually and hypothetically without naming specific companies.
- [ ] **Results may vary disclaimer** — All performance claims include or are accompanied by a "results may vary" qualifier at the appropriate placement for the channel format.

### Downstream Quality Check

- [ ] **Activation hypothesis is realistic** — The activation hypothesis in the brief describes a plausible path from click to campaign launch, not just from click to signup. The hook should attract owners who will use the product, not just register.
- [ ] **Hook is not misleading about product scope** — The creative should not imply features Tablr doesn't have, a pricing tier that doesn't match the actual offer, or a level of effort (e.g., "done for you") that the product does not provide in the trial tier.
- [ ] **Expected quality is documented** — The `expected_quality` field in the brief is set (high / medium / low) and justified by the `activation_hypothesis`. This sets the bar for post-launch evaluation.
- [ ] **FOMO hooks are flagged for extra monitoring** — If `hook_type: FEAR_OF_MISSING_OUT`, mark this creative for elevated attention in the week-2 activation rate review. FOMO hooks historically show high CTR with variable activation quality.

### Legal and Compliance

- [ ] **Results may vary** — Confirm this qualifier appears in or alongside any outcome claim in the final creative asset.
- [ ] **GDPR/CCPA awareness** — If the creative references audience data (e.g., "restaurant owners in your neighborhood"), confirm that audience targeting meets applicable privacy compliance standards. Flag for legal review if the creative implies personal data is being used to target.
- [ ] **No fabricated statistics in copy** — All numbers in copy are either approximate ("under an hour"), framed as hypothetical examples, or drawn from documented synthetic data that is clearly labeled as simulation. Do not present synthetic data results as real performance proof.
- [ ] **Trademark clearance for visual assets** — Confirm that any logos, UI screenshots, or app interfaces shown in production assets do not include third-party trademarked elements without permission.
- [ ] **Free trial terms are accurate** — If copy references "free trial," confirm the offer terms (14-day trial, no credit card required) are current and accurately stated.

---

## After Launch — Performance Review

*Run this review at 7 days and again at the end of the evaluation window.*

- [ ] **CTR is within expected range for this hook type** — Compare observed CTR to the expected range for the hook type and channel documented in `docs/hook_taxonomy.md`. Flag if significantly above or below.
  - CONTRAST / FOMO on Meta: expect 1.2–2.4%
  - OUTCOME / SOCIAL_PROOF on Meta: expect 0.8–1.8%
  - DEMONSTRATION on YouTube/LinkedIn: expect 0.3–1.0%
- [ ] **Activation rate is tracking above the baseline** — Monitor the `onboarding_completion_rate` for trial signups from this creative. If rate drops below 40% at the 7-day mark, flag for investigation.
- [ ] **Primary metric trend is directional** — CPAO should be trending toward or below the channel baseline. If CPAO is more than 30% above baseline after 5+ days of data, flag for creative review.
- [ ] **Guardrail metrics are stable** — Confirm `trial_signup_cvr`, `onboarding_completion_rate`, and `m1_retention` (where data is mature) are not significantly below the control or channel average.
- [ ] **Sample size check** — Confirm whether the minimum click threshold per variant has been reached. If not, mark as `INSUFFICIENT_DATA` and do not evaluate performance directionally.
- [ ] **Creative fatigue review — flag after week 4** — Set a reminder to review frequency and engagement rate at the 28-day mark. Signs of fatigue: CTR declining week-over-week for 2+ consecutive weeks while impression volume holds steady. If observed, add to the `REVISE` queue.
- [ ] **High-CTR, low-activation alert** — If the creative is generating strong CTR but `onboarding_completion_rate` or `campaign_launched` event rate is significantly below the baseline, flag as a "clicks but doesn't activate" pattern. This is a known synthetic data pattern and a key analytical signal in this project.

---

## Red Flags — Stop and Review

The following situations require immediate escalation before any further creative is produced, budget is adjusted, or experiment results are acted upon:

**1. An experiment shows a winner before reaching minimum click threshold.**
Premature winner declarations corrupt the experiment record and create false confidence. Mark as `INSUFFICIENT_DATA` and do not allow a budget or creative change until the threshold is met.

**2. Creative copy contains a specific performance claim that cannot be documented.**
Any copy referencing a specific customer count ("10,000 restaurants"), revenue figure, or success rate that is not traceable to the synthetic data with a visible simulation label is a compliance violation. Pull the creative, do not launch, and require revision.

**3. CPAO for a new creative is dramatically better than any other creative in the portfolio.**
An outlier that looks too good is a data quality signal, not a win. Check for tagging errors, attribution window mismatches, duplicate click counting, or targeting overlap with a concurrent conversion-optimized campaign before acting.

**4. A FOMO hook is generating a CTR above 3.0% on Meta but onboarding rate is below 30%.**
This is the "high-CTR, low-quality" synthetic pattern in the data. It indicates the hook is attracting clicks from owners who are not a genuine fit for the product. Pause spend increase on this creative and investigate who is actually clicking — audience composition may have drifted.

**5. Any creative references a real restaurant, a real owner by name, or a real competitor.**
This triggers an immediate legal review. No real company names, owner names, or identifiable businesses may appear in any Tablr creative, including this simulation. Pull the asset and require full revision before relaunching.
