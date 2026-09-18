"""
Insurance Lead Intelligence — Synthetic Data Generator
Generates 6 months of realistic raw data for:
  - raw_ad_performance
  - raw_quote_events
  - raw_leads
  - raw_routing_attempts
  - raw_partners
  - raw_revenue_events

Run: python scripts/generate_synthetic_data.py
Output: data/raw/*.csv

Design targets (realistic insurance lead gen):
  - ~7,500 leads submitted (35K sessions × ~22% CVR)
  - Platform overclaim: 10-22% above warehouse (not 98%)
  - Portfolio ROAS: ~0.85-0.95x (near break-even, some campaigns above)
  - Partner acceptance: 64-85% range
"""

import csv
import random
import uuid
from datetime import datetime, timedelta, date
from collections import defaultdict
from pathlib import Path

random.seed(42)

# ─── Config ───────────────────────────────────────────────────────────────────

START_DATE = date(2025, 1, 1)
END_DATE   = date(2025, 6, 30)
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "raw"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CHANNELS  = ["google", "meta", "affiliate", "organic", "direct"]
VERTICALS = ["auto", "home", "health", "life"]
DEVICES   = ["desktop", "mobile", "tablet"]
STATES    = ["CA", "TX", "FL", "NY", "OH", "PA", "IL", "GA", "NC", "MI"]

CAMPAIGNS = [
    {"campaign_id": "C001", "channel": "google",    "vertical": "auto",   "state_focus": ["CA","TX","FL"]},
    {"campaign_id": "C002", "channel": "google",    "vertical": "home",   "state_focus": ["NY","PA","OH"]},
    {"campaign_id": "C003", "channel": "meta",      "vertical": "auto",   "state_focus": ["CA","TX","GA"]},
    {"campaign_id": "C004", "channel": "meta",      "vertical": "health", "state_focus": ["FL","NC","IL"]},
    {"campaign_id": "C005", "channel": "affiliate", "vertical": "life",   "state_focus": ["MI","OH","NY"]},
    {"campaign_id": "C006", "channel": "organic",   "vertical": "auto",   "state_focus": STATES},
    {"campaign_id": "C007", "channel": "direct",    "vertical": "home",   "state_focus": STATES},
]

PARTNERS = [
    # Realistic US insurance lead payout rates (CPL model, carrier-side)
    # Auto: $55-80, Home: $65-85, Health: $90-110, Life: $110-135
    {"partner_id": "P001", "name": "Progressive Direct",   "verticals": ["auto"],              "states": STATES,               "capacity": 50,  "base_payout": 65.00},
    {"partner_id": "P002", "name": "State Farm Network",   "verticals": ["auto","home"],       "states": STATES,               "capacity": 80,  "base_payout": 75.00},
    {"partner_id": "P003", "name": "Allstate Connect",     "verticals": ["auto","home"],       "states": STATES,               "capacity": 60,  "base_payout": 68.00},
    {"partner_id": "P004", "name": "BlueCross Health",     "verticals": ["health"],            "states": ["CA","TX","FL","NY"], "capacity": 40,  "base_payout": 95.00},
    {"partner_id": "P005", "name": "UnitedHealth Direct",  "verticals": ["health"],            "states": STATES,               "capacity": 55,  "base_payout": 105.00},
    {"partner_id": "P006", "name": "MetLife Life",         "verticals": ["life"],              "states": STATES,               "capacity": 30,  "base_payout": 118.00},
    {"partner_id": "P007", "name": "Prudential Life",      "verticals": ["life"],              "states": STATES,               "capacity": 25,  "base_payout": 128.00},
    {"partner_id": "P008", "name": "Farmers Home",         "verticals": ["home"],              "states": ["CA","TX","FL","IL"], "capacity": 35,  "base_payout": 78.00},
    {"partner_id": "P009", "name": "Liberty Mutual Auto",  "verticals": ["auto"],              "states": STATES,               "capacity": 70,  "base_payout": 58.00},
    {"partner_id": "P010", "name": "Nationwide Multi",     "verticals": ["auto","home","life"],"states": STATES,               "capacity": 90,  "base_payout": 72.00},
]

# Partner acceptance rates — realistic spread: some below 70% (at-risk), most 70-85%
PARTNER_ACCEPTANCE = {
    "P001": 0.78, "P002": 0.83, "P003": 0.71, "P004": 0.86, "P005": 0.80,
    "P006": 0.74, "P007": 0.68, "P008": 0.76, "P009": 0.63, "P010": 0.73,
}

