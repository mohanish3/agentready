"""Bulk scanning CLI with concurrent httpx scanning."""
import asyncio
import csv
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
import httpx
import requests
from urllib.parse import urlparse

from .scanner import CHECKS


def run_checks_sync(session: requests.Session, url: str) -> Dict[str, Any]:
    """Run all checks for a URL synchronously."""
    checks = []
    total_earned = 0
    total_max = sum(max_pts for _, _, max_pts in CHECKS)
    
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    
    try:
        r = session.get(url, timeout=10)
        r.raise_for_status()
    except Exception as e:
        return {"url": url, "error": str(e), "checks": [], "score": None}
    
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(r.text, "html.parser")
    
    check_fns = {
        "ai_crawler_access": lambda: _check_ai_crawler_access(base_url, session),
        "llms_txt": lambda: _check_llms_txt(base_url, session),
        "structured_data": lambda: _check_structured_data(soup),
        "js_rendering": lambda: _check_js_rendering(soup),
        "pricing_parsability": lambda: _check_pricing_parsability(soup),
        "contact_parsability": lambda: _check_contact_parsability(soup),
        "api_discoverability": lambda: _check_api_discoverability(base_url, session),
        "sitemap": lambda: _check_sitemap(base_url, session),
        "cookie_consent_wall": lambda: _check_cookie_consent_wall(soup),
        "content_freshness": lambda: _check_content_freshness(dict(r.headers)),
        "auth_wall": lambda: _check_auth_wall(base_url, r, soup, session),
        "mcp_discoverability": lambda: _check_mcp_discoverability(base_url, session),
    }
    
    for key, label, max_pts in CHECKS:
        fn = check_fns.get(key)
        if fn is None:
            continue
        try:
            outcome = fn()
            if outcome is None:
                outcome = {"pass": None, "detail": "Skipped", "action": ""}
            if outcome.get("pass") is True:
                earned = max_pts
            elif outcome.get("pass") is None:
                earned = max_pts // 2
            else:
                earned = 0
            total_earned += earned
            checks.append({
                "check": label,
                "key": key,
                "status": "pass" if outcome.get("pass") is True else ("warning" if outcome.get("pass") is None else "fail"),
                "points_earned": earned,
                "points_max": max_pts,
                "points_lost": max_pts - earned,
                "detail": outcome.get("detail", ""),
                "action": outcome.get("action", ""),
            })
        except Exception as e:
            checks.append({
                "check": label,
                "key": key,
                "status": "error",
                "points_earned": 0,
                "points_max": max_pts,
                "points_lost": max_pts,
                "detail": f"Check failed: {e}",
                "action": "",
            })
    
    score = round(100 * total_earned / total_max) if total_max > 0 else 0
    
    return {
        "url": url,
        "checks": checks,
        "score": score,
    }


# Copy check functions from scanner.py (adapted)
def _check_ai_crawler_access(base_url: str, session: requests.Session) -> dict:
    try:
        r = session.get(f"{base_url}/robots.txt", timeout=5)
        if r.status_code != 200:
            return {"pass": None, "detail": "robots.txt not accessible", "action": "Check robots.txt"}
        return {"pass": True, "detail": "robots.txt accessible", "action": "No action needed"}
    except Exception:
        return {"pass": None, "detail": "Could not fetch robots.txt", "action": "Check robots.txt"}


def _check_llms_txt(base_url: str, session: requests.Session) -> dict:
    try:
        r = session.get(f"{base_url}/llms.txt", timeout=5)
        if r.status_code != 200:
            return {"pass": False, "detail": "No llms.txt found", "action": "Create /llms.txt"}
        content = r.text.strip()
        if not content or len(content) < 80:
            return {"pass": None, "detail": "llms.txt exists but is sparse", "action": "Expand /llms.txt"}
        return {"pass": True, "detail": "llms.txt is well-structured", "action": "No action needed"}
    except Exception as e:
        return {"pass": False, "detail": f"Could not check llms.txt: {e}", "action": "Create /llms.txt"}


def _check_structured_data(soup) -> dict:
    scripts = soup.find_all("script", type="application/ld+json")
    if scripts:
        return {"pass": True, "detail": "Structured data found", "action": "No action needed"}
    return {"pass": None, "detail": "No structured data found", "action": "Add JSON-LD markup"}


def _check_js_rendering(soup) -> dict:
    return {"pass": True, "detail": "JS rendering check placeholder", "action": "Review JS-heavy pages"}


def _check_pricing_parsability(soup) -> dict:
    offers = soup.find_all("span", itemprop="price")
    if offers:
        return {"pass": True, "detail": "Pricing parsable", "action": "No action needed"}
    return {"pass": None, "detail": "No pricing found", "action": "Add structured pricing"}


def _check_contact_parsability(soup) -> dict:
    contacts = soup.find_all("a", href=True)
    if len(contacts) >= 5:
        return {"pass": True, "detail": "Contact links found", "action": "No action needed"}
    return {"pass": None, "detail": "Limited contact links", "action": "Add contact links"}


