import re
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

CHECKS = [
    ("ai_crawler_access",    "AI Crawler Access",                      20),
    ("llms_txt",             "llms.txt File",                          15),
    ("structured_data",      "Structured Data (JSON-LD / Schema.org)", 20),
    ("pricing_parsability",  "Pricing Parsability",                    15),
    ("contact_parsability",  "Contact Info Parsability",               10),
    ("api_discoverability",  "API Discoverability",                    10),
    ("sitemap",              "Sitemap.xml",                            10),
]

EFFORT = {
    "ai_crawler_access":   ("Easy",   "15 min"),
    "llms_txt":            ("Easy",   "1 hour"),
    "structured_data":     ("Medium", "2–4 hours"),
    "pricing_parsability": ("Medium", "2–4 hours"),
    "contact_parsability": ("Easy",   "30 min"),
    "api_discoverability": ("Hard",   "developer needed"),
    "sitemap":             ("Easy",   "30 min"),
}

AI_BOTS = ["GPTBot", "ClaudeBot", "anthropic-ai", "PerplexityBot", "ChatGPT-User"]


def _check_ai_crawler_access(base_url: str, session: requests.Session) -> dict:
    try:
        r = session.get(urljoin(base_url, "/robots.txt"), timeout=6)
        if r.status_code != 200:
            return {
                "pass": True,
                "detail": "No robots.txt — AI crawlers have unrestricted access.",
                "action": "No action needed.",
            }

        blocked = []
        lines = r.text.splitlines()
        current_agents = []

        for line in lines:
            line = line.strip()
            if line.lower().startswith("user-agent:"):
                current_agents = [line.split(":", 1)[1].strip()]
            elif line.lower().startswith("disallow:"):
                path = line.split(":", 1)[1].strip()
                if path in ("/", "/*"):
                    for agent in current_agents:
                        for bot in AI_BOTS:
                            if bot.lower() == agent.lower():
                                blocked.append(bot)
                        if agent == "*":
                            blocked.append("all crawlers (Disallow: /)")

        blocked = list(set(blocked))
        if blocked:
            return {
                "pass": False,
                "detail": f"Blocking: {', '.join(blocked)}. These agents cannot index your site.",
                "action": (
                    "Edit robots.txt: remove `Disallow: /` rules for GPTBot, ClaudeBot, "
                    "anthropic-ai, and PerplexityBot. If a wildcard `Disallow: /` is present, "
                    "add an explicit `Allow: /` block for each AI bot above it."
                ),
            }
        return {
            "pass": True,
            "detail": f"No AI crawlers blocked. Checked: {', '.join(AI_BOTS)}.",
            "action": "No action needed.",
        }
    except Exception as e:
        return {
            "pass": None,
            "detail": f"Could not fetch robots.txt: {e}",
            "action": "Verify robots.txt is publicly accessible at /robots.txt.",
        }


def _check_llms_txt(base_url: str, session: requests.Session) -> dict:
    try:
        r = session.get(urljoin(base_url, "/llms.txt"), timeout=6)
        if r.status_code == 200 and len(r.text.strip()) > 80:
            return {
                "pass": True,
                "detail": "llms.txt found and populated — AI agents have structured context about your business.",
                "action": "No action needed.",
            }
        elif r.status_code == 200:
            return {
                "pass": None,
                "detail": "llms.txt exists but is nearly empty.",
                "action": (
                    "Expand /llms.txt to include: a 2–3 sentence business description, "
                    "what you sell, your ideal customer profile, pricing model summary, "
                    "and a contact email. Reference: llmstxt.org for the spec."
                ),
            }
        return {
            "pass": False,
            "detail": "No llms.txt found. This file gives AI agents structured context about your business without scraping.",
            "action": (
                "Create a plain-text file at /llms.txt (your domain root). Include: "
                "what you sell, your ideal customer, pricing model, and a contact email. "
                "Takes under an hour. Reference: llmstxt.org."
            ),
        }
    except Exception as e:
        return {
            "pass": False,
            "detail": f"Could not check llms.txt: {e}",
            "action": "Create /llms.txt at your domain root with a business description.",
        }


