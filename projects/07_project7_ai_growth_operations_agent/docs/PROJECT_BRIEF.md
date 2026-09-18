# Project Brief

## AI-Powered Creative Optimization & Growth Operations Agent

**Project type:** Independent portfolio simulation  
**Primary domain:** B2B SaaS growth and performance marketing  
**Simulated company:** Tablr — AI-powered growth OS for independent restaurants  
**Document status:** Baseline project specification

## 1. Purpose

This project demonstrates how a growth team could connect paid acquisition, performance creative, experimentation, product activation, retention, lifetime value, and AI-assisted operations in one explainable workflow.

The goal is not to create a fully autonomous media buyer. The goal is to build a credible decision-support system that:

1. Converts audience and business strategy into testable creative concepts.
2. Organizes controlled experiments across paid channels.
3. Connects ad performance to downstream product behavior.
4. Recommends evidence-based actions.
5. Requires human approval before any live campaign mutation.
6. Documents what was learned and what should be tested next.

## 2. Portfolio Positioning

This project is designed to provide evidence relevant to roles such as:

- Growth Marketing Manager
- Performance Marketing Manager
- Paid Acquisition Lead
- Creative Strategy Lead
- Creative Director, Performance Marketing
- Growth Operations Manager
- Marketing Analytics Manager

It should demonstrate the intersection of four capabilities:

| Capability        | Evidence produced by this project                                             |
| ----------------- | ----------------------------------------------------------------------------- |
| Growth strategy   | Funnel, personas, channel roles, budget model, and KPI tree                   |
| Creative strategy | Message map, hooks, briefs, scripts, and testing matrix                       |
| Analytics         | CAC, activation, retention, LTV, cohort, and creative-quality analysis        |
| AI operations     | Structured generation, evaluation, recommendations, approvals, and audit logs |

## 3. Portfolio Disclosure

This is an independent portfolio simulation based on a hypothetical company and synthetic data.

> I built an independent portfolio simulation of an AI-assisted growth operations system for Tablr, a B2B SaaS platform for independent restaurant owners. It connects performance creative and paid acquisition to trial activation, subscription retention, and LTV — with human approval required for campaign actions.

## 4. Hypothetical Company

### Company overview

**Tablr** is an AI-native growth operating system for independent restaurant owners. It helps them attract new customers, convert walk-ins and online visitors, and build lasting loyalty — without hiring a marketing team.

Tablr competes in the local restaurant tech space alongside platforms like Owner.com, Popmenu, and Olo, but focuses exclusively on independent operators (1–5 locations) who lack the resources of national chains.

These are project assumptions, not claims about any real company.

### Product promise

Give independent restaurant owners the marketing infrastructure that chains take for granted — automated campaigns, smart loyalty programs, and AI-driven insights — in a single platform they can run in under an hour a week.

### Business model assumptions

The simulation assumes a B2B SaaS subscription model:

- Free 14-day trial (no credit card required)
- Paid subscription per location per month
- Higher tiers unlock advanced AI features, multi-location management, and integrations
- Potential future marketplace revenue (vendor partnerships, booking fees)

### Growth stage

- Post-seed, scaling paid acquisition
- Product-market fit validated in 3–5 metro markets
- Needs a repeatable, high-velocity creative testing system
- Must balance new location acquisition with activation quality and churn reduction

### Primary business challenge

Tablr can drive trial signups through paid channels, but it needs to identify which channels, audiences, messages, and creative concepts acquire restaurant owners who actually activate the platform, launch their first campaign, and convert to paid — rather than signing up and going dark.

## 5. Business Objective

### Primary objective

Acquire more activated restaurant owners at an economically sustainable cost.

### Secondary objectives

- Increase the percentage of trial signups who launch their first Tablr campaign within 14 days.
- Improve Month 1 and Month 3 retention among paid subscribers.
- Identify creative attributes associated with high-LTV restaurant owners.
- Reduce the time required to move from performance insight to the next creative test.
- Establish a repeatable and auditable growth experimentation process.

### North Star metric

**Monthly Active Restaurants (MAR)**

A Monthly Active Restaurant is a paying subscriber that has launched at least one customer-facing campaign or loyalty action through Tablr during the calendar month.

### Primary paid-growth metric

**Cost per Activated Owner (CPAO)**

```text
CPAO = Paid Media Spend / Number of Paid-Acquired Activated Restaurant Owners
```