# Channel quality → valid lead rate
CHANNEL_QUALITY = {
    "google": 0.88, "meta": 0.72, "affiliate": 0.65,
    "organic": 0.92, "direct": 0.90,
}

# Platform overclaim factor by channel (how much platforms inflate vs warehouse reality)
# Realistic range: 8-25%
CHANNEL_OVERCLAIM = {
    "google":    (1.08, 1.18),   # Google: 8-18% overclaim
    "meta":      (1.15, 1.25),   # Meta: 15-25% overclaim (worst offender)
    "affiliate": (1.10, 1.22),   # Affiliate: 10-22% overclaim
}

# ─── Helpers ──────────────────────────────────────────────────────────────────

def date_range(start: date, end: date):
    for n in range((end - start).days + 1):
        yield start + timedelta(n)

def rand_ts(d: date, hour_min=7, hour_max=22):
    h = random.randint(hour_min, hour_max)
    m = random.randint(0, 59)
    s = random.randint(0, 59)
    return datetime(d.year, d.month, d.day, h, m, s)

def uid(prefix=""):
    return prefix + str(uuid.uuid4()).replace("-", "")[:12].upper()

def weighted_choice(items, weights):
    return random.choices(items, weights=weights, k=1)[0]

# ─── 1. raw_partners ──────────────────────────────────────────────────────────

def generate_partners():
    rows = []
    for p in PARTNERS:
        rows.append({
            "partner_id":            p["partner_id"],
            "partner_name":          p["name"],
            "insurance_verticals":   "|".join(p["verticals"]),
            "accepted_states":       "|".join(p["states"]),
            "active_status":         "active",
            "minimum_quality_score": random.randint(40, 60),
            "daily_lead_capacity":   p["capacity"],
            "pricing_model":         random.choice(["cpl", "cpa"]),
            "base_payout":           p["base_payout"],
            "created_at":            "2023-01-01",
        })
    return rows

# ─── 2. raw_quote_events + raw_leads ─────────────────────────────────────────
#   Generated FIRST so ad_performance can be calibrated to actual lead counts.

def generate_quote_events_and_leads(total_sessions=35000):
    events = []
    leads  = []

    for i in range(total_sessions):
        d = START_DATE + timedelta(days=random.randint(0, (END_DATE - START_DATE).days))

        channel = weighted_choice(CHANNELS, weights=[35, 25, 15, 15, 10])
        # Pick randomly among ALL campaigns for this channel (not just the first)
        channel_camps = [c for c in CAMPAIGNS if c["channel"] == channel]
        camp = random.choice(channel_camps) if channel_camps else None
        campaign_id = camp["campaign_id"] if camp else None
        vertical    = camp["vertical"]    if camp else random.choice(VERTICALS)

        state     = random.choice(STATES)
        device    = weighted_choice(DEVICES, weights=[45, 45, 10])
        session_id   = uid("S")
        quote_id     = uid("Q")
        customer_id  = uid("CUS")
        base_ts      = rand_ts(d)

        # Funnel pass-through probabilities
        funnel_steps = [
            ("landing_page_view",             1.00),
            ("quote_started",                 0.60),
            ("contact_information_completed", 0.75),
            ("insurance_details_completed",   0.72),
            ("quote_completed",               0.85),
            ("lead_submitted",                0.80),
        ]

        reached = []
        ts = base_ts
        for event_name, prob in funnel_steps:
            if random.random() > prob:
                break
            ts = ts + timedelta(seconds=random.randint(15, 300))
            reached.append((event_name, ts))
            events.append({
                "event_id":           uid("E"),
                "customer_id":        customer_id,
                "session_id":         session_id,
                "quote_id":           quote_id,
                "event_timestamp":    ts.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "event_name":         event_name,
                "channel":            channel,
                "campaign_id":        campaign_id,
                "utm_source":         channel,
                "utm_medium":         "cpc" if channel in ("google","meta") else channel,
                "utm_campaign":       campaign_id,
                "device_type":        device,
                "insurance_vertical": vertical,
                "state":              state,
            })

        if reached and reached[-1][0] == "lead_submitted":
            lead_id      = uid("L")
            submitted_ts = reached[-1][1]

            quality      = CHANNEL_QUALITY.get(channel, 0.80)
            is_duplicate = random.random() < 0.06
            is_fraud     = random.random() < 0.02
            is_valid     = (not is_duplicate) and (not is_fraud) and (random.random() < quality)
            rejection    = None
            if is_duplicate:
                rejection = "duplicate"
            elif is_fraud:
                rejection = "suspected_fraud"
            elif not is_valid:
                rejection = random.choice(["low_quality_score", "ineligible_state", "missing_fields"])

            leads.append({
                "lead_id":            lead_id,
                "quote_id":           quote_id,
                "customer_id":        customer_id,
                "campaign_id":        campaign_id,
                "channel":            channel,
                "submitted_at":       submitted_ts.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "insurance_vertical": vertical,
                "state":              state,
                "device_type":        device,
                "lead_quality_score": random.randint(30, 100),
                "is_valid":           str(is_valid).upper(),
                "is_duplicate":       str(is_duplicate).upper(),
                "is_test_lead":       "FALSE",
                "is_suspected_fraud": str(is_fraud).upper(),
                "rejection_reason":   rejection or "",
                "lead_status":        "valid" if is_valid else "rejected",
            })

    return events, leads