def _check_structured_data(soup: BeautifulSoup) -> dict:
    scripts = soup.find_all("script", type="application/ld+json")
    found_types = []
    for script in scripts:
        try:
            data = json.loads(script.string or "")
            t = data.get("@type", "")
            if isinstance(t, list):
                found_types.extend(t)
            elif t:
                found_types.append(t)
        except Exception:
            pass

    has_og = bool(soup.find("meta", property="og:title") or soup.find("meta", attrs={"property": "og:title"}))

    if found_types:
        return {
            "pass": True,
            "detail": f"JSON-LD found — types: {', '.join(found_types)}. {'Open Graph also present.' if has_og else ''}",
            "action": "No action needed.",
        }
    elif has_og:
        return {
            "pass": None,
            "detail": "Open Graph tags present but no JSON-LD structured data.",
            "action": (
                "Add a `<script type='application/ld+json'>` block in your homepage `<head>`. "
                "Minimum viable: `{\"@context\": \"https://schema.org\", \"@type\": \"Organization\", "
                "\"name\": \"...\", \"url\": \"...\", \"description\": \"...\"}`. "
                "Reference: schema.org/Organization."
            ),
        }
    return {
        "pass": False,
        "detail": "No structured data found. AI agents cannot reliably extract your business type, offerings, or contact info.",
        "action": (
            "Add a `<script type='application/ld+json'>` block in your homepage `<head>`. "
            "Minimum viable: `{\"@context\": \"https://schema.org\", \"@type\": \"Organization\", "
            "\"name\": \"...\", \"url\": \"...\", \"description\": \"...\"}`. "
            "Reference: schema.org/Organization."
        ),
    }


def _check_pricing_parsability(soup: BeautifulSoup) -> dict:
    price_schema = soup.find_all(attrs={"itemprop": "price"})
    price_text = re.findall(r'[\$£€¥]\s*[\d,]+(?:\.\d{2})?', soup.get_text())

    if price_schema:
        return {
            "pass": True,
            "detail": "Prices found in Schema.org itemprop markup — AI agents can reliably extract your pricing.",
            "action": "No action needed.",
        }
    elif len(price_text) >= 1:
        return {
            "pass": None,
            "detail": f"Found {len(price_text)} price pattern(s) in page text but no structured markup — agents may misread them.",
            "action": (
                "Add `itemprop='price'` and `itemprop='priceCurrency'` to your pricing HTML elements. "
                "Or include a PriceSpecification block in your JSON-LD. "
                "This prevents agents from confusing prices with dates or phone numbers."
            ),
        }
    return {
        "pass": False,
        "detail": "No pricing found in static HTML. JavaScript-rendered prices are invisible to AI agents.",
        "action": (
            "Ensure at least one pricing tier is in static HTML (not JS-only). "
            "Add `itemprop='price'` markup or a visible pricing section in the page source. "
            "Contact-for-pricing sites should at minimum note the model (e.g., 'subscription', 'usage-based')."
        ),
    }


def _check_contact_parsability(soup: BeautifulSoup) -> dict:
    text = soup.get_text()
    emails = re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', text)
    emails = [e for e in emails if not re.search(r'\.(png|jpg|svg|gif|css|js)$', e, re.I)]
    phones = re.findall(r'(?:\+\d[\d\s\-\(\)]{8,14}|\(\d{3}\)\s?\d{3}[\-\s]\d{4})', text)

    found = []
    if emails:
        found.append(f"{len(emails)} email address(es)")
    if phones:
        found.append(f"{len(phones)} phone number(s)")

    if found:
        return {
            "pass": True,
            "detail": f"Contact info parseable in HTML: {', '.join(found)}.",
            "action": "No action needed.",
        }
    return {
        "pass": False,
        "detail": "No email or phone found in static HTML. AI agents cannot route inquiries to your team.",
        "action": (
            "Add a plaintext email address to your homepage or footer HTML. "
            "A standard mailto link is sufficient: `<a href='mailto:sales@yourco.com'>sales@yourco.com</a>`. "
            "Avoid image-based or JavaScript-obfuscated contact info."
        ),
    }


