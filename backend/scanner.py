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
    ("api_discoverability",  "API Discoverability & CORS",             10),
    ("sitemap",              "Sitemap.xml",                            10),
    ("cookie_consent_wall",  "Cookie Consent Wall",                    10),
    ("content_freshness",    "Content Freshness Headers",              10),
    ("auth_wall",            "Authentication Wall",                    15),
    ("mcp_discoverability",  "MCP Agent Endpoint",                     10),
]

EFFORT = {
    "ai_crawler_access":   ("Easy",   "15 min"),
    "llms_txt":            ("Easy",   "1 hour"),
    "structured_data":     ("Medium", "2-4 hours"),
    "js_rendering":        ("Hard",   "developer needed"),
    "pricing_parsability": ("Medium", "2-4 hours"),
    "contact_parsability": ("Easy",   "30 min"),
    "api_discoverability": ("Hard",   "developer needed"),
    "sitemap":             ("Easy",   "30 min"),
    "cookie_consent_wall": ("Medium", "1-2 hours"),
    "content_freshness":   ("Easy",   "30 min"),
    "auth_wall":           ("Medium", "varies"),
    "mcp_discoverability": ("Hard",   "developer needed"),
}

HIGH_VALUE_SCHEMA_TYPES = {
    "FAQPage", "Product", "Service", "SoftwareApplication",
    "ContactPoint", "PriceSpecification", "ItemList", "Article",
    "BlogPosting", "Event", "Person", "Review", "AggregateRating",
    "HowTo", "QAPage",
}
GENERIC_SCHEMA_TYPES = {"Organization", "WebSite", "WebPage", "BreadcrumbList"}

CSR_ROOT_IDS = ["root", "app", "__next", "gatsby-focus-wrapper", "nuxt", "__nuxt"]

AI_BOTS = ["GPTBot", "ClaudeBot", "anthropic-ai", "PerplexityBot", "ChatGPT-User"]

CMP_SCRIPT_SIGNATURES = [
    "cookielaw.org", "onetrust.com", "cookiebot.com", "trustarc.com",
    "cookiepro.com", "didomi.io", "quantcast.com/choice", "usercentrics",
    "iubenda.com", "cookiefirst.com",
]
CMP_ELEMENT_IDS = [
    "onetrust-consent-sdk", "cybotcookiebotdialog", "trustarc-consent-manager",
    "didomi-host", "uc-main-dialog",
]

MCP_PATHS = [
    "/.well-known/mcp.json",
    "/mcp/manifest.json",
    "/.well-known/agent.json",
]

SUBPAGE_KEYWORDS = {
    "pricing": ["pricing", "plans", "price"],
    "contact": ["contact", "talk to us", "reach us", "get in touch"],
    "docs":    ["docs", "documentation", "developer", "api reference"],
}

