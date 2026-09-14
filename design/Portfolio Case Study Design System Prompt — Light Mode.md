Create a portfolio case study page using the following **light-mode design system** and content principles.

## Overall Direction

The page should feel:

- Light, minimal, editorial, and premium
- Analytical rather than decorative
- Clear enough for a recruiter to scan in 2–3 minutes
- Structured like a product/data/strategy case study
- Senior and systems-oriented
- Calm, precise, and evidence-driven
- Spacious, modern, and understated

Avoid:

- Glossy SaaS landing-page aesthetics
- Excessive gradients
- Generic AI visuals
- Loud color combinations
- Large decorative illustrations
- Heavy animations
- Overly rounded “consumer app” styling
- Dense dashboard-like layouts

The design should communicate:

> Clear thinking, structured systems, evidence, and decision quality.

---

## Visual Style

### Color Palette

Use a warm-white or soft-neutral background rather than pure white.

```css
--bg: #f7f7f4;
--bg-soft: #f0f1ed;
--surface: #ffffff;
--surface-2: #f5f6f2;

--text: #17191c;
--text-soft: #2c3035;
--muted: #697078;
--muted-2: #92989f;

--line: rgba(23, 25, 28, 0.10);
--line-strong: rgba(23, 25, 28, 0.16);

--accent: #5f7f16;
--accent-dark: #46600f;
--accent-soft: rgba(95, 127, 22, 0.08);
--accent-border: rgba(95, 127, 22, 0.24);
```

Optional semantic colors:

```css
--blue: #4267a9;
--yellow: #a97816;
--red: #b84f4f;
--purple: #7353a6;
```

The primary accent should be muted and natural rather than neon.

Use it sparingly for:

- Eyebrows
- Section labels
- Key phrases
- Selected cards
- Status indicators
- Data-classification markers

Do not use the accent as a large background color.

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

The typography should feel editorial, modern, and highly readable.

### Heading behavior

Use:

- Large hero typography
- Tight letter spacing
- Compact line height
- Strong hierarchy
- Moderate font weights

Example:

```css
h1 {
  font-size: clamp(48px, 8vw, 92px);
  line-height: 1.04;
  letter-spacing: -0.045em;
  font-weight: 700;
  color: var(--text);
}

h2 {
  font-size: clamp(34px, 5vw, 56px);
  line-height: 1.08;
  letter-spacing: -0.04em;
  font-weight: 650;
}
```

Body copy should use `--muted`.

Lead paragraphs should use `--text-soft`.

Avoid using pure black everywhere.

---

## Layout

Use a centered maximum page width:

```css
--max-width: 1180px;
--content-width: 820px;
```

Use generous whitespace.

Typical section:

```css
.section {
  padding: 100px 0;
  border-top: 1px solid var(--line);
}
```

Use narrow text columns for explanation.

Use wider layouts for:

- Frameworks
- Comparison grids
- Decision models
- Metrics
- Architecture
- Workflows
- Tables

The page should feel spacious, not sparse.

---

## Page Background

Use a soft off-white base.

Optional subtle background treatment:

```css
body {
  background:
    radial-gradient(
      circle at 85% 10%,
      rgba(95, 127, 22, 0.05),
      transparent 24rem
    ),
    var(--bg);
}
```

Keep gradients extremely subtle.

The page should still read visually as a light editorial document.

---

## Navigation

Use a minimal top navigation.

Structure:

- Name / brand on left
- Work / About / Contact on right

Style:

- Transparent or background-colored nav
- Thin bottom border
- Dark primary text
- Muted secondary links
- No drop shadow
- No large logo

Example:

```css
.site-nav {
  border-bottom: 1px solid var(--line);
}
```

---

## Hero Structure

The hero should contain:

1. Small category eyebrow
2. Large project title
3. Concise project description
4. Capability tags
5. Metadata row

Example:

```text
GTM Intelligence · Decision Systems

GTM Intelligence Agent

An evidence-backed decision system designed to help teams...
```

Tags may include:

- GTM Strategy
- Revenue Analytics
- Decision Systems
- Product Analytics
- Experimentation
- AI System Design
- Growth Analytics

Tags should look like subtle outlined pills.