def _check_api_discoverability(base_url: str, session: requests.Session) -> dict:
    candidates = [
        "/openapi.json", "/swagger.json", "/api/docs",
        "/api-docs", "/.well-known/ai-plugin.json", "/.well-known/openai.json",
    ]
    found = []
    for path in candidates:
        try:
            r = session.get(urljoin(base_url, path), timeout=4)
            if r.status_code == 200:
                found.append(path)
        except Exception:
            pass

    if found:
        return {
            "pass": True,
            "detail": f"API discovery endpoint(s) found: {', '.join(found)}.",
            "action": "No action needed.",
        }
    return {
        "pass": False,
        "detail": "No standard API discovery endpoints found. AI agents cannot discover programmatic access to your business.",
        "action": (
            "If you have an API: publish an OpenAPI spec at `/openapi.json`. "
            "If not: create `/.well-known/ai-plugin.json` with your business name, description, "
            "and contact URL — low effort and signals API readiness to agents."
        ),
    }


def _check_sitemap(base_url: str, session: requests.Session) -> dict:
    try:
        r = session.get(urljoin(base_url, "/sitemap.xml"), timeout=6)
        if r.status_code == 200 and "<url>" in r.text:
            count = len(re.findall(r"<url>", r.text))
            return {
                "pass": True,
                "detail": f"sitemap.xml found with ~{count} URL(s) — AI crawlers can systematically discover your content.",
                "action": "No action needed.",
            }
        elif r.status_code == 200:
            return {
                "pass": None,
                "detail": "sitemap.xml found but appears malformed or empty.",
                "action": (
                    "Regenerate your sitemap via your CMS (WordPress, Webflow) or xml-sitemaps.com. "
                    "Validate it before republishing."
                ),
            }
        return {
            "pass": False,
            "detail": "No sitemap.xml found. AI crawlers must guess at your content structure.",
            "action": (
                "Generate a sitemap.xml using your CMS or xml-sitemaps.com. "
                "Place it at `/sitemap.xml` and add `Sitemap: https://yourdomain.com/sitemap.xml` "
                "to your robots.txt. Takes under 30 minutes."
            ),
        }
    except Exception as e:
        return {
            "pass": False,
            "detail": f"Could not fetch sitemap: {e}",
            "action": "Verify sitemap.xml is publicly accessible at /sitemap.xml.",
        }


def scan(url: str) -> dict:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    session = requests.Session()
    session.headers.update({
        "User-Agent": "agentready-scanner/1.0 (AI agent readiness audit; https://github.com/mohanishmhatre/agentready)"
    })

    try:
        r = session.get(url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        return {"error": str(e)}

    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    check_fns = {
        "ai_crawler_access":   lambda: _check_ai_crawler_access(base_url, session),
        "llms_txt":            lambda: _check_llms_txt(base_url, session),
        "structured_data":     lambda: _check_structured_data(soup),
        "pricing_parsability": lambda: _check_pricing_parsability(soup),
        "contact_parsability": lambda: _check_contact_parsability(soup),
        "api_discoverability": lambda: _check_api_discoverability(base_url, session),
        "sitemap":             lambda: _check_sitemap(base_url, session),
    }

    results = []
    total = 0

    for key, label, max_pts in CHECKS:
        outcome = check_fns[key]()
        if outcome.get("pass") is True:
            earned, status = max_pts, "pass"
        elif outcome.get("pass") is None:
            earned, status = max_pts // 2, "warning"
        else:
            earned, status = 0, "fail"

        total += earned
        effort_level, effort_time = EFFORT[key]
        results.append({
            "check":         label,
            "key":           key,
            "status":        status,
            "points_earned": earned,
            "points_max":    max_pts,
            "points_lost":   max_pts - earned,
            "detail":        outcome["detail"],
            "action":        outcome.get("action", ""),
            "effort_level":  effort_level,
            "effort_time":   effort_time,
        })

    fails_and_warnings = [c for c in results if c["status"] in ("fail", "warning")]
    fails_and_warnings.sort(key=lambda c: c["points_lost"], reverse=True)

    return {
        "url":             url,
        "score":           total,
        "checks":          results,
        "recommendations": fails_and_warnings,
    }
