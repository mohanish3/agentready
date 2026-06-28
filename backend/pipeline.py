from pathlib import Path
from typing import Iterator

from scanner import scan_stream
from storage import DEFAULT_DB_PATH, finish_pipeline_run, save_scan_result, start_pipeline_run


def scan_pipeline_stream(url: str, fail_below: int = None, db_path: str | Path = DEFAULT_DB_PATH) -> Iterator[dict]:
    run_id = start_pipeline_run(url, db_path=db_path)
    scan_id = None

    try:
        for event in scan_stream(url, fail_below=fail_below):
            if event.get("type") == "complete":
                scan_id = save_scan_result({k: v for k, v in event.items() if k != "type"}, db_path=db_path)
                event["scan_id"] = scan_id
                event["pipeline_run_id"] = run_id
                finish_pipeline_run(run_id, scan_id=scan_id, status="complete", db_path=db_path)
            elif event.get("type") == "error":
                finish_pipeline_run(
                    run_id,
                    scan_id=None,
                    status="error",
                    error=event.get("error", "unknown scanner error"),
                    db_path=db_path,
                )
            yield event
    except Exception as exc:
        finish_pipeline_run(run_id, scan_id=scan_id, status="error", error=str(exc), db_path=db_path)
        raise


def run_scan_pipeline(url: str, fail_below: int = None, db_path: str | Path = DEFAULT_DB_PATH) -> dict:
    for event in scan_pipeline_stream(url, fail_below=fail_below, db_path=db_path):
        if event.get("type") == "complete":
            return {k: v for k, v in event.items() if k != "type"}
        if event.get("type") == "error":
            return {"error": event["error"]}
    return {"error": "Scan produced no result"}
