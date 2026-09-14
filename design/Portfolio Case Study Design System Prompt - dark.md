Create a portfolio case study page using the following design system and content principles.

## Overall Direction

The page should feel:

- Dark, minimal, editorial, and premium
- Analytical rather than decorative
- Clear enough for a recruiter to scan in 2–3 minutes
- Structured like a product/data/strategy case study, not a marketing landing page
- Senior and systems-oriented
- Calm, precise, and evidence-driven

Avoid:

- Overly glossy SaaS visuals
- Excessive gradients
- Generic AI aesthetics
- Neon cyberpunk styling
- Too many illustrations
- Heavy animations
- Decorative UI that competes with the content

The design should communicate:

> Clear thinking, structured systems, evidence, and decision quality.

---

## Visual Style

### Color Palette

Use a near-black background with subtle layered surfaces.

```css
--bg: #0b0d10;
--bg-soft: #111419;
--card: #15191f;
--card-2: #1a1f26;

--text: #f4f5f7;
--muted: #9da5b0;
--muted-2: #717985;

--line: rgba(255, 255, 255, 0.10);
--line-strong: rgba(255, 255, 255, 0.16);

--accent: #b8ff5a;
--accent-soft: rgba(184, 255, 90, 0.10);
--accent-border: rgba(184, 255, 90, 0.28);
```

Optional semantic colors:

```css
--blue: #79a8ff;
--yellow: #ffd66b;
--red: #ff8f8f;
--purple: #ba9cff;
```

The primary accent should be used sparingly for:

- Eyebrows
- Important labels
- Key statements
- Selected/highlighted cards
- Decision states
- Small status indicators

Do not flood large areas with the accent color.

---

## Typography

Use:

```css
font-family:
  Inter,
  ui-sans-serif,
  -apple-system,
  BlinkMacSystemFont,
  "Segoe UI",
  sans-serif;
```

Typography should feel editorial and spacious.

### Heading behavior

- Large hero headline
- Tight letter-spacing
- Relatively compact line-height
- Strong visual hierarchy
- Avoid excessive font weights

Example:

```css
h1 {
  font-size: clamp(48px, 8vw, 94px);
  line-height: 1.05;
  letter-spacing: -0.04em;
  font-weight: 700;
}

h2 {
  font-size: clamp(34px, 5vw, 58px);
  line-height: 1.08;
  letter-spacing: -0.04em;
}
```

Body text should use muted gray rather than pure white.

Lead paragraphs should be slightly brighter and larger than body copy.

---

## Layout

Use a centered maximum page width:

```css
--max-width: 1180px;
--content-width: 820px;
```

Main content should use generous vertical spacing.

Sections should typically use:

```css
padding: 100px 0;
border-top: 1px solid var(--line);
```

Do not make every section full-width visually.

Use a narrower content column for explanatory text and a wider layout for:

- comparison grids
- system diagrams
- evidence models
- metrics
- architecture
- workflows

---

## Navigation

Use a very minimal top navigation.

Structure:

- Brand / name on the left
- Work / About / Contact on the right

Styling:

- 1px bottom border
- No large logo
- No colored nav background
- Small muted links
- Simple hover to brighter text

---

## Hero Structure

The hero should contain:

1. Small category eyebrow
2. Large project title
3. One concise project description
4. Small capability tags
5. A metadata row

Example hierarchy:

```text
GTM Intelligence · Decision Systems

GTM Intelligence Agent

An evidence-backed decision system designed to help teams...
```

Tags can represent:

- Strategy
- Analytics
- Decision Systems
- Experimentation
- AI System Design
- Product Analytics
- Revenue Intelligence

Metadata row should contain 3–4 items such as:

- Role
- Primary user
- Project stage
- Core principle
- Tools
- Duration

Do not overload the hero with details.

---

## Eyebrows

Each major section should begin with a small uppercase eyebrow.

Example:

```text
PROBLEM
DECISION FRAMEWORK
DESIGN PRINCIPLES
EVALUATION
ARCHITECTURE
CURRENT STATUS
```

Style:

- Uppercase
- Small font
- Wide letter spacing
- Accent color
- Small circular accent dot before the label

---

## Section Structure

Use this general case-study hierarchy:

1. Hero
2. Project Snapshot
3. Problem
4. Core Insight / Key Statement
5. Decision or Analytical Framework
6. Method / Workflow
7. System or Data Design
8. Key Logic / Evidence Model
9. MVP or Scope
10. Example Decision / Analysis
11. Evaluation or Results
12. Architecture / Technical Design
13. Current Status or Learnings
14. Final Takeaway

Not every project must use every section.

Adapt the structure to the project.

---

## Cards

Cards should be:

- Flat
- Dark
- Slightly lighter than background
- 1px border
- 16–20px radius
- Generous internal padding

Example:

```css
.card {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 20px;
  padding: 28px;
}
```

Avoid:

- strong drop shadows
- glassmorphism
- glossy gradients
- oversized icons

Cards should communicate information, not decoration.

---

## Project Snapshot

Near the top, include 2 concise cards:

### The Challenge

Explain the business or analytical problem.

### The Approach

Explain the system, method, or analytical solution.

Keep each card short enough to understand in under 10 seconds.

---

## Problem Section

Turn the problem into 3–5 specific failure modes.

Example structure:

```text
01
Evidence gets fragmented

Research, analytics, and stakeholder inputs live across disconnected systems.
```

Use a grid with minimal borders.

Each problem should contain:

- number
- short title
- one short explanation

---

## Key Statement Section

Use a large editorial statement to express the core idea of the project.

Example pattern:

```text
The goal is not to automate strategy.

The goal is to make decisions more evidence-backed,
traceable, and testable.
```

Style:

- large text
- no card
- top and bottom border
- accent only on the key phrase

Every project should have one strong thesis statement.

---

## Framework Sections

If the project has a strategic or analytical framework, show it as numbered questions or stages.

Example:

```text
01  Where are we?
02  Where should we compete?
03  How should we win?
04  How should we launch?
05  What should we improve next?
```

Layout:

- narrow number column
- middle title column
- wider explanation column

This should feel like a system rather than a bullet list.

---

## Design Principles

Use a 2-column card grid.

Each principle should have:

- Small index label
- Short principle name
- 1–2 sentence explanation

Examples:

```text
01 / EVIDENCE
Evidence before recommendation

02 / LOGIC
Deterministic rules before AI judgment

03 / CONTROL
Human approval for consequential decisions

04 / TRACEABILITY
Every important decision should be explainable
```

These cards should communicate how the project was designed, not just what features it contains.

---

## Process / Learning Loop

When possible, visualize the project as a simple horizontal system.

Example:

```text
Evidence → Decision → Action → Measurement → Learning
```

Or:

```text
Data → Analysis → Insight → Recommendation → Experiment
```

Use simple boxed nodes and arrows.

Avoid complicated diagrams unless necessary.

On mobile, the sequence should stack vertically.

---

## Tables and Evidence Models

Tables should feel like product UI, not spreadsheet UI.

Use:

- 1px borders
- dark surfaces
- clear row spacing
- muted descriptions
- small semantic colored dots where useful

For classification systems, use subtle semantic colors.

Example:

- Verified Fact — green
- Inference — blue
- Assumption — yellow
- Recommendation — purple
- Unknown — red

Do not use bright filled rows.

---

## Human / AI / Logic Boundaries

For projects involving AI, explicitly show system boundaries.

Preferred structure:

```text
Deterministic Logic
Calculates

AI Layer
Interprets & Proposes

Human Owner
Decides
```

Use a 3-column card layout.

The Human Owner card may receive a subtle accent border.

This avoids presenting the project as an AI wrapper.

---

## MVP / Scope Section

Clearly separate:

### Included

What is actually part of the MVP or current system.

### Deferred

What is intentionally not included.

