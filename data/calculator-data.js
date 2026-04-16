/**
 * CCTS Calculator — Frontend Logic
 * JavaScript mirror of calculator.py
 * All sector constants sourced from data/sectors.js (must load first).
 */

const PRICE_FLOOR = 150;
const PRICE_EXPECTED = 250;
const PRICE_CEILING = 600;
const INR_TO_USD = 0.012;
const INR_TO_CRORE = 1e7;

const COMPLIANCE_STATUS = {
  OVER_COMPLIER:  "over_complier",
  UNDER_COMPLIER: "under_complier",
  AT_THRESHOLD:   "at_threshold",
};

// ─── Benchmark ──────────────────────────────────────────────────────────────

function calculateBenchmark(sectorKey, actualIntensity) {
  const s = SECTOR_DATA[sectorKey];
  const target = s.baselineIntensity * (1 - s.reductionTargetPct);
  const avg    = s.baselineIntensity;
  const topQ   = s.topQuartileIntensity;
  const worst  = avg * 1.40;
  const best   = topQ * 0.80;

  let percentile;
  if (actualIntensity >= worst)       percentile = 0;
  else if (actualIntensity <= best)   percentile = 100;
  else if (actualIntensity >= avg)    percentile = 50 * (worst - actualIntensity) / (worst - avg);
  else if (actualIntensity >= topQ)   percentile = 50 + 25 * (avg - actualIntensity) / (avg - topQ);
  else                                percentile = 75 + 25 * (topQ - actualIntensity) / (topQ - best);

  return {
    sectorName:            s.name,
    userIntensity:         +actualIntensity.toFixed(4),
    sectorAvgIntensity:    +avg.toFixed(4),
    cctsTargetIntensity:   +target.toFixed(4),
    topQuartileIntensity:  +topQ.toFixed(4),
    percentile:            +percentile.toFixed(1),
    gapToTargetPct:        +((actualIntensity - target) / target).toFixed(4),
    gapToTopQuartilePct:   +((actualIntensity - topQ) / topQ).toFixed(4),
    outputUnit:            s.outputUnit,
  };
}

// ─── Recommendations ────────────────────────────────────────────────────────

