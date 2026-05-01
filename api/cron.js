require('dotenv').config();
const fetch = require('node-fetch');
const { CCTS_ALERTS } = require('../data/ccts-alerts');

// ── Upstash Redis helper ────────────────────────────────────────────────────
async function redis(command) {
  const res = await fetch(process.env.UPSTASH_REDIS_REST_URL, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${process.env.UPSTASH_REDIS_REST_TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(command),
  });
  return res.json();
}

// ── Email template ──────────────────────────────────────────────────────────
function buildAlertEmail(alerts) {
  const alertBlocks = alerts.map(a => `
    <div style="border:1px solid #e0e0e0;border-left:4px solid #86BC25;border-radius:4px;padding:1rem 1.25rem;margin-bottom:1.25rem;">
      <div style="font-size:0.72rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#6b6b6b;margin-bottom:0.4rem;">
        ${new Date(a.date).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}
      </div>
      <div style="font-size:1rem;font-weight:700;color:#1a1a1a;margin-bottom:0.6rem;line-height:1.3;">${a.title}</div>
      <div style="font-size:0.875rem;color:#444;line-height:1.65;margin-bottom:0.75rem;">${a.summary}</div>
      <div style="background:#f0fce6;border-radius:4px;padding:0.6rem 0.875rem;font-size:0.82rem;color:#1a5c1a;line-height:1.55;margin-bottom:0.6rem;">
        <strong>What this means for you:</strong> ${a.impact}
      </div>
      <div style="font-size:0.75rem;color:#999;">Source: ${a.source}</div>
    </div>
  `).join('');

  const count = alerts.length;
  const heading = count === 1 ? '1 CCTS Update' : `${count} CCTS Updates`;

  return `
    <div style="font-family:Inter,Arial,sans-serif;max-width:580px;margin:0 auto;color:#1a1a1a;">
      <div style="background:#000;padding:1.25rem 1.5rem;border-bottom:3px solid #86BC25;">
        <span style="color:#86BC25;font-weight:700;font-size:0.95rem;letter-spacing:0.12em;text-transform:uppercase;">Carbon Intelligence India</span>
      </div>
      <div style="background:#86BC25;padding:0.5rem 1.5rem;">
        <span style="font-size:0.75rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#000;">CCTS Regulatory Alert</span>
      </div>
      <div style="padding:1.5rem;">
        <p style="font-size:0.95rem;line-height:1.6;color:#333;margin-top:0;">
          There ${count === 1 ? 'is' : 'are'} <strong>${heading}</strong> relevant to your subscription since your last digest.
        </p>
        ${alertBlocks}
        <div style="margin-top:1.5rem;padding-top:1rem;border-top:1px solid #eee;">
          <p style="font-size:0.875rem;color:#555;line-height:1.6;">
            Run your compliance calculation with the latest figures at
            <a href="https://carbonintel.snehatatiwala.com" style="color:#009A44;font-weight:600;">carbonintel.snehatatiwala.com</a>.
          </p>
        </div>
        <p style="font-size:0.75rem;color:#aaa;margin-top:1.25rem;line-height:1.5;">
          You are receiving this because you subscribed to CCTS regulatory alerts.
          This is a prototype demonstration tool. Outputs are indicative only and do not constitute legal or compliance advice.
        </p>
      </div>
    </div>
  `;
}

// ── Handler ─────────────────────────────────────────────────────────────────
module.exports = async function handler(req, res) {
  // Vercel passes Authorization: Bearer {CRON_SECRET} for cron invocations.
  // Allow GET (Vercel cron) or POST (manual trigger with the same secret).
  const cronSecret = process.env.CRON_SECRET;
  if (cronSecret) {
    const auth = req.headers.authorization ?? '';
    if (auth !== `Bearer ${cronSecret}`) {
      return res.status(401).json({ error: 'Unauthorized' });
    }
  }

  const upstashUrl   = process.env.UPSTASH_REDIS_REST_URL;
  const upstashToken = process.env.UPSTASH_REDIS_REST_TOKEN;
  const resendKey    = process.env.RESEND_API_KEY;

  if (!upstashUrl || !upstashToken) {
    return res.status(500).json({ error: 'Upstash not configured — set UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN.' });
  }
  if (!resendKey) {
    return res.status(500).json({ error: 'RESEND_API_KEY not set.' });
  }

  // Get the date we last sent alerts (ISO string stored in Redis)
  const { result: lastSentRaw } = await redis(['GET', 'ccts:last_alert_sent']);
  const lastSent = lastSentRaw ? new Date(lastSentRaw) : new Date('2000-01-01');

  // Find all alerts newer than the last send date
  const newAlerts = CCTS_ALERTS.filter(a => new Date(a.date) > lastSent);

  if (newAlerts.length === 0) {
    return res.json({ ok: true, message: 'No new alerts since last send.', lastSent: lastSentRaw });
  }

  // Get all subscriber emails
  const { result: emails } = await redis(['SMEMBERS', 'ccts:subscribers']);
  if (!emails || emails.length === 0) {
    return res.json({ ok: true, message: 'No subscribers yet.' });
  }

  let sent = 0;
  let failed = 0;

  for (const email of emails) {
    // Get subscriber sector preference
    const { result: sector } = await redis(['HGET', `ccts:sub:${email}`, 'sector']);
    const watchedSector = sector || 'all';

    // Filter alerts relevant to this subscriber
    const relevant = newAlerts.filter(a =>
      watchedSector === 'all' || a.sectors.includes(watchedSector) || a.sectors.includes('all')
    );

    if (relevant.length === 0) continue;

    try {
      const emailRes = await fetch('https://api.resend.com/emails', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${resendKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          from: 'Carbon Intelligence India <alerts@snehatatiwala.com>',
          to: [email],
          subject: `CCTS Update: ${relevant[0].title}${relevant.length > 1 ? ` + ${relevant.length - 1} more` : ''}`,
          html: buildAlertEmail(relevant),
        }),
      });

      if (emailRes.ok) {
        sent++;
      } else {
        const err = await emailRes.json().catch(() => ({}));
        console.error(`[cron] Failed to send to ${email}:`, err);
        failed++;
      }
    } catch (err) {
      console.error(`[cron] Error sending to ${email}:`, err.message);
      failed++;
    }
  }

  // Update last sent timestamp to the newest alert's date
  const newest = newAlerts.reduce((max, a) => a.date > max ? a.date : max, '');
  await redis(['SET', 'ccts:last_alert_sent', newest]);

  console.log(`[cron] Done. Sent: ${sent}, Failed: ${failed}, New alerts: ${newAlerts.length}`);
  return res.json({ ok: true, sent, failed, newAlerts: newAlerts.length, lastSentUpdatedTo: newest });
};