Example:

```css
.tag {
  border: 1px solid var(--line);
  background: rgba(255,255,255,0.55);
  color: var(--text-soft);
}
```

Do not make tags brightly colored.

---

## Eyebrows

Each major section should begin with a small uppercase eyebrow.

Examples:

```text
PROJECT SNAPSHOT
PROBLEM
DECISION FRAMEWORK
METHOD
EVALUATION
ARCHITECTURE
CURRENT STATUS
```

Style:

- Small uppercase type
- Wide letter spacing
- Accent color
- Small accent dot before text

Example:

```css
.eyebrow {
  color: var(--accent-dark);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
```

---

## Section Structure

Use this general case-study hierarchy:

1. Hero
2. Project Snapshot
3. Problem
4. Core Insight
5. Framework
6. Method / Workflow
7. System or Data Design
8. Key Logic / Evidence Model
9. MVP / Scope
10. Example Analysis or Decision
11. Evaluation or Results
12. Architecture
13. Current Status / Learnings
14. Final Takeaway

Not every project needs every section.

Adapt the sequence to the project type.

---

## Cards

Cards should be clean and slightly separated from the background.

Use:

```css
.card {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 28px;
}
```

Optionally use a very subtle shadow:

```css
box-shadow: 0 1px 2px rgba(0,0,0,0.025);
```

Avoid:

- Heavy shadows
- Glassmorphism
- Strong gradients
- Large colored blocks
- Excessive rounding

Cards should look like structured editorial containers.

---

## Project Snapshot

Near the top, include two concise cards.

### The Challenge

State the business or analytical problem.

### The Approach

Explain the system, method, or analytical response.

Keep these concise and recruiter-friendly.

---

## Problem Section

Translate the problem into 3–5 failure modes.

Example:

```text
01
Evidence gets fragmented

Research, analytics, and stakeholder inputs live across disconnected systems.
```

Use a grid with:

- very light neutral surfaces
- thin borders
- minimal visual decoration

The number can use the accent color.

---

## Key Statement

Use one large editorial statement between sections.

Example:

```text
The goal is not to automate strategy.

The goal is to make decisions more evidence-backed,
traceable, and testable.
```

Style:

- No card
- Large type
- Plenty of whitespace
- Thin top and bottom rules
- Only the important phrase uses accent color

This is one of the strongest visual moments on the page.

---

## Framework Sections

For analytical frameworks or strategic systems, use numbered rows.

Example:

```text
01  Where are we?
02  Where should we compete?
03  How should we win?
04  How should we launch?
05  What should we improve next?
```

Use:

- small number column
- medium title column
- wider explanation column

Use horizontal borders rather than cards when possible.

This creates a more editorial and senior feel.

---

## Design Principles

Use a two-column grid.

Each principle includes:

- Small index
- Principle name
- Short explanation

Example:

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

Use white cards against the off-white page background.

---

## Process / Learning Loop

Visualize the process with simple nodes and arrows.

Example:

```text
Evidence → Decision → Action → Measurement → Learning
```

Use:

- White or soft-neutral nodes
- Thin borders
- Accent border for the first or most important node
- Dark text
- Gray arrows

No heavy diagram styling.

Mobile layout should stack vertically.

---

## Tables and Classification Models

Use clean editorial tables.

Example structure:

```text
Verified Fact
Inference
Assumption
Recommendation
Unknown
```

Use semantic color only as a small dot or tiny label.

Suggested colors:

- Verified Fact — muted green
- Inference — muted blue
- Assumption — muted gold
- Recommendation — muted purple
- Unknown — muted red

Table rows should remain mostly white or neutral.

Do not use large colored backgrounds.

---

## AI / Logic / Human Boundaries

For AI-enabled projects, explicitly show responsibility boundaries.

Example:

```text
Deterministic Logic
Calculates

AI Layer
Interprets & Proposes

Human Owner
Decides
```

Use a 3-column card layout.

Suggested styling:

- Deterministic card: white
- AI card: white
- Human card: very subtle accent-tinted background or border

The design should emphasize that AI is one layer of the system, not the entire system.

---

## MVP / Scope Section

Use two cards:

### Included in MVP

