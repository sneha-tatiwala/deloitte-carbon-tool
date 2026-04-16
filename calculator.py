"""
CCTS Compliance Calculator — Python Engine
==========================================
Deloitte India | Carbon Intelligence & CCTS Compliance Platform

Calculates a company's compliance position under India's Carbon Credit
Trading Scheme (CCTS 2023), notified under the Energy Conservation
(Amendment) Act 2022. First compliance period: FY2026 (April 2025 –
March 2026). Full secondary market trading: mid-2026.

Methodology
-----------
1. The CCTS sets sector-specific GHG emission *intensity* targets
   (tCO2e per unit of production output) for each obligated entity,
   based on their individual FY2023-24 baseline intensity.
2. This tool uses published Indian industry average intensities as
   proxies for the sector baseline where a company's individual
   baseline is not known.
3. The compliance gap is: (actual intensity − CCTS target intensity)
   × annual production output = CCC surplus (negative) or deficit
   (positive) in tonnes CO2e.
4. Financial exposure is calculated at three CCTS price scenarios
   reflecting the published price collar and expected market average.

Important Limitation
--------------------
Outputs are indicative, not legally binding. Each obligated entity's
actual CCTS target is set individually by MoEFCC against their own
FY2023-24 baseline. Where a company's individual baseline is unknown,
this tool substitutes the sector average — clearly flagged in all outputs.

Sources
-------
- BEE Carbon Credit Trading Scheme Notification, June 2023
- MoEFCC CCTS Sector-Specific Emission Intensity Targets, FY2026
- India Climate & Environment Policy Landscape Report, April 2026
- Carbon Footprint Trading in India: Mechanics, Markets, and the
  Role of Advisory Firms, April 2026
- CII / IEA India Energy & Emissions Data, 2024
- Bureau of Energy Efficiency (BEE) PAT Cycle Documentation

Author: Built as a portfolio demonstration for Deloitte India's
        Sustainability & Climate Practice.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


# ---------------------------------------------------------------------------
# Price Scenarios (CCTS Price Collar per BEE/CERC guidance)
# ---------------------------------------------------------------------------

PRICE_FLOOR_INR = 150       # ₹/tCO2e  — regulatory floor
PRICE_EXPECTED_INR = 250    # ₹/tCO2e  — expected market average at launch
PRICE_CEILING_INR = 600     # ₹/tCO2e  — regulatory ceiling
INR_TO_USD = 0.012          # approximate conversion rate (April 2026)

# ---------------------------------------------------------------------------
# Sector Data
# ---------------------------------------------------------------------------
# Each entry contains:
#   baseline_intensity   : Indian sector average tCO2e / unit output (FY2023-24)
#   reduction_target_pct : midpoint of BEE-notified % reduction range for FY2026
#   reduction_range      : (low, high) — actual BEE-notified range
#   ccts_target_intensity: baseline × (1 − reduction_target_pct)
#   top_quartile_intensity: best-performer benchmark (approx. top 25% of sector)
#   output_unit          : unit of production for emission intensity denominator
#   covered_entities     : approximate number of CCTS-obligated units (FY2026)
#   source               : citation for baseline intensity figure
#
# NOTE on Iron & Steel, Fertilisers, Petroleum Refining, Petrochemicals,
# Pulp & Paper, Textiles: reduction % targets had not been publicly
# notified at time of writing (noted as TBD in BEE documentation as of
# April 2026). Industry-standard reduction ranges of 3–6% applied as
# proxies, consistent with the notified sectors. Flagged in outputs.

SECTOR_DATA = {
    "cement": {
        "name": "Cement",
        "output_unit": "tonne of cement",
        "baseline_intensity": 0.719,
        "reduction_target_pct": 0.061,       # midpoint of 4.7%–7.6% (BEE notified)
        "reduction_range": (0.047, 0.076),
        "top_quartile_intensity": 0.610,
        "covered_entities": 180,
        "target_officially_notified": True,
        "source": (
            "BEE CCTS Sector Target Notification FY2026; "
            "CII Cement Sector GHG Benchmark 2024; "
            "IEA India Cement Emissions 2023"
        ),
    },
    "aluminium": {
        "name": "Aluminium",
        "output_unit": "tonne of aluminium",
        "baseline_intensity": 13.2,
        "reduction_target_pct": 0.049,       # midpoint of 2.8%–7.06% (BEE notified)
        "reduction_range": (0.028, 0.071),
        "top_quartile_intensity": 10.8,
        "covered_entities": 12,
        "target_officially_notified": True,
        "source": (
            "BEE CCTS Sector Target Notification FY2026; "
            "Aluminium Association of India Energy Benchmarks 2024; "
            "IEA Primary Aluminium GHG Data 2023"
        ),
    },
    "chlor_alkali": {
        "name": "Chlor-Alkali",
        "output_unit": "tonne of chlorine equivalent",
        "baseline_intensity": 2.05,
        "reduction_target_pct": 0.072,       # midpoint of 3.3%–11% (BEE notified)
        "reduction_range": (0.033, 0.110),
        "top_quartile_intensity": 1.60,
        "covered_entities": 35,
        "target_officially_notified": True,
        "source": (
            "BEE CCTS Sector Target Notification FY2026; "
            "ICC Chlor-Alkali Industry Report 2023"
        ),
    },
    "iron_steel": {
        "name": "Iron & Steel",
        "output_unit": "tonne of crude steel",
        "baseline_intensity": 2.21,
        "reduction_target_pct": 0.045,       # proxy — target TBD as of April 2026
        "reduction_range": (0.030, 0.060),
        "top_quartile_intensity": 1.75,
        "covered_entities": 35,
        "target_officially_notified": False,
        "source": (
            "BEE CCTS Documentation (target TBD as of April 2026); "
            "WSA World Steel Association India GHG Data 2024; "
            "McKinsey Decarbonising India Report 2022 — proxy range applied"
        ),
    },
    "cement_clinker": {
        "name": "Cement (Clinker sub-process)",
        "output_unit": "tonne of clinker",
        "baseline_intensity": 0.845,
        "reduction_target_pct": 0.061,
        "reduction_range": (0.047, 0.076),
        "top_quartile_intensity": 0.720,
        "covered_entities": 180,
        "target_officially_notified": True,
        "source": (
            "BEE CCTS Sector Target Notification FY2026; "
            "IEA Clinker Emission Factor India 2023"
        ),
    },
    "petroleum_refining": {
        "name": "Petroleum Refining",
        "output_unit": "tonne of crude throughput",
        "baseline_intensity": 0.058,
        "reduction_target_pct": 0.040,       # proxy — target TBD as of April 2026
        "reduction_range": (0.025, 0.055),
        "top_quartile_intensity": 0.042,
        "covered_entities": 23,
        "target_officially_notified": False,
        "source": (
            "BEE CCTS Documentation (target TBD as of April 2026); "
            "MoPNG Refinery Energy & Emissions Data 2024 — proxy range applied"
        ),
    },
    "petrochemicals": {
        "name": "Petrochemicals",
        "output_unit": "tonne of product",
        "baseline_intensity": 1.18,
        "reduction_target_pct": 0.042,       # proxy — target TBD as of April 2026
        "reduction_range": (0.025, 0.060),
        "top_quartile_intensity": 0.90,
        "covered_entities": 12,
        "target_officially_notified": False,
        "source": (
            "BEE CCTS Documentation (target TBD as of April 2026); "
            "IEA Chemicals & Petrochemicals India 2023 — proxy range applied"
        ),
    },
    "pulp_paper": {
        "name": "Pulp & Paper",
        "output_unit": "tonne of paper",
        "baseline_intensity": 1.02,
        "reduction_target_pct": 0.042,       # proxy — target TBD as of April 2026
        "reduction_range": (0.025, 0.060),
        "top_quartile_intensity": 0.72,
        "covered_entities": 22,
        "target_officially_notified": False,
        "source": (
            "BEE CCTS Documentation (target TBD as of April 2026); "
            "IPMA India Pulp & Paper GHG Benchmarks 2023 — proxy range applied"
        ),
    },
    "textiles": {
        "name": "Textiles",
        "output_unit": "tonne of product",
        "baseline_intensity": 3.85,
        "reduction_target_pct": 0.042,       # proxy — target TBD as of April 2026
        "reduction_range": (0.025, 0.060),
        "top_quartile_intensity": 2.80,
        "covered_entities": 180,
        "target_officially_notified": False,
        "source": (
            "BEE CCTS Documentation (target TBD as of April 2026); "
            "CITI Textiles Energy Benchmark Report 2023 — proxy range applied"
        ),
    },
    "fertilisers": {
        "name": "Fertilisers",
        "output_unit": "tonne of urea equivalent",
        "baseline_intensity": 2.95,
        "reduction_target_pct": 0.042,       # proxy — target TBD as of April 2026
        "reduction_range": (0.025, 0.060),
        "top_quartile_intensity": 2.30,
        "covered_entities": 30,
        "target_officially_notified": False,
        "source": (
            "BEE CCTS Documentation (target TBD as of April 2026); "
            "FAI Fertiliser Industry Statistics 2024 — proxy range applied"
        ),
    },
}


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

class ComplianceStatus(Enum):
    OVER_COMPLIER = "over_complier"       # intensity below target — can sell CCCs
    UNDER_COMPLIER = "under_complier"     # intensity above target — must buy CCCs
    AT_THRESHOLD = "at_threshold"         # within 2% of target


@dataclass
class PriceScenario:
    label: str
    price_inr: float
    price_usd: float
    total_exposure_inr: float             # positive = cost, negative = revenue
    total_exposure_usd: float
    per_unit_exposure_inr: float          # per tonne of production output
    per_unit_exposure_usd: float


@dataclass
class PeerBenchmark:
    sector_name: str
    user_intensity: float
    sector_average_intensity: float
    ccts_target_intensity: float
    top_quartile_intensity: float
    percentile_vs_sector: float           # estimated percentile (0=worst, 100=best)
    gap_to_target_pct: float              # % above(+) or below(-) CCTS target
    gap_to_top_quartile_pct: float        # % above(+) or below(-) top quartile
    output_unit: str


@dataclass
class DeloitteRecommendation:
    service: str
    description: str
    urgency: str                          # "Immediate", "Within 6 months", "Strategic"
    trigger: str                          # what in the company's result triggers this


@dataclass
class CCTSResult:
    # Inputs
    sector_key: str
    sector_name: str
    annual_production_tonnes: float
    actual_intensity: float
    intensity_was_estimated: bool         # True if user selected "I don't know"

    # Compliance position
    ccts_target_intensity: float
    compliance_status: ComplianceStatus
    ccc_delta_tonnes: float               # negative = surplus (can sell), positive = deficit (must buy)

    # Price scenarios
    price_scenarios: list[PriceScenario]

    # Benchmarks
    benchmark: PeerBenchmark

    # Deloitte recommendations
    recommendations: list[DeloitteRecommendation]

    # Metadata
    target_officially_notified: bool
    data_source: str
    methodology_note: str


# ---------------------------------------------------------------------------
# Deloitte Service Recommendations Logic
# ---------------------------------------------------------------------------

def _build_recommendations(
    status: ComplianceStatus,
    gap_to_target_pct: float,
    gap_to_top_quartile_pct: float,
    intensity_was_estimated: bool,
    target_officially_notified: bool,
) -> list[DeloitteRecommendation]:
    """
    Map the company's compliance position to Deloitte advisory services.
    Each recommendation is triggered by a specific condition in the result.
    """
    recs = []

    # MRV is always the first priority — it is the operational backbone of CCTS
    recs.append(DeloitteRecommendation(
        service="Monitoring, Reporting & Verification (MRV) Setup",
        description=(
            "CCTS compliance requires a BEE-approved Monitoring Plan and annual "
            "third-party verification by an accredited Carbon Verification Agency "
            "(ACVA) under ISO 14064. Deloitte's audit infrastructure provides "
            "verification capability for all 9 CCTS sectors. India currently faces "
            "a structural MRV capacity gap — early accreditation is a competitive "
            "advantage."
        ),
        urgency="Immediate",
        trigger="Required for all CCTS-obligated entities regardless of compliance position.",
    ))

    if status == ComplianceStatus.UNDER_COMPLIER:
        if gap_to_target_pct > 0.15:
            recs.append(DeloitteRecommendation(
                service="Decarbonisation Roadmap & Capital Planning",
                description=(
                    "Your emission intensity is significantly above the CCTS target. "
                    "Deloitte's decarbonisation advisory maps 100+ abatement levers "
                    "against your sector's specific process emissions (per McKinsey "
                    "Decarbonising India 2022 framework), prioritised by cost-per-tonne "
                    "and capital requirements. This becomes the basis for a credible "
                    "board-level net-zero strategy."
                ),
                urgency="Immediate",
                trigger=f"Emission intensity {gap_to_target_pct * 100:.1f}% above CCTS target — material compliance cost exposure.",
            ))
        recs.append(DeloitteRecommendation(
            service="CCC Procurement & Trading Advisory",
            description=(
                "As an under-complier, you must purchase Carbon Credit Certificates "
                "to cover your deficit. Deloitte advises on procurement strategy: "
                "bilateral OTC vs. exchange trading on IEX/PXIL/HPX, timing relative "
                "to price collar dynamics (₹150–₹600/tCO2e), and bankability "
                "provisions under CCTS rules."
            ),
            urgency="Within 6 months",
            trigger="Under-complier status requires CCC purchase before compliance period closes.",
        ))

    if status == ComplianceStatus.OVER_COMPLIER:
        recs.append(DeloitteRecommendation(
            service="CCC Monetisation & Carbon Revenue Strategy",
            description=(
                "Your emission intensity is below the CCTS target — you are eligible "
                "to receive and sell Carbon Credit Certificates. Deloitte advises on "
                "CCC issuance timing, pricing strategy relative to the market price "
                "collar, and long-term banking strategy given the expected price "
                "appreciation as CCTS targets tighten in successive compliance periods."
            ),
            urgency="Within 6 months",
            trigger="Over-complier status generates CCC surplus with monetisation potential.",
        ))

    # BRSR is relevant to all listed companies
    recs.append(DeloitteRecommendation(
        service="BRSR Core Assurance & Scope 3 Measurement",
        description=(
            "SEBI's BRSR framework mandates Scope 1, 2, and 3 GHG disclosures for "
            "India's top 1,000 listed companies (Scope 3 mandatory from FY2025–26 "
            "for top 250). Deloitte India's BRSR practice covers data collection, "
            "measurement, third-party assurance, and ESRS/GRI/ISSB alignment for "
            "companies with EU-facing operations. The Emissions Calculation Center "
            "(ECC) automates Scope 3 measurement across supply chains."
        ),
        urgency="Within 6 months",
        trigger="BRSR compliance obligation applies to all listed Indian companies.",
    ))

    if gap_to_top_quartile_pct > 0.20:
        recs.append(DeloitteRecommendation(
            service="Energy Efficiency & Process Optimisation",
            description=(
                "Your emission intensity is significantly above the top quartile in "
                "your sector. This gap represents both a compliance risk and a cost "
                "opportunity — energy is typically 30–60% of operating cost in "
                "CCTS-covered sectors. Deloitte's operational improvement practice "
                "identifies process-level efficiency levers with payback periods "
                "under three years."
            ),
            urgency="Strategic",
            trigger=f"Intensity {gap_to_top_quartile_pct * 100:.1f}% above sector top quartile — material efficiency gap.",
        ))

    if intensity_was_estimated:
        recs.append(DeloitteRecommendation(
            service="GHG Baseline Assessment & Data Quality Audit",
            description=(
                "This analysis used the sector average intensity because your "
                "facility-level emission data was not available. Your actual CCTS "
                "target is set against your individual FY2023-24 baseline. Deloitte "
                "can conduct a GHG baseline assessment to establish your precise "
                "starting position, quantify the gap to your individual target, and "
                "build the Monitoring Plan required for BEE accreditation."
            ),
            urgency="Immediate",
            trigger="Sector average used — individual baseline assessment required for accurate CCTS compliance position.",
        ))

    if not target_officially_notified:
        recs.append(DeloitteRecommendation(
            service="Policy Monitoring & Regulatory Watch",
            description=(
                "BEE had not yet officially notified the emission intensity targets "
                "for your sector at time of this analysis. This tool uses a proxy "
                "reduction range consistent with notified sectors. Deloitte's "
                "regulatory watch service monitors BEE, MoEFCC, and Ministry of "
                "Power notifications and provides 48-hour briefings when your "
                "sector's targets are formalised."
            ),
            urgency="Immediate",
            trigger="Sector-specific CCTS targets not yet officially notified as of April 2026.",
        ))

    return recs


# ---------------------------------------------------------------------------
# Peer Benchmark Calculator
# ---------------------------------------------------------------------------

def _calculate_benchmark(
    sector_key: str,
    actual_intensity: float,
) -> PeerBenchmark:
    s = SECTOR_DATA[sector_key]
    target = s["baseline_intensity"] * (1 - s["reduction_target_pct"])
    avg = s["baseline_intensity"]
    top_q = s["top_quartile_intensity"]

    # Estimate percentile: linear interpolation
    # 0th percentile = sector worst (assume 40% above average)
    # 50th percentile = sector average
    # 75th percentile = top quartile threshold
    # 100th percentile = best in class (assume 20% below top quartile)
    worst = avg * 1.40
    best = top_q * 0.80

    if actual_intensity >= worst:
        percentile = 0.0
    elif actual_intensity <= best:
        percentile = 100.0
    elif actual_intensity >= avg:
        # Between worst and average: 0–50th percentile
        percentile = 50.0 * (worst - actual_intensity) / (worst - avg)
    elif actual_intensity >= top_q:
        # Between average and top quartile: 50–75th percentile
        percentile = 50.0 + 25.0 * (avg - actual_intensity) / (avg - top_q)
    else:
        # Between top quartile and best: 75–100th percentile
        percentile = 75.0 + 25.0 * (top_q - actual_intensity) / (top_q - best)

    gap_to_target_pct = (actual_intensity - target) / target
    gap_to_top_quartile_pct = (actual_intensity - top_q) / top_q

    return PeerBenchmark(
        sector_name=s["name"],
        user_intensity=round(actual_intensity, 4),
        sector_average_intensity=round(avg, 4),
        ccts_target_intensity=round(target, 4),
        top_quartile_intensity=round(top_q, 4),
        percentile_vs_sector=round(percentile, 1),
        gap_to_target_pct=round(gap_to_target_pct, 4),
        gap_to_top_quartile_pct=round(gap_to_top_quartile_pct, 4),
        output_unit=s["output_unit"],
    )


# ---------------------------------------------------------------------------
# Price Scenario Calculator
# ---------------------------------------------------------------------------

def _calculate_price_scenarios(ccc_delta_tonnes: float) -> list[PriceScenario]:
    """
    Calculate financial exposure at three CCTS price scenarios.
    ccc_delta_tonnes: positive = deficit (cost), negative = surplus (revenue).
    """
    scenarios = []
    for label, price_inr in [
        ("Floor (₹150/tCO₂e)", PRICE_FLOOR_INR),
        ("Expected (₹250/tCO₂e)", PRICE_EXPECTED_INR),
        ("Ceiling (₹600/tCO₂e)", PRICE_CEILING_INR),
    ]:
        total_inr = ccc_delta_tonnes * price_inr
        total_usd = total_inr * INR_TO_USD
        scenarios.append(PriceScenario(
            label=label,
            price_inr=price_inr,
            price_usd=round(price_inr * INR_TO_USD, 2),
            total_exposure_inr=round(total_inr, 0),
            total_exposure_usd=round(total_usd, 0),
            per_unit_exposure_inr=0.0,  # calculated below in main function
            per_unit_exposure_usd=0.0,
        ))
    return scenarios


# ---------------------------------------------------------------------------
# Main Calculator Function
# ---------------------------------------------------------------------------

def calculate_ccts_compliance(
    sector_key: str,
    annual_production_tonnes: float,
    actual_intensity: Optional[float] = None,
    energy_consumption_gj: Optional[float] = None,
    co2e_from_energy: Optional[float] = None,
) -> CCTSResult:
    """
    Calculate a company's CCTS compliance position.

    Parameters
    ----------
    sector_key : str
        One of the keys in SECTOR_DATA (e.g. "cement", "iron_steel").
    annual_production_tonnes : float
        Annual production output in tonnes of the relevant product unit.
    actual_intensity : float, optional
        Company's GHG emission intensity in tCO2e per unit of output.
        If None, the sector average is used as a proxy and flagged.
    energy_consumption_gj : float, optional
        Annual energy consumption in gigajoules. Used to cross-check
        intensity if actual_intensity is not provided.
    co2e_from_energy : float, optional
        Total tCO2e from energy combustion. Used with production to
        derive intensity if actual_intensity is not provided.

    Returns
    -------
    CCTSResult
        Full compliance analysis dataclass.

    Raises
    ------
    ValueError
        If sector_key is not in SECTOR_DATA, or production is non-positive.

    Examples
    --------
    # Cement company knows its intensity
    >>> result = calculate_ccts_compliance(
    ...     sector_key="cement",
    ...     annual_production_tonnes=2_000_000,
    ...     actual_intensity=0.74,
    ... )
    >>> result.compliance_status
    <ComplianceStatus.UNDER_COMPLIER: 'under_complier'>

    # Steel company doesn't know intensity; use sector average fallback
    >>> result = calculate_ccts_compliance(
    ...     sector_key="iron_steel",
    ...     annual_production_tonnes=500_000,
    ... )
    >>> result.intensity_was_estimated
    True
    """
    # --- Input validation ---
    if sector_key not in SECTOR_DATA:
        raise ValueError(
            f"Sector '{sector_key}' not found. "
            f"Valid options: {list(SECTOR_DATA.keys())}"
        )
    if annual_production_tonnes <= 0:
        raise ValueError("annual_production_tonnes must be a positive number.")

    s = SECTOR_DATA[sector_key]
    intensity_was_estimated = False

    # --- Resolve emission intensity ---
    if actual_intensity is not None:
        if actual_intensity < 0:
            raise ValueError("actual_intensity cannot be negative.")
        resolved_intensity = actual_intensity
    elif co2e_from_energy is not None and annual_production_tonnes > 0:
        # Derive intensity from total CO2e and production
        resolved_intensity = co2e_from_energy / annual_production_tonnes
    else:
        # Fallback to sector average
        resolved_intensity = s["baseline_intensity"]
        intensity_was_estimated = True

    # --- CCTS target intensity ---
    ccts_target = s["baseline_intensity"] * (1 - s["reduction_target_pct"])

    # --- CCC delta ---
    # Positive = deficit (must buy CCCs)
    # Negative = surplus (can sell CCCs)
    intensity_gap = resolved_intensity - ccts_target
    ccc_delta = intensity_gap * annual_production_tonnes

    # --- Compliance status ---
    threshold_band = ccts_target * 0.02   # within 2% = "at threshold"
    if abs(intensity_gap) <= threshold_band / ccts_target * ccts_target:
        status = ComplianceStatus.AT_THRESHOLD
    elif ccc_delta > 0:
        status = ComplianceStatus.UNDER_COMPLIER
    else:
        status = ComplianceStatus.OVER_COMPLIER

    # --- Price scenarios ---
    scenarios = _calculate_price_scenarios(ccc_delta)
    for sc in scenarios:
        per_unit_inr = sc.total_exposure_inr / annual_production_tonnes
        sc.per_unit_exposure_inr = round(per_unit_inr, 2)
        sc.per_unit_exposure_usd = round(per_unit_inr * INR_TO_USD, 4)

    # --- Benchmark ---
    benchmark = _calculate_benchmark(sector_key, resolved_intensity)

    # --- Deloitte recommendations ---
    recommendations = _build_recommendations(
        status=status,
        gap_to_target_pct=benchmark.gap_to_target_pct,
        gap_to_top_quartile_pct=benchmark.gap_to_top_quartile_pct,
        intensity_was_estimated=intensity_was_estimated,
        target_officially_notified=s["target_officially_notified"],
    )

    # --- Methodology note ---
    methodology_note = (
        "CCTS target intensity calculated as sector average baseline intensity "
        f"× (1 − {s['reduction_target_pct']*100:.1f}% reduction target midpoint). "
    )
    if not s["target_officially_notified"]:
        methodology_note += (
            "Note: BEE had not officially notified this sector's reduction target "
            "as of April 2026. A proxy range of "
            f"{s['reduction_range'][0]*100:.1f}%–{s['reduction_range'][1]*100:.1f}% "
            "has been applied, consistent with notified sectors of comparable "
            "energy intensity."
        )
    if intensity_was_estimated:
        methodology_note += (
            " Emission intensity was not provided by the user; sector average "
            f"({s['baseline_intensity']} tCO₂e/{s['output_unit']}) used as proxy."
        )

    return CCTSResult(
        sector_key=sector_key,
        sector_name=s["name"],
        annual_production_tonnes=annual_production_tonnes,
        actual_intensity=round(resolved_intensity, 4),
        intensity_was_estimated=intensity_was_estimated,
        ccts_target_intensity=round(ccts_target, 4),
        compliance_status=status,
        ccc_delta_tonnes=round(ccc_delta, 2),
        price_scenarios=scenarios,
        benchmark=benchmark,
        recommendations=recommendations,
        target_officially_notified=s["target_officially_notified"],
        data_source=s["source"],
        methodology_note=methodology_note,
    )


# ---------------------------------------------------------------------------
# Pretty Printer (CLI use and Jupyter notebook display)
# ---------------------------------------------------------------------------

def print_result(result: CCTSResult) -> None:
    """Print a formatted summary of a CCTSResult to stdout."""
    status_labels = {
        ComplianceStatus.OVER_COMPLIER:  "OVER-COMPLIER  ✓  (eligible to sell CCCs)",
        ComplianceStatus.UNDER_COMPLIER: "UNDER-COMPLIER ✗  (must purchase CCCs)",
        ComplianceStatus.AT_THRESHOLD:   "AT THRESHOLD   ~  (within 2% of target)",
    }

    print("\n" + "=" * 70)
    print("  CCTS COMPLIANCE ASSESSMENT — Deloitte India")
    print("=" * 70)
    print(f"  Sector          : {result.sector_name}")
    print(f"  Annual Output   : {result.annual_production_tonnes:,.0f} {result.benchmark.output_unit}s")
    print(f"  Actual Intensity: {result.actual_intensity:.4f} tCO₂e / {result.benchmark.output_unit}"
          + (" [ESTIMATED — sector average used]" if result.intensity_was_estimated else ""))
    print(f"  CCTS Target     : {result.ccts_target_intensity:.4f} tCO₂e / {result.benchmark.output_unit}"
          + ("" if result.target_officially_notified else " [PROXY — target not yet officially notified]"))
    print()
    print(f"  STATUS: {status_labels[result.compliance_status]}")
    print()

    delta_label = "DEFICIT (must buy)" if result.ccc_delta_tonnes > 0 else "SURPLUS (can sell)"
    print(f"  CCC {delta_label}: {abs(result.ccc_delta_tonnes):,.0f} tonnes CO₂e")
    print()

    print("  FINANCIAL EXPOSURE")
    print(f"  {'Scenario':<30} {'Total (₹ crore)':>16} {'Total (USD M)':>14} {'Per tonne (₹)':>14}")
    print("  " + "-" * 76)
    for sc in result.price_scenarios:
        crore = sc.total_exposure_inr / 1e7
        usd_m = sc.total_exposure_usd / 1e6
        sign = "+" if sc.total_exposure_inr < 0 else ""
        print(f"  {sc.label:<30} {sign}{crore:>14.2f}  {sign}{usd_m:>12.2f}  {sc.per_unit_exposure_inr:>13.1f}")
    print("  (positive = cost to company; negative = revenue to company)")
    print()

    b = result.benchmark
    print("  PEER BENCHMARK")
    print(f"  Your intensity       : {b.user_intensity:.4f}")
    print(f"  Sector average       : {b.sector_average_intensity:.4f}")
    print(f"  CCTS target          : {b.ccts_target_intensity:.4f}")
    print(f"  Top quartile         : {b.top_quartile_intensity:.4f}")
    print(f"  Est. sector percentile: {b.percentile_vs_sector:.0f}th  "
          f"({'above' if b.gap_to_target_pct > 0 else 'below'} CCTS target by "
          f"{abs(b.gap_to_target_pct)*100:.1f}%)")
    print()

    print("  DELOITTE ADVISORY RECOMMENDATIONS")
    for i, rec in enumerate(result.recommendations, 1):
        print(f"\n  {i}. {rec.service} [{rec.urgency}]")
        print(f"     Trigger: {rec.trigger}")
        # Word-wrap description at 65 chars
        words = rec.description.split()
        line = "     "
        for word in words:
            if len(line) + len(word) + 1 > 70:
                print(line)
                line = "     " + word + " "
            else:
                line += word + " "
        if line.strip():
            print(line)

    print()
    print("  METHODOLOGY")
    print(f"  {result.methodology_note}")
    print()
    print(f"  Source: {result.data_source}")
    print()
    print("  DISCLAIMER: Outputs are indicative only. Each obligated entity's")
    print("  actual CCTS target is set individually by MoEFCC against their own")
    print("  FY2023-24 baseline. Consult a Deloitte CCTS advisory specialist for")
    print("  a verified compliance assessment.")
    print("=" * 70 + "\n")


# ---------------------------------------------------------------------------
# Helper: list all available sectors
# ---------------------------------------------------------------------------

def list_sectors() -> dict:
    """Return a dict of sector_key → sector_name for all CCTS sectors."""
    return {k: v["name"] for k, v in SECTOR_DATA.items()}


# ---------------------------------------------------------------------------
# Quick demo (run directly)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n--- Demo 1: Cement company, intensity known, under-complier ---")
    r1 = calculate_ccts_compliance(
        sector_key="cement",
        annual_production_tonnes=2_000_000,
        actual_intensity=0.74,
    )
    print_result(r1)

    print("\n--- Demo 2: Steel company, intensity not known, sector average used ---")
    r2 = calculate_ccts_compliance(
        sector_key="iron_steel",
        annual_production_tonnes=500_000,
    )
    print_result(r2)

    print("\n--- Demo 3: Aluminium company, over-complier ---")
    r3 = calculate_ccts_compliance(
        sector_key="aluminium",
        annual_production_tonnes=80_000,
        actual_intensity=11.5,
    )
    print_result(r3)
