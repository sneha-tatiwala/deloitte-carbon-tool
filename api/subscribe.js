require('dotenv').config();
const fetch = require('node-fetch');

const SECTOR_NAMES = {
  cement:            'Cement',
  aluminium:         'Aluminium',
  chlor_alkali:      'Chlor-Alkali',
  iron_steel:        'Iron & Steel',
  cement_clinker:    'Cement (Clinker)',
  petroleum_refining:'Petroleum Refining',
  petrochemicals:    'Petrochemicals',
  pulp_paper:        'Pulp & Paper',
  textiles:          'Textiles',
  fertilisers:       'Fertilisers',
  all:               'All sectors',
};

module.exports = async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { email, sector } = req.body || {};

  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return res.status(400).json({ error: 'A valid email address is required.' });
  }

  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) {
    // Graceful fallback — log and acknowledge without breaking the site
    console.log(`[subscribe] RESEND_API_KEY not set. Subscriber: ${email}, sector: ${sector}`);
    return res.json({ ok: true, note: 'Subscription recorded (email delivery not configured).' });
  }

  const sectorLabel = SECTOR_NAMES[sector] || 'All sectors';
  const now = new Date().toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' });

  try {
    // Confirmation to subscriber
    await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        from: 'Carbon Intelligence India <alerts@snehatatiwala.com>',
        to: [email],
        subject: `CCTS Regulatory Alert — ${sectorLabel} subscription confirmed`,
        html: `
          <div style="font-family:Inter,sans-serif;max-width:560px;margin:0 auto;color:#1a1a1a;">
            <div style="background:#000;padding:1.25rem 1.5rem;border-bottom:3px solid #86BC25;">
              <span style="color:#86BC25;font-weight:700;font-size:1rem;letter-spacing:0.1em;">CARBON INTELLIGENCE INDIA</span>
            </div>
            <div style="padding:1.5rem;">
              <p style="font-size:0.95rem;line-height:1.7;">You are now subscribed to CCTS regulatory alerts for <strong>${sectorLabel}</strong>.</p>
              <p style="font-size:0.88rem;color:#555;line-height:1.7;">
                You will be notified when BEE publishes official emission intensity targets for your sector, or when significant CCTS policy changes occur.
                The tool currently uses proxy targets for ${sectorLabel === 'All sectors' ? 'most sectors' : sectorLabel} pending BEE notification.
              </p>
              <p style="font-size:0.88rem;color:#555;line-height:1.7;">
                Run your compliance calculation any time at
                <a href="https://carbonintel.snehatatiwala.com" style="color:#009A44;">carbonintel.snehatatiwala.com</a>.
              </p>
              <p style="font-size:0.78rem;color:#aaa;margin-top:1.5rem;border-top:1px solid #eee;padding-top:1rem;">
                This is a prototype demonstration tool. Outputs are indicative only.
                Not affiliated with or authorised by any advisory firm. ${now}.
              </p>
            </div>
          </div>`,
      }),
    });

    // Notification to site owner
    await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        from: 'Carbon Intelligence India <alerts@snehatatiwala.com>',
        to: ['snehaa@bu.edu'],
        subject: `New CCTS alert subscriber — ${sectorLabel}`,
        text: `New subscriber: ${email}\nSector: ${sectorLabel}\nDate: ${now}`,
      }),
    });

    return res.json({ ok: true });

  } catch (err) {
    console.error('[subscribe] Resend error:', err);
    return res.status(500).json({ error: 'Failed to send confirmation. Please try again.' });
  }
};
