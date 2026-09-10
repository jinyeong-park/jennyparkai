Write a complete, executable Python script named `generate_synthetic_data.py` using `pandas`, `numpy`, and `faker` (or standard libraries) to generate realistic Growth & Marketing Analytics datasets for a Multi-Touch Attribution & Incrementality project.

---

### 1. Requirements & Data Characteristics

1. **Volume & Timeframe:**
   - Timeframe: 6 months of historical data (e.g., 2026-01-01 to 2026-06-30).
   - Total Unique Users: ~10,000 users.
   - Total Conversions: ~3,000 purchases.
   - Total Touchpoints: ~15,000 to 20,000 click events.

2. **Geographic Coverage (DMAs):**
   - Distribute traffic across 50 US Designated Market Areas (DMAs) (e.g., `DMA_807_SAN_FRANCISCO`, `DMA_501_NEW_YORK`, `DMA_602_CHICAGO`, etc.).
   - Mark 10 specific DMAs as `Holdout_Control` DMAs, where Meta ad spend is intentionally set to $0 for the month of June 2026 (for Geo-Incrementality testing).

3. **Injected Data Anomalies & Noise (Crucial for SQL Cleaning Practice):**
   - **Case Inconsistency:** Mix case in UTM parameters and campaign names (e.g., `Meta`, `meta_paid_social`, `META`, `BlackFriday_2026`, `black_friday_2026`).
   - **Missing Values:** Insert ~5% `null` values in `utm_source`, `utm_medium`, and `campaign_name`.
   - **Duplicate Logs:** Introduce ~3% exact/near-duplicate click logs within 1 second of each other (simulating double-firing tracking pixels).
   - **Data Anomalies:** Create a few orphan conversions with no prior click logs.

4. **Multi-Touch User Journey Behaviors:**
   Simulate realistic conversion paths:
   - *Path A (Direct/Organic):* Organic Search -> Purchase (1 touchpoint, $0 ad cost).
   - *Path B (Multi-Channel):* Meta Ad Click -> Google Paid Search Click -> Email CRM Click -> Purchase (3-4 touchpoints over 1-14 days).
   - *Path C (Non-Converting):* Multiple Ad clicks -> Abandoned (No conversion).

---

### 2. Output File Schemas (Save as CSV in `data/raw/`)

Generates 3 CSV files with the following schemas:

#### File 1: `data/raw/raw_user_touchpoints.csv`
- `event_id` (UUID string)
- `user_id` (String, e.g., `USR_001923`)
- `timestamp` (Datetime string, ISO format)
- `channel` (e.g., `meta_paid_social`, `google_paid_search`, `google_organic`, `email_crm`, `tiktok_ads`)
- `utm_source`, `utm_medium`, `campaign_name` (Contains injected case noise and nulls)
- `dma_code` (e.g., `DMA_807_SAN_FRANCISCO`)

#### File 2: `data/raw/raw_conversions.csv`
- `conversion_id` (UUID string)
- `user_id` (Foreign key to touchpoints)
- `order_id` (String, e.g., `ORD_98212`)
- `converted_at` (Datetime string, timestamp AFTER the last touchpoint)
- `order_value_usd` (Float, log-normal distribution between $20.00 and $400.00)
- `dma_code` (Matching user's DMA)

#### File 3: `data/raw/raw_ad_spend.csv`
- `date` (YYYY-MM-DD)
- `channel` (e.g., `meta_paid_social`, `google_paid_search`, `tiktok_ads`)
- `dma_code` (DMA level daily spend)
- `daily_spend_usd` (Float, daily spend per channel per DMA)
- `platform_reported_conversions` (Integer: Intentionally over-reported by 30-40% compared to actual conversions to simulate ad platform self-attribution bias)

---

### 3. Deliverables
1. Complete Python code that creates the `data/raw/` directory automatically and exports the 3 clean/dirty CSV files.
2. Output printed summaries showing total rows, conversion rates, and missing value counts for verification.