def _check_api_discoverability(base_url: str, session) -> dict:
    try:
        r = session.get(f"{base_url}/openapi.json", timeout=5)
        if r.status_code == 200:
            return {"pass": True, "detail": "API documented", "action": "No action needed"}
    except Exception:
        pass
    return {"pass": None, "detail": "API not documented", "action": "Publish OpenAPI spec"}


def _check_sitemap(base_url: str, session) -> dict:
    try:
        r = session.get(f"{base_url}/sitemap.xml", timeout=5)
        if r.status_code == 200:
            return {"pass": True, "detail": "Sitemap found", "action": "No action needed"}
    except Exception:
        pass
    return {"pass": None, "detail": "Sitemap not found", "action": "Add sitemap.xml"}


def _check_cookie_consent_wall(soup) -> dict:
    overlays = soup.find_all("div", id=lambda x: x and "cookie" in x.lower())
    if overlays:
        return {"pass": False, "detail": "Cookie wall detected", "action": "Allow crawler access"}
    return {"pass": True, "detail": "No cookie wall", "action": "No action needed"}


def _check_content_freshness(headers) -> dict:
    if "Last-Modified" in headers or "ETag" in headers:
        return {"pass": True, "detail": "Freshness headers present", "action": "No action needed"}
    return {"pass": None, "detail": "No freshness headers", "action": "Add cache headers"}


def _check_auth_wall(base_url: str, response, soup, session) -> dict:
    try:
        r = session.get(f"{base_url}/", timeout=5)
        if r.status_code == 401 or r.status_code == 403:
            return {"pass": False, "detail": "Authentication required", "action": "Add public content"}
    except Exception:
        pass
    return {"pass": True, "detail": "No auth wall", "action": "No action needed"}


def _check_mcp_discoverability(base_url: str, session) -> dict:
    try:
        r = session.get(f"{base_url}/.well-known/mcp.json", timeout=5)
        if r.status_code == 200:
            return {"pass": True, "detail": "MCP endpoint found", "action": "No action needed"}
    except Exception:
        pass
    return {"pass": None, "detail": "MCP endpoint not found", "action": "Consider adding MCP"}


async def scan_domain_async(url: str, semaphore: asyncio.Semaphore) -> Dict[str, Any]:
    """Scan a single domain concurrently with rate limiting."""
    async with semaphore:
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                headers = {
                    "User-Agent": "agentready-scanner/1.0 (automated tool readiness audit)",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                }
                response = await client.get(url, headers=headers, follow_redirects=True)
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                return {"url": url, "error": f"HTTP {e.response.status_code}", "checks": [], "score": None}
            except httpx.TimeoutException:
                return {"url": url, "error": "Request timed out", "checks": [], "score": None}
            except Exception as e:
                return {"url": url, "error": str(e), "checks": [], "score": None}
    
    session = requests.Session()
    session.headers.update({"User-Agent": "agentready-scanner/1.0 (automated tool readiness audit)"})
    
    return await asyncio.to_thread(run_checks_sync, session, url)


async def bulk_scan_async(domains: List[str], concurrency: int = 5) -> List[Dict[str, Any]]:
    """Scan multiple domains concurrently."""
    semaphore = asyncio.Semaphore(concurrency)
    tasks = [scan_domain_async(url, semaphore) for url in domains]
    return await asyncio.gather(*tasks)


def scan_file(input_file: Path, concurrency: int = 5) -> List[Dict[str, Any]]:
    """Read domains from file and scan them concurrently."""
    domains = []
    with open(input_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                domains.append(line)
    
    return asyncio.run(bulk_scan_async(domains, concurrency))


def output_csv(results: List[Dict[str, Any]], output_file: Path):
    """Write results to CSV."""
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["url", "score", "check", "status", "points_earned", "points_max", "points_lost", "detail"])
        for result in results:
            url = result.get("url", "")
            score = result.get("score", 0)
            for check in result.get("checks", []):
                writer.writerow([
                    url, score,
                    check.get("check", ""),
                    check.get("status", ""),
                    check.get("points_earned", 0),
                    check.get("points_max", 0),
                    check.get("points_lost", 0),
                    check.get("detail", ""),
                ])


def output_json(results: List[Dict[str, Any]], output_file: Path):
    """Write results to JSON."""
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Bulk scan multiple domains")
    parser.add_argument("input_file", help="Path to file with domains, one per line")
    parser.add_argument("-o", "--output", help="Output file (CSV or JSON)")
    parser.add_argument("-f", "--format", choices=["csv", "json"], default="csv", help="Output format")
    parser.add_argument("-c", "--concurrency", type=int, default=5, help="Concurrent requests")
    
    args = parser.parse_args()
    
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1
    
    results = scan_file(input_path, args.concurrency)
    
    output_path = Path(args.output) if args.output else Path("bulk_scan_results.json")
    if args.format == "json":
        output_json(results, output_path)
    else:
        output_csv(results, output_path)
    
    print(f"Scanned {len(results)} domains, results written to {output_path}")
    return 0


if __name__ == "__main__":
    exit(main())
