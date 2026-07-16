import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse, JSONResponse
from pydantic import BaseModel
from storage import save_scan_result, get_scan

from scanner import CHECKS, scan
from pipeline import run_scan_pipeline, scan_pipeline_stream
from reports import generate_txt, generate_pdf

app = FastAPI(title="agentready API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScanRequest(BaseModel):
    url: str
    user_agent: str | None = None
    fail_below: int | None = None


class CompareRequest(BaseModel):
    urls: list[str]
    previous_results: list[dict] | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/scan/stream")
def scan_stream_endpoint(url: str):
    def generate():
        for event in scan_pipeline_stream(url):
            yield f"data: {json.dumps(event)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/scan")
def scan_endpoint(body: ScanRequest) -> dict[str, Any]:
    result = run_scan_pipeline(body.url, fail_below=body.fail_below)
    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])
    return result


@app.get("/api/scan/{domain}/raw")
def scan_raw_endpoint(domain: str):
    """
    GET /api/scan/:domain/raw
    
    Returns the most recent scan result in structured JSON format.
    Returns 200 with scan result if exists, 404 if no scan found for domain.
    """
    # Extract domain from URL
    parsed = urlparse(domain)
    url = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme else domain
    
    # Try to get cached scan result
    result = get_scan()
    
    # Filter by URL if multiple scans exist
    if result is None or not isinstance(result, list):
        # No cached results, return 404
        return JSONResponse(status_code=404, content={"error": "No scan results found"})
    
    # Find most recent scan for this domain
    domain_scans = [r for r in result if r.get("url") == url]
    if not domain_scans:
        return JSONResponse(status_code=404, content={"error": "No scan found for this domain"})
    
    # Return the most recent scan
    latest = domain_scans[-1]
    return JSONResponse(status_code=200, content=latest)


@app.post("/api/scan")
def scan_endpoint_with_save(body: ScanRequest) -> dict[str, Any]:
    """Scan endpoint that saves result to storage."""
    result = run_scan_pipeline(body.url, fail_below=body.fail_below)
    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])
    # Save to storage
    save_scan_result(result)
    return result


@app.post("/api/compare")
def compare_endpoint(body: CompareRequest) -> list[dict[str, Any]]:
    urls = body.urls[:3]
    ordered = list(urls)
    results_map: dict[str, Any] = {}
    previous_results = body.previous_results or []

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(scan, u): u for u in urls}
        for future in as_completed(futures):
            u = futures[future]
            try:
                results_map[u] = future.result()
            except Exception as e:
                results_map[u] = {"url": u, "error": str(e)}

    # Build comparison view
    comparison = []
    for url, result in results_map.items():
        if "error" in result:
            comparison.append({"url": url, "error": result["error"]})
            continue
        
        comp_entry = {
            "url": url,
            "score": result.get("score"),
            "checks": result.get("checks", []),
        }
        
        # Compare with previous results if available
        prev = next((p for p in previous_results if p.get("url") == url), None)
        if prev and "score" in prev:
            comp_entry["previous_score"] = prev["score"]
            score_change = result["score"] - prev["score"]
            comp_entry["score_change"] = score_change
            if score_change > 0:
                comp_entry["trend"] = "improved"
            elif score_change < 0:
                comp_entry["trend"] = "degraded"
            else:
                comp_entry["trend"] = "unchanged"
        
        comparison.append(comp_entry)
    
    return comparison


@app.post("/api/report/txt")
def report_txt(result: dict[str, Any]):
    content = generate_txt(result)
    safe = result.get("url", "report").replace("https://", "").replace("http://", "").replace("/", "_")
    return Response(
        content=content,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="agentready_{safe}.txt"'},
    )


@app.post("/api/report/pdf")
def report_pdf(result: dict[str, Any]):
    try:
        pdf_bytes = generate_pdf(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")
    safe = result.get("url", "report").replace("https://", "").replace("http://", "").replace("/", "_")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="agentready_{safe}.pdf"'},
    )


@app.get("/api/checks")
def list_checks():
    return [{"key": k, "label": l, "max_pts": p} for k, l, p in CHECKS]