Use a white card.

### Intentionally Deferred

Use a slightly gray or neutral card.

This visual distinction should communicate prioritization, not success vs failure.

Do not imply future functionality already exists.

---

## Example Decision / Example Analysis

Show one worked example.

Use structured key-value rows.

Example:

```text
Claim
Classification
Evidence
Confidence
Strategic Impact
Decision
Next Action
```

For analytics projects:

```text
Observation
Business Implication
Recommended Action
Validation Metric
```

Use:

- left label column in muted gray
- right content column in dark text
- thin horizontal rules

This should feel like a professional decision memo.

---

## Evaluation

Use 3- or 6-card metric grids.

Each card should contain:

- Small index
- Metric name
- One sentence explanation

Example metrics:

- Evidence coverage
- Unsupported-claim rate
- Forecast accuracy
- Incremental lift
- Human revision rate
- Recommendation acceptance
- Revenue reconciliation accuracy
- Retention lift
- Experiment validity
- Traceability
- Actionability

If the project has no measured results yet, describe the evaluation framework.

Never invent results.

---

## Architecture

Simplify architecture into conceptual layers.

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

Use 3–4 restrained cards.

For AI projects, visually distinguish:

- deterministic calculations
- generative interpretation
- human decision authority

Do not show the full repository tree unless it adds real value.

---

## Current Status

If the project is unfinished, include a transparent status section.

Two-column layout:

### Completed

- Product scope
- Architecture
- Data model
- Decision logic
- Evidence rules

### Next

- Dataset
- MVP build
- Evaluation
- Case study results

Use:

- muted green check marks
- gray circles for unfinished items

Do not overuse bright success colors.

---

## Final Takeaway

End with a soft accent-tinted panel.

Example:

```text
WHAT THIS PROJECT DEMONSTRATES

I am interested in the layer between data,
AI, and the business decision that actually needs to get made.
```

Suggested style:

```css
.takeaway {
  background: var(--accent-soft);
  border: 1px solid var(--accent-border);
  border-radius: 22px;
}
```

Keep the accent very subtle.

The takeaway should reinforce the professional identity demonstrated by the project.

Possible identities:

- Decision Intelligence
- Revenue Analytics
- Growth Analytics
- Product Analytics
- Data Product Design
- Experimentation
- AI-enabled decision systems

---

## Writing Style

Use concise, confident English.

Writing should feel:

- Specific
- Analytical
- Business-aware
- Calm
- Evidence-oriented
- Non-hype

Prefer:

> Designed a measurement system that reconciles platform-reported conversions with warehouse-level customer outcomes.

Avoid:

> Built a groundbreaking AI-powered platform that transforms marketing intelligence.

Prefer:

> The analysis suggests...

Avoid:

> The analysis proves...

Prefer:

> Designed to support...

Avoid:

> Revolutionizes...

Avoid words such as:

- revolutionary
- game-changing
- cutting-edge
- groundbreaking
- next-generation
- powerful AI
- transformative

AI should be described according to its actual system responsibility.

---

## Visual Hierarchy Principle

Use contrast through:

- Typography
- Whitespace
- Borders
- Surface changes
- Small accent details

Do not rely on color alone.

The light-mode page should still feel high-contrast and intentional.

A good ratio is:

- 70% neutral background
- 20% white or slightly elevated surfaces
- 10% accent or semantic detail

---

## Responsive Behavior

Desktop:

- Use 2-column and 3-column grids when appropriate
- Keep body text relatively narrow
- Use wider layouts for systems and frameworks

Mobile:

- Stack all grids vertically
- Stack workflows vertically
- Reduce hero size while preserving hierarchy
- Keep section spacing generous
- Simplify navigation if necessary

---

## Final Design Goal

The finished page should feel like:

> A thoughtful product/data strategist documenting how a complex business decision or analytical system works.

It should resemble:

- A premium editorial report
- A senior product strategy case study
- A modern design-engineering portfolio

It should not resemble:

- A startup sales page
- A generic SaaS template
- An AI demo landing page
- A dashboard screenshot gallery

The visual system should reinforce the same core philosophy:

**Evidence → Decision → Action → Measurement → Learning**