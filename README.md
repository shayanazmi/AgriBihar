# AgriBihar: deploy on GitHub Pages

```
index.html  app.js  config.js  theme-init.js  fb.js   the site (no build step)
fonts/      vendor/                                    self-hosted fonts and jsPDF 4.2.1 (licences included)
configure.py                                           sets the AI address in config.js AND the security policy
worker/                                                the AI proxy (Cloudflare Worker), deployed separately
SECURITY_AUDIT.md   SHA256SUMS                         audit report and file checksums
```

The site is static: it works as-is, with the AI assistant switched off, until you complete steps 1 to 3.

## 0. First: the key you pasted in chat
Revoke it at build.nvidia.com (Settings, API Keys) and create a new one. Treat any key that has appeared in a chat, an email or a repo as public. The key must only ever live in a Worker secret.

## 1. Deploy the AI Worker (optional, enables live web search and NVIDIA NIM)
```
cd worker
npm i -g wrangler && wrangler login
# edit wrangler.toml: ALLOWED_ORIGINS = "https://YOUR-USERNAME.github.io"
wrangler secret put NVIDIA_API_KEY        # paste the NEW key when prompted
wrangler secret put TAVILY_API_KEY        # a web-search key (or GOOGLE_API_KEY + GOOGLE_CX)
wrangler deploy                           # prints https://agribihar-ai.<you>.workers.dev
```
Then in the NVIDIA and search dashboards set a monthly spend cap and an alert.

## 2. Point the site at the Worker (one command)
```
python configure.py https://agribihar-ai.<you>.workers.dev/ask
```
This updates `config.js` and the `connect-src` rule in the Content-Security-Policy so the browser may call only your Worker. Use `python configure.py --off` to switch the AI off again.

## 3. Publish
Create a repo, commit **everything except `worker/`** (you may commit `worker/` too; it contains no secrets), then Settings, Pages, Deploy from a branch, and tick **Enforce HTTPS**. The site is then at `https://YOUR-USERNAME.github.io/REPO/`.

## 4. Check it
- Open DevTools, Console: there should be **no Content-Security-Policy violations**.
- Open any chart point, press "Explain with AI": you should get an answer with sources (or a clear message).
- Share a view (the ⤴ button), open the link in a private window: the same view should appear.
- Try PDF export (⇩): it should download without any network request to another site (DevTools, Network).

## Local testing
`python -m http.server 8080` in this folder, open http://localhost:8080. To test the AI locally, temporarily add `http://localhost:8080` to `ALLOWED_ORIGINS` and redeploy; remove it afterwards.

## Updating dependencies
jsPDF and the fonts are vendored. To update jsPDF: download the new `dist/jspdf.umd.min.js` from the npm package, replace `vendor/jspdf.umd.min.js`, recompute the SHA-384 and set it as `PDF_SRI` in `app.js`. Check https://github.com/parallax/jsPDF/security/advisories before upgrading.
