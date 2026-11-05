"use client";
import { useEffect, useState, useCallback } from "react";
import type { ScanSummary, ScanResult } from "@/types/scan";
import { listScans, getScanById, downloadReport } from "@/lib/api";
import ScoreGauge from "./ScoreGauge";
import CheckCard from "./CheckCard";
import FixList from "./FixList";
import NextStepPanel from "./NextStepPanel";

function domain(url: string) {
  return url.replace(/https?:\/\//, "").split("/")[0];
}

function formatDate(raw: string) {
  if (!raw) return "";
  // Backend returns YYYY-MM-D{T}HH:MM (compact); convert to ISO for Date parsing
  const iso = raw.replace(/{T}/, "T").replace(/^(\d{4})-(\d{2})-(\d{1,2})T(\d{2}):(\d{2})$/,
    (m, y, mo, d, h, mi) => y + "-" + mo + "-" + ("0" + d).slice(-2) + "T" + h + ":" + mi + ":00");
  const d = new Date(iso);
  if (isNaN(d.getTime())) return raw;
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" }) +
    " " + d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
}

function scoreColor(score: number) {
  if (score >= 80) return "text-green-400";
  if (score >= 60) return "text-green-400";
  if (score >= 40) return "text-amber-400";
  if (score >= 20) return "text-red-400";
  return "text-red-400";
}

export default function HistoryTab() {
  const [scans, setScans]             = useState<ScanSummary[]>([]);
  const [loading, setLoading]          = useState(true);
  const [error, setError]              = useState("");

  const [selected, setSelected]         = useState<ScanResult | null>(null);
  const [selectedId, setSelectedId]    = useState<number | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>("");
  const [loadError, setLoadError]      = useState("");
  const [downloading, setDl]           = useState<"txt" | "pdf" | null>(null);
  const [showAllChecks, setShowAll]    = useState(false);

  const loadList = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setScans(await listScans(50));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load history");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadList(); }, [loadList]);

  const openScan = async (id: number, createdAt: string) => {
    setSelected(null);
    setLoadError("");
    setShowAll(false);
    setSelectedId(id);
    setSelectedDate(createdAt);
    try {
      const result = await getScanById(id);
      // Ensure fields that may be absent from older stored results are present
      if (!result.recommendations) result.recommendations = [];
      if (!result.subpages) result.subpages = {};
      setSelected(result);
    } catch (e) {
      setLoadError(e instanceof Error ? e.message : "Failed to load scan");
      setSelectedId(null);
      setSelectedDate("");
    }
  };

  const handleDownload = async (type: "txt" | "pdf") => {
    if (!selected) return;
    setDl(type);
    try { await downloadReport(selected, type); }
    catch { /* handled inline */ }
    finally { setDl(null); }
  };

  const backToList = () => {
    setSelected(null);
    setSelectedId(null);
    setSelectedDate("");
    setLoadError("");
    setShowAll(false);
  };

  // --- Detail view ---
  if (selected) {
    const n = { pass: 0, warning: 0, fail: 0 };
    selected.checks.forEach((c) => n[c.status]++);

    return (
      <div className="space-y-10 animate-fade-in">
        {loadError && (
          <div className="rounded-lg bg-red-950/20 border border-red-900/30 px-4 py-4">
            <p className="text-sm text-red-400">{loadError}</p>
          </div>
        )}

        <div className="flex items-center justify-between">
          <button
            onClick={backToList}
            className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
          >
            ← Back to history
          </button>
          <span className="text-xs text-gray-600">
            Scanned {formatDate(selectedDate)}
          </span>
        </div>

        {/* Next action */}
        <NextStepPanel result={selected} onRescan={() => {}} />

        {/* Score */}
        <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6 rounded-lg border border-white/[0.06] p-4">
          <div className="w-32 shrink-0">
            <ScoreGauge score={selected.score} animate={false} />
          </div>
          <div className="flex-1 w-full space-y-4 sm:pt-2">
            <div className="flex gap-6">
              {([
                ["Passed",   n.pass,    "text-green-400"],
                ["Warnings", n.warning, "text-amber-400"],
                ["Failed",   n.fail,    "text-red-400"],
              ] as const).map(([label, val, cls]) => (
                <div key={label}>
                  <p className={`text-2xl font-black tabular-nums ${cls}`}>{val}</p>
                  <p className="text-xs text-gray-600 mt-0.5">{label}</p>
                </div>
              ))}
            </div>
            <a
              href={selected.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-gray-600 hover:text-gray-400 transition-colors truncate block"
            >
              {selected.url}
            </a>
          </div>
        </div>

        {/* Priority fixes */}
        <section>
          <p className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-4">
            Remaining Fixes
          </p>
          <FixList recs={selected.recommendations} />
        </section>

        {/* All checks */}
        <section>
          <button
            onClick={() => setShowAll((v) => !v)}
            className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-gray-500 hover:text-gray-300 transition-colors mb-4"
          >
            <span>All Checks</span>
            <span className="text-[8px] text-gray-700">{showAllChecks ? "▲" : "▼"}</span>
          </button>
          {showAllChecks && (
            <div className="space-y-0.5 animate-fade-in">
              {selected.checks.map((c) => (
                <CheckCard key={c.key} check={c} defaultOpen={c.status !== "pass"} />
              ))}
            </div>
          )}
        </section>

        {/* Actions */}
        <div className="flex flex-wrap items-center gap-4 pt-4 border-t border-white/[0.06]">
          <button
            onClick={() => handleDownload("txt")}
            disabled={downloading === "txt"}
            className="text-xs text-gray-500 hover:text-gray-200 transition-colors disabled:opacity-40"
          >
            {downloading === "txt" ? "Generating…" : "↓ Download .txt"}
          </button>
          <button
            onClick={() => handleDownload("pdf")}
            disabled={downloading === "pdf"}
            className="text-xs text-gray-500 hover:text-gray-200 transition-colors disabled:opacity-40"
          >
            {downloading === "pdf" ? "Generating…" : "↓ Download PDF"}
          </button>
        </div>
      </div>
    );
  }

  // --- List view ---
  return (
    <div className="space-y-6">
      <p className="text-sm text-gray-400">
        Browse past scans. Click one to see the full breakdown and re-download reports.
      </p>

      {loading && (
        <div className="flex items-center gap-3 py-8 justify-center">
          <span className="inline-block w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
          <span className="text-sm text-gray-500">Loading history…</span>
        </div>
      )}

      {error && (
        <div className="rounded-lg bg-red-950/20 border border-red-900/30 px-4 py-4">
          <p className="text-sm text-red-400">{error}</p>
          <button onClick={loadList} className="mt-2 text-xs text-gray-500 hover:text-gray-300 underline">
            Retry
          </button>
        </div>
      )}

      {!loading && !error && scans.length === 0 && (
        <p className="text-sm text-gray-600 py-8 text-center">
          No scans yet. Run a scan from the Scan tab and it will appear here.
        </p>
      )}

      {!loading && !error && scans.length > 0 && (
        <div className="rounded-xl border border-white/[0.06] overflow-hidden">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b border-white/[0.06]">
                <th className="text-left px-4 py-3 text-[10px] font-bold uppercase tracking-wider text-gray-600 w-1/3">Domain</th>
                <th className="text-left px-4 py-3 text-[10px] font-bold uppercase tracking-wider text-gray-600 w-1/4">Score</th>
                <th className="text-left px-4 py-3 text-[10px] font-bold uppercase tracking-wider text-gray-600 w-1/3">Scanned</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {scans.map((s) => (
                <tr
                  key={s.id}
                  onClick={() => openScan(s.id, s.created_at)}
                  className={`cursor-pointer hover:bg-white/[0.03] transition-colors ${selectedId === s.id ? "bg-blue-950/20" : ""}`}
                >
                  <td className="px-4 py-3 text-sm text-gray-300 truncate">{domain(s.url)}</td>
                  <td className={`px-4 py-3 text-sm font-black tabular-nums ${scoreColor(s.score)}`}>
                    {s.score}/100
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-500">{formatDate(s.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
