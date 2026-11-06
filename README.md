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

## Live readiness badge

The API serves a GitHub-ready badge backed by the most recent stored scan, so a
README badge shows a site's real machine-readiness and refreshes each time it is
re-scanned (the badge reflects the latest *stored* score, not a live re-scan):

```
GET /api/badge/{domain}             -> SVG badge (image/svg+xml)
GET /api/badge/{domain}?format=markdown -> README-ready snippet
```

The domain accepts a bare host, a full URL, a `domain:port`, or a `www.`-prefixed
host; all are normalized to the bare host before the lookup. If a domain has never
been scanned the endpoint returns `404` rather than a placeholder score.

Paste this into a README (the score updates on re-scan):

```markdown
[![AgentReadiness example.com | 88/100](http://localhost:8000/api/badge/example.com)](http://localhost:8000)
```

In the web app, the **Copy badge** button on a finished scan copies this snippet
with the current score to your clipboard.

The badge image URL can be pointed at a custom host by setting the
`AGENTREADY_PUBLIC_URL` environment variable on the backend.

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

## How it works

Fetches the target URL and its `robots.txt` with a declared scanner user agent, runs the 8 checks against the static HTML response, and returns a per-check score breakdown with remediation notes.

## Who it's for

- B2B growth and RevOps teams auditing sites ahead of agentic-commerce workflows
- Developers who want a technical checklist rather than a brand-mention tracker
- Agencies auditing client sites before an AI-driven GTM push

## License

MIT
