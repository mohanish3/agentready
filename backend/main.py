import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel

from scanner import scan, scan_stream, CHECKS
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


class CompareRequest(BaseModel):
    urls: list[str]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/scan/stream")
def scan_stream_endpoint(url: str):
    def generate():
        for event in scan_stream(url):
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
    result = scan(body.url)
    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])
    return result


@app.post("/api/compare")
def compare_endpoint(body: CompareRequest) -> list[dict[str, Any]]:
    urls = body.urls[:3]
    ordered = list(urls)
    results_map: dict[str, Any] = {}

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(scan, u): u for u in urls}
        for future in as_completed(futures):
            u = futures[future]
            try:
                results_map[u] = future.result()
            except Exception as e:
                results_map[u] = {"url": u, "error": str(e)}

    return [results_map[u] for u in ordered if u in results_map]


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
