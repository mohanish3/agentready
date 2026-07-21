import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


DEFAULT_DB_PATH = Path(__file__).resolve().parent / "agentready.sqlite3"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str | Path = DEFAULT_DB_PATH) -> None:
    with closing(connect(db_path)) as conn:
        conn.executescript(
            """
            create table if not exists scans (
                id integer primary key autoincrement,
                url text not null,
                score integer not null,
                result_json text not null,
                created_at text not null
            );

            create table if not exists checks (
                id integer primary key autoincrement,
                scan_id integer not null references scans(id) on delete cascade,
                check_key text not null,
                label text not null,
                status text not null,
                points_earned integer not null,
                points_max integer not null,
                points_lost integer not null,
                detail text not null,
                action text,
                research_url text,
                confidence text,
                created_at text not null
            );

            create table if not exists pipeline_runs (
                id integer primary key autoincrement,
                scan_id integer references scans(id) on delete set null,
                url text not null,
                status text not null,
                started_at text not null,
                completed_at text,
                error text
            );

            create table if not exists research_sources (
                check_key text primary key,
                title text not null,
                url text not null,
                rationale text not null,
                last_reviewed text not null
            );
            """
        )
        conn.commit()


def start_pipeline_run(url: str, db_path: str | Path = DEFAULT_DB_PATH) -> int:
    init_db(db_path)
    with closing(connect(db_path)) as conn:
        cur = conn.execute(
            "insert into pipeline_runs (url, status, started_at) values (?, ?, ?)",
            (url, "running", _now()),
        )
        conn.commit()
        return int(cur.lastrowid)


def finish_pipeline_run(
    run_id: int,
    *,
    scan_id: int | None,
    status: str,
    error: str | None = None,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> None:
    with closing(connect(db_path)) as conn:
        conn.execute(
            """
            update pipeline_runs
            set scan_id = ?, status = ?, completed_at = ?, error = ?
            where id = ?
            """,
            (scan_id, status, _now(), error, run_id),
        )
        conn.commit()


def save_scan_result(result: dict[str, Any], db_path: str | Path = DEFAULT_DB_PATH) -> int:
    init_db(db_path)
    created_at = _now()
    with closing(connect(db_path)) as conn:
        cur = conn.execute(
            "insert into scans (url, score, result_json, created_at) values (?, ?, ?, ?)",
            (result["url"], result["score"], json.dumps(result), created_at),
        )
        scan_id = int(cur.lastrowid)

        for check in result.get("checks", []):
            source = check.get("research_source") or {}
            conn.execute(
                """
                insert into checks (
                    scan_id, check_key, label, status, points_earned, points_max,
                    points_lost, detail, action, research_url, confidence, created_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    scan_id,
                    check["key"],
                    check["check"],
                    check["status"],
                    check["points_earned"],
                    check["points_max"],
                    check["points_lost"],
                    check["detail"],
                    check.get("action"),
                    source.get("url"),
                    check.get("confidence"),
                    created_at,
                ),
            )

            if source:
                conn.execute(
                    """
                    insert into research_sources (check_key, title, url, rationale, last_reviewed)
                    values (?, ?, ?, ?, ?)
                    on conflict(check_key) do update set
                        title = excluded.title,
                        url = excluded.url,
                        rationale = excluded.rationale,
                        last_reviewed = excluded.last_reviewed
                    """,
                    (
                        check["key"],
                        source["title"],
                        source["url"],
                        source["rationale"],
                        source["last_reviewed"],
                    ),
                )

        conn.commit()
        return scan_id


def get_scan(scan_id: int, db_path: str | Path = DEFAULT_DB_PATH) -> dict[str, Any] | None:
    with closing(connect(db_path)) as conn:
        row = conn.execute("select result_json from scans where id = ?", (scan_id,)).fetchone()
    if row is None:
        return None
    return json.loads(row["result_json"])


def get_all_scans(db_path: str | Path = DEFAULT_DB_PATH) -> list[dict[str, Any]]:
    """Get all scans ordered by created_at descending."""
    with closing(connect(db_path)) as conn:
        rows = conn.execute("select * from scans order by created_at desc").fetchall()
    results = []
    for row in rows:
        result = {
            "id": row["id"],
            "url": row["url"],
            "score": row["score"],
            "created_at": row["created_at"],
        }
        result["result_json"] = json.loads(row["result_json"])
        results.append(result)
    return results


def get_last_scan_by_url(url: str, db_path: str | Path = DEFAULT_DB_PATH) -> dict[str, Any] | None:
    """Get the most recent scan for a specific URL."""
    with closing(connect(db_path)) as conn:
        row = conn.execute(
            "select * from scans where url = ? order by created_at desc limit 1",
            (url,)
        ).fetchone()
    if row is None:
        return None
    result = {
        "id": row["id"],
        "url": row["url"],
        "score": row["score"],
        "created_at": row["created_at"],
    }
    result["result_json"] = json.loads(row["result_json"])
    return result


def get_last_scan(db_path: str | Path = DEFAULT_DB_PATH) -> list[dict[str, Any]]:
    """Get all scans in reverse chronological order (alias for get_all_scans)."""
    return get_all_scans(db_path)
