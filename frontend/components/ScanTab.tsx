"use client";
import { useState, useRef, useCallback } from "react";
import type { CheckResult, ScanPhase, ScanResult } from "@/types/scan";
import { streamScan, downloadReport } from "@/lib/api";
import CheckCard from "./CheckCard";
import ScoreGauge from "./ScoreGauge";
import FixList from "./FixList";
import SubpageAnalysis from "./SubpageAnalysis";

const EXAMPLES = ["stripe.com", "hubspot.com", "salesforce.com"];
const TOTAL_CHECKS = 12;

export default function ScanTab() {
  const [url, setUrl]               = useState("");
  const [phase, setPhase]           = useState<ScanPhase>("idle");
  const [checks, setChecks]         = useState<CheckResult[]>([]);
  const [result, setResult]         = useState<ScanResult | null>(null);
  const [error, setError]           = useState("");
  const [downloading, setDl]        = useState<"txt" | "pdf" | null>(null);
  const [showAllChecks, setShowAll] = useState(false);
  const stopRef = useRef<(() => void) | null>(null);

  const startScan = useCallback((target: string) => {
    const clean = target.startsWith("http") ? target : `https://${target}`;
    if (!clean.trim()) return;
    stopRef.current?.();
    setPhase("scanning");
    setChecks([]);
    setResult(null);
    setError("");
    setShowAll(false);
    stopRef.current = streamScan(
      clean,
      (raw) => setChecks((prev) => [...prev, raw as CheckResult]),
      (res) => { setResult(res); setPhase("complete"); },
      (msg) => { setError(msg); setPhase("error"); },
    );
  }, []);

  const handleSubmit = (e: React.FormEvent) => { e.preventDefault(); startScan(url); };
  const handleExample = (ex: string) => { setUrl(`https://${ex}`); startScan(ex); };

  const handleDownload = async (type: "txt" | "pdf") => {
    if (!result) return;
    setDl(type);
    try { await downloadReport(result, type); }
    catch { /* handled inline */ }
    finally { setDl(null); }
  };

  const reset = () => {
    stopRef.current?.();
    setPhase("idle");
    setChecks([]);
    setResult(null);
    setError("");
  };

  const progress = Math.round((checks.length / TOTAL_CHECKS) * 100);
  const n = { pass: 0, warning: 0, fail: 0 };
  checks.forEach((c) => n[c.status]++);

  return (
    <div className="space-y-6">
      {/* Input */}
      <form onSubmit={handleSubmit}>
        <div className="flex gap-2 p-1.5 rounded-xl bg-white/[0.04] border border-white/[0.08] focus-within:border-blue-500/40 transition-colors">
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="yourcompany.com"
            className="flex-1 bg-transparent px-3 py-2 text-sm text-gray-100 placeholder-gray-600 focus:outline-none"
            disabled={phase === "scanning"}
          />
          <button
            type="submit"
            disabled={!url.trim() || phase === "scanning"}
            className="px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed text-sm font-semibold transition-colors shrink-0"
          >
            {phase === "scanning" ? "Scanning…" : "Scan"}
          </button>
        </div>
      </form>

      {/* Examples */}
      {phase === "idle" && (
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 animate-fade-in">
          <span className="text-xs text-gray-600">Try:</span>
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              onClick={() => handleExample(ex)}
              className="text-xs text-gray-500 hover:text-blue-400 transition-colors"
            >
              {ex}
            </button>
          ))}
        </div>
      )}

      {/* Scanning */}
      {phase === "scanning" && (
        <div className="space-y-4">
          <div className="space-y-1.5">
            <div className="h-0.5 rounded-full bg-white/[0.06] overflow-hidden">
              <div
                className="h-full rounded-full bg-blue-500 transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-xs text-gray-600">{checks.length} / {TOTAL_CHECKS} checks complete</p>
          </div>
          <div className="space-y-0.5">
            {checks.map((c) => (
              <CheckCard key={c.key} check={c} defaultOpen={false} />
            ))}
          </div>
        </div>
      )}

      {/* Complete */}
      {phase === "complete" && result && (
        <div className="space-y-10 animate-fade-in">

          {/* Score */}
          <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6">
            <div className="w-44 shrink-0">
              <ScoreGauge score={result.score} />
            </div>
            <div className="flex-1 w-full space-y-4 sm:pt-2">
              <div className="flex gap-6">
                {([
                  ["Passed",   n.pass,    "text-green-400"],
                  ["Warnings", n.warning, "text-amber-400"],
                  ["Failed",   n.fail,    "text-red-400"  ],
                ] as const).map(([label, val, cls]) => (
                  <div key={label}>
                    <p className={`text-2xl font-black tabular-nums ${cls}`}>{val}</p>
                    <p className="text-xs text-gray-600 mt-0.5">{label}</p>
                  </div>
                ))}
              </div>
              <div className="flex gap-0.5 h-1 rounded-full overflow-hidden">
                {result.checks.map((c) => (
                  <div
                    key={c.key}
                    title={c.check}
                    className="flex-1"
                    style={{
                      background:
                        c.status === "pass" ? "#22c55e"
                        : c.status === "warning" ? "#f59e0b"
                        : "#ef4444",
                    }}
                  />
                ))}
              </div>
              <a
                href={result.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-gray-600 hover:text-gray-400 transition-colors truncate block"
              >
                {result.url}
              </a>
            </div>
          </div>

          {/* Priority fixes */}
          <section>
            <p className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-4">
              Priority Fixes
            </p>
            <FixList recs={result.recommendations} />
          </section>

          {/* All checks (collapsible) */}
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
                {result.checks.map((c) => (
                  <CheckCard key={c.key} check={c} defaultOpen={c.status !== "pass"} />
                ))}
              </div>
            )}
          </section>

          {/* Sub-pages */}
          <SubpageAnalysis subpages={result.subpages} />

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
            <button
              onClick={reset}
              className="text-xs text-gray-600 hover:text-gray-300 transition-colors ml-auto"
            >
              New scan
            </button>
          </div>
        </div>
      )}

      {/* Error */}
      {phase === "error" && (
        <div className="rounded-lg bg-red-950/20 border border-red-900/30 px-4 py-4 animate-fade-in">
          <p className="text-sm text-red-400 font-semibold mb-1">Scan failed</p>
          <p className="text-xs text-gray-400 leading-relaxed">{error}</p>
          <button onClick={reset} className="mt-3 text-xs text-gray-500 hover:text-gray-300 underline">
            Try again
          </button>
        </div>
      )}
    </div>
  );
}
