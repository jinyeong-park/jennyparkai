# ============================================================
# View: lead_funnel
# Source: mart_lead_funnel
# Grain: channel × vertical × month
#
# Business question: "Lead volume went up 20% but revenue
# stayed flat. Where is the funnel breaking?"
#
# This view tracks the full conversion funnel from session →
# quote start → completion → lead submitted → valid lead.
# Drop-off at each step points to where to fix.
# ============================================================

view: lead_funnel {
  sql_table_name: `insurance-lead-intelligence.insurance_analytics_marts.mart_lead_funnel` ;;

  # ── Dimensions ───────────────────────────────────────────

  dimension: funnel_key {
    primary_key: yes
    hidden:      yes
    type:        string
    sql:         CONCAT(${TABLE}.channel, '|', ${TABLE}.insurance_vertical, '|', CAST(${TABLE}.month AS STRING)) ;;
    description: "Surrogate key: channel + vertical + month"
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

  dimension: insurance_vertical {
    type:        string
    sql:         ${TABLE}.insurance_vertical ;;
    description: "Insurance type: auto, home, life, health"
  }

  # ── Funnel Volume Measures ────────────────────────────────

  measure: total_sessions {
    type:        sum
    sql:         ${TABLE}.sessions ;;
    description: "Total user sessions (top of funnel)"
    drill_fields: [channel, insurance_vertical, total_sessions]
  }

  measure: total_quote_starts {
    type:        sum
    sql:         ${TABLE}.quote_starts ;;
    description: "Sessions where user started a quote"
  }

  measure: total_quote_completions {
    type:        sum
    sql:         ${TABLE}.quote_completions ;;
    description: "Sessions where user completed the quote form"
  }

  measure: total_leads_submitted {
    type:        sum
    sql:         ${TABLE}.leads_submitted ;;
    description: "Leads submitted to our system"
    drill_fields: [channel, insurance_vertical, total_leads_submitted]
  }

  measure: total_valid_leads {
    type:        sum
    sql:         ${TABLE}.valid_leads ;;
    description: "Leads that passed validation"
  }

  measure: total_duplicate_leads {
    type:        sum
    sql:         ${TABLE}.duplicate_leads ;;
    description: "Leads flagged as duplicates"
  }

  # ── Funnel Rate Measures ──────────────────────────────────

  measure: session_to_quote_rate {
    type:             number
    sql:              SAFE_DIVIDE(${total_quote_starts}, ${total_sessions}) ;;
    value_format_name: percent_1
    description:      "% of sessions that started a quote. Low = acquisition or UX issue at top of funnel."
    drill_fields:     [channel, session_to_quote_rate]
  }

  measure: quote_to_completion_rate {
    type:             number
    sql:              SAFE_DIVIDE(${total_quote_completions}, ${total_quote_starts}) ;;
    value_format_name: percent_1
    description:      "% of quote starts that were completed. Low = form friction or confusing UX."
    drill_fields:     [channel, quote_to_completion_rate]
  }

  measure: completion_to_lead_rate {
    type:             number
    sql:              SAFE_DIVIDE(${total_leads_submitted}, ${total_quote_completions}) ;;
    value_format_name: percent_1
    description:      "% of completions that became submitted leads. Should be near 100%."
  }

  measure: overall_cvr {
    type:             number
    sql:              SAFE_DIVIDE(${total_leads_submitted}, ${total_sessions}) ;;
    value_format_name: percent_2
    description:      "Session-to-lead conversion rate. The headline funnel efficiency metric."
    drill_fields:     [channel, insurance_vertical, overall_cvr, session_to_quote_rate, quote_to_completion_rate]
  }

  measure: valid_lead_rate {
    type:             number
    sql:              SAFE_DIVIDE(${total_valid_leads}, ${total_leads_submitted}) ;;
    value_format_name: percent_1
    description:      "% of leads that are valid. Affiliate ~65%, Google/organic 88-92%."
    drill_fields:     [channel, valid_lead_rate]
  }

  measure: duplicate_rate {
    type:             number
    sql:              SAFE_DIVIDE(${total_duplicate_leads}, ${total_leads_submitted}) ;;
    value_format_name: percent_1
    description:      "% of leads that are duplicates. High rate = retargeting overlap or data quality issue."
  }
}
