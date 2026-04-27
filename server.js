require('dotenv').config();

const express = require('express');
const path    = require('path');
const fs      = require('fs');

const app  = express();
const PORT = process.env.PORT || 3001;

app.use(require('express').json());

// ── Auto-mount api/ handlers ─────────────────────────────────
const apiDir = path.join(__dirname, 'api');
if (fs.existsSync(apiDir)) {
  fs.readdirSync(apiDir)
    .filter(f => f.endsWith('.js'))
    .forEach(file => {
      const route   = `/api/${file.slice(0, -3)}`;
      const handler = require(path.join(apiDir, file));
      app.all(route, handler);
      console.log(`  Mounted: ${route}`);
    });
}

// ── Serve static files ───────────────────────────────────────
app.use(require('express').static(__dirname, {
  index: 'index.html',
  dotfiles: 'ignore',
}));

// ── Fallback ─────────────────────────────────────────────────
app.use((req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, () => {
  console.log(`\n  Site:   http://localhost:${PORT}`);
  console.log(`  API:    http://localhost:${PORT}/api/chat\n`);
});
