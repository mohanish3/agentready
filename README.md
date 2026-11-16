# agentready

Static analysis tool that scores whether a website is machine-readable by AI agents: crawlable, parseable pricing and contact info, structured data, and API discoverability.

## Problem

AI agents increasingly act as intermediaries in B2B research and procurement. A site built only for human browsers (pricing rendered client-side, no structured data, crawlers blocked in robots.txt) is invisible to those agents regardless of how it looks to a person.

Existing GEO tools (Profound, Peec AI) measure whether a brand is *mentioned* in AI answers. They do not check whether an agent can extract pricing, contact details, or a machine-readable product description from the site itself. agentready checks that directly, with deterministic rules rather than an LLM call.

## What it checks

8 checks run against the static HTML response of the target URL. No LLM involved — every result is reproducible.

| Check | Points | Tests |
|---|---|---|
| AI crawler access | 20 | robots.txt does not block GPTBot, ClaudeBot, PerplexityBot |
| llms.txt | 15 | Present, with H1 title, blockquote summary, linked pages |
| Structured data | 20 | JSON-LD present; FAQPage/Product/SoftwareApplication scores above a generic Organization type |
| JavaScript rendering | 15 | Key content present in the raw HTML response, since AI crawlers do not execute JavaScript |
| Pricing parsability | 15 | Prices visible in static HTML |
| Contact parsability | 10 | Email or phone findable without JavaScript execution |
| API discoverability | 10 | `/openapi.json` or `/.well-known/ai-plugin.json` present |
| Sitemap | 10 | Valid `sitemap.xml` |

Score is normalized to 0–100.

## Score trend

After a scan completes, the scanner stores the result so you can track how a site's machine-readability score moves over time. Next to the score gauge in the Scan tab a compact **trend badge** appears:

- Green up arrow with `+N vs last scan` when the score rose
- Red down arrow with `-N vs last scan` when it fell
- A neutral dot when there is no prior scan to compare against

The badge is fetched from a small endpoint and hides itself silently if the request fails, so it never blocks the main scan view.

### API

`GET /api/trend?url=<url>&n=<count>` returns the last `n` scan scores for a URL as a time series:

```json
{ "url": "https://example.com", "scores": [50, 62, 74], "delta": 12 }
```

`delta` is the change from the previous scan (last minus second-to-last) and is `null` when fewer than two scans exist. `n` defaults to 5.

## Quickstart

Backend (FastAPI):

```bash
git clone https://github.com/mohanish3/agentready
cd agentready/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Frontend (Next.js), in a second terminal:

```bash
cd agentready/frontend
npm install
npm run dev
```

Open `http://localhost:3000` and enter a URL to scan.


## Scan history

Every scan is saved automatically. Open the **History** tab in the UI to browse past scans, view the full check breakdown for any previous result, and re-download the TXT or PDF report without re-scanning.

The backend also exposes two read-only endpoints:

- `GET /api/scans?limit=N` — most recent scan summaries (id, url, score, created_at), capped at 50 by default
- `GET /api/scans/{id}` — the full stored result for a single scan (404 if not found)

## How it works

Fetches the target URL and its `robots.txt` with a declared scanner user agent, runs the 8 checks against the static HTML response, and returns a per-check score breakdown with remediation notes.

## One-Click llms.txt + JSON-LD Generator

When a scan finds that `llms.txt` or structured data (JSON-LD) is missing, the **Fix Toolkit** shows a **Download your llms.txt / JSON-LD** button. Clicking it generates and downloads two ready-to-use files, pre-filled from what the scanner already detected about the site:

- **`llms_<domain>.txt`** — an `llms.txt` file following the [llmstxt.org](https://llmstxt.org/) spec: an H1 title from your domain, a blockquote summary, a Key Pages section with the detected pricing/docs/contact URLs, an About block, and a For Automated Tools section. Replace the bracketed placeholders with your real copy and drop it at your domain root.
- **`schema-<domain>.json`** — a JSON-LD snippet with `Organization`, `SoftwareApplication`, and `FAQPage` blocks pre-filled with your domain and contact/pricing URLs. Paste it into your `<head>`.

Both files are generated server-side by `POST /api/generate/llms-txt` and `POST /api/generate/json-ld`, which accept a scan result object and return the file for download. The same two checks are always offered as copy-paste blocks in the Fix Toolkit, so the generator is a convenience on top of, not a replacement for, the inline templates.

### API

`POST /api/generate/llms-txt` — body: a scan result object (as returned by `POST /api/scan`). Returns the file as `text/plain` with a `Content-Disposition` attachment header.

`POST /api/generate/json-ld` — body: a scan result object. Returns the file as `application/ld+json` with a `Content-Disposition` attachment header.

Both return `400` when the body is missing the `url` field.

## Who it's for

- B2B growth and RevOps teams auditing sites ahead of agentic-commerce workflows
- Developers who want a technical checklist rather than a brand-mention tracker
- Agencies auditing client sites before an AI-driven GTM push

## License

MIT
