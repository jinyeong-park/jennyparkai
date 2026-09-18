# ============================================================
# View: reconciliation
# Source: mart_reconciliation
# Grain: channel × month
#
# Business question: "Meta Ads Manager says we got 144
# conversions. Our warehouse shows 132 leads. Which is right —
# and why is there a gap?"
#
# This view puts platform numbers and warehouse numbers side
# by side. The warehouse number is always the verified source
# of truth for budget decisions.
# ============================================================

view: reconciliation {
  sql_table_name: `insurance-lead-intelligence.insurance_analytics_marts.mart_reconciliation` ;;

  # ── Dimensions ───────────────────────────────────────────

  dimension: reconciliation_key {
    primary_key: yes
    hidden:      yes
    type:        string
    sql:         CONCAT(${TABLE}.channel, '|', CAST(${TABLE}.month AS STRING)) ;;
    description: "Surrogate key: channel + month"
  }

  dimension_group: month {
    type:        time
    timeframes:  [month, quarter, year]
    datatype:    date
    sql:         ${TABLE}.month ;;
    description: "Month"
  }

  dimension: channel {
    type:        string
    sql:         ${TABLE}.channel ;;
    description: "Ad channel: google, meta, affiliate, organic, direct"
  }

  # ── Lead Count Measures ───────────────────────────────────

  measure: total_platform_leads {
    type:        sum
    sql:         ${TABLE}.platform_leads ;;
    description: "Leads claimed by the ad platform (overcounts due to attribution windows, pixel errors)"
    drill_fields: [channel, month_month, total_platform_leads]
  }

  measure: total_warehouse_leads {
    type:        sum
    sql:         ${TABLE}.warehouse_leads ;;
    description: "Leads verified in our warehouse — the source of truth"
    drill_fields: [channel, month_month, total_warehouse_leads]
  }

  measure: total_valid_leads {
    type:        sum
    sql:         ${TABLE}.valid_leads ;;
    description: "Subset of warehouse leads that passed validation"
  }

  measure: total_lead_discrepancy {
    type:        sum
    sql:         ${TABLE}.lead_discrepancy ;;
    description: "platform_leads − warehouse_leads. Positive = platform overclaims."
    drill_fields: [channel, total_lead_discrepancy, platform_overclaim_rate]
  }

  # ── Platform Overclaim Measure ────────────────────────────

  measure: platform_overclaim_rate {
    type:             number
    sql:              SAFE_DIVIDE(${total_platform_leads} - ${total_warehouse_leads}, NULLIF(${total_platform_leads}, 0)) ;;
    value_format_name: percent_1
    description:      "% by which platform overclaims vs warehouse. Meta 15-40%, Google 5-20%."
    drill_fields:     [channel, month_month, platform_overclaim_rate, total_platform_leads, total_warehouse_leads]
  }

  # ── Spend & Revenue Measures ─────────────────────────────

  measure: total_spend {
    type:             sum
    sql:              ${TABLE}.total_spend ;;
    value_format_name: usd
    description:      "Total ad spend (from ad platform)"
  }

  measure: total_platform_revenue {
    type:             sum
    sql:              ${TABLE}.platform_revenue ;;
    value_format_name: usd
    description:      "Revenue reported by ad platform (inflated by same attribution issues)"
  }

  # ── Derived ROAS Measures ─────────────────────────────────

  measure: platform_roas {
    type:             number
    sql:              SAFE_DIVIDE(${total_platform_revenue}, ${total_spend}) ;;
    value_format_name: decimal_2
    description:      "ROAS as reported by platform. Inflated — use only for platform benchmarking."
  }

  measure: cpl_warehouse {
    type:             number
    sql:              SAFE_DIVIDE(${total_spend}, ${total_warehouse_leads}) ;;
    value_format_name: usd
    description:      "Cost per lead using verified warehouse count. More accurate than platform CPL."
    drill_fields:     [channel, cpl_warehouse, platform_overclaim_rate]
  }
}