This is important for showing prioritization and product judgment.

Never imply that planned features are already built.

---

## Example Decision / Example Analysis

Show one realistic worked example.

Structure:

```text
Claim
Classification
Evidence
Confidence
Strategic Impact
Decision
Next Action
```

Or for analytics projects:

```text
Observation
Business Implication
Recommended Action
Validation Metric
```

This should demonstrate reasoning, not just output.

---

## Evaluation

Evaluation should focus on decision quality, analytical validity, or business usefulness.

Use metric cards.

Examples:

- Evidence coverage
- Unsupported-claim rate
- Forecast accuracy
- Incremental lift
- Experiment validity
- Human revision rate
- Recommendation acceptance
- Traceability
- Actionability
- Retention lift
- Revenue reconciliation accuracy

Each metric card should include:

- small index
- metric name
- one sentence explaining what it measures

Do not invent numeric results if the project has not yet been evaluated.

---

## Architecture

Architecture should be simplified for portfolio readers.

Show conceptual layers instead of dumping repository structure first.

Example:

```text
Product Layer
Features

Domain Layer
Business Logic

AI Layer
Interpretation

Data Layer
Evidence and Metrics
```

If the project involves AI, make clear what is deterministic and what is generative.

Avoid making the architecture section look like a raw engineering README.

---

## Current Status

If the project is unfinished, include a transparent status section.

Use two columns:

### Completed

- Product scope
- System architecture
- Data model
- Analytical logic
- Design rules

### Next

- Dataset
- MVP build
- Evaluation
- Case study results

Use check marks only for genuinely completed items.

Never manufacture outcomes.

---

## Final Takeaway

End with one strong statement about what the project demonstrates about the creator.

Example structure:

```text
WHAT THIS PROJECT DEMONSTRATES

I am interested in the layer between data,
AI, and the business decision that actually needs to get made.
```

Then add a short supporting paragraph.

The final section should summarize the professional identity demonstrated by the project.

Examples:

- Decision Intelligence
- Growth Analytics
- Revenue Analytics
- Product Analytics
- Experimentation
- Data Product Design
- AI-enabled decision systems

Do not end with generic phrases such as:

“Thanks for reading.”

---

## Writing Style

Use concise, confident English.

Writing should be:

- Specific
- Analytical
- Business-aware
- Calm
- Non-hype
- Evidence-oriented

Prefer:

> Designed a measurement system that reconciles platform-reported conversions with warehouse-level customer outcomes.

Over:

> Built an innovative cutting-edge analytics platform powered by advanced technology.

Prefer:

> The analysis suggests...

Over:

> The analysis proves...

Prefer:

> Designed to support...

Over:

> Revolutionizes...

Avoid:

- revolutionary
- cutting-edge
- game-changing
- groundbreaking
- next-generation
- powerful AI
- AI-powered everywhere
- leverage AI to unlock

Use AI only when explaining its actual system role.

---

## Content Principle

For every project, answer these questions clearly:

1. What was the business problem?
2. Why was the existing approach insufficient?
3. What did I design or analyze?
4. What logic or methodology did I use?
5. How did I separate data, interpretation, and decision?
6. What did the output help someone decide?
7. How was or will the work be evaluated?
8. What was intentionally out of scope?
9. What does this project demonstrate about my skills?

The case study should prioritize **decision quality** over feature quantity.

---

## Responsive Behavior

Desktop:

- Use 2-column and 3-column layouts where useful
- Keep explanatory text narrow
- Use wide sections for frameworks and diagrams

Mobile:

- Collapse all grids to one column
- Stack arrows vertically
- Keep headline size strong but readable
- Preserve generous spacing
- Hide secondary navigation if necessary

---

## Final Design Goal

The finished page should feel like:

> A thoughtful data/product strategist documenting how a complex business decision system works.

Not:

> A startup landing page trying to sell an AI product.

The visual and writing system should reinforce the same idea:

**Evidence → Decision → Action → Measurement → Learning**