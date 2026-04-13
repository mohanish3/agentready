import re
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

CHECKS = [
    ("ai_crawler_access",    "AI Crawler Access",                      20),
    ("llms_txt",             "llms.txt File",                          15),
    ("structured_data",      "Structured Data (JSON-LD / Schema.org)", 20),
    ("js_rendering",         "JavaScript Rendering (SSR Check)",       15),
    ("pricing_parsability",  "Pricing Parsability",                    15),
    ("contact_parsability",  "Contact Info Parsability",               10),
    ("api_discoverability",  "API Discoverability",                    10),
    ("sitemap",              "Sitemap.xml",                            10),
]

EFFORT = {
    "ai_crawler_access":   ("Easy",   "15 min"),
    "llms_txt":            ("Easy",   "1 hour"),
    "structured_data":     ("Medium", "2–4 hours"),
    "js_rendering":        ("Hard",   "developer needed"),
    "pricing_parsability": ("Medium", "2–4 hours"),
    "contact_parsability": ("Easy",   "30 min"),
    "api_discoverability": ("Hard",   "developer needed"),
    "sitemap":             ("Easy",   "30 min"),
}

# Schema types that AI answer engines strongly weight for citations and extraction
HIGH_VALUE_SCHEMA_TYPES = {
    "FAQPage", "Product", "Service", "SoftwareApplication",
    "ContactPoint", "PriceSpecification", "ItemList", "Article",
    "BlogPosting", "Event", "Person", "Review", "AggregateRating",
    "HowTo", "QAPage",
}
GENERIC_SCHEMA_TYPES = {"Organization", "WebSite", "WebPage", "BreadcrumbList"}

