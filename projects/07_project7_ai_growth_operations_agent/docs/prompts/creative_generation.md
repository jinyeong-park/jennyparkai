# Creative Generation Task

## Brief Context

- **Brief ID:** {brief_id}
- **Persona:** {persona}
- **Channel:** {channel}
- **Hook Type:** {hook_type}
- **Messaging Territory:** {messaging_territory}

## Strategic Inputs

- **Primary Pain:** {primary_pain}
- **Desired Outcome:** {desired_outcome}
- **Primary Barrier:** {primary_barrier}
- **Primary Hook (approved):** {primary_hook}

## Format Constraints

- **Format:** {format}
- **Channel Copy Limits:** {channel_copy_limits}

## Generation Instructions

Generate **{n_variants}** distinct creative variants.

Each variant must vary **{variable_tested}** while keeping all other strategic elements constant. Do not change the persona, channel, proof mechanism, or core value proposition between variants — only the declared variable should differ.

Variant IDs must follow the convention: `{brief_id}_v1`, `{brief_id}_v2`, etc.

Each variant must include:
- `variant_id`: `{brief_id}_v1`, `{brief_id}_v2`, etc.
- `brief_id`: `{brief_id}`
- `creative_id`: same as the brief's creative_id
- `experiment_id`: same as the brief's experiment_id
- `persona`: `{persona}`
- `channel`: `{channel}`
- `format`: `{format}`
- `hook_type`: the hook type for this specific variant (may vary if hook_type is the variable_tested)
- `headline`: channel-compliant headline (META max 40 chars)
- `primary_text`: channel-compliant body copy (LINKEDIN/TIKTOK max 150 chars)
- `cta`: one of the approved CTAs
- `visual_concept`: specific direction for a producer — no generic descriptions
- `opening_3_seconds`: null if not a video format; otherwise a specific scene description
- `hypothesis`: copied verbatim from the brief — do not alter
- `variable_tested`: `{variable_tested}`
- `compliance_notes`: carried forward from the brief plus any new copy-specific notes
- `prompt_template_version`: `"creative_generation_v1"`
- `provider`: set by the system, leave as empty string `""`
- `model`: set by the system, leave as null
- `brief_version`: `"1.0"`
- `generation_timestamp`: set by the system, leave as empty string `""`
- `run_id`: set by the system, leave as empty string `""`
- `review_status`: `"pending"`
- `validation_findings`: `[]`
- `data_origin`: `"SYNTHETIC"`

## Quality Standards

Each variant must:
1. Feel distinct from the other variants — different opening angle, tone shift, or copy approach
2. Stay true to the persona's voice and concerns
3. Contain no prohibited claims (no guaranteed results, no specific revenue percentages, no competitor names)
4. Include a visual_concept specific enough for a producer to execute without a briefing call
5. Have a CTA that matches the stage of awareness (`{persona}` on `{channel}`)

Output only a valid JSON array starting with `[` and ending with `]`. No prose.
