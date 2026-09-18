# ============================================================
# View: partner_performance
# Source: mart_partner_performance
# Grain: partner_id × date
#
# Business question: "P003's acceptance rate dropped from 71%
# to 45% over two weeks. Is this a real trend or noise?"
#
# This view surfaces daily acceptance rate (volatility) vs
# 7-day rolling rate (trend) so ops can tell the difference
# between a one-day fluke and a capacity/quality problem.
# ============================================================

view: partner_performance {
  sql_table_name: `insurance-lead-intelligence.insurance_analytics_marts.mart_partner_performance` ;;

  # ── Dimensions ───────────────────────────────────────────

  dimension: partner_date_key {
    primary_key: yes
    hidden:      yes
    type:        string
    sql:         CONCAT(${TABLE}.partner_id, '|', CAST(${TABLE}.route_date AS STRING)) ;;
    description: "Surrogate key: partner_id + route_date"
  }

  dimension_group: route_date {
    type:        time
    timeframes:  [date, week, month, quarter]
    datatype:    date
    sql:         ${TABLE}.route_date ;;
    description: "Date leads were routed to this partner"
  }

  dimension: partner_id {
    type:        string
    sql:         ${TABLE}.partner_id ;;
    description: "Partner identifier (P001–P010)"
  }

  dimension: partner_name {
    type:        string
    sql:         ${TABLE}.partner_name ;;
    description: "Partner company name (e.g. Progressive, GEICO)"
  }

  dimension: insurance_verticals {
    type:        string
    sql:         ${TABLE}.insurance_verticals ;;
    description: "Comma-separated verticals this partner covers"
  }

  # ── Daily Routing Volume Measures ────────────────────────

  measure: total_leads_delivered {
    type:        sum
    sql:         ${TABLE}.leads_delivered ;;
    description: "Total leads routed to partners"
    drill_fields: [partner_name, route_date_date, total_leads_delivered]
  }

  measure: total_leads_accepted {
    type:        sum
    sql:         ${TABLE}.leads_accepted ;;
    description: "Leads accepted by partners"
  }

  measure: total_leads_rejected {
    type:        sum
    sql:         ${TABLE}.leads_rejected ;;
    description: "Leads explicitly rejected by partners"
  }

  measure: total_no_response {
    type:        sum
    sql:         ${TABLE}.no_response ;;
    description: "Leads with no response from partner (timeout)"
  }

  measure: total_capacity_exceeded {
    type:        sum
    sql:         ${TABLE}.capacity_exceeded ;;
    description: "Leads rejected due to partner capacity limits. Spike = partner hitting cap."
    drill_fields: [partner_name, route_date_date, total_capacity_exceeded]
  }

  # ── Acceptance Rate Measures ─────────────────────────────

  measure: acceptance_rate {
    type:             number
    sql:              SAFE_DIVIDE(${total_leads_accepted}, ${total_leads_delivered}) ;;
    value_format_name: percent_1
    description:      "Overall acceptance rate across selected date range (volume-weighted)"
    drill_fields:     [partner_name, route_date_date, acceptance_rate]
  }

  measure: avg_daily_acceptance_rate {
    type:             average
    sql:              ${TABLE}.daily_acceptance_rate ;;
    value_format_name: percent_1
    description:      "Simple average of daily acceptance rates. Use acceptance_rate for volume-weighted."
  }

  measure: avg_rolling_7d_acceptance_rate {
    type:             average
    sql:              ${TABLE}.rolling_7d_acceptance_rate ;;
    value_format_name: percent_1
    description:      "Average of the 7-day rolling acceptance rate. Smooths out daily noise."
    drill_fields:     [partner_name, route_date_date, avg_rolling_7d_acceptance_rate]
  }

  # ── Response Speed Measure ────────────────────────────────

  measure: avg_response_sec {
    type:             average
    sql:              ${TABLE}.avg_response_sec ;;
    value_format_name: decimal_1
    description:      "Average seconds for partner to respond. Faster responders tend to accept more."
    drill_fields:     [partner_name, avg_response_sec, acceptance_rate]
  }

  # ── Revenue Measures ──────────────────────────────────────

  measure: total_revenue {
    type:             sum
    sql:              ${TABLE}.daily_revenue ;;
    value_format_name: usd
    description:      "Total revenue from partner payouts"
    drill_fields:     [partner_name, route_date_date, total_revenue]
  }

  measure: revenue_per_delivered_lead {
    type:             number
    sql:              SAFE_DIVIDE(${total_revenue}, ${total_leads_delivered}) ;;
    value_format_name: usd
    description:      "Revenue per delivered lead. High acceptance rate + high revenue = strong partner."
    drill_fields:     [partner_name, revenue_per_delivered_lead, acceptance_rate]
  }

  measure: avg_rolling_7d_revenue {
    type:             average
    sql:              ${TABLE}.rolling_7d_revenue ;;
    value_format_name: usd
    description:      "Average 7-day rolling revenue per partner"
  }

  # cumulative_revenue is a running total computed in SQL.
  # Do NOT use this measure when multiple partners are selected — MAX picks the
  # last cumulative value per partner, which is only meaningful for a single partner.
  # For multi-partner revenue totals, use total_revenue (SUM of daily_revenue) instead.
  measure: total_cumulative_revenue {
    type:             max
    sql:              ${TABLE}.cumulative_revenue ;;
    value_format_name: usd
    description:      "Running total revenue per partner (use with single partner filter)"
  }
}