CPAO is more useful than trial CAC because it accounts for whether acquired owners actually use the platform to run marketing — not just sign up and go dark.

## 6. Target Audiences

The initial simulation uses five audience segments. These are hypotheses to test rather than proven market facts.

### Persona 1: The Scrappy Independent Owner

- Runs 1–2 locations, handles marketing personally or not at all.
- Time-constrained; skeptical of tools that promise too much.
- Responds to proof of simplicity and real results from owners like them.
- Primary barrier: "I don't have time to learn another platform."
- Desired action: Start a free trial, complete onboarding, launch first campaign.

### Persona 2: The Growth-Minded Operator

- Runs 2–4 locations, already using some digital marketing (Google Ads, email).
- Wants to scale what's working without adding headcount.
- Responds to efficiency, ROI data, and competitive advantage messaging.
- Primary barrier: Concerned about switching costs and integration complexity.
- Desired action: Trial Tablr as a replacement or consolidation layer.

### Persona 3: The New Restaurant Owner

- Opened within the last 6–18 months, still building their customer base.
- Urgently needs to drive awareness and first-time visits.
- Responds to "get your first 100 loyal customers" framing.
- Primary barrier: Budget-conscious; afraid of wasting money on marketing.
- Desired action: Start trial, run a new customer acquisition campaign.

### Persona 4: The Delivery-Heavy Owner

- Heavily dependent on DoorDash or Uber Eats; wants to own the customer relationship.
- Worried about margin erosion from third-party commissions.
- Responds to direct ordering, loyalty, and margin-recovery messaging.
- Primary barrier: Doesn't believe they can win customers back from the apps.
- Desired action: Set up direct ordering and launch a re-engagement campaign.

### Persona 5: The Community-Focused Chef-Owner

- Strong local identity; regulars are core to the business.
- Values authenticity; suspicious of generic marketing tools.
- Responds to neighborhood-specific social proof and personal stories.
- Primary barrier: Fears the tool will make their brand feel corporate.
- Desired action: Set up a loyalty program and automate review requests.

## 7. Customer Journey

| Stage         | Owner question                                          | Desired behavior                          | Example metric              |
| ------------- | ------------------------------------------------------- | ----------------------------------------- | --------------------------- |
| Awareness     | Is this relevant to my restaurant?                      | Stop scrolling; watch or click            | Hook rate, CTR              |
| Consideration | Can it actually help me get more customers?             | Visit landing page; explore features      | Landing-page view rate      |
| Acquisition   | Is a free trial worth 10 minutes of my time?            | Start free trial                          | Trial CVR, trial CAC        |
| Activation    | Can I set this up and see value quickly?                | Complete onboarding; launch first campaign | Activation rate, CPAO      |
| Retention     | Is this worth paying for every month?                   | Convert to paid; continue using           | Trial-to-paid CVR, M1, M3  |
| Expansion     | Can I use this across my other locations?               | Add a second or third location            | Expansion revenue, NRR      |
| Referral      | Would I recommend this to another owner I know?         | Refer a peer restaurant owner             | Referral rate, referral CAC |

## 8. Funnel and Event Definitions

### Core funnel

```text
Ad Impression
→ Ad Engagement or Click
→ Landing-Page View
→ Trial Signup
→ Onboarding Completed
→ Restaurant Profile Created
→ First Campaign Launched
→ First Customer Acquired via Tablr
→ Subscription Started
→ Location Added (expansion)
```

### Required product events

| Event                       | Definition                                                      |
| --------------------------- | --------------------------------------------------------------- |
| `ad_click`                  | A tracked paid-media click                                      |
| `landing_page_view`         | A valid landing-page load after paid acquisition                |
| `trial_signup`              | A restaurant owner successfully creates a free trial account    |
| `onboarding_completed`      | Owner completes the setup wizard (profile + first integration)  |
| `profile_created`           | Restaurant profile is published on the Tablr platform           |
| `campaign_launched`         | Owner publishes their first customer-facing campaign            |
| `first_customer_acquired`   | First tracked customer attributed to a Tablr campaign           |
| `subscription_started`      | Owner converts from trial to a paid subscription                |
| `location_added`            | Owner adds a second or subsequent restaurant location           |
| `revenue_generated`         | Recognized MRR is associated with the account                   |

### Activation definition

