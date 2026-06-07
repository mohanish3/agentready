"use client";
import { useMemo, useState } from "react";
import type { ScanResult } from "@/types/scan";
import { selectNextStep } from "@/lib/nextStep";

export default function NextStepPanel({
  result,
  onRescan,
}: {
  result: ScanResult;
  onRescan: () => void;
}) {
  const next = useMemo(() => selectNextStep(result), [result]);
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    await navigator.clipboard.writeText(next.action);
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  };

  const complete = next.key === "complete";

  return (
    <section className="rounded-lg border border-blue-500/30 bg-blue-950/20 p-6 sm:p-8">
      <div className="flex flex-col gap-6">
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div className="min-w-0">
            <p className="text-xs font-bold uppercase tracking-widest text-blue-300 mb-3">
              Next Step
            </p>
            <h2 className="text-3xl sm:text-4xl font-black leading-tight text-white">
              {next.label}
            </h2>
          </div>
          <div className="shrink-0 rounded-md border border-white/[0.08] px-4 py-3">
            <p className="text-3xl font-black tabular-nums text-blue-300">+{next.pointsGain}</p>
            <p className="text-xs text-gray-500">possible points</p>
          </div>
        </div>

        {!complete && (
          <div className="grid sm:grid-cols-[1fr_auto] gap-4">
            <div>
              <p className="text-sm text-gray-300 leading-relaxed mb-3">{next.detail}</p>
              <p className="text-base text-white leading-relaxed">{next.action}</p>
            </div>
            <div className="sm:text-right">
              <p className="text-xs font-semibold text-gray-400">{next.effort}</p>
              <p className="text-xs text-gray-600 mt-1">confidence: {next.confidence ?? "high"}</p>
            </div>
          </div>
        )}

        {complete && <p className="text-base text-green-300">{next.action}</p>}

        {next.source && (
          <a
            href={next.source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-blue-300 hover:text-blue-200 transition-colors"
          >
            Source: {next.source.title}
          </a>
        )}

        <div className="flex flex-wrap gap-3">
          {!complete && (
            <button
              onClick={copy}
              className="px-5 py-3 rounded-md bg-blue-600 hover:bg-blue-500 text-sm font-bold transition-colors"
            >
              {copied ? "Copied" : next.cta}
            </button>
          )}
          <button
            onClick={onRescan}
            className="px-5 py-3 rounded-md border border-white/[0.12] text-sm font-semibold text-gray-200 hover:bg-white/[0.04] transition-colors"
          >
            Rescan
          </button>
        </div>
      </div>
    </section>
  );
}
