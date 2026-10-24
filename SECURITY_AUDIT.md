# AgriBihar: security audit (GitHub Pages deployment)

Date: 23 October 2026 · Scope: `index.html`, `app.js`, `config.js`, `fb.js`, `theme-init.js`, vendored jsPDF 4.2.1, fonts, and the AI Worker.
Architecture: a static site on GitHub Pages (no server code, no accounts, no cookies, no free-text input) plus an optional Cloudflare Worker that holds the API keys.

## Verdict
**Safe to deploy once you complete finding F1 (revoke the leaked key) and set spend limits (F2).** No exploitable vulnerability was found in the site itself. Seven weaknesses were found and fixed; four risks remain and are listed under "Residual risk".

## Findings

| ID | Severity | Finding | Status |
|---|---|---|---|
| F1 | **Critical** | A live NVIDIA API key was pasted into the chat. Anything pasted into a chat, email or repo must be treated as public. | **ACTION REQUIRED (you).** Revoke and create a new key. Store it only with `wrangler secret put`. Never commit `.env` (`.gitignore` provided). The key appears in none of the delivered files (pattern-scanned). |
| F2 | **High** | The AI endpoint is public. CORS and the `Origin` check stop other *websites*, but a script can forge `Origin`, so it is not authentication. Abuse means cost and a free LLM relay. | **Fixed + residual.** Worker now: exact-origin allowlist, `application/json` only, 24 KB cap, strict schema validation with length limits, server-built prompt (client prompt text is no longer sent or used), fixed model / `max_tokens` / no streaming, 10 s / 25 s timeouts, generic errors, rate limiting (Cloudflare binding, else weak per-instance fallback). 21 automated tests pass. **You must set spend caps and a WAF rate rule.** |
| F3 | Medium | jsPDF 2.5.1 was used. Versions before 4.2.0 have CVE-2026-25535 (DoS via `addImage`), CVE-2026-25755 (PDF object injection via `addJS`) and CVE-2026-25940 (AcroForm injection), all fixed in 4.2.0 (source: IBM PSIRT bulletin of 4 May 2026). | **Fixed.** Upgraded to 4.2.1 (latest on npm, released 17 Mar 2026). The site only passes self-generated chart images and never calls `addJS` or AcroForm, so the old version was not exploitable as used, but it should not ship. |
| F4 | Medium | Third-party code and styles loaded at runtime (Google Fonts, a CDN script): supply-chain risk and visitor IP/privacy leak, and no Subresource Integrity. | **Fixed.** Fonts and jsPDF are vendored in the repo; jsPDF is loaded with SRI (`sha384`). Zero third-party requests at page load (verified). |
| F5 | Medium | No Content-Security-Policy. | **Fixed.** Meta CSP: `script-src 'self'` (the site has **no inline scripts or event handlers**, verified), `object-src 'none'`, `base-uri 'none'`, `form-action 'none'`, `frame-src 'none'`, `connect-src` limited to your Worker. `configure.py` keeps it in sync with `config.js`. |
| F6 | Low | Values from a shared link (URL hash) were interpolated into HTML templates in several places. **I fuzzed all 32 parameters on all 11 pages and 20 insight payload forms against the unvalidated code and found no working XSS**, because the code threw before reaching the unsafe line, but that protection was accidental. | **Fixed (hardening).** Every parameter is now accepted only if it exactly matches a known value; insight payloads are validated by type and arity. `esc()` now also escapes `'`. 14 hostile-link probes and 5 AI-reply probes are neutralised. |
| F7 | Low | AI/proxy "sources" were rendered as links without checking the URL scheme, so a compromised or malicious proxy or search result could return `javascript:` links. | **Fixed.** Only `http(s)` URLs are linkable (client) and only `https` (Worker). AI text is always HTML-escaped. External links use `rel="noopener noreferrer"`. |
| F8 | Low | Clickjacking: GitHub Pages cannot send `X-Frame-Options` / `frame-ancestors`, and a meta CSP cannot either. | **Mitigated.** `fb.js` hides the page unless it is top-level and navigates the top window away if framed. Fails safe (page stays hidden if scripts are blocked). Full protection needs a host that sends headers (e.g. Cloudflare in front, or a custom domain). |
| F9 | Low | Fragile error handling: "Failed to fetch" appeared when the Worker URL was a placeholder or unreachable; raw error text was displayed. | **Fixed.** Unconfigured AI shows "switched off, see README"; network errors, 429, 5xx and malformed replies each show a clear fixed message; 30 s timeout; no URLs or stack traces shown. |
| F10 | Info | Browser storage: `localStorage` (theme, language) and `sessionStorage` (intro seen) only. Values are validated to fixed options. No cookies, accounts, analytics or personal data. Referrer policy is `no-referrer`. | OK |
| F11 | Info | All pages under `YOUR-USERNAME.github.io` share one origin (and one `localStorage`). A weakness in any other project page there is in the same trust zone. | Accept, or use a custom domain / dedicated account. |
| F12 | Info | A public repo publishes everything in it: code, the data files and the article summaries. | Confirm you may publish the datasets (state APY, national workbook, climate, MSP). Articles are linked and summarised in our own words; none is copied. |
| F13 | Info | Prompt injection: web results and the client's fields are untrusted text. | Mitigated. They sit inside `<<<DATA … DATA>>>` markers with an instruction to ignore commands in them; the model has no tools and no secrets; output is escaped. Residual: an answer can still be wrong or slanted. Answers show sources and split Documented / Possible / Unknown. |

