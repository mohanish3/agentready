# agentready

> Scan any B2B website and find out if AI purchasing agents can actually do business with you.

**by Mohanish** · MIT License

---

## The Problem

GEO tools (Profound, Peec AI, Gauge) track whether AI assistants *mention* your brand. That's a brand awareness metric. It doesn't tell you whether an AI agent can *act* — find your pricing, route an inquiry, discover your API, or complete a procurement workflow.

Most B2B websites are built for human browsers. They block AI crawlers in robots.txt, hide prices behind JavaScript, bury contact info in PDFs, and have no machine-readable description of what they actually sell. As AI agents take over B2B buying workflows, these sites become invisible to the systems making the decisions.

**The cost of inaction:** Gartner projects that by end of 2026, 40% of enterprise applications will embed AI agents for procurement and vendor evaluation. A site that scores poorly on agent-readiness gets filtered out before a human ever sees it.

---

## Who This Is For

- **B2B growth and RevOps teams** preparing for agentic commerce
- **Website owners and developers** who want a technical checklist, not just brand tracking
- **Agencies** auditing client sites before launching AI-driven GTM motions

---

## Why Nothing Else Works

| Tool | What it does | What it misses |
|------|-------------|----------------|
| Profound / Peec AI | Tracks if AI mentions your brand | Doesn't audit technical actionability |
| Google Lighthouse | Audits human UX (speed, accessibility) | Zero awareness of AI agent access patterns |
| Manual checklist | Whatever you remember to check | Inconsistent, not repeatable |

---

## What Success Looks Like

A 100/100 score means: any AI purchasing agent that discovers your site can understand what you sell, see your pricing, find how to contact you, and optionally transact programmatically via your API. No human required to interpret your site.

---

## Quickstart

```bash
git clone https://github.com/mohanishmhatre/agentready
cd agentready
pip install -r requirements.txt
streamlit run app.py
```

Then enter any URL in the browser UI.

---

## The 7 Checks

| Check | Points | What it tests |
|-------|--------|---------------|
| AI Crawler Access | 20 | robots.txt not blocking GPTBot, ClaudeBot, PerplexityBot |
| llms.txt | 15 | /llms.txt file with business context for AI agents |
| Structured Data | 20 | JSON-LD / Schema.org markup (Product, Organization, ContactPoint) |
| Pricing Parsability | 15 | Prices visible in static HTML, not just JavaScript |
| Contact Parsability | 10 | Email/phone findable without JavaScript execution |
| API Discoverability | 10 | /openapi.json or /.well-known/ai-plugin.json present |
| Sitemap.xml | 10 | Valid sitemap for systematic content discovery |

---

## How It Works

agentready fetches your URL and robots.txt with a declared scanner user-agent, then runs 7 deterministic checks against the static HTML response. No LLM involved — every finding is reproducible and explainable. Each check is independently scored, so you get a breakdown of exactly where you're losing points and what to do about it.
