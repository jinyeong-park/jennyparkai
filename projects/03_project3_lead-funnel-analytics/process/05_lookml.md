# Phase 4: LookML Semantic Layer

> **Core Question:** How do we define business metrics once so every dashboard uses the same definition?

---

## What LookML Does

```
BigQuery mart tables
        ↓
LookML (views + model + explores)
        ↓
Looker generates SQL automatically
        ↓
Dashboards always use consistent, governed metrics
```

Without LookML, every dashboard tile could calculate `acceptance_rate` differently.
With LookML, it's defined once and reused everywhere.

---

## File Structure

```
looker/
├── models/
│   └── insurance_analytics.model.lkml   ← connection + explore definitions
├── views/
│   ├── lead_funnel.view.lkml            ← mart_lead_funnel
│   ├── campaign_performance.view.lkml   ← mart_campaign_performance
│   ├── partner_performance.view.lkml    ← mart_partner_performance
│   ├── attribution.view.lkml            ← mart_attribution
│   └── reconciliation.view.lkml         ← mart_reconciliation
└── dashboards/
    └── (built in Looker UI)
```

---

## The Three Building Blocks

**View** — a single mart table with its fields defined.
Each view file maps to one BigQuery mart table and declares which columns are dimensions (for filtering/grouping) and which are measures (for aggregation). Think of it as "what data exists and what can you do with it."

**Model** — the entry point that wires everything together.
It declares the database connection and lists which explores are available. One model file per project; users never edit it directly.

**Explore** — what analysts actually interact with in the Looker UI.
An explore exposes one or more views as a self-service query surface. Analysts pick dimensions and measures here without writing any SQL — Looker generates the query automatically.

```
View   →  defines the fields (what columns exist, how to calculate them)
Model  →  defines the connection and registers the explores
Explore → exposes views to end users as a query interface
```

---

## Core LookML Concepts Used

### View → maps to one mart table

```lookml
view: campaign_performance {
  sql_table_name: `insurance-lead-intelligence.insurance_analytics_marts.mart_campaign_performance` ;;
  ...
}
```

### Dimension → a column you filter or group by

```lookml
dimension: channel {
  type: string
  sql: ${TABLE}.channel ;;
}

dimension: month {
  type: date_month
  sql: ${TABLE}.month ;;
}
```

### Measure → a calculated metric (never filter by a measure)

```lookml
measure: total_spend {
  type: sum
  sql: ${TABLE}.total_spend ;;
  value_format_name: usd
}

-- ❌ WRONG: type: average on a pre-computed ratio column
-- AVG(cpl) across rows = simple average of daily rates = ignores volume differences
measure: cpl {
  type: average          -- wrong for ratio metrics
  sql: ${TABLE}.cpl ;;
  value_format_name: usd
}

-- ✅ CORRECT: type: number, recompute from summed numerator / denominator
measure: cpl {
  type: number
  sql: SAFE_DIVIDE(${total_spend}, ${total_warehouse_leads}) ;;
  value_format_name: usd
}

-- ❌ WRONG: AVG of daily acceptance rates ignores that each day has different lead volume
measure: acceptance_rate {
  type: average
  sql: ${TABLE}.daily_acceptance_rate ;;
  value_format_name: percent_1
}

-- ✅ CORRECT: volume-weighted rate from summed accepted / summed delivered
measure: acceptance_rate {
  type: number
  sql: SAFE_DIVIDE(${total_leads_accepted}, ${total_leads_delivered}) ;;
  value_format_name: percent_1
}
```

### Explore → what users see in the Looker UI

```lookml
explore: campaign_performance {
  label: "Campaign Performance"
  description: "Spend, CPL, revenue per lead, and ROAS by campaign and channel"
}
```

---

## Key Design Decisions

### 1. One view per mart (not one view per raw table)

```
❌ Views on raw tables → complex joins in every explore
✅ Views on mart tables → joins already done in SQL, LookML stays simple
```

### 2. `value_format_name` in LookML, not in the dashboard

```lookml
-- ✅ Define formatting here once (use type: number for derived ratios, not type: average)
measure: revenue_per_lead {
  type: number
  sql: SAFE_DIVIDE(${total_revenue}, ${total_warehouse_leads}) ;;
  value_format_name: usd     -- shows as $46.67 everywhere
}
```

