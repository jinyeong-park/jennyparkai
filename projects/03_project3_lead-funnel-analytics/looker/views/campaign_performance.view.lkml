# ============================================================
# View: campaign_performance
# Source: mart_campaign_performance
# Grain: campaign_id × month
#
# Business question: "C002 has a lower CPL than C001.
# Should we shift budget?"
#
# CPL alone is misleading — a cheap lead that never converts
# generates zero revenue. This view connects spend → leads →
# revenue so you can compare CPL AND ROAS side by side.
# ============================================================

view: campaign_performance {
  sql_table_name: `insurance-lead-intelligence.insurance_analytics_marts.mart_campaign_performance` ;;

  # ── Dimensions ───────────────────────────────────────────

  # Surrogate primary key: grain is campaign × month, so campaign_id alone is not unique.
  # Looker uses primary_key to prevent fan-out on joins — must be unique per row.
  dimension: campaign_month_key {
    primary_key: yes
    hidden:      yes
    type:        string
    sql:         CONCAT(${TABLE}.campaign_id, '|', CAST(${TABLE}.month AS STRING)) ;;
    description: "Surrogate key: campaign_id + month"
  }

  dimension: campaign_id {
    type:        string
    sql:         ${TABLE}.campaign_id ;;
    description: "Campaign identifier (C001–C007)"
  }

  dimension_group: month {
    type:        time
    timeframes:  [month, quarter, year]
    datatype:    date
    sql:         ${TABLE}.month ;;
    description: "Month the campaign ran"
  }

  dimension: channel {
    type:        string
    sql:         ${TABLE}.channel ;;
    description: "Ad channel: google, meta, affiliate, organic, direct"
  }

  dimension: insurance_vertical {
    type:        string
    sql:         ${TABLE}.insurance_vertical ;;
    description: "Insurance type: auto, home, life, health"
  }

  # ── Spend & Traffic Measures ─────────────────────────────

  measure: total_spend {
    type:             sum
    sql:              ${TABLE}.total_spend ;;
    value_format_name: usd
    description:      "Total ad spend across campaigns"
    drill_fields:     [campaign_id, channel, total_spend]
  }

  measure: total_impressions {
    type:        sum
    sql:         ${TABLE}.impressions ;;
    description: "Total impressions served"
  }

  measure: total_clicks {
    type:        sum
    sql:         ${TABLE}.clicks ;;
    description: "Total clicks"
  }

  # CTR and CPC are ratio metrics — averaging them gives wrong results.
  # AVG(ctr across rows) ignores that each row has different impression volume.
  # Correct: recompute from summed numerator / summed denominator (volume-weighted).
  measure: avg_ctr {
    type:             number
    sql:              SAFE_DIVIDE(${total_clicks}, ${total_impressions}) ;;
    value_format_name: percent_2
    description:      "Click-through rate: total clicks / total impressions (volume-weighted)"
  }

  measure: avg_cpc {
    type:             number
    sql:              SAFE_DIVIDE(${total_spend}, ${total_clicks}) ;;
    value_format_name: usd
    description:      "Cost per click: total spend / total clicks (volume-weighted)"
  }

  # ── Lead Volume & Quality Measures ───────────────────────

  measure: total_warehouse_leads {
    type:        sum
    sql:         ${TABLE}.warehouse_leads ;;
    description: "Leads recorded in our warehouse (verified count)"
    drill_fields: [campaign_id, channel, total_warehouse_leads]
  }

  measure: total_platform_leads {
    type:        sum
    sql:         ${TABLE}.platform_reported_leads ;;
    description: "Leads claimed by the ad platform (may include overcounting)"
  }

  measure: total_valid_leads {
    type:        sum
    sql:         ${TABLE}.valid_leads ;;
    description: "Leads that passed validation (not duplicate, correct format)"
  }

  measure: total_duplicate_leads {
    type:        sum
    sql:         ${TABLE}.duplicate_leads ;;
    description: "Leads flagged as duplicates"
  }

  measure: valid_lead_rate {
    type:             number
    sql:              SAFE_DIVIDE(${total_valid_leads}, ${total_warehouse_leads}) ;;
    value_format_name: percent_1
    description:      "% of submitted leads that are valid. Low rate = quality problem."
    drill_fields:     [campaign_id, channel, valid_lead_rate]
  }

  measure: platform_overclaim_rate {
    type:             number
    sql:              SAFE_DIVIDE(${total_platform_leads} - ${total_warehouse_leads}, NULLIF(${total_platform_leads}, 0)) ;;
    value_format_name: percent_1
    description:      "% more conversions the platform claims vs warehouse. Meta 15-40%, Google 5-20%."
    drill_fields:     [campaign_id, channel, platform_overclaim_rate]
  }

  # ── Revenue & Efficiency Measures ────────────────────────

  measure: total_revenue {
    type:             sum
    sql:              ${TABLE}.total_revenue ;;
    value_format_name: usd
    description:      "Total verified revenue from this campaign"
    drill_fields:     [campaign_id, channel, total_revenue]
  }

  measure: cpl {
    type:             number
    sql:              SAFE_DIVIDE(${total_spend}, ${total_warehouse_leads}) ;;
    value_format_name: usd
    description:      "Cost per lead. WARNING: low CPL ≠ good ROI if valid_lead_rate is low."
    drill_fields:     [campaign_id, channel, cpl, valid_lead_rate]
  }

  measure: cost_per_valid_lead {
    type:             number
    sql:              SAFE_DIVIDE(${total_spend}, ${total_valid_leads}) ;;
    value_format_name: usd
    description:      "Cost per valid (non-duplicate, validated) lead — more meaningful than CPL"
  }

  measure: revenue_per_lead {
    type:             number
    sql:              SAFE_DIVIDE(${total_revenue}, ${total_warehouse_leads}) ;;
    value_format_name: usd
    description:      "Revenue generated per submitted lead"
  }

  measure: roas {
    type:             number
    sql:              SAFE_DIVIDE(${total_revenue}, ${total_spend}) ;;
    value_format_name: decimal_2
    description:      "Return on ad spend (revenue / spend). >1.0 = profitable."
    drill_fields:     [campaign_id, channel, roas, cpl]
  }

  measure: roi {
    type:             number
    sql:              SAFE_DIVIDE(${total_revenue} - ${total_spend}, ${total_spend}) ;;
    value_format_name: percent_1
    description:      "Return on investment ((revenue - spend) / spend)"
  }
}
