# ============================================================
# View: attribution
# Source: mart_attribution
# Grain: one row per lead_id
#
# Business question: "Google Search shows strong ROAS in the
# platform dashboard. But is Google the FIRST channel users
# interact with — or are they coming from organic/social first?"
#
# submitted_channel = last session before submission (last touch)
# first_touch_channel = earliest recorded touchpoint
# ~15% of leads have a different first vs last touch channel.
# ============================================================

view: attribution {
  sql_table_name: `insurance-lead-intelligence.insurance_analytics_marts.mart_attribution` ;;

  # ── Dimensions ───────────────────────────────────────────

  dimension: lead_id {
    primary_key: yes
    type:        string
    sql:         ${TABLE}.lead_id ;;
    description: "Unique lead identifier"
  }

  dimension: campaign_id {
    type:        string
    sql:         ${TABLE}.campaign_id ;;
    description: "Campaign that submitted the lead"
  }

  dimension: submitted_channel {
    type:        string
    sql:         ${TABLE}.submitted_channel ;;
    description: "Channel at time of lead submission (last touch)"
  }

  dimension: first_touch_channel {
    type:        string
    sql:         ${TABLE}.first_touch_channel ;;
    description: "Channel of the earliest quote event before submission (first touch)"
  }

  dimension: first_touch_campaign {
    type:        string
    sql:         ${TABLE}.first_touch_campaign ;;
    description: "Campaign of the earliest quote event (first touch)"
  }

  dimension_group: submitted {
    type:        time
    timeframes:  [date, week, month, quarter]
    datatype:    date
    sql:         ${TABLE}.submitted_date ;;
    description: "Date the lead was submitted"
  }

  dimension: insurance_vertical {
    type:        string
    sql:         ${TABLE}.insurance_vertical ;;
    description: "Insurance type: auto, home, life, health"
  }

  dimension: state {
    type:        string
    sql:         ${TABLE}.state ;;
    description: "US state of the lead"
    map_layer_name: us_states
  }

  dimension: is_valid {
    type:        yesno
    sql:         ${TABLE}.is_valid ;;
    description: "Whether the lead passed validation"
  }

  dimension: is_duplicate {
    type:        yesno
    sql:         ${TABLE}.is_duplicate ;;
    description: "Whether the lead is a duplicate"
  }

  dimension: is_monetized {
    type:        yesno
    sql:         ${TABLE}.is_monetized ;;
    description: "Whether this lead generated any revenue"
  }

  dimension: is_multi_touch {
    type:        yesno
    sql:         ${TABLE}.touchpoint_count > 1 ;;
    description: "True if the user had more than one touchpoint before submitting"
  }

  dimension: channel_changed {
    type:        yesno
    sql:         ${TABLE}.first_touch_channel != ${TABLE}.submitted_channel ;;
    description: "True if first-touch and submitted channel are different (cross-channel journey)"
  }

  dimension: hours_to_submit {
    type:        number
    sql:         ${TABLE}.hours_to_submit ;;
    description: "Hours from first touchpoint to lead submission. <1h = direct intent; >24h = discovery journey."
  }

  dimension: hours_to_submit_tier {
    type:  string
    sql:   CASE
             WHEN ${TABLE}.hours_to_submit < 1  THEN '< 1 hour'
             WHEN ${TABLE}.hours_to_submit < 6  THEN '1–6 hours'
             WHEN ${TABLE}.hours_to_submit < 24 THEN '6–24 hours'
             ELSE '24+ hours'
           END ;;
    description: "Bucketed time from first touch to submission"
  }

  dimension: touchpoint_count {
    type:        number
    sql:         ${TABLE}.touchpoint_count ;;
    description: "Number of quote events before submission"
  }

  # ── Lead Count Measures ───────────────────────────────────

  measure: total_leads {
    type:        count_distinct
    sql:         ${TABLE}.lead_id ;;
    description: "Total unique leads"
    drill_fields: [lead_id, submitted_channel, first_touch_channel, insurance_vertical, state]
  }

  measure: total_valid_leads {
    type:        count_distinct
    sql:         CASE WHEN ${TABLE}.is_valid THEN ${TABLE}.lead_id END ;;
    description: "Valid (non-duplicate, validated) leads"
  }

  measure: total_monetized_leads {
    type:        count_distinct
    sql:         CASE WHEN ${TABLE}.is_monetized THEN ${TABLE}.lead_id END ;;
    description: "Leads that generated revenue"
  }

  measure: multi_touch_rate {
    type:             number
    sql:              SAFE_DIVIDE(
                        COUNT(DISTINCT CASE WHEN ${TABLE}.touchpoint_count > 1 THEN ${TABLE}.lead_id END),
                        COUNT(DISTINCT ${TABLE}.lead_id)
                      ) ;;
    value_format_name: percent_1
    description:      "% of leads with more than one touchpoint before submitting"
  }

  measure: channel_switch_rate {
    type:             number
    sql:              SAFE_DIVIDE(
                        COUNT(DISTINCT CASE WHEN ${TABLE}.first_touch_channel != ${TABLE}.submitted_channel THEN ${TABLE}.lead_id END),
                        COUNT(DISTINCT ${TABLE}.lead_id)
                      ) ;;
    value_format_name: percent_1
    description:      "% of leads where first-touch ≠ submitted channel. ~15% in this dataset."
  }

  # ── Revenue Measures ──────────────────────────────────────

  measure: total_revenue {
    type:             sum
    sql:              ${TABLE}.revenue_amount ;;
    value_format_name: usd
    description:      "Total revenue from leads in this segment"
    drill_fields:     [first_touch_channel, submitted_channel, total_revenue, total_leads]
  }

  measure: revenue_per_lead {
    type:             number
    sql:              SAFE_DIVIDE(${total_revenue}, ${total_leads}) ;;
    value_format_name: usd
    description:      "Revenue per lead. Organic first-touch typically higher than paid."
    drill_fields:     [first_touch_channel, revenue_per_lead]
  }

  measure: avg_hours_to_submit {
    type:             average
    sql:              ${TABLE}.hours_to_submit ;;
    value_format_name: decimal_1
    description:      "Average hours from first touch to lead submission by channel"
    drill_fields:     [first_touch_channel, avg_hours_to_submit]
  }
}
