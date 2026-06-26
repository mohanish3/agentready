"""Per-check playbook with concrete fix recommendations."""
from typing import Dict, Any

# Check key to recommendation mapping
PLAYBOOK: Dict[str, Dict[str, Any]] = {
    "ai_crawler_access": {
        "recommendation": "Review and update robots.txt to allow access for AI crawlers (GPTBot, ClaudeBot, PerplexityBot). Remove 'Disallow: /' rules for these bots or add explicit 'Allow: /' directives.",
        "effort": "Low",
        "time": "30 minutes",
        "research_source": "OpenAI, Anthropic, and Perplexity crawler controls",
        "url": "https://developers.openai.com/api/docs/bots",
    },
    "llms_txt": {
        "recommendation": "Create a /llms.txt file at your domain root with an H1 title, a blockquote business summary, and links to key pages. This file provides structured context for AI inference systems.",
        "effort": "Low",
        "time": "1 hour",
        "research_source": "The /llms.txt file specification",
        "url": "https://llmstxt.org/",
    },
    "structured_data": {
        "recommendation": "Add JSON-LD structured data markup using Schema.org vocabulary. Include @type properties for Organization, Product, Offer, and ContactPoint entities to make content machine-readable.",
        "effort": "Medium",
        "time": "2-4 hours",
        "research_source": "Intro to structured data markup",
        "url": "https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data",
    },
    "js_rendering": {
        "recommendation": "Implement server-side rendering (SSR) or progressive enhancement for critical content. Ensure AI crawlers can access content in initial HTML without requiring JavaScript execution.",
        "effort": "High",
        "time": "1-2 days",
        "research_source": "Overview of OpenAI Crawlers",
        "url": "https://developers.openai.com/api/docs/bots",
    },
    "pricing_parsability": {
        "recommendation": "Add structured pricing information using Schema.org Offer properties. Include price, currency, availability, and priceValidUntil fields for machine-readable pricing data.",
        "effort": "Medium",
        "time": "2-3 hours",
        "research_source": "Schema.org Offer specification",
        "url": "https://schema.org/Offer",
    },
    "contact_parsability": {
        "recommendation": "Add structured contact information using Schema.org ContactPoint markup. Include telephone, areaCode, contactType, and availableHours for AI systems to route inquiries.",
        "effort": "Low",
        "time": "1-2 hours",
        "research_source": "Schema.org ContactPoint specification",
        "url": "https://schema.org/ContactPoint",
    },
    "api_discoverability": {
        "recommendation": "Publish an OpenAPI specification at /openapi.json or /swagger.json. This enables AI tools to discover and interact with your API programmatically.",
        "effort": "Medium",
        "time": "4-6 hours",
        "research_source": "OpenAPI Specification",
        "url": "https://spec.openapis.org/oas/latest.html",
    },
    "sitemap": {
        "recommendation": "Create and submit an XML sitemap at /sitemap.xml. List all important pages with lastmod, changefreq, and priority attributes for efficient crawling.",
        "effort": "Low",
        "time": "1-2 hours",
        "research_source": "Robots Exclusion Protocol RFC 9309",
        "url": "https://www.ietf.org/rfc/rfc9309.html",
    },
    "cookie_consent_wall": {
        "recommendation": "Modify cookie consent banner to allow crawler access without interaction. Use 'Accept Necessary Only' mode or add user-agent checks to bypass consent for bots.",
        "effort": "Medium",
        "time": "2-3 hours",
        "research_source": "Robots Exclusion Protocol RFC 9309",
        "url": "https://www.ietf.org/rfc/rfc9309.html",
    },
    "content_freshness": {
        "recommendation": "Add HTTP caching headers (Last-Modified, ETag, Cache-Control) to enable efficient content validation. Use 304 Not Modified responses for unchanged content.",
        "effort": "Low",
        "time": "1-2 hours",
        "research_source": "HTTP Semantics RFC 9110",
        "url": "https://www.rfc-editor.org/rfc/rfc9110.html",
    },
    "auth_wall": {
        "recommendation": "Provide a public landing page without authentication requirements. AI crawlers cannot authenticate, so ensure core content is accessible without login.",
        "effort": "High",
        "time": "1-2 days",
        "research_source": "Overview of OpenAI Crawlers",
        "url": "https://developers.openai.com/api/docs/bots",
    },
    "mcp_discoverability": {
        "recommendation": "Implement Model Context Protocol (MCP) at /.well-known/mcp.json to expose resources, prompts, and tools. This enables AI agents to discover and use your services.",
        "effort": "Medium",
        "time": "3-5 hours",
        "research_source": "Model Context Protocol specification",
        "url": "https://modelcontextprotocol.io/specification/2024-11-05/basic",
    },
}


def get_recommendation(check_key: str) -> Dict[str, Any]:
    """Get the playbook recommendation for a check."""
    return PLAYBOOK.get(check_key, {
        "recommendation": "No specific recommendation available for this check.",
        "effort": "Unknown",
        "time": "Unknown",
    })


def get_recommendations_for_result(result: Dict[str, Any]) -> list:
    """Get recommendations for failed/warning checks in a result."""
    recommendations = []
    for check in result.get("checks", []):
        if check.get("status") in ("fail", "warning"):
            rec = get_recommendation(check.get("key", ""))
            recommendations.append({
                "key": check.get("key", ""),
                "check": check.get("check", ""),
                "status": check.get("status", ""),
                "points_lost": check.get("points_lost", 0),
                "recommendation": rec.get("recommendation", ""),
                "effort": rec.get("effort", ""),
                "time": rec.get("time", ""),
                "research_source": rec.get("research_source", ""),
                "url": rec.get("url", ""),
            })
    return recommendations