function buildRecommendations(status, benchmark, intensityWasEstimated, targetOfficiallyNotified) {
  const recs = [];

  recs.push({
    service:     "Monitoring, Reporting & Verification (MRV) Setup",
    urgency:     "Immediate",
    description: "CCTS compliance requires a BEE-approved Monitoring Plan and annual third-party verification by an accredited Carbon Verification Agency (ACVA) under ISO 14064. Deloitte's audit infrastructure covers all 9 CCTS sectors. India faces a structural MRV capacity gap — early accreditation is a first-mover advantage.",
    trigger:     "Required for all CCTS-obligated entities regardless of compliance position.",
    icon:        "🔍",
  });

  if (status === COMPLIANCE_STATUS.UNDER_COMPLIER) {
    if (benchmark.gapToTargetPct > 0.15) {
      recs.push({
        service:     "Decarbonisation Roadmap & Capital Planning",
        urgency:     "Immediate",
        description: "Your emission intensity is significantly above the CCTS target. Deloitte's decarbonisation advisory maps 100+ abatement levers against your sector's process emissions, prioritised by cost-per-tonne and capital requirements — the basis for a credible board-level net-zero strategy.",
        trigger:     `Emission intensity ${(benchmark.gapToTargetPct * 100).toFixed(1)}% above CCTS target — material compliance cost exposure.`,
        icon:        "📉",
      });
    }
    recs.push({
      service:     "CCC Procurement & Trading Advisory",
      urgency:     "Within 6 months",
      description: "As an under-complier, you must purchase Carbon Credit Certificates before the compliance period closes. Deloitte advises on procurement strategy: bilateral OTC vs. exchange trading on IEX/PXIL/HPX, timing relative to the price collar (₹150–₹600/tCO₂e), and bankability provisions.",
      trigger:     "Under-complier status requires CCC purchase before compliance period closes.",
      icon:        "💹",
    });
  }

  if (status === COMPLIANCE_STATUS.OVER_COMPLIER) {
    recs.push({
      service:     "CCC Monetisation & Carbon Revenue Strategy",
      urgency:     "Within 6 months",
      description: "Your emission intensity is below the CCTS target — you are eligible to receive and sell Carbon Credit Certificates. Deloitte advises on CCC issuance timing, pricing strategy relative to the price collar, and long-term banking strategy as CCTS targets tighten in successive periods.",
      trigger:     "Over-complier status generates CCC surplus with monetisation potential.",
      icon:        "💰",
    });
  }

  recs.push({
    service:     "BRSR Core Assurance & Scope 3 Measurement",
    urgency:     "Within 6 months",
    description: "SEBI's BRSR framework mandates Scope 1, 2, and 3 GHG disclosures for India's top 1,000 listed companies (Scope 3 mandatory from FY2025–26 for top 250). Deloitte's Emissions Calculation Center (ECC) automates Scope 3 measurement across complex supply chains. ESRS/GRI/ISSB alignment for EU-facing operations.",
    trigger:     "BRSR compliance obligation applies to all listed Indian companies.",
    icon:        "📊",
  });

  if (benchmark.gapToTopQuartilePct > 0.20) {
    recs.push({
      service:     "Energy Efficiency & Process Optimisation",
      urgency:     "Strategic",
      description: "Your emission intensity is significantly above the sector's top quartile. This gap represents both a compliance risk and a cost opportunity — energy is typically 30–60% of operating cost in CCTS-covered sectors. Deloitte's operational improvement practice identifies process-level levers with payback periods under three years.",
      trigger:     `Intensity ${(benchmark.gapToTopQuartilePct * 100).toFixed(1)}% above sector top quartile — material efficiency gap.`,
      icon:        "⚡",
    });
  }

  if (intensityWasEstimated) {
    recs.push({
      service:     "GHG Baseline Assessment & Data Quality Audit",
      urgency:     "Immediate",
      description: "This analysis used the sector average because your facility-level emission data was unavailable. Your actual CCTS target is set against your individual FY2023–24 baseline. Deloitte can establish your precise starting position, quantify the individual gap, and build the Monitoring Plan required for BEE accreditation.",
      trigger:     "Sector average used — individual baseline assessment required for accurate compliance position.",
      icon:        "📋",
    });
  }

  if (!targetOfficiallyNotified) {
    recs.push({
      service:     "Policy Monitoring & Regulatory Watch",
      urgency:     "Immediate",
      description: "BEE had not yet officially notified the emission intensity targets for your sector as of April 2026. This tool uses a proxy reduction range. Deloitte's regulatory watch service monitors BEE, MoEFCC, and Ministry of Power notifications and provides 48-hour briefings when your sector's targets are formalised.",
      trigger:     "Sector-specific CCTS targets not yet officially notified as of April 2026.",
      icon:        "🔔",
    });
  }

  return recs;
}

// ─── Main Calculator ─────────────────────────────────────────────────────────

