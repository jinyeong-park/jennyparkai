# Portfolio website for data analyst / growth analyst role

updated on Sep, 5, 2026

# project plan

https://github.com/jinyeong-park/marketing-analyst-projects

---

Bay Area tech companies (Meta, Uber, Snowflake, Airbnb, and scaling B2B SaaS startups) do not hire marketing analysts to build basic dashboards or track vanity metrics like clicks and impressions. They hire analysts who can answer **incrementality, retention, multi-touch attribution, and pipeline revenue questions using production-grade SQL, Python, and statistical modeling**.

To position bootcamp graduates for Bay Area growth teams, build three real-world, portfolio-defining projects.

---

### Project 1: Multi-Touch Attribution & Incrementality Engine

Repository: https://github.com/jinyeong-park/jynlab-growth-attribution-system

**Target Focus:** B2C Tech, E-commerce, Performance Marketing (e.g., DoorDash, Instacart, Meta)

#### The Problem

A D2C brand spends $500K/month across Meta, Google Search, TikTok, and CTV. Ad networks over-report conversions (e.g., Meta claims credit for the same sale Google claims). Students must determine true channel ROI and recommend spend reallocations.

#### What Students Build

- **Data Stack:** PostgreSQL / Snowflake, Python (Pandas, Scipy), Streamlit / Tableau.
- **Pipeline:** Clean raw user touchpoint logs containing `user_id`, `timestamp`, `channel`, `campaign`, and `conversion_event`.
- **Attribution Modeling:** Write advanced SQL window functions to model First-Touch, Last-Touch, Linear, and Time-Decay attribution side-by-side.
- **Geo-Incrementality Test:** Run an A/B or matched-market geo-experiment in Python (control vs. treatment regions) to calculate true **incremental CAC** vs. self-reported platform CAC.
- **Deliverable:** An interactive Streamlit app or Tableau dashboard mapping _Attributed ROAS vs. Incremental ROAS_ with a $100K budget re-allocation strategy.

#### Why Bay Area Recruiters Care

- Demonstrates mastery of **Window Functions** in SQL (`LAG`, `LEAD`, `FIRST_VALUE`).
- Proves the student understands **privacy-first measurement** (Post-iOS 14 cookie decay) and won't blindly trust ad network reporting.

---

### Project 2: B2B SaaS Customer Lifecycle & Cohort Retention Analysis

**Target Focus:** B2B SaaS & Product-Led Growth (PLG) (e.g., Snowflake, Notion, Figma, HubSpot)

#### The Problem

A freemium B2B SaaS company sees declining Net Revenue Retention (NRR). The VP of Growth wants to identify which user onboarding paths lead to long-term enterprise conversions vs. early churn.

#### What Students Build

- **Data Stack:** Snowflake / BigQuery, Python (Lifelines, Plotly), dbt (data build tool).
- **Cohort & Funnel Modeling:** Use dbt to transform product activity logs into a unified SaaS metric datamart:
- **Product Metrics:** Product-Qualified Leads (PQLs), activation rate, feature adoption.
- **Revenue Metrics:** MRR, ARR, CAC payback period, Churn Rate, NRR.

- **Retention Analysis:** Perform survival analysis in Python (Kaplan-Meier estimates) to predict when users churn and identify the "aha moment" feature (e.g., inviting 3 teammates within 7 days).
- **Deliverable:** A dbt project + executive memo detailing product levers that decrease churn by $X or boost free-to-paid conversion by Y%.

#### Why Bay Area Recruiters Care

- **dbt + Snowflake** is the standard analytical stack across Silicon Valley startups.
- Connects **product analytics (usage) with financial outcomes (ARR/NRR)**, bridging marketing, product, and finance teams.

---

### Project 3: AI-Assisted Marketing Mix Modeling (MMM) & Forecasting

**Target Focus:** Enterprise, Multi-Channel Tech, Growth Analytics (e.g., Uber, Gap Inc., Apple)

#### The Problem

With third-party cookies phased out, privacy regulations restrict granular user tracking. The company needs a macro-level top-down model to understand how offline (sponsorships, TV) and digital spend drive revenue.

#### What Students Build

- **Data Stack:** Python (PyMC or Meta’s LightweightMMM/Robyn framework), LLM API integrations (Claude/OpenAI), Looker / Sigma.
- **Adstock & Saturation Modeling:** Build a Bayesian time-series model in Python that accounts for:
- **Adstock (Carryover effect):** Memory lingering after seeing an ad.
- **Diminishing Returns:** Identifying the saturation point for channel budgets.

- **AI Copilot Workflow:** Build an automated Python pipeline using LLMs to ingest MMM results, draft campaign summaries, and alert marketers when channels hit diminishing returns.
- **Deliverable:** A channel optimization curve tool and automated insight generator predicting next quarter's revenue based on custom marketing budget allocations.

