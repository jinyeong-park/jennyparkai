# Creative Testing Matrix

**Document status:** Synthetic portfolio simulation. All experiments, creative IDs, and performance expectations are hypothetical.

---

## Testing Philosophy

Tablr's creative testing program is built on one foundational rule: **one variable per experiment**. Every controlled experiment in this matrix isolates a single primary variable — hook type, format, message territory, CTA, persona targeting, landing page match, or channel — while holding all other factors as constant as operationally possible. This discipline is what converts creative iteration into learnable evidence.

Each experiment includes a control creative and one or more variants. The control is the current baseline or best-known version. Variants change only the primary variable. Primary metric is always **cost_per_activated_owner (CPAO)** — not CTR, not trial CAC — because Tablr's business problem is acquisition quality, not raw volume. Guardrail metrics catch unintended consequences: a variant that reduces CPAO but also collapses onboarding rates has not solved the problem.

Experiments run for a minimum number of clicks per variant before evaluation to prevent premature winner calls. Evaluation windows are set by channel (Meta: 14 days, Google/LinkedIn: 21 days). Experiments with insufficient data are marked `INSUFFICIENT_DATA` — this is not a failure state; it is an honest representation of evidence quality.

**The matrix is a planning document, not a scoreboard.** Experiments should be read alongside the experiment readout for each row when results are available.

---

## Experiment Matrix

