"use client";
import { useState } from "react";
import type { ComparePhase, ScanResult } from "@/types/scan";
import { compareUrls } from "@/lib/api";
import ScoreGauge from "./ScoreGauge";
import { CHECKS } from "@/lib/checks";

const STATUS_ICON: Record<string, string> = { pass: "✓", warning: "⚠", fail: "✕" };
const STATUS_CLS:  Record<string, string> = {
  pass:    "text-green-400",
  warning: "text-amber-400",
  fail:    "text-red-400",
};

function domain(url: string) {
  return url.replace(/https?:\/\//, "").split("/")[0];
}

function scoreColor(score: number) {
  if (score >= 80) return "#22c55e";
  if (score >= 60) return "#16a34a";
  if (score >= 40) return "#f59e0b";
  if (score >= 20) return "#ef4444";
  return "#dc2626";
}

export default function CompareTab() {
  const [urls, setUrls]   = useState(["", "", ""]);
  const [phase, setPhase] = useState<ComparePhase>("idle");
  const [results, setRes] = useState<ScanResult[]>([]);
  const [error, setError] = useState("");

  const setUrl = (i: number, v: string) =>
    setUrls((prev) => prev.map((u, idx) => (idx === i ? v : u)));

  const valid = urls.filter((u) => u.trim()).length >= 2;

  const handleCompare = async () => {
    const targets = urls.filter((u) => u.trim());
    setPhase("loading");
    setError("");
    setRes([]);
    try {
      setRes(await compareUrls(targets));
      setPhase("complete");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Compare failed");
      setPhase("idle");
    }
  };

  const urlLabels = ["Your site", "Competitor 1", "Competitor 2 (optional)"];

  return (
    <div className="space-y-6">
      <p className="text-sm text-gray-400">Enter up to 3 URLs to scan in parallel and compare side by side.</p>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {urls.map((u, i) => (
          <div key={i}>
            <label className="block text-xs text-gray-600 mb-1.5">{urlLabels[i]}</label>
            <input
              type="text"
              value={u}
              onChange={(e) => setUrl(i, e.target.value)}
              placeholder={i === 0 ? "yourcompany.com" : `competitor${i}.com`}
              disabled={phase === "loading"}
              className="w-full rounded-lg bg-white/[0.04] border border-white/[0.08] px-3 py-2.5 text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:border-blue-500/40 transition-colors"
            />
          </div>
        ))}
      </div>

      <button
        onClick={handleCompare}
        disabled={!valid || phase === "loading"}
        className="px-5 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed text-sm font-semibold transition-colors"
      >
        {phase === "loading" ? (
          <span className="flex items-center gap-2">
            <span className="inline-block w-3.5 h-3.5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
            Scanning {urls.filter((u) => u.trim()).length} sites…
          </span>
        ) : "Compare"}
      </button>

      {error && (
        <p className="text-sm text-red-400 rounded-lg bg-red-950/20 border border-red-900/30 px-4 py-3">
          {error}
        </p>
      )}

      {phase === "complete" && results.length > 0 && (
        <div className="space-y-8 animate-fade-in">
          {/* Score gauges */}
          <div className={`grid gap-4 ${results.length === 2 ? "grid-cols-2" : "grid-cols-3"}`}>
            {results.map((r, i) => (
              <div key={i} className="flex flex-col items-center gap-2 py-4">
                {"error" in r ? (
                  <p className="text-sm text-red-400 text-center">
                    Failed: {(r as { error: string }).error}
                  </p>
                ) : (
                  <>
                    <ScoreGauge score={r.score} />
                    <p className="text-xs text-gray-500 text-center truncate max-w-full">{domain(r.url)}</p>
                  </>
                )}
              </div>
            ))}
          </div>

          {/* Comparison table */}
          <div className="rounded-xl border border-white/[0.06] overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="border-b border-white/[0.06]">
                    <th className="text-left px-4 py-3 text-[10px] font-bold uppercase tracking-wider text-gray-600 w-1/3">
                      Check
                    </th>
                    {results.map((r, i) => (
                      <th key={i} className="text-left px-4 py-3 text-xs font-semibold text-gray-300">
                        {"error" in r ? "—" : domain(r.url)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.04]">
                  {CHECKS.map(({ key, label }) => (
                    <tr key={key} className="hover:bg-white/[0.02] transition-colors">
                      <td className="px-4 py-2.5 text-xs text-gray-500">{label}</td>
                      {results.map((r, i) => {
                        if ("error" in r) return <td key={i} className="px-4 py-2.5 text-gray-700">—</td>;
                        const chk = r.checks.find((c) => c.key === key);
                        if (!chk) return <td key={i} className="px-4 py-2.5 text-gray-700">—</td>;
                        return (
                          <td key={i} className={`px-4 py-2.5 text-xs font-semibold ${STATUS_CLS[chk.status]}`}>
                            {STATUS_ICON[chk.status]} {chk.points_earned}/{chk.points_max}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                  {/* Total row */}
                  <tr className="border-t border-white/[0.06]">
                    <td className="px-4 py-3 text-xs font-bold text-gray-400">Total Score</td>
                    {results.map((r, i) => {
                      if ("error" in r) return <td key={i} className="px-4 py-3 text-gray-700">—</td>;
                      return (
                        <td key={i} className="px-4 py-3 text-sm font-black tabular-nums" style={{ color: scoreColor(r.score) }}>
                          {r.score}/100
                        </td>
                      );
                    })}
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <button
            onClick={() => { setPhase("idle"); setRes([]); setUrls(["", "", ""]); }}
            className="text-xs text-gray-600 hover:text-gray-300 transition-colors"
          >
            New comparison
          </button>
        </div>
      )}
    </div>
  );
}
