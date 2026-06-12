require('dotenv').config();
const express = require('express');
const http    = require('http');
const app     = express();

app.use(express.json());
app.use(express.static('public'));

// Where MoCraft's Python API server is running
const PYTHON_HOST = process.env.MOCRAFT_HOST || 'localhost';
const PYTHON_PORT = parseInt(process.env.MOCRAFT_PORT || '8000', 10);

/**
 * Forward a request to the MoCraft Python server.
 * Pipes the response back — works for both JSON and SSE streams.
 */
function proxyToPython(pyPath, req, res, timeoutMs = 0) {
    const options = {
        hostname: PYTHON_HOST,
        port:     PYTHON_PORT,
        path:     pyPath,
        method:   req.method,
        headers:  { 'Content-Type': 'application/json' },
    };

    const proxyReq = http.request(options, (proxyRes) => {
        res.writeHead(proxyRes.statusCode, proxyRes.headers);
        proxyRes.pipe(res, { end: true });
    });

    proxyReq.on('error', () => {
        if (!res.headersSent) {
            res.status(502).json({
                error:
                    'MoCraft Python server is not running.\n' +
                    'Start it first:  cd MoCraft && python server.py',
            });
        }
    });

    if (timeoutMs > 0) {
        proxyReq.setTimeout(timeoutMs, () => {
            proxyReq.destroy();
            if (!res.headersSent) res.status(504).json({ error: 'Request to MoCraft timed out.' });
        });
    }

    if (req.method === 'POST' && req.body && Object.keys(req.body).length) {
        proxyReq.write(JSON.stringify(req.body));
    }
    proxyReq.end();
}

// ── Route proxies ─────────────────────────────────────────────

app.get('/status',  (req, res) => proxyToPython('/status',  req, res, 10000));
app.post('/task',   (req, res) => proxyToPython('/task',    req, res, 15000));

// SSE stream — no timeout (long-lived connection)
app.get('/task/:id/stream', (req, res) =>
    proxyToPython(`/task/${req.params.id}/stream`, req, res));

app.get('/workspace', (req, res) => {
    const qs = req.query.task ? `?task=${encodeURIComponent(req.query.task)}` : '';
    proxyToPython('/workspace' + qs, req, res, 10000);
});

app.use('/files', (req, res) =>
    proxyToPython('/files' + req.url, req, res, 10000));

// ── Start ─────────────────────────────────────────────────────

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`MoCraft Web  → http://localhost:${PORT}`);
    console.log(`Python API   → http://${PYTHON_HOST}:${PYTHON_PORT}`);
    console.log('');
    console.log('Start the backend first:  cd MoCraft && python server.py');
});