#### Why Bay Area Recruiters Care

- Bay Area companies expect analysts to be **AI-native**—using LLMs for analytical automation, not just text drafting.
- MMM is the most requested advanced marketing data skill in modern growth teams due to privacy shifts.

---

### 💡 Portfolio Presentation Standard for Your Bootcamp

To ensure graduates get interviews in the Bay Area, each project repository should follow this rule:

1. **No Jupyter Notebooks as the final output:** Code must be structured as production `.py` files, modular SQL models, or interactive web applications (Streamlit/Evidence.dev).
2. **Business First, Math Second:** Each GitHub README must open with an **Executive Summary** highlighting the financial recommendation (e.g., _"Reallocating $45K from Meta to Google Search lowers overall CAC by 14%"_).
3. **Live Links:** Include live interactive app links and recorded video walkthroughs (Loom) so non-technical hiring managers can evaluate their communication skills immediately.

--

이 프로젝트 3개 중 가장 중요한 프로젝트가 뭐야

지원하시는 목표 직무(Role Target)에 따라 가장 중요한 프로젝트가 명확히 달라집니다.

하지만 실리콘밸리/산호세 현지 테크 기업 채용 시장의 수급과 유행을 기준으로 딱 하나만 꼽아야 한다면, Project 1: Multi-Touch Attribution & Incrementality Engine이 단연 1위입니다.

🏆 지원 직무별 가장 중요한 프로젝트
[ 지원 목표 직무 ] ──────────────────> [ 최우선 프로젝트 ]

1. Growth Analyst / Growth Marketing ──> Project 1 (Attribution & Incrementality)
2. Marketing Analyst / MarTech ──> Project 1 (Attribution & Incrementality)
3. Product Analyst / Product Growth ──> Project 2 (SaaS Cohort & Retention)
4. Senior Analytics / Lead Growth ──> Project 3 (AI-Assisted MMM)
   🥇 왜 Project 1이 가장 강력하고 중요한가?
5. 현지 기업들이 가장 골머리를 썩이는 문제 (High Pain Point)
   실리콘밸리 B2C/B2B 테크 기업들은 Meta, Google, TikTok, LinkedIn 등에 매달 수십만~수백만 달러의 광고비를 씁니다. 하지만 Apple의 iOS 14+ 프라이버시 정책 강화 이후 "어떤 광고가 진짜 매출을 일으켰는가?"를 밝혀내는 것이 현지 Growth팀의 최우선 과제가 되었습니다. Project 1은 이 문제를 정확히 타겟팅합니다.

6. SQL 테크닉을 가장 확실하게 보여주는 프로젝트
   면접관(Hiring Manager)이 분석가의 기술력을 검증할 때 SQL Window Functions(LAG, LEAD, FIRST_VALUE, SUM OVER) 능력을 가장 중점적으로 봅니다. Project 1의 터치포인트 정렬 및 기여도 분배 로직은 수강생의 하드 스킬(SQL 수준)을 증명하기에 가장 완벽한 주제입니다.

7. 단순 '분석'을 넘어 '비즈니스 성과(ROI)'로 직결
   "대시보드를 만들었습니다" 수준에 그치지 않고, "플랫폼의 허위 리포팅을 가려내어 실제 예산 $100K를 재배치하고 CAC를 X% 낮췄다"는 가장 직관적이고 강력한 임팩트를 보여줄 수 있습니다.

💡 2위, 3위 프로젝트는 언제 빛을 발하나요?
Project 2 (SaaS Retention)가 1위가 되는 경우:

지원하는 회사가 Snowflake, Notion, Figma 같은 B2B PLG(Product-Led Growth) SaaS 기업일 때입니다.

이때는 마케팅 채널보다 "제품 안에서 유저가 어떻게 행동하고 언제 결제/이탈하는가"가 훨씬 중요해지므로 Project 2가 메인 카드가 됩니다.

Project 3 (AI-Assisted MMM)의 역할:

최근 산호세/실리콘밸리 기업들은 모든 직군에 "AI를 업무 흐름(Workflow)에 얼마나 접목할 수 있는가?"를 물어봅니다.

Project 3은 메인 서사라기보다는 "최신 고급 통계(MMM)도 할 줄 알고, LLM API를 연결해 분석 자동화도 할 줄 아는 최첨단 분석가"라는 차별화(Edge) 포인트를 더해주는 필살기 역할을 합니다.

📌 한 줄 요약
포트폴리오의 메인 대표작(Hero Project)은 Project 1으로 배치하시고, 지원하는 회사의 성격(B2C 마케팅 중심 vs B2B 프로덕트 중심)에 따라 Project 2를 메인으로 교체하여 어필하시는 전략을 추천합니다.