# ─── 3. raw_ad_performance ────────────────────────────────────────────────────
#   Generated AFTER leads so platform_reported_leads = actual × overclaim_factor.
#   This ensures overclaim is always in the realistic 10-25% range.

def generate_ad_performance(leads):
    # Build actual warehouse leads per (campaign_id, date)
    daily_actual = defaultdict(int)
    for lead in leads:
        day     = lead["submitted_at"][:10]
        camp_id = lead["campaign_id"]
        if camp_id and camp_id not in ("C006", "C007"):  # only paid campaigns
            daily_actual[(camp_id, day)] += 1

    rows = []
    for d in date_range(START_DATE, END_DATE):
        for camp in CAMPAIGNS:
            if camp["channel"] in ("organic", "direct"):
                continue  # no paid spend for organic/direct

            ch  = camp["channel"]
            base_spend = {"google": 300, "meta": 200, "affiliate": 100}[ch]
            dow_mult   = 1.2 if d.weekday() < 5 else 0.7
            spend      = round(base_spend * dow_mult * random.uniform(0.8, 1.3), 2)

            impressions = int(spend * random.uniform(80, 150))
            clicks      = int(impressions * random.uniform(0.02, 0.06))

            # Platform reported leads = actual warehouse leads × overclaim factor
            # On days with 0 actual leads, platform still reports 0-2 (attribution noise)
            actual = daily_actual.get((camp["campaign_id"], d.isoformat()), 0)
            lo, hi = CHANNEL_OVERCLAIM[ch]
            overclaim_factor = random.uniform(lo, hi)

            if actual > 0:
                platform_leads = max(actual + 1, round(actual * overclaim_factor))
            else:
                # Low-probability noise even on zero-lead days
                platform_leads = random.choices([0, 1, 2], weights=[75, 20, 5])[0]

            # Platform conversions and revenue (platform further inflates)
            platform_conversions = int(platform_leads * random.uniform(1.02, 1.08))
            platform_revenue     = round(platform_conversions * random.uniform(35, 65), 2)

            state = random.choice(camp["state_focus"])

            rows.append({
                "performance_date":              d.isoformat(),
                "channel":                       ch,
                "campaign_id":                   camp["campaign_id"],
                "insurance_vertical":            camp["vertical"],
                "state":                         state,
                "spend":                         spend,
                "impressions":                   impressions,
                "clicks":                        clicks,
                "platform_reported_leads":       platform_leads,
                "platform_reported_conversions": platform_conversions,
                "platform_reported_revenue":     platform_revenue,
            })
    return rows

# ─── 4. raw_routing_attempts + raw_revenue_events ────────────────────────────

