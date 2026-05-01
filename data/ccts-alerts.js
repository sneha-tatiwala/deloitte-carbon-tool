/**
 * CCTS Regulatory Alerts
 * Add a new entry here whenever there is significant CCTS news.
 * The weekly cron will pick up any items newer than the last send date
 * and email them to matching subscribers.
 *
 * sectors: array of sector keys that are relevant, or ['all'] for all subscribers.
 * id: must be unique — used to prevent duplicate sends.
 */

const CCTS_ALERTS = [
  {
    id: 'bee-oct-2025-four-sectors',
    date: '2025-10-15',
    sectors: ['iron_steel', 'petroleum_refining', 'petrochemicals', 'pulp_paper', 'all'],
    title: 'BEE Notifies Official CCTS Targets for Four Additional Sectors',
    summary: 'The Bureau of Energy Efficiency officially notified Carbon Credit Trading Scheme emission intensity targets for Iron & Steel, Petroleum Refining, Petrochemicals, and Pulp & Paper, effective FY2026. These sectors previously relied on proxy estimates in this tool.',
    impact: 'Obligated entities in these sectors now have official BEE targets. Compliance calculations using proxy figures should be revisited.',
    source: 'BEE CCTS Sector Target Notification, October 2025',
  },
  {
    id: 'bee-jan-2026-remaining-sectors',
    date: '2026-01-20',
    sectors: ['textiles', 'fertilisers', 'all'],
    title: 'BEE Completes CCTS Target Notifications — Textiles and Fertilisers Now Official',
    summary: 'BEE has notified final intensity reduction targets for Textiles and Fertilisers, completing the first round of CCTS sector notifications ahead of the full secondary market trading launch in mid-2026. All nine CCTS sectors now have official or near-official targets in place.',
    impact: 'Obligated entities should initiate BEE-approved Monitoring Plans immediately if not already done. MRV setup is a prerequisite for CCC issuance.',
    source: 'BEE CCTS Sector Target Notification, January 2026',
  },
  {
    id: 'mh-cifp-launch-feb-2026',
    date: '2026-02-18',
    sectors: ['cement', 'iron_steel', 'all'],
    title: 'Maharashtra Climate Investment Facilitation Programme Launched at Mumbai Climate Week',
    summary: 'Climate Group, AVPN, and the Government of Maharashtra announced the MH CIFP at Mumbai Climate Week, targeting ₹3 lakh crore in climate finance by 2030. Cement and steel are identified as priority workstreams, with a blended finance structure designed to support obligated entities in meeting CCTS targets.',
    impact: 'Obligated entities in Maharashtra\'s cement and steel sectors may benefit from structured access to concessional finance instruments being developed under MH CIFP.',
    source: 'Climate Group / Mumbai Climate Week, February 2026',
  },
  {
    id: 'ccts-trading-timeline-apr-2026',
    date: '2026-04-10',
    sectors: ['cement', 'iron_steel', 'aluminium', 'chlor_alkali', 'petroleum_refining', 'petrochemicals', 'textiles', 'fertilisers', 'pulp_paper', 'cement_clinker', 'all'],
    title: 'CCTS Full Secondary Market Trading Confirmed for Mid-2026',
    summary: 'BEE has confirmed that Carbon Credit Certificate secondary market trading on IEX, PXIL, and HPX remains on schedule for mid-2026. The price collar of ₹150–₹600/tCO₂e is in effect for the first compliance period.',
    impact: 'Obligated entities without BEE-approved Monitoring Plans risk delays in CCC issuance. The MRV bottleneck is acute — India needs 750+ accredited Carbon Verification Agencies and current capacity is well below that. Early engagement with ACVAs is strongly recommended.',
    source: 'BEE CCTS Roadmap Update, April 2026',
  },
];

if (typeof module !== 'undefined') module.exports = { CCTS_ALERTS };