### 3. `primary_key` on every view

Prevents fanout when views are joined.

```lookml
dimension: lead_id {
  primary_key: yes
  type: string
  sql: ${TABLE}.lead_id ;;
}
```

### 4. Drill fields — click a number to see the rows behind it

```lookml
measure: leads_submitted {
  type: sum
  sql: ${TABLE}.leads_submitted ;;
  drill_fields: [lead_detail*]     -- clicking the number shows these fields
}

set: lead_detail {
  fields: [month, channel, insurance_vertical, leads_submitted, valid_lead_rate, overall_cvr]
}
```

---

## Interview Q&A

### Q. LookML에서 dimension이랑 measure 차이가 뭔가요?

**Dimension**은 데이터를 필터링하거나 그룹핑하는 데 쓰는 컬럼입니다.
`channel`, `month`, `campaign_id`처럼 "어떤 기준으로 쪼갤 것인가"에 해당합니다.

**Measure**는 숫자를 계산하는 메트릭입니다.
`total_spend`, `cpl`, `roas`처럼 "얼마인가"에 해당합니다.

핵심 차이는 **집계 여부**입니다.
Dimension은 raw 값 그대로 쓰고, measure는 SUM / COUNT / SAFE_DIVIDE 같은 집계 로직이 들어갑니다.

```lookml
-- Dimension: 그룹핑 기준, 집계 없음
dimension: channel {
  type: string
  sql: ${TABLE}.channel ;;
}

-- Measure: 집계 계산, 필터/그룹핑 불가
measure: total_spend {
  type: sum
  sql: ${TABLE}.total_spend ;;
  value_format_name: usd
}
```

실무에서 자주 하는 실수는 measure를 WHERE 조건에 쓰려는 것인데,
measure는 집계 후 값이라 필터링 단계에서 존재하지 않습니다.
필터가 필요하면 dimension 기준으로 걸어야 합니다.

---

### Q. 비율 메트릭(CPL, acceptance rate)을 LookML에서 어떻게 정의하나요?

`type: average`로 정의하면 안 됩니다.
각 행의 비율을 단순 평균하면 볼륨 차이를 무시하기 때문입니다.

예를 들어 CPL을 `AVG(cpl)`로 계산하면:
- 1월: spend $100, leads 10 → CPL $10
- 2월: spend $1,000, leads 10 → CPL $100
- AVG = **$55** ← 틀림
- 올바른 계산: $1,100 / 20 = **$55**가 우연히 같지만, leads 수가 다르면 결과가 완전히 달라집니다.

올바른 방법은 **분자와 분모를 각각 SUM한 뒤 나누는 것**입니다.

```lookml
-- ❌ 잘못된 방법: 각 행의 비율을 단순 평균
measure: cpl {
  type: average
  sql: ${TABLE}.cpl ;;
}

-- ✅ 올바른 방법: 분자/분모를 각각 합산 후 나눔
measure: cpl {
  type: number
  sql: SAFE_DIVIDE(${total_spend}, ${total_warehouse_leads}) ;;
  value_format_name: usd
}

-- ✅ acceptance_rate도 동일한 원칙
measure: acceptance_rate {
  type: number
  sql: SAFE_DIVIDE(${total_leads_accepted}, ${total_leads_delivered}) ;;
  value_format_name: percent_1
}
```

이 원칙은 LookML에만 해당하는 게 아니라 SQL에서 rolling window를 쓸 때도 동일합니다.
`mart_partner_performance`의 `rolling_7d_acceptance_rate`도 같은 이유로
`AVG(daily_acceptance_rate)`가 아닌 `SUM(accepted) / SUM(delivered)`로 계산했습니다.

---

## Status

| File | Status |
| ---- | ------ |
| `models/insurance_analytics.model.lkml` | ✅ Created |
| `views/lead_funnel.view.lkml` | ✅ Created |
| `views/campaign_performance.view.lkml` | ✅ Created |
| `views/partner_performance.view.lkml` | ✅ Created |
| `views/attribution.view.lkml` | ✅ Created |
| `views/reconciliation.view.lkml` | ✅ Created |
| Looker connection configured | ⏳ Next step |
| Explores validated | ⏳ Next step |
