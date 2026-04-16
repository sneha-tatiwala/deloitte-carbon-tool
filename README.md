# Carbon Intelligence India

A prototype CCTS compliance and policy intelligence tool built for India's carbon advisory market. Demonstrates what a client-facing platform could look like for a firm advising industrial companies under India's Carbon Credit Trading Scheme.

Built independently as a portfolio project. Not affiliated with or authorised by Deloitte Touche Tohmatsu Limited.

---

## What This Is

Three components:

**1. CCTS Compliance Calculator**
Takes a company's sector, annual production, and emission intensity and calculates:
- Compliance status (over-complier / under-complier / at threshold)
- CCC surplus or deficit in tonnes CO₂e
- Financial exposure at three price scenarios (₹150 / ₹250 / ₹600 per tCO₂e)
- Sector peer benchmark percentile
- Advisory service recommendations mapped to compliance position

**2. Policy Intelligence Tracker**
Searchable, filterable database of 31 India climate and environmental policies from 1972 to 2070 — historical foundations, the 2022–2024 legislative reform wave, active programs, and forthcoming commitments.

**3. AI Chat Assistant**
Domain-specific assistant covering CCTS mechanics, carbon price signals, sector benchmarks, MRV, BRSR, PAT transition, and India's broader climate policy landscape.

---

## Python Engine

The calculation logic is implemented in `calculator.py` as a standalone module — the source of truth for all compliance calculations. The JavaScript frontend mirrors this logic exactly.

```bash
# Run the test suite
python3 -m pytest test_calculator.py -v
```

**45 tests across 9 classes:**

| Test Class | What It Covers |
|---|---|
| `TestInputValidation` | Invalid sector keys, negative production, negative intensity |
| `TestIntensityFallback` | Sector average used when intensity not provided |
| `TestComplianceStatus` | Over-complier, under-complier, at-threshold classification |
| `TestCCCDelta` | CCC surplus/deficit calculation across sectors |
| `TestPriceScenarios` | Floor/expected/ceiling financial exposure |
| `TestBenchmarks` | Percentile interpolation across four reference points |
| `TestRecommendations` | Service recommendations mapped to compliance position |
| `TestListSectors` | Sector registry integrity |
| `TestAllSectorsSmoke` | Parametrized smoke test across all 10 sectors |

### Key constants

```python
PRICE_FLOOR_INR     = 150    # ₹/tCO₂e
PRICE_EXPECTED_INR  = 250
PRICE_CEILING_INR   = 600
INR_TO_USD          = 0.012  # ~₹84.5/USD, April 2026
```

### Calculation methodology

```python
ccts_target  = sector_baseline × (1 − reduction_target_pct)
ccc_delta    = (actual_intensity − ccts_target) × annual_production
exposure_inr = ccc_delta × price_inr
```

Positive `ccc_delta` = deficit (entity must buy CCCs).  
Negative `ccc_delta` = surplus (entity can sell CCCs).

Benchmark percentile uses linear interpolation across four reference points: worst performer (40% above sector average → 0th percentile), sector average (50th), top quartile (75th), best-in-class (20% below top quartile → 100th).

---

## CCTS Sector Coverage

| Sector | Baseline (tCO₂e/unit) | Target Notified? | Share of CCTS Emissions |
|---|---|---|---|
| Cement | 0.719 / tonne cement | Yes (BEE FY2026) | 28% |
| Iron & Steel | 2.21 / tonne crude steel | No (proxy applied) | 30% |
| Aluminium | 13.2 / tonne aluminium | Yes (BEE FY2026) | 6% |
| Chlor-Alkali | 2.05 / tonne Cl equivalent | Yes (BEE FY2026) | 3% |
| Petroleum Refining | 0.058 / tonne crude throughput | No | 7% |
| Petrochemicals | 1.18 / tonne product | No | 5% |
| Textiles | 3.85 / tonne product | No | 10% |
| Fertilisers | 2.95 / tonne urea equivalent | No | 8% |
| Pulp & Paper | 1.02 / tonne paper | No | 3% |
| Cement (Clinker) | 0.845 / tonne clinker | Yes (BEE FY2026) | 18% |

Iron, steel, and cement together account for 76% of total CCTS-covered emissions.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Calculation engine | Python 3, dataclasses, enums |
| Test suite | pytest (45 tests) |
| Frontend | Vanilla JS, HTML, CSS |
| AI assistant | Claude via OpenRouter API |
| Server | Express (local dev) / Vercel serverless (production) |
| Fonts | Inter (Google Fonts) |

---

## Local Development

```bash
# Install dependencies
npm install

# Add your OpenRouter API key
echo "OPENROUTER_API_KEY=your_key_here" > .env

# Start the server
npm start
# → http://localhost:3001

# Run Python tests
pip3 install pytest
python3 -m pytest test_calculator.py -v
```

---

## Data Sources

- BEE Carbon Credit Trading Scheme Notification, June 2023
- MoEFCC CCTS Sector-Specific Emission Intensity Targets, FY2026
- UNFCCC India NDC Registry (2015, 2022, 2035)
- IEA India Energy & Emissions Data 2023–24
- WSA World Steel Association India GHG Benchmarks 2024
- CII Cement Sector GHG Benchmark Report 2024
- McKinsey — Decarbonising India, October 2022
- Climate Action Tracker — India Country Profile 2026
- PIB, MoEFCC, MNRE, BEE, PRS India (policy notifications)

---

## Scope and Limitations

- All sector baseline intensities for non-notified sectors are third-party estimates from industry benchmarks, not BEE's individual entity survey. Actual compliance positions may differ materially.
- Financial outputs use an indicative INR/USD rate. Verify before any financial decision.
- This tool does not cover voluntary carbon market project development (Verra VCS, Gold Standard, CDM legacy).
- MVP uses static data. A production version would automate updates via scheduled scraping of open-access government sources.

---

*Prototype demonstration only. Not for legal or compliance advice. Built April 2026.*