| experiment_id | business_question | hypothesis | variable_tested | control_creative | variant_creatives | channel | persona | primary_metric | guardrail_metrics | min_clicks_per_variant | eval_window_days | status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| exp_001 | Does a CONTRAST hook or an OUTCOME hook produce a lower cost per activated owner for scrappy independent owners on Meta? | CONTRAST hook ("You vs. the chains") will generate higher CTR but similar or lower CPAO compared to OUTCOME because scrappy independents respond to competitive frustration as a primary motivator — but OUTCOME may attract a higher-intent subset. | hook_type | cr_meta_001_001 (CONTRAST, SHORT_FORM_VIDEO) | cr_meta_006_003 (OUTCOME, SHORT_FORM_VIDEO) | META | scrappy_independent | cost_per_activated_owner | ctr, trial_signup_cvr, onboarding_completion_rate | 300 | 14 | OBSERVE |
| exp_002 | For new restaurant owners on Meta, does a CONTRAST hook or a SOCIAL_PROOF hook produce better downstream activation? | SOCIAL_PROOF will outperform CONTRAST for new_owner on activation rate, because new owners respond more to peer validation than to competitive framing — they don't yet have competitors to fear, but they do want to see other new owners succeed. | hook_type | cr_meta_005_001 (CONTRAST, SHORT_FORM_VIDEO) | cr_meta_004_003 (SOCIAL_PROOF, SHORT_FORM_VIDEO) | META | new_owner | cost_per_activated_owner | ctr, trial_signup_cvr, onboarding_completion_rate, m1_retention | 300 | 14 | OBSERVE |
| exp_003 | Does a short-form video outperform a static image for growth_minded operators on Meta? | SHORT_FORM_VIDEO will produce a lower CPAO than STATIC_IMAGE for growth_minded operators because this persona evaluates tools visually and responds to seeing the product in action — static images can communicate the value prop but can't demonstrate workflow efficiency. | creative_format | cr_meta_006_001 (OUTCOME, STATIC_IMAGE) | cr_meta_004_002 (OUTCOME, PRODUCT_DEMO) | META | growth_minded | cost_per_activated_owner | ctr, trial_signup_cvr, onboarding_completion_rate | 300 | 14 | OBSERVE |
| exp_004 | On TikTok for scrappy independent owners, does "Stop losing to the chains" (CONTRAST territory) or "Marketing that runs itself" (SIMPLICITY territory) produce a lower CPAO? | "Marketing that runs itself" will produce a lower CPAO on TikTok for scrappy_independent because on a short-form native video platform, the simplicity promise is more immediately credible and actionable — the competitive framing works better with more visual context than TikTok typically provides. | messaging_territory | cr_tiktok_015_002 (CONTRAST, scrappy_independent) | cr_tiktok_016_002 (OUTCOME, scrappy_independent) | TIKTOK | scrappy_independent | cost_per_activated_owner | ctr, trial_signup_cvr, onboarding_completion_rate | 300 | 14 | OBSERVE |
| exp_005 | Which CTA — "Start free trial," "Get your first 100 customers," or "See how it works" — produces the highest trial signup CVR and activation rate for new restaurant owners on Meta? | "Get your first 100 customers" will outperform both alternatives for new_owner because it is outcome-specific, directly matches this persona's primary desired outcome, and lowers the perceived commitment compared to "start free trial" which implies a decision is being made. | cta | cr_meta_002_001 (OUTCOME, PRODUCT_DEMO, start_free_trial control) | cr_meta_009_003 (SOCIAL_PROOF, see_how_it_works); cr_meta_009_002 (CONTRAST, get_your_first_100_customers) | META | new_owner | cost_per_activated_owner | ctr, trial_signup_cvr, onboarding_completion_rate | 300 | 14 | OBSERVE |
| exp_006 | When the same creative is shown to scrappy_independent vs. delivery_heavy audiences on Meta, does persona targeting meaningfully change CPAO? | The delivery_heavy audience will show lower CPAO when exposed to a generic contrast creative, because delivery-heavy owners have a more acute and specific pain (commission drain) that makes them more likely to activate once they reach the product — even without messaging tailored to their use case. | persona_targeting | cr_meta_007_002 (CONTRAST, DELIVERY_HEAVY audience) | cr_meta_001_001 (FEAR_OF_MISSING_OUT, SCRAPPY_INDEPENDENT audience) | META | scrappy_independent vs. delivery_heavy | cost_per_activated_owner | ctr, trial_signup_cvr, onboarding_completion_rate, m1_retention | 300 | 14 | OBSERVE |
| exp_007 | Does message match between the Meta ad and the landing page improve trial signup CVR and activation rate for scrappy independent owners? | Matched landing page messaging (ad says "stop losing to the chains" → landing page leads with same framing) will produce higher trial signup CVR and onboarding completion than mismatched messaging because cognitive continuity reduces friction and confirms the owner arrived in the right place. | landing_page_message_match | cr_meta_001_001 (CONTRAST hook → matched landing page) | cr_meta_005_003 (FEAR_OF_MISSING_OUT hook → generic landing page) | META | scrappy_independent | cost_per_activated_owner | trial_signup_cvr, onboarding_completion_rate, ctr | 300 | 14 | OBSERVE |
| exp_008 | Does the same creative concept produce meaningfully different CPAO on Meta vs. TikTok for community_focused owners? | TikTok will show higher CTR but lower activation quality for community_focused owners, because TikTok's algorithmic discovery exposes the creative to a broader, less-targeted audience — and community_focused owners on TikTok are harder to target precisely. Meta's interest-based targeting will reach a more qualified subset. | channel | cr_meta_008_001 (SOCIAL_PROOF, SHORT_FORM_VIDEO, community_focused) | cr_tiktok_016_003 (SOCIAL_PROOF, CAROUSEL, scrappy_independent as proxy) | META vs. TIKTOK | community_focused | cost_per_activated_owner | ctr, trial_signup_cvr, onboarding_completion_rate, m1_retention | 300 | 14 | OBSERVE |
| exp_009 | On YouTube, does a DEMONSTRATION hook or an OUTCOME hook produce a lower CPAO for growth_minded operators? | DEMONSTRATION will outperform OUTCOME on YouTube for growth_minded because this persona is actively evaluating solutions and responds to seeing the product workflow — YouTube's longer dwell time supports a full demonstration, while OUTCOME hooks can feel underdeveloped without sufficient follow-through in a long-form context. | hook_type | cr_meta_004_002 (OUTCOME, PRODUCT_DEMO — used as YouTube analog) | cr_linkedin_030_001 (DEMONSTRATION, STATIC_IMAGE — product walkthrough) | LINKEDIN | growth_minded | cost_per_activated_owner | ctr, trial_signup_cvr, onboarding_completion_rate, m1_retention | 150 | 21 | OBSERVE |
| exp_010 | Does a new LinkedIn creative concept for growth_minded operators show sufficient evidence to evaluate performance vs. the current control? | Insufficient evidence — this creative is in early learning phase. Minimum click threshold has not been reached. No directional conclusion can be drawn from current data. | new_creative | cr_linkedin_029_001 (CONTRAST, STATIC_IMAGE — current control) | cr_linkedin_030_003 (FEAR_OF_MISSING_OUT, SHORT_FORM_VIDEO — new concept) | LINKEDIN | growth_minded | cost_per_activated_owner | ctr, trial_signup_cvr, onboarding_completion_rate | 150 | 21 | INSUFFICIENT_DATA |

