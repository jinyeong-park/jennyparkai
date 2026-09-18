# ============================================================
# Model: insurance_analytics
# Project: insurance-lead-intelligence
#
# This model defines 4 Explores — one per analytical question:
#   1. campaign_performance  → spend + leads + ROAS by campaign
#   2. lead_funnel           → session-to-lead conversion funnel
#   3. partner_performance   → acceptance rates + partner revenue
#   4. attribution           → first-touch vs last-touch channel
#
# mart_reconciliation is accessed via its own explore so
# analysts can compare platform vs warehouse numbers directly.
#
# Design decisions:
#   - Each explore reads a pre-aggregated mart (not raw tables)
#     → no fan-out risk, no complex joins in Looker
#   - attribution explore joins campaign_performance on campaign_id
#     to layer in spend context alongside first-touch revenue
#   - reconciliation is a standalone explore (no joins needed —
#     the mart already has both platform and warehouse columns)
# ============================================================

connection: "insurance_lead_intelligence"

include: "/looker/views/*.view.lkml"

# ── Explore 1: Campaign Performance ──────────────────────────
# Answers: "Which campaign delivers the best ROAS? Where should
# we shift budget?"

explore: campaign_performance {
  label:       "Campaign Performance"
  description: "Ad spend, leads, and revenue by campaign and month. Use this to compare CPL vs ROAS across campaigns."

  join: attribution {
    type:        left_outer
    sql_on:      ${campaign_performance.campaign_id} = ${attribution.campaign_id} ;;
    relationship: one_to_many
    # Fan-out note: campaign_performance is aggregated (1 row per campaign × month).
    # Joining attribution (1 row per lead) creates a fan-out for aggregated measures.
    # Use measures from attribution view directly; don't SUM campaign_performance
    # spend fields when this join is active.
    fields:      [
      attribution.total_leads,
      attribution.total_valid_leads,
      attribution.total_monetized_leads,
      attribution.channel_switch_rate,
      attribution.multi_touch_rate,
      attribution.avg_hours_to_submit
    ]
  }
}

# ── Explore 2: Lead Funnel ────────────────────────────────────
# Answers: "Lead volume went up 20% but revenue stayed flat.
# Where is the funnel breaking — top, middle, or bottom?"

explore: lead_funnel {
  label:       "Lead Funnel"
  description: "Session → quote → completion → lead → valid lead conversion rates by channel and vertical."
}

# ── Explore 3: Partner Performance ───────────────────────────
# Answers: "P003's acceptance rate dropped. Real trend or
# one-day fluke? Which partner has the best revenue per lead?"

explore: partner_performance {
  label:       "Partner Performance"
  description: "Daily partner acceptance rates, 7-day rolling trends, response speed, and revenue. Use date filters to spot declining trends."
}

# ── Explore 4: Attribution ────────────────────────────────────
# Answers: "Is Google actually driving first-touch awareness,
# or are users discovering us via organic/social first?"

explore: attribution {
  label:       "Attribution (First Touch)"
  description: "First-touch vs last-touch channel comparison. ~15% of leads have different first and submitted channels."
}

# ── Explore 5: Reconciliation ─────────────────────────────────
# Answers: "Meta claims 144 conversions. Our warehouse shows 132.
# Which number is right? How much does each platform overclaim?"

explore: reconciliation {
  label:       "Platform Reconciliation"
  description: "Platform-reported leads vs warehouse-verified leads by channel and month. Use this before sharing ROAS numbers with stakeholders."
}