# SPA root element IDs that indicate client-side rendering
CSR_ROOT_IDS = ["root", "app", "__next", "gatsby-focus-wrapper", "nuxt", "__nuxt"]

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
        if r.status_code != 200:
            return {
                "pass": False,
                "detail": "No llms.txt found. This file gives AI agents structured context about your business without scraping.",
                "action": (
                    "Create a plain-text Markdown file at /llms.txt. Structure it with: "
                    "an H1 title (`# Company Name`), a blockquote summary (`> What you sell in 1–2 sentences`), "
                    "and links to your key pages. Reference: llmstxt.org."
                ),
            }

        content = r.text.strip()
        if not content:
            return {
                "pass": False,
                "detail": "llms.txt exists but is empty.",
                "action": (
                    "Populate /llms.txt with: an H1 title, a blockquote business summary, "
                    "and links to key pages (pricing, docs, contact). Reference: llmstxt.org."
                ),
            }

        lines = content.splitlines()
        has_h1 = any(line.startswith("# ") for line in lines)
        has_blockquote = any(line.startswith("> ") for line in lines)
        has_link = bool(re.search(r'\[.+?\]\(https?://', content))

        structure_signals = [has_h1, has_blockquote, has_link]
        structure_count = sum(structure_signals)

        if structure_count >= 2:
            found = []
            if has_h1: found.append("H1 title")
            if has_blockquote: found.append("blockquote summary")
            if has_link: found.append("linked pages")
            return {
                "pass": True,
                "detail": f"llms.txt is well-structured ({', '.join(found)}) — AI agents have reliable, parseable context about your business.",
                "action": "No action needed.",
            }
        elif len(content) > 80:
            missing = []
            if not has_h1: missing.append("H1 title (`# Company Name`)")
            if not has_blockquote: missing.append("blockquote summary (`> What you sell`)")
            if not has_link: missing.append("links to key pages")
            return {
                "pass": None,
                "detail": f"llms.txt exists but lacks proper structure — AI models may misparse it.",
                "action": (
                    f"Add the missing elements: {'; '.join(missing)}. "
                    "A structured llms.txt becomes the AI's canonical mental model of your business."
                ),
            }
        else:
            return {
                "pass": None,
                "detail": "llms.txt exists but is too sparse (under 80 characters) to give AI agents useful context.",
                "action": (
                    "Expand /llms.txt with: an H1 title, a blockquote business summary (1–3 sentences), "
                    "and links to your pricing, docs, and contact pages. Reference: llmstxt.org."
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
            # Handle @graph arrays (common in WordPress/Yoast)
            if "@graph" in data:
                for node in data["@graph"]:
                    t = node.get("@type", "")
                    if isinstance(t, list):
                        found_types.extend(t)
                    elif t:
                        found_types.append(t)
            else:
                t = data.get("@type", "")
                if isinstance(t, list):
                    found_types.extend(t)
                elif t:
                    found_types.append(t)
        except Exception:
            pass

    has_og = bool(soup.find("meta", property="og:title") or soup.find("meta", attrs={"property": "og:title"}))

    if not found_types:
        if has_og:
            return {
                "pass": None,
                "detail": "Open Graph tags present but no JSON-LD structured data.",
                "action": (
                    "Add a `<script type='application/ld+json'>` block in your homepage `<head>`. "
                    "Prioritise high-citation types: FAQPage, Product, or SoftwareApplication — "
                    "pages with FAQPage schema receive 2.7× more AI citations than those without. "
                    "Reference: schema.org."
                ),
            }
        return {
            "pass": False,
            "detail": "No structured data found. AI agents cannot reliably extract your business type, offerings, or contact info.",
            "action": (
                "Add a `<script type='application/ld+json'>` block in your homepage `<head>`. "
                "Start with Organization, then add FAQPage or Product for high-value AI citation types. "
                "Reference: schema.org."
            ),
        }

    high_value = [t for t in found_types if t in HIGH_VALUE_SCHEMA_TYPES]
    generic = [t for t in found_types if t in GENERIC_SCHEMA_TYPES]

    if high_value:
        return {
            "pass": True,
            "detail": (
                f"High-value JSON-LD types found: {', '.join(high_value)}."
                + (f" Also generic types: {', '.join(generic)}." if generic else "")
                + (" Open Graph also present." if has_og else "")
                + " AI agents can extract structured business intent from this page."
            ),
            "action": "No action needed.",
        }
    else:
        # Only generic types present — partial credit
        return {
            "pass": None,
            "detail": (
                f"JSON-LD found but only generic types: {', '.join(generic or found_types)}. "
                "These help AI agents identify your site but don't signal products, pricing, or FAQs."
            ),
            "action": (
                "Add high-citation schema types: FAQPage (2.7× more AI citations), "
                "Product or SoftwareApplication (for B2B offering clarity), "
                "or ContactPoint (for inquiry routing). "
                "Keep your existing Organization schema and layer these on top."
            ),
        }


def _check_js_rendering(soup: BeautifulSoup) -> dict:
    body = soup.body
    text = (body or soup).get_text(separator=" ", strip=True)
    text_len = len(text)
    script_count = len(soup.find_all("script"))

    # Check for known SPA root elements
    csr_root = next(
        (soup.find("div", {"id": rid}) for rid in CSR_ROOT_IDS if soup.find("div", {"id": rid})),
        None,
    )

    if text_len < 200 and script_count > 0:
        return {
            "pass": False,
            "detail": (
                f"Only {text_len} characters of static text found alongside {script_count} script tags. "
                "This page is almost certainly client-side rendered — AI crawlers (GPTBot, ClaudeBot, "
                "PerplexityBot) do not execute JavaScript and will see empty content."
            ),
            "action": (
                "Implement server-side rendering (SSR) using Next.js, Nuxt, or Angular Universal, "
                "or use static site generation (SSG). Ensure pricing, product descriptions, and contact "
                "info appear in the raw HTML source. Test by viewing page source: if content isn't "
                "there, AI agents can't see it."
            ),
        }
    elif csr_root is not None and text_len < 600:
        return {
            "pass": None,
            "detail": (
                f"SPA root element detected (`id='{csr_root.get('id')}'`) with only {text_len} chars of "
                "static text. Some key content may be invisible to AI crawlers that don't execute JavaScript."
            ),
            "action": (
                "Verify that pricing, product descriptions, and contact info appear in the raw HTML "
                "page source (Ctrl+U in browser). Any content missing from page source is invisible to "
                "GPTBot, ClaudeBot, and PerplexityBot. Use SSR or pre-rendering for critical pages."
            ),
        }
    return {
        "pass": True,
        "detail": (
            f"Page contains {text_len} characters of static text — AI crawlers can read your "
            "content without JavaScript execution."
        ),
        "action": "No action needed.",
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
        "js_rendering":        lambda: _check_js_rendering(soup),
        "pricing_parsability": lambda: _check_pricing_parsability(soup),
        "contact_parsability": lambda: _check_contact_parsability(soup),
        "api_discoverability": lambda: _check_api_discoverability(base_url, session),
        "sitemap":             lambda: _check_sitemap(base_url, session),
    }

    results = []
    raw_total = 0
    max_total = sum(max_pts for _, _, max_pts in CHECKS)

    for key, label, max_pts in CHECKS:
        outcome = check_fns[key]()
        if outcome.get("pass") is True:
            earned, status = max_pts, "pass"
        elif outcome.get("pass") is None:
            earned, status = max_pts // 2, "warning"
        else:
            earned, status = 0, "fail"

        raw_total += earned
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

    # Normalise to 0–100 so the gauge always reads out of 100
    score = round(raw_total * 100 / max_total)

    fails_and_warnings = [c for c in results if c["status"] in ("fail", "warning")]
    fails_and_warnings.sort(key=lambda c: c["points_lost"], reverse=True)

    return {
        "url":             url,
        "score":           score,
        "checks":          results,
        "recommendations": fails_and_warnings,
    }