For the MVP, an **Activated Owner** is a trial-acquired restaurant owner who launches their first customer-facing campaign within 14 days of signup.

This definition must be configurable. The project should later compare it with alternative definitions such as `first_customer_acquired` or `subscription_started`, and explain how metric selection changes conclusions.

### Retention definitions

- **M1 retained:** Owner is still on a paid subscription 30 days after conversion.
- **M3 retained:** Owner is still on a paid subscription 90 days after conversion.
- **M6 retained:** Owner is still on a paid subscription 180 days after conversion.

Exact window logic must be defined in `data/data_dictionary.md` before implementation.

## 9. KPI Tree

### Business outcome

```text
Sustainable Restaurant Owner Growth
├── Monthly Active Restaurants (MAR)
│   ├── New Activated Owners
│   │   ├── Paid Traffic (trials)
│   │   ├── Trial Signup CVR
│   │   └── Trial-to-Activation Rate
│   └── Retained Subscribers
│       ├── M1 Retention
│       ├── M3 Retention
│       └── Feature Adoption Depth
└── Unit Economics
    ├── Cost per Activated Owner (CPAO)
    ├── LTV per Acquired Cohort
    ├── LTV:CAC
    └── Payback Period
```

### Metric hierarchy

| Level               | Metrics                                      | Purpose                              |
| ------------------- | -------------------------------------------- | ------------------------------------ |
| Business            | MAR, MRR, NRR, LTV:CAC                       | Evaluate sustainable growth          |
| Acquisition quality | CPAO, activation rate, trial-to-paid CVR     | Evaluate acquired-owner quality      |
| Conversion          | Trial CAC, landing-page CVR, onboarding CVR  | Diagnose funnel effectiveness        |
| Media               | CPM, CTR, CPC, frequency                     | Diagnose delivery and engagement     |
| Creative            | Hook rate, hold rate, angle performance      | Diagnose creative execution          |
| Operations          | Cycle time, approval rate, failure rate      | Evaluate workflow efficiency         |

## 10. Channel Strategy

The project models four paid channels. Channel roles are assumptions to test.

| Channel       | Primary role                                 | Example creative or intent                 |
| ------------- | -------------------------------------------- | ------------------------------------------ |
| Meta          | Scaled discovery and creative testing        | UGC, product demos, static concepts        |
| TikTok        | Native discovery and rapid creative learning | Owner-led UGC, before/after transformations      |
| Google Search | Capture existing intent                      | "restaurant marketing software", "get more customers" |
| YouTube       | Demonstration and consideration              | Shorts, product walkthroughs, owner success stories  |

Programmatic and CTV are advanced extensions. They are not required for the MVP because they introduce additional measurement and access complexity.

## 11. Simulated Media Budget

### Monthly budget assumption

**$150,000 per month**, using synthetic data only.

### Initial allocation

| Channel       |       Budget |    Share | Portfolio rationale                              |
| ------------- | -----------: | -------: | ------------------------------------------------ |
| Meta          |      $60,000 |      40% | Broad creative testing and scalable acquisition  |
| TikTok        |      $37,500 |      25% | Native short-form discovery and concept velocity |
| Google Search |      $30,000 |      20% | Capture higher-intent demand                     |
| YouTube       |      $22,500 |      15% | Product education and demonstration              |
| **Total**     | **$150,000** | **100%** | Synthetic planning assumption                    |

The initial allocation is not a performance claim. The budget simulator should later recommend reallocations based on marginal CPAO, downstream retention, LTV, data sufficiency, and exploration requirements.

### Exploration policy

The simulation should reserve part of each channel budget for learning rather than allocating everything to current winners.

Suggested starting assumption:

- 70% proven or scaling concepts
- 20% iterations on promising concepts
- 10% new exploratory concepts

This ratio must remain configurable and should not be treated as a universal best practice.

## 12. Creative Strategy

### Initial messaging territories

1. **Stop losing to the chains:** Independent restaurants can now compete with the marketing infrastructure of national brands.
2. **Own your customer relationship:** Break free from third-party delivery app dependency and build direct loyalty.
3. **Marketing that runs itself:** AI handles the campaigns so owners can focus on the food and the floor.
4. **Your first 100 loyal customers:** Concrete, outcome-focused promise for new and growing restaurants.
5. **Built for owners, not marketers:** Reduce perceived complexity — no agency, no marketing degree required.

### Creative formats

