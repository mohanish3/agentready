export const CHECKS = [
  { key: "ai_crawler_access",   label: "AI Crawler Access",                      max_pts: 20 },
  { key: "llms_txt",            label: "llms.txt File",                           max_pts: 15 },
  { key: "structured_data",     label: "Structured Data (JSON-LD / Schema.org)",  max_pts: 20 },
  { key: "js_rendering",        label: "JavaScript Rendering (SSR Check)",        max_pts: 15 },
  { key: "pricing_parsability", label: "Pricing Parsability",                     max_pts: 15 },
  { key: "contact_parsability", label: "Contact Info Parsability",                max_pts: 10 },
  { key: "api_discoverability", label: "API Discoverability & CORS",              max_pts: 10 },
  { key: "sitemap",             label: "Sitemap.xml",                             max_pts: 10 },
  { key: "cookie_consent_wall", label: "Cookie Consent Wall",                     max_pts: 10 },
  { key: "content_freshness",   label: "Content Freshness Headers",               max_pts: 10 },
  { key: "auth_wall",           label: "Authentication Wall",                     max_pts: 15 },
  { key: "mcp_discoverability", label: "MCP Agent Endpoint",                      max_pts: 10 },
] as const;
