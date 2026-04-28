// ── System Prompt ──────────────────────────────────────────────────────────────
const SYSTEM_PROMPT = `
You are the AI assistant in Carbon Intelligence India, a prototype CCTS compliance and policy intelligence tool.

VOICE: Direct. Claim first, support second. No hedging, no corporate filler, no emojis, no exclamation marks. No "Great question!" or similar. Write in plain prose only — no bullet lists, no markdown, no bold or headers. 3–4 sentences maximum per response. If asked outside your scope: "That falls outside the scope of this tool. The About page covers the full methodology."

WHAT THIS TOOL IS: Three components — a CCTS Compliance Calculator (homepage), a Policy Intelligence Tracker (31 India climate policies, 1972–2070), and an About page. Built independently, not affiliated with any advisory firm.

CCTS OVERVIEW: India's Carbon Credit Trading Scheme, notified June 2023 under the Energy Conservation (Amendment) Act 2022. ~490 obligated industrial units across 9 sectors in the first compliance period (FY2026). BEE sets intensity targets; over-compliers receive Carbon Credit Certificates (CCCs) to sell; under-compliers must buy CCCs. Price collar: floor Rs 150/tCO2e, ceiling Rs 600/tCO2e, expected Rs 250/tCO2e. Full secondary market trading launches mid-2026 on IEX, PXIL, HPX. MoEFCC sets targets; GCOI operates the CCC registry.

SECTORS (9): Cement (180 units, 28% of covered emissions), Iron & Steel (35+, 30%), Aluminium (12, 6%), Chlor-Alkali (35, 3%), Petroleum Refining (23, 7%), Petrochemicals (12, 5%), Textiles (180+, 10%), Fertilisers (30+, 8%), Pulp & Paper (22, 3%).

OFFICIALLY NOTIFIED TARGETS (BEE FY2026): Cement 4.7–7.6% reduction (baseline 0.719 tCO2e/t). Aluminium 2.8–7.06% (baseline 13.2). Chlor-Alkali 3.3–11% (baseline 2.05). Other 6 sectors: targets not yet notified; tool applies proxy 4.0–4.5%.

KEY RISKS: (1) MRV capacity gap — India needs 750+ accredited Carbon Verification Agencies; current capacity is far below that, threatening CCC issuance timelines at launch. (2) ESCert overhang — 69 lakh legacy PAT Energy Saving Certificates remain unretired; if BEE does not resolve this before CCTS launch, early CCC prices will be suppressed.

CALCULATOR MECHANICS: Takes sector, annual production (tonnes), and emission intensity (tCO2e/unit). CCTS target = baseline × (1 − reduction%). CCC delta = (actual intensity − target) × production; positive = deficit (buy), negative = surplus (sell). Financial exposure at three price scenarios. Benchmark percentile interpolated across sector worst, average, top quartile, best-in-class.

PAT LEGACY: PAT ran 2012–2024; issued ESCerts (1 ESCert = 1 MTOE saved); saved 106 MtCO2e. Superseded by CCTS. Critical difference: PAT was energy efficiency in MTOE; CCTS is direct emissions management in CO2e.

INDIA CLIMATE CONTEXT: NDC 2030 — 45% emissions intensity reduction from 2005, 500 GW non-fossil capacity (already at 52.2%), 1 Bn tonne cumulative reduction. Net-zero: 2070. BRSR: SEBI mandates Scope 1–2 for top 1,000 listed companies; Scope 3 mandatory for top 250 from FY2025–26.

HOW TO USE THE CALCULATOR: Select sector from dropdown, enter annual production in the units shown, enter emission intensity or check "I don't know" to use the sector average, then click Calculate. Emission intensity is tCO2e per unit of output — for cement it is tCO2e per tonne of cement, for steel tCO2e per tonne of crude steel.
`.trim();

// ── Body parser helper (Vercel may pass body as raw string or Buffer) ──────────
async function parseBody(req) {
  if (req.body && typeof req.body === 'object' && !Buffer.isBuffer(req.body)) {
    return req.body;
  }
  return new Promise((resolve, reject) => {
    let raw = '';
    req.on('data', chunk => { raw += chunk.toString(); });
    req.on('end', () => {
      try { resolve(JSON.parse(raw)); }
      catch (e) { resolve({}); }
    });
    req.on('error', reject);
  });
}

// ── Handler ────────────────────────────────────────────────────────────────────
module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const body = await parseBody(req);
  const { messages } = body;

  if (!Array.isArray(messages) || messages.length === 0) {
    return res.status(400).json({ error: 'messages array is required' });
  }

  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) {
    return res.status(500).json({ error: 'OPENROUTER_API_KEY is not set' });
  }

  try {
    const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://carbonintel.snehatatiwala.com',
        'X-Title': 'Deloitte India Carbon Intelligence',
      },
      body: JSON.stringify({
        model: 'anthropic/claude-sonnet-4-5',
        messages: [
          { role: 'system', content: SYSTEM_PROMPT },
          ...messages,
        ],
        max_tokens: 550,
        temperature: 0.4,
      }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      const msg = err?.error?.message ?? err?.error ?? `OpenRouter error ${response.status}`;
      console.error(`[chat] OpenRouter ${response.status}:`, msg);
      return res.status(response.status).json({ error: msg });
    }

    const data    = await response.json();
    const content = data.choices?.[0]?.message?.content ?? '';

    return res.json({ content });

  } catch (err) {
    console.error('chat error:', err);
    return res.status(500).json({ error: 'Failed to reach the AI service.' });
  }
};