---

## Reading the Matrix

**experiment_id:** Unique identifier that links to experiment readouts, creative briefs (via `experiment_id` in YAML), and the recommendation agent output.

**business_question:** The strategic question the experiment answers. Every test should be traceable to a business priority.

**hypothesis:** A falsifiable prediction — not a hope. Hypotheses state the expected direction and the reasoning behind it. If the experiment contradicts the hypothesis, that is still a learning.

**variable_tested:** The single thing that changes between control and variant. If more than one thing changes, the experiment cannot attribute the outcome to the variable of interest.

**control_creative:** The current baseline or best-known version. Control creative IDs reference real rows in `dim_creatives.csv`. In early experiments, the control may be the first creative tested in a concept category.

**variant_creatives:** One or more creative IDs that change only the primary variable. Multiple variants are allowed in CTA tests (exp_005) because each is compared independently to the same control.

**channel:** The delivery platform. Channel selection affects minimum evidence thresholds and evaluation windows.

**persona:** The audience segment the experiment targets. In exp_006, persona targeting is itself the variable, so both are listed.

**primary_metric:** Always `cost_per_activated_owner`. A test that optimizes only for CTR or trial_signup_cvr without checking downstream activation quality has not answered Tablr's core business question.

**guardrail_metrics:** Metrics that should not be meaningfully harmed by the winning variant. A variant that reduces CPAO but also reduces m1_retention to below the baseline has introduced a downstream risk that the primary metric cannot see. All declared guardrail breaches must be flagged in the readout before a recommendation is made.

**min_clicks_per_variant:** The minimum number of tracked clicks required before the experiment enters evaluation. Experiments below this threshold receive `INSUFFICIENT_DATA` status regardless of observed direction. This prevents premature winner calls based on small samples.

**eval_window_days:** The time window after experiment start before the first evaluation. Meta and TikTok: 14 days. Google Search and LinkedIn: 21 days (higher CPC means slower volume accumulation, longer signal development).

**status:** Current experiment state.

| Status | Meaning |
|---|---|
| OBSERVE | Running; not yet at evaluation threshold |
| INSUFFICIENT_DATA | Below minimum clicks — no direction can be declared |
| SCALE_CANDIDATE | Variant outperforms control on primary metric; guardrails intact; recommended for budget increase |
| REVISE | Variant shows a directional signal but needs creative adjustment before scaling |
| HOLD | Results are mixed or guardrail was breached; do not scale or pause yet |
| PAUSE_CANDIDATE | Control or variant is underperforming baseline with sufficient evidence; requires human review |

**Important limitations:**
- Experiments in this matrix are controlled only within each channel and targeting configuration. Cross-channel comparisons (exp_008, exp_009) are directional, not causal.
- Cohort maturity matters: guardrail metrics like `m1_retention` require 30+ days post-trial-signup to evaluate. Early readouts will show incomplete downstream data.
- No experiment result should trigger a campaign action without human review. All recommendations require explicit approval.