LOGIN_KEYWORDS = ["login", "signin", "sign-in", "/auth/", "/sso", "saml"]


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
                    "an H1 title (`# Company Name`), a blockquote summary (`> What you sell in 1-2 sentences`), "
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

        structure_count = sum([has_h1, has_blockquote, has_link])

        if structure_count >= 2:
            found = []
            if has_h1:         found.append("H1 title")
            if has_blockquote: found.append("blockquote summary")
            if has_link:       found.append("linked pages")
            return {
                "pass": True,
                "detail": f"llms.txt is well-structured ({', '.join(found)}) -- AI agents have reliable, parseable context about your business.",
                "action": "No action needed.",
            }
        elif len(content) > 80:
            missing = []
            if not has_h1:         missing.append("H1 title (`# Company Name`)")
            if not has_blockquote: missing.append("blockquote summary (`> What you sell`)")
            if not has_link:       missing.append("links to key pages")
            return {
                "pass": None,
                "detail": "llms.txt exists but lacks proper structure -- AI models may misparse it.",
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
                    "Expand /llms.txt with: an H1 title, a blockquote business summary (1-3 sentences), "
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
                    "Prioritise high-citation types: FAQPage, Product, or SoftwareApplication -- "
                    "pages with FAQPage schema receive 2.7x more AI citations than those without. "
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
    generic    = [t for t in found_types if t in GENERIC_SCHEMA_TYPES]

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
        return {
            "pass": None,
            "detail": (
                f"JSON-LD found but only generic types: {', '.join(generic or found_types)}. "
                "These help AI agents identify your site but don't signal products, pricing, or FAQs."
            ),
            "action": (
                "Add high-citation schema types: FAQPage (2.7x more AI citations), "
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

    csr_root = next(
        (soup.find("div", {"id": rid}) for rid in CSR_ROOT_IDS if soup.find("div", {"id": rid})),
        None,
    )

    if text_len < 200 and script_count > 0:
        return {
            "pass": False,
            "detail": (
                f"Only {text_len} characters of static text found alongside {script_count} script tags. "
                "This page is almost certainly client-side rendered -- AI crawlers (GPTBot, ClaudeBot, "
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
            f"Page contains {text_len} characters of static text -- AI crawlers can read your "
            "content without JavaScript execution."
        ),
        "action": "No action needed.",
    }


def _check_pricing_parsability(soup: BeautifulSoup) -> dict:
    price_schema = soup.find_all(attrs={"itemprop": "price"})
    price_text = re.findall(r'[\$\xa3€\xa5]\s*[\d,]+(?:\.\d{2})?', soup.get_text())

    if price_schema:
        return {
            "pass": True,
            "detail": "Prices found in Schema.org itemprop markup -- AI agents can reliably extract your pricing.",
            "action": "No action needed.",
        }
    elif len(price_text) >= 1:
        return {
            "pass": None,
            "detail": f"Found {len(price_text)} price pattern(s) in page text but no structured markup -- agents may misread them.",
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
    if emails: found.append(f"{len(emails)} email address(es)")
    if phones: found.append(f"{len(phones)} phone number(s)")

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
    cors_present = False

    for path in candidates:
        try:
            r = session.get(urljoin(base_url, path), timeout=4)
            if r.status_code == 200:
                found.append(path)
                if r.headers.get("Access-Control-Allow-Origin"):
                    cors_present = True
        except Exception:
            pass

    if found:
        if cors_present:
            return {
                "pass": True,
                "detail": f"API endpoint(s) found: {', '.join(found)}. CORS headers present -- AI agents can call this API cross-origin.",
                "action": "No action needed.",
            }
        return {
            "pass": None,
            "detail": f"API endpoint(s) found ({', '.join(found)}) but no CORS headers detected. AI agents may be blocked from calling your API cross-origin.",
            "action": (
                "Add `Access-Control-Allow-Origin: *` (or your specific agent domains) to your API responses. "
                "Without CORS headers, browser-based AI agents and tools cannot invoke your API directly."
            ),
        }
    return {
        "pass": False,
        "detail": "No standard API discovery endpoints found. AI agents cannot discover programmatic access to your business.",
        "action": (
            "If you have an API: publish an OpenAPI spec at `/openapi.json`. "
            "If not: create `/.well-known/ai-plugin.json` with your business name, description, "
            "and contact URL -- low effort and signals API readiness to agents."
        ),
    }


def _check_sitemap(base_url: str, session: requests.Session) -> dict:
    try:
        r = session.get(urljoin(base_url, "/sitemap.xml"), timeout=6)
        if r.status_code == 200 and "<url>" in r.text:
            count = len(re.findall(r"<url>", r.text))
            return {
                "pass": True,
                "detail": f"sitemap.xml found with ~{count} URL(s) -- AI crawlers can systematically discover your content.",
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


def _check_cookie_consent_wall(soup: BeautifulSoup) -> dict:
    detected = set()

    for script in soup.find_all("script", src=True):
        src = script.get("src", "").lower()
        for sig in CMP_SCRIPT_SIGNATURES:
            if sig in src:
                detected.add(sig.split(".")[0])
                break

    page_html = str(soup).lower()
    for eid in CMP_ELEMENT_IDS:
        if eid in page_html:
            detected.add(eid.split("-")[0])

    if detected:
        providers = ", ".join(sorted(detected))
        return {
            "pass": None,
            "detail": (
                f"Consent Management Platform detected ({providers}). Cookie consent popups may "
                "block AI crawlers from seeing JavaScript-loaded content, since crawlers don't "
                "interact with consent dialogs."
            ),
            "action": (
                "Ensure all key content (pricing, product descriptions, contact info) is present "
                "in static HTML before any consent-gated scripts fire. Test with JavaScript disabled "
                "in your browser -- if content disappears, AI crawlers can't see it either."
            ),
        }
    return {
        "pass": True,
        "detail": "No consent management platform (CMP) scripts detected in static HTML.",
        "action": "No action needed.",
    }


def _check_content_freshness(headers: dict) -> dict:
    last_modified = headers.get("Last-Modified") or headers.get("last-modified")
    etag = headers.get("ETag") or headers.get("etag")

    if last_modified and etag:
        return {
            "pass": True,
            "detail": "Both cache freshness headers present (Last-Modified + ETag). AI crawlers can efficiently decide when to re-index your content.",
            "action": "No action needed.",
        }
    elif last_modified:
        return {
            "pass": None,
            "detail": "Last-Modified present but ETag missing. Partial freshness signaling -- crawlers may re-fetch content unnecessarily.",
            "action": "Enable ETag on your server. Nginx: `etag on;` in http/server block. Apache: `FileETag All`. Cloudflare enables both automatically.",
        }
    elif etag:
        return {
            "pass": None,
            "detail": "ETag present but Last-Modified missing. Partial freshness signaling.",
            "action": "Enable Last-Modified headers alongside ETag. Most web servers support this with a single config line.",
        }
    return {
        "pass": False,
        "detail": "No Last-Modified or ETag headers. AI crawlers cannot determine if your content has changed, leading to inefficient re-crawling or stale indexing.",
        "action": (
            "Enable both headers on your web server. "
            "Nginx: add `etag on;` to your server block. Apache: `FileETag All` in .htaccess. "
            "Cloudflare and most CDNs emit both by default."
        ),
    }


def _check_auth_wall(base_url: str, response: requests.Response, soup: BeautifulSoup, session: requests.Session) -> dict:
    final_url = response.url.lower()
    if any(kw in final_url for kw in LOGIN_KEYWORDS):
        return {
            "pass": False,
            "detail": f"Homepage redirected to an authentication page ({response.url}). AI agents cannot access gated content.",
            "action": "Ensure public-facing pages are accessible without authentication.",
        }

    has_password = bool(soup.find("input", {"type": "password"}))
    text_len = len(soup.get_text(separator=" ", strip=True))

    if has_password and text_len < 600:
        return {
            "pass": False,
            "detail": "Login form with minimal visible content -- homepage appears fully gated behind authentication.",
            "action": "Make key public pages (pricing, product info, overview) accessible without authentication.",
        }

    key_paths = ["/pricing", "/plans", "/docs", "/documentation"]
    gated = []
    for path in key_paths:
        try:
            r = session.get(urljoin(base_url, path), timeout=5)
            if r.status_code in (401, 403):
                gated.append(path)
            elif any(kw in r.url.lower() for kw in LOGIN_KEYWORDS):
                gated.append(path)
        except Exception:
            pass

    if gated:
        return {
            "pass": None,
            "detail": f"Authentication wall on key sub-pages: {', '.join(gated)}. AI agents cannot read this content.",
            "action": (
                "Consider making at least a summary of pricing and docs publicly accessible. "
                "Even a static overview page helps AI agents understand your offering without login."
            ),
        }

    if has_password:
        return {
            "pass": None,
            "detail": "Login form present. Some content may require authentication to access.",
            "action": "Verify that pricing, product descriptions, and contact info are accessible without login.",
        }

    return {
        "pass": True,
        "detail": "No authentication walls detected on homepage or common sub-pages (/pricing, /docs).",
        "action": "No action needed.",
    }


def _check_mcp_discoverability(base_url: str, session: requests.Session) -> dict:
    found = []
    for path in MCP_PATHS:
        try:
            r = session.get(urljoin(base_url, path), timeout=4)
            if r.status_code == 200 and "json" in r.headers.get("Content-Type", ""):
                found.append(path)
        except Exception:
            pass

    if found:
        return {
            "pass": True,
            "detail": f"MCP manifest found: {', '.join(found)}. AI agents supporting the Model Context Protocol can discover and invoke your tools.",
            "action": "No action needed.",
        }
    return {
        "pass": False,
        "detail": "No MCP (Model Context Protocol) manifest found. AI agents cannot discover your available tools or actions.",
        "action": (
            "Publish an MCP manifest at /.well-known/mcp.json listing tools your site or API exposes "
            "(e.g., product lookup, quote generation, support ticket creation). "
            "MCP is an emerging standard -- early adopters gain agent framework compatibility first."
        ),
    }


def _detect_subpages(soup: BeautifulSoup, base_url: str) -> dict:
    domain = urlparse(base_url).netloc
    found = {}

    for a in soup.find_all("a", href=True):
        if len(found) == len(SUBPAGE_KEYWORDS):
            break
        text = a.get_text(strip=True).lower()
        href = a["href"].strip()

        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue

        abs_href = urljoin(base_url, href) if not href.startswith("http") else href

        if urlparse(abs_href).netloc != domain:
            continue

        href_lower = abs_href.lower()
        for page_type, keywords in SUBPAGE_KEYWORDS.items():
            if page_type in found:
                continue
            if any(kw in text or kw in href_lower for kw in keywords):
                found[page_type] = abs_href
                break

    return found


def _fetch_subpage(url: str, session: requests.Session):
    try:
        r = session.get(url, timeout=8)
        if r.status_code != 200:
            return None
        return BeautifulSoup(r.text, "html.parser")
    except Exception:
        return None


def scan_stream(url: str):
    """Generator that yields SSE-ready dicts for each check, then a final complete event."""
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
        yield {"type": "error", "error": str(e)}
        return

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
        "cookie_consent_wall": lambda: _check_cookie_consent_wall(soup),
        "content_freshness":   lambda: _check_content_freshness(dict(r.headers)),
        "auth_wall":           lambda: _check_auth_wall(base_url, r, soup, session),
        "mcp_discoverability": lambda: _check_mcp_discoverability(base_url, session),
    }

    results = []
    raw_total = 0
    max_total = sum(max_pts for _, _, max_pts in CHECKS)

    for key, label, max_pts in CHECKS:
        try:
            outcome = check_fns[key]()
        except Exception as e:
            outcome = {"pass": None, "detail": f"Check failed unexpectedly: {e}", "action": ""}

        if outcome.get("pass") is True:
            earned, status = max_pts, "pass"
        elif outcome.get("pass") is None:
            earned, status = max_pts // 2, "warning"
        else:
            earned, status = 0, "fail"

        raw_total += earned
        effort_level, effort_time = EFFORT[key]
        check_result = {
            "type":          "check",
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
        }
        results.append({k: v for k, v in check_result.items() if k != "type"})
        yield check_result

    score = round(raw_total * 100 / max_total)
    fails_and_warnings = sorted(
        [c for c in results if c["status"] in ("fail", "warning")],
        key=lambda c: c["points_lost"],
        reverse=True,
    )

    subpage_urls = _detect_subpages(soup, base_url)
    subpages = {}
    for page_type, page_url in subpage_urls.items():
        sub_soup = _fetch_subpage(page_url, session)
        if sub_soup is None:
            continue
        entry = {"url": page_url}
        if page_type == "pricing":
            entry["pricing_parsability"] = _check_pricing_parsability(sub_soup)
            entry["js_rendering"]        = _check_js_rendering(sub_soup)
        elif page_type == "contact":
            entry["contact_parsability"] = _check_contact_parsability(sub_soup)
        elif page_type == "docs":
            entry["structured_data"] = _check_structured_data(sub_soup)
            entry["js_rendering"]    = _check_js_rendering(sub_soup)
        subpages[page_type] = entry

    yield {
        "type":            "complete",
        "url":             url,
        "score":           score,
        "checks":          results,
        "recommendations": fails_and_warnings,
        "subpages":        subpages,
    }


def scan(url: str) -> dict:
    """Blocking scan that collects the stream into a single result dict."""
    for event in scan_stream(url):
        if event.get("type") == "complete":
            return {k: v for k, v in event.items() if k != "type"}
        if event.get("type") == "error":
            return {"error": event["error"]}
    return {"error": "Scan produced no result"}