## Residual risk (what remains after the fixes)
1. **Cost abuse by a determined script** (forged `Origin`). Cap spend, alert on usage, add a Cloudflare WAF rate-limiting rule and the Rate Limiting binding. Adding a CAPTCHA (Cloudflare Turnstile) is the next step if abuse appears.
2. **`style-src 'unsafe-inline'`** is needed because charts set inline styles. It permits CSS-only injection, not script execution.
3. **Meta-tag CSP** cannot set `frame-ancestors` or report violations.
4. **Third-party services you opt into** (NVIDIA, your search provider, Cloudflare) receive the topic, a handful of data values and the crop/place/year you click. They do not receive visitor IPs (the Worker makes the calls) or anything typed by the visitor (there is no free-text input).

## How this was tested
- Static scan of `index.html` and `app.js`: 0 inline `<script>`, 0 inline event handlers, 0 `javascript:` URLs, 0 `eval`/`new Function`, 0 `document.write`, 0 auto-loaded external URLs, 0 secret patterns; 19 article links, all `https`, click-only.
- Parameter fuzzing: 32 URL parameters × 11 pages and 20 payload forms, with and without validation; 14 hostile links; hostile AI replies.
- Worker: 21 tests (origin, method, content type, size, schema, prompt injection, URL filtering, rate limiting, error leakage).
- Failure modes: network error, 429, 502, non-JSON reply, hostile reply.
- Real load of the site from files: scripts load in order, 0 errors, vendored jsPDF loads, AI shows the "switched off" message when unset.
- Dependency check: jsPDF advisories reviewed; fonts are SIL OFL (licences in `fonts/`).

**Not tested:** a real browser enforcing the CSP (the test environment does not enforce it), mobile browsers, and Cloudflare/GitHub infrastructure. After deploying, open DevTools and confirm the Console shows no CSP violations (README step 4).

## Hardening checklist for your account
- [ ] Revoke the leaked NVIDIA key; create a new one (F1).
- [ ] Spend caps and alerts on NVIDIA, search and Cloudflare (F2).
- [ ] GitHub: 2FA on, branch protection on `main`, secret scanning and Dependabot on, "Enforce HTTPS" on.
- [ ] `ALLOWED_ORIGINS` contains only your real site origin; remove `http://localhost:8080` after testing.
- [ ] Never commit `.env`, `.dev.vars` or keys. Rotate the key if you ever do.
- [ ] Verify files against `SHA256SUMS` before deploying.