def generate_routing_and_revenue(leads):
    routing = []
    revenue = []

    for lead in leads:
        if lead["is_valid"] != "TRUE":
            continue

        vertical     = lead["insurance_vertical"]
        state        = lead["state"]
        submitted_ts = datetime.strptime(lead["submitted_at"], "%Y-%m-%d %H:%M:%S UTC")

        eligible = [
            p for p in PARTNERS
            if vertical in p["verticals"] and state in p["states"]
        ]
        if not eligible:
            continue

        n_attempts = weighted_choice([1, 2, 3], weights=[60, 30, 10])
        chosen     = random.sample(eligible, min(n_attempts, len(eligible)))

        for priority, partner in enumerate(chosen, start=1):
            attempt_id  = uid("RA")
            routed_ts   = submitted_ts + timedelta(seconds=random.randint(5, 60))
            accept_rate = PARTNER_ACCEPTANCE[partner["partner_id"]]

            quality_adj = int(lead["lead_quality_score"]) / 100
            final_rate  = accept_rate * (0.7 + 0.3 * quality_adj)

            accepted = random.random() < final_rate
            if accepted:
                response_status = "accepted"
            else:
                response_status = random.choice(["rejected", "no_response", "capacity_exceeded"])

            resp_ts = routed_ts + timedelta(seconds=random.randint(10, 300))

            routing.append({
                "routing_attempt_id": attempt_id,
                "lead_id":            lead["lead_id"],
                "partner_id":         partner["partner_id"],
                "routed_at":          routed_ts.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "routing_priority":   priority,
                "bid_amount":         round(partner["base_payout"] * random.uniform(0.85, 1.15), 2),
                "delivery_status":    "delivered",
                "response_status":    response_status,
                "response_timestamp": resp_ts.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "rejection_reason":   "" if accepted else random.choice(
                    ["price_too_low", "capacity", "quality", "state_not_covered"]),
            })

            if accepted:
                rev_ts = resp_ts + timedelta(seconds=random.randint(60, 3600))
                payout = round(partner["base_payout"] * random.uniform(0.90, 1.20), 2)
                revenue.append({
                    "revenue_event_id":   uid("REV"),
                    "lead_id":            lead["lead_id"],
                    "partner_id":         partner["partner_id"],
                    "revenue_timestamp":  rev_ts.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "revenue_type":       "lead_sale",
                    "revenue_amount":     payout,
                    "transaction_status": "confirmed",
                })
                break  # Stop routing once accepted

    return routing, revenue

# ─── Write CSVs ───────────────────────────────────────────────────────────────

def write_csv(filename, rows):
    if not rows:
        print(f"  ⚠️  No rows for {filename}")
        return
    path = OUTPUT_DIR / filename
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  ✅  {filename:40s}  {len(rows):>6,} rows  →  {path}")

# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n🔧  Generating Insurance Lead Intelligence synthetic data...")
    print(f"    Period : {START_DATE} → {END_DATE}")
    print(f"    Output : {OUTPUT_DIR}\n")

    # Order matters: leads first → ad performance calibrated to actual lead counts
    partners            = generate_partners()
    events, leads       = generate_quote_events_and_leads(total_sessions=35000)
    ad_perf             = generate_ad_performance(leads)
    routing, revenue    = generate_routing_and_revenue(leads)

    write_csv("raw_partners.csv",         partners)
    write_csv("raw_ad_performance.csv",   ad_perf)
    write_csv("raw_quote_events.csv",     events)
    write_csv("raw_leads.csv",            leads)
    write_csv("raw_routing_attempts.csv", routing)
    write_csv("raw_revenue_events.csv",   revenue)

    print("\n📊  Summary")
    print(f"    Partners            : {len(partners)}")
    print(f"    Ad performance rows : {len(ad_perf)}")
    print(f"    Quote events        : {len(events)}")
    print(f"    Leads submitted     : {len(leads)}")
    valid    = sum(1 for l in leads if l["is_valid"] == "TRUE")
    dups     = sum(1 for l in leads if l["is_duplicate"] == "TRUE")
    print(f"      → Valid           : {valid}  ({valid/len(leads)*100:.1f}%)")
    print(f"      → Duplicates      : {dups}   ({dups/len(leads)*100:.1f}%)")

    plat_total = sum(r["platform_reported_leads"] for r in ad_perf)
    wh_paid    = sum(1 for l in leads if l["campaign_id"] not in (None, "C006", "C007"))
    print(f"\n    Platform leads (paid) : {plat_total:,}")
    print(f"    Warehouse leads (paid): {wh_paid:,}")
    if plat_total > 0:
        print(f"    Overclaim rate        : {(plat_total-wh_paid)/plat_total:.1%}")

    print(f"\n    Routing attempts    : {len(routing)}")
    accepted = sum(1 for r in routing if r["response_status"] == "accepted")
    print(f"      → Accepted        : {accepted}  ({accepted/len(routing)*100:.1f}%)")
    print(f"    Revenue events      : {len(revenue)}")
    total_rev  = sum(float(r["revenue_amount"]) for r in revenue)
    total_spend = sum(float(r["spend"]) for r in ad_perf)
    print(f"      → Total revenue   : ${total_rev:,.0f}")
    print(f"      → Total spend     : ${total_spend:,.0f}")
    print(f"      → ROAS            : {total_rev/total_spend:.2f}x")
    print("\n✅  Done.\n")