function calculateCCTS({ sectorKey, annualProduction, actualIntensity = null }) {
  const s = SECTOR_DATA[sectorKey];
  if (!s) throw new Error(`Unknown sector: ${sectorKey}`);
  if (!annualProduction || annualProduction <= 0) throw new Error("Annual production must be a positive number.");

  const intensityWasEstimated = actualIntensity === null || actualIntensity === undefined;
  const resolved = intensityWasEstimated ? s.baselineIntensity : +actualIntensity;

  if (resolved < 0) throw new Error("Emission intensity cannot be negative.");

  const cctsTarget = s.baselineIntensity * (1 - s.reductionTargetPct);
  const intensityGap = resolved - cctsTarget;
  const cccDelta = intensityGap * annualProduction;  // + = deficit, - = surplus

  // Compliance status
  const thresholdBand = cctsTarget * 0.02;
  let status;
  if (Math.abs(intensityGap) <= thresholdBand) status = COMPLIANCE_STATUS.AT_THRESHOLD;
  else if (cccDelta > 0)                        status = COMPLIANCE_STATUS.UNDER_COMPLIER;
  else                                           status = COMPLIANCE_STATUS.OVER_COMPLIER;

  // Price scenarios
  const priceScenarios = [
    { label: "Floor",    labelFull: "Floor (₹150/tCO₂e)",    priceInr: PRICE_FLOOR },
    { label: "Expected", labelFull: "Expected (₹250/tCO₂e)", priceInr: PRICE_EXPECTED },
    { label: "Ceiling",  labelFull: "Ceiling (₹600/tCO₂e)",  priceInr: PRICE_CEILING },
  ].map(sc => {
    const totalInr    = cccDelta * sc.priceInr;
    const totalUsd    = totalInr * INR_TO_USD;
    const totalCrore  = totalInr / INR_TO_CRORE;
    const perUnitInr  = totalInr / annualProduction;
    return {
      ...sc,
      totalInr:    +totalInr.toFixed(0),
      totalUsd:    +totalUsd.toFixed(0),
      totalCrore:  +totalCrore.toFixed(2),
      perUnitInr:  +perUnitInr.toFixed(2),
    };
  });

  const benchmark = calculateBenchmark(sectorKey, resolved);
  const recommendations = buildRecommendations(
    status, benchmark, intensityWasEstimated, s.targetOfficiallyNotified
  );

  const methodologyNote = `CCTS target = sector average baseline (${s.baselineIntensity} tCO₂e/${s.outputUnit}) × (1 − ${(s.reductionTargetPct * 100).toFixed(1)}% reduction midpoint).`
    + (!s.targetOfficiallyNotified ? ` Proxy range ${(s.reductionRange[0]*100).toFixed(1)}%–${(s.reductionRange[1]*100).toFixed(1)}% applied — target not officially notified as of April 2026.` : "")
    + (intensityWasEstimated ? ` Emission intensity not provided; sector average used as proxy.` : "");

  return {
    sectorKey,
    sectorName:                s.name,
    outputUnit:                s.outputUnit,
    annualProduction,
    actualIntensity:           +resolved.toFixed(4),
    intensityWasEstimated,
    cctsTarget:                +cctsTarget.toFixed(4),
    status,
    cccDelta:                  +cccDelta.toFixed(0),
    priceScenarios,
    benchmark,
    recommendations,
    targetOfficiallyNotified:  s.targetOfficiallyNotified,
    source:                    s.source,
    methodologyNote,
  };
}

// ─── Regulatory Calendar ─────────────────────────────────────────────────────

const REGULATORY_DEADLINES = [
  {
    date: "Mid-2026",
    sortKey: "2026-06",
    title: "CCTS Full Trading Launch",
    description: "Full secondary market trading of CCCs opens on IEX, PXIL, HPX.",
    urgency: "critical",
    sectors: ["cement","iron_steel","aluminium","petroleum_refining","fertilisers","textiles","pulp_paper","chlor_alkali","petrochemicals"],
  },
  {
    date: "FY2025–26",
    sortKey: "2026-03",
    title: "BRSR Scope 3 Mandatory",
    description: "Scope 3 GHG disclosure mandatory for India's top 250 listed companies.",
    urgency: "critical",
    sectors: ["all"],
  },
  {
    date: "April 1, 2027",
    sortKey: "2027-04",
    title: "CAFE III Takes Effect",
    description: "Fleet average CO₂ drops to 91.7 g/km. EV production must scale significantly.",
    urgency: "high",
    sectors: ["all"],
  },
  {
    date: "2027+",
    sortKey: "2027-06",
    title: "CCTS Sector Expansion",
    description: "Coverage expected to expand beyond initial 9 sectors in FY2028 compliance period.",
    urgency: "medium",
    sectors: ["all"],
  },
  {
    date: "2027+",
    sortKey: "2027-09",
    title: "Article 6 ITMO Framework",
    description: "India expected to enter bilateral Article 6.2 agreements — carbon export pathway opens.",
    urgency: "medium",
    sectors: ["all"],
  },
  {
    date: "2029",
    sortKey: "2029-01",
    title: "India TNFD Alignment",
    description: "SEBI expected to mandate TNFD biodiversity risk and dependency disclosures.",
    urgency: "medium",
    sectors: ["all"],
  },
  {
    date: "2030",
    sortKey: "2030-01",
    title: "NDC 2030 Targets",
    description: "500 GW non-fossil capacity; 45% emissions intensity cut; 1B tonne cumulative reduction.",
    urgency: "high",
    sectors: ["all"],
  },
  {
    date: "2035",
    sortKey: "2035-01",
    title: "Updated NDC 2035 Targets",
    description: "47% emissions intensity cut; 60% non-fossil capacity; 3.5–4B tCO₂e sink.",
    urgency: "medium",
    sectors: ["all"],
  },
];