- Static image
- Short-form vertical video
- UGC or creator-led video
- Product demonstration
- Before-and-after transformation
- Challenge or community concept
- Landing-page message variation
- Lifecycle email concept

### Creative testing rule

Each experiment should isolate one primary variable whenever practical:

- Hook
- Message angle
- Persona
- Proof type
- Visual format
- Opening three seconds
- CTA
- Landing-page message match

Every creative must link to a `creative_id`, `experiment_id`, hypothesis, control where applicable, and the variable tested.

## 13. Analytics Questions

The completed project must be able to answer:

1. Which channels and creatives generate the lowest trial CAC?
2. Which generate the lowest Cost per Activated Owner (CPAO)?
3. Does the highest-CTR creative also produce high-quality, retained subscribers?
4. Which persona has the strongest M1 and M3 retention after converting to paid?
5. Which hooks attract trial signups but show weak onboarding or campaign launch rates?
6. Which creative attributes correlate with owners who add a second location?
7. Where does creative fatigue appear across the campaign portfolio?
8. Which campaigns should be observed, revised, held, scaled, or considered for pausing?
9. How would budget allocation change when optimizing for CPAO or LTV instead of platform ROAS?
10. What should the growth team test next, and why?

## 14. Synthetic Data Requirements

The baseline data generator should produce:

- 12 weeks of daily performance
- 4 paid channels (Meta, YouTube, Google Search, LinkedIn)
- At least 10 campaigns
- At least 30 ad sets or comparable targeting groups
- At least 90 creative variants
- 5 personas (restaurant owner segments)
- At least 5,000 simulated restaurant owner trials
- Trial signup, onboarding, campaign launch, subscription, and revenue events

The generator should contain intentional patterns that support meaningful analysis:

- A high-CTR creative with low onboarding completion (clicks but doesn't activate)
- A lower-CTR persona with stronger M3 retention and higher LTV
- A previously strong creative experiencing fatigue after week 6
- A platform-reported winner (Meta ROAS) that is weak on blended CPAO
- A new creative with insufficient evidence (under minimum click threshold)
- A genuine simulated winner with strong activation and M3 retention
- Delayed trial-to-paid conversions and missing attribution values
- At least one data-quality issue that requires detection and documentation

All generation must be reproducible with a fixed random seed. Every output must be visibly labeled as synthetic.

## 15. Decision Framework

The system produces recommendations, not unquestioned commands.

Allowed recommendation states:

- `OBSERVE`
- `REVISE`
- `HOLD`
- `SCALE_CANDIDATE`
- `PAUSE_CANDIDATE`
- `INSUFFICIENT_DATA`

Each recommendation must include:

- Recommended state
- Supporting metrics
- Baseline or comparison group
- Data volume and evaluation window
- Confidence or evidence assessment
- Downstream activation and retention context
- Expected tradeoff
- Suggested next step
- Human approval status

No single fixed CTR, CVR, or spend threshold may determine a live action by itself.

## 16. Safety and Governance

### Default settings

```env
DRY_RUN=true
RECOMMEND_ONLY=true
ALLOW_LIVE_MUTATIONS=false
```

### Mandatory rules

- Do not publish ads or alter live campaigns by default.
- Do not expose, log, or commit credentials.
- Do not use real customer data in the portfolio repository.
- Do not pass unvalidated LLM output into downstream systems.
- Do not make unsupported advertising claims.
- Do not treat synthetic findings as real performance.
- Record approved actions and material decisions in an audit trail.
- Make platform connectors optional; the local demo must run without them.

### Human approval required for

- Publishing or activating an ad
- Changing a budget or bid
- Pausing or deleting a campaign, ad set, or ad
- Uploading customer or audience data
- Changing attribution or optimization settings

## 17. Technical Assumptions

- Python 3.11+
- Pydantic for structured validation
- Pandas and DuckDB for initial analysis
- Parquet and CSV for local portfolio data
- Pytest for automated testing
- Ruff and MyPy for quality checks
- LLM provider and model selected through configuration
- Mock connectors implemented before platform connectors
- GitHub Actions used for tests and static checks

The system should avoid unnecessary infrastructure until the local MVP works end to end.

## 18. MVP Deliverables

The MVP is complete only when the repository contains:

1. Reproducible synthetic campaign and product-event data.
2. A complete data dictionary.
3. Validated schemas for personas, creatives, experiments, events, and recommendations.
4. At least three creative concepts for each initial testing scenario.
5. An experiment registry with controls and variants.
6. Acquisition, activation, retention, and LTV analysis.
7. Explainable recommendation output with human-review status.
8. A Creative Intelligence dashboard or report.
9. A weekly growth review.
10. Unit, integration, and data-quality tests.
11. A case study clearly labeling simulated findings.
12. Working local demo instructions.

Live Meta or TikTok integration is not required for MVP completion.

## 19. Success Criteria

### Functional success

- A new user can run the local simulation without marketing-platform credentials.
- The same random seed produces the same data and core results.
- Campaign data joins correctly to product events.
- Metrics match documented formulas.
- The system distinguishes insufficient evidence from poor performance.
- Recommendations include activation and retention context.
- Structured AI outputs pass validation or fail safely.

### Portfolio success

- A reviewer can understand the business problem within two minutes.
- A reviewer can trace a creative from hypothesis to performance and next decision.
- The case study explains why CTR or trial CAC alone can mislead.
- Simulated work is clearly separated from real professional experience.
- Tradeoffs, limitations, and the next experiment are clearly articulated.

### Safety success

- Live mutations are disabled by default.
- Secrets and personal data never appear in the repository or logs.
- Every advanced action requires explicit approval and is auditable.

## 20. Out of Scope for the Initial MVP

- Real-money media buying
- Fully autonomous campaign control
- Production multi-touch attribution
- Identity resolution across devices
- Incrementality or geo-lift experiments
- Production-grade data warehouse infrastructure
- CTV and broad programmatic activation
- Real customer-data ingestion
- Automated generation of final visual assets at production scale

These may be added only after the local MVP is complete and documented.

## 21. Key Risks and Limitations

| Risk                                   | Required response                                    |
| -------------------------------------- | ---------------------------------------------------- |
| Synthetic results appear real          | Label datasets, dashboards, and case studies clearly |
| LLM invents claims                     | Validate outputs and require claim review            |
| Small samples create false winners     | Use evidence requirements and `INSUFFICIENT_DATA`    |
| Platform attribution overstates impact | Compare with first-party and blended metrics         |
| Retention window is incomplete         | Mark cohorts immature and delay decisions            |
| API operation is duplicated            | Use idempotency keys and audit logs                  |
| Scope becomes too large                | Complete local MVP before advanced connectors        |

## 22. Working Principles

1. Business reasoning comes before automation.
2. Acquisition quality matters more than cheap clicks.
3. Creative volume is not a substitute for controlled learning.
4. AI output must be structured, evaluated, and reviewable.
5. Missing data must be represented honestly.
6. Human judgment remains accountable for consequential actions.
7. Every recommendation should lead to a clear decision or next experiment.

## 23. Open Decisions

The following decisions have been finalized or remain open.

### Finalized

| Decision | Value | Rationale |
| -------- | ----- | --------- |
| Company name | Tablr | AI-powered growth OS for independent restaurants |
| Primary industry | Restaurant SaaS | Aligned with Owner.com JD target vertical |
| Geographic market | United States, USD | Simplifies tax, pricing, and attribution assumptions |
| Dashboard technology | Streamlit (MVP), exportable to HTML | Consistent with other portfolio projects |
| Attribution window | 7-day click, 1-day view | Standard Meta default; documented in data dictionary |
| Activation definition (MVP) | Campaign launched within 14 days of trial signup | Measures meaningful product use, not just registration |

### Still open

- Subscription tier pricing (e.g. $99/$199/$399 per location per month)
- Target CPAO and LTV assumptions (to be derived from synthetic data baseline)
- M3 retention target (to be set after cohort analysis)
- Whether an authorized draft-only Meta or LinkedIn connector will be included

When a decision is finalized, update this table and record the rationale in `DECISIONS.md`.

## 24. Definition of Done

The project is done when the portfolio can demonstrate the complete reasoning chain:

```text
Business Objective
→ Audience Hypothesis
→ Creative Hypothesis
→ Controlled Experiment
→ Acquisition Result
→ Activation and Retention Result
→ Economic Interpretation
→ Human-Reviewed Recommendation
→ Next Test
```

The final portfolio should show not only what the system built, but also how growth decisions were made, how uncertainty was handled, how unsafe automation was prevented, and what would require real-world validation before acting.
