"""Badge server for serving readiness score SVG badges."""
import re
from typing import Optional
from pathlib import Path

try:
    from fastapi import FastAPI, HTTPException, Query
    from fastapi.responses import HTMLResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.middleware.cors import CORSMiddleware
    
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

# SVG badge colors
COLORS = {
    "pass": "#4CAF50",      # Green
    "warning": "#FFC107",   # Yellow/Amber
    "fail": "#F44336",      # Red
    "unknown": "#9E9E9E",   # Grey
    "text": "#FFFFFF",
    "bg": "#1A1A1A",
}


def _truncate_domain(domain: str) -> str:
    """Truncate domain if too long for display."""
    short_domain = domain.replace("https://", "").replace("http://", "").rstrip("/")
    if len(short_domain) > 18:
        short_domain = short_domain[:15] + "..."
    return short_domain


def generate_svg(score: int, domain: str, width: int = 300, height: int = 50) -> str:
    """Generate an SVG badge with the readiness score."""
    # Determine color based on score
    if score is None:
        status = "unknown"
        color = COLORS["unknown"]
    elif score >= 80:
        status = "pass"
        color = COLORS["pass"]
    elif score >= 50:
        status = "warning"
        color = COLORS["warning"]
    else:
        status = "fail"
        color = COLORS["fail"]
    
    # Truncate domain if too long
    short_domain = _truncate_domain(domain)
    
    # SVG content
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height}" role="img" aria-label="AgentReady badge for {domain}: {score}/100">
  <title>AgentReady Badge for {domain}</title>
  <defs>
    <linearGradient id="b" x2="0" y2="100%">
      <stop offset="0" stop-color="#777"/>
      <stop offset="100%" stop-color="#fff"/>
    </linearGradient>
    <linearGradient id="a" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0" stop-color="#333"/>
      <stop offset="100%" stop-color="#555"/>
    </linearGradient>
  </defs>
  <rect rx="10" width="{width}" height="{height}" fill="url(#a)"/>
  <text x="{width/2}" y="{height*0.6}" fill="#eee" font-family="system-ui, sans-serif" font-size="{height*0.7}" text-anchor="middle">{score}</text>
  <text x="{width/2}" y="{height*0.75}" fill="{color}" font-family="system-ui, sans-serif" font-size="{height*0.4}" text-anchor="middle">{status.upper()}</text>
</svg>'''
    
    return svg


def generate_svg_with_domain(score: int, domain: str) -> str:
    """Generate an SVG badge with domain link."""
    # Determine color based on score
    if score is None:
        status = "unknown"
        color = COLORS["unknown"]
    elif score >= 80:
        status = "pass"
        color = COLORS["pass"]
    elif score >= 50:
        status = "warning"
        color = COLORS["warning"]
    else:
        status = "fail"
        color = COLORS["fail"]
    
    # Truncate domain if too long
    short_domain = _truncate_domain(domain)
    
    # SVG content with link - use truncated domain in text
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="320" height="50" role="img" aria-label="AgentReady badge for {domain}: {score}/100">
  <title>AgentReady Badge for {domain}</title>
  <a xlink:href="{domain}" target="_blank" rel="noopener">
    <text x="160" y="35" fill="#eee" font-family="system-ui, sans-serif" font-size="28" text-anchor="middle">{score}</text>
    <text x="160" y="47" fill="{color}" font-family="system-ui, sans-serif" font-size="14" text-anchor="middle">{status.upper()}</text>
    <text x="160" y="62" fill="#999" font-family="system-ui, sans-serif" font-size="10" text-anchor="middle">{short_domain}</text>
  </a>
</svg>'''
    
    return svg


def make_badge_app() -> FastAPI:
    """Create the FastAPI app for badge serving."""
    app = FastAPI(title="AgentReady Badge Server")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/badge/{domain}")
    def badge(domain: str, score: Optional[int] = Query(None)) -> str:
        """Get a badge for a domain with optional score."""
        # Handle empty domain
        if not domain:
            raise HTTPException(status_code=400, detail="Empty domain not allowed")
        
        # Validate domain
        if not re.match(r'^[a-zA-Z0-9][-a-zA-Z0-9.]*$', domain):
            raise HTTPException(status_code=400, detail="Invalid domain format")
        
        # Handle score parameter
        if score is not None:
            if score < 0 or score > 100:
                raise HTTPException(status_code=400, detail="Score must be between 0 and 100")
            return generate_svg_with_domain(score, domain)
        
        # For now, we can't get the actual score without scanning
        # Return badge with placeholder score
        return generate_svg_with_domain(0, domain)
    
    @app.get("/badge/{domain}/image")
    def badge_image(domain: str, score: Optional[int] = Query(None)) -> bytes:
        """Get badge as image bytes."""
        content = generate_svg_with_domain(score or 0, domain)
        return content.encode("utf-8"), "image/svg+xml"
    
    @app.get("/health")
    def health():
        return {"status": "ok"}
    
    @app.get("/api/badge/{domain}")
    def badge_json(domain: str, score: Optional[int] = Query(None)):
        """Get badge info as JSON."""
        return {
            "domain": domain,
            "score": score,
            "status": "pass" if score and score >= 80 else ("warning" if score and score >= 50 else "fail" if score else "unknown"),
        }
    
    return app


if __name__ == "__main__":
    import uvicorn
    
    app = make_badge_app()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
