# Product Tracking Plan

## Instrumentation Principles

Emit events at the moment a user completes an action. Include a stable event ID, event timestamp, user ID, organization ID, session context where applicable, and an event-version field so metric definitions can evolve without silently changing history.

| Event | Trigger | Required properties |
| --- | --- | --- |
| `sign_up_completed` | User completes account signup | `user_id`, `org_id`, `signup_method`, `acquisition_source`, `company_size`, `region`, `event_version` |
| `workspace_created` | A workspace is successfully created | `user_id`, `org_id`, `workspace_id`, `template_selected`, `event_version` |
| `teammate_invited` | An invite is sent | `user_id`, `org_id`, `invitee_role`, `invite_method`, `event_version` |
| `integration_connected` | An integration connection succeeds | `user_id`, `org_id`, `integration_name`, `connection_method`, `event_version` |
| `project_created` | A project is created | `user_id`, `org_id`, `project_id`, `template_selected`, `event_version` |
| `dashboard_viewed` | A dashboard is viewed | `user_id`, `org_id`, `dashboard_id`, `view_context`, `event_version` |
| `report_exported` | A report export completes | `user_id`, `org_id`, `report_id`, `export_format`, `event_version` |
| `checkout_initiated` | A billing checkout begins | `user_id`, `org_id`, `plan_type`, `billing_interval`, `price_shown`, `event_version` |
| `trial_started` | A trial begins | `user_id`, `org_id`, `plan_type`, `trial_length_days`, `event_version` |
| `paid_conversion` | A trial or free account becomes paid | `user_id`, `org_id`, `plan_type`, `mrr_amount`, `billing_interval`, `event_version` |
| `support_ticket_created` | A support ticket is created | `user_id`, `org_id`, `ticket_category`, `priority`, `channel`, `event_version` |
| `subscription_canceled` | A subscription cancellation completes | `user_id`, `org_id`, `plan_type`, `mrr_amount`, `cancellation_reason`, `tenure_days`, `event_version` |

## Experiment Properties

For any event generated while a user is eligible for onboarding, attach `experiment_id`, `variant`, and `assignment_timestamp`. Assignment must occur before the first treatment-specific experience and remain stable for the account.

## Data Quality Checks

- Reject events missing `event_id`, `event_timestamp`, `user_id`, or `org_id`.
- Maintain a versioned event dictionary and alert on unexpected event-name or property-value changes.
- Reconcile `paid_conversion` and `subscription_canceled` events to billing-system records.
- Monitor duplicate-event rates and late-arriving event rates before publishing experiment or retention metrics.
