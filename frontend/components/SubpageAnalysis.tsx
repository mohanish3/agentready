"use client";
import { useState } from "react";
import type { ScanResult } from "@/types/scan";

const PAGE_LABELS: Record<string, string> = {
  pricing: "Pricing Page",
  contact: "Contact Page",
  docs:    "Docs Page",
};

const CHECK_LABELS: Record<string, string> = {
  pricing_parsability: "Pricing Parsability",
  contact_parsability: "Contact Parsability",
  js_rendering:        "JS Rendering",
  structured_data:     "Structured Data",
};

export default function SubpageAnalysis({ subpages }: { subpages: ScanResult["subpages"] }) {
  const [open, setOpen] = useState(false);
  if (!Object.keys(subpages).length) return null;

  return (
    <section>
      <button
        className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-gray-500 hover:text-gray-300 transition-colors mb-4"
        onClick={() => setOpen(!open)}
      >
        <span>Sub-page Analysis</span>
        <span className="text-[8px] font-normal text-gray-700 normal-case tracking-normal">
          (informational · does not affect score)
        </span>
        <span className="text-[8px] text-gray-700">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div className="space-y-4 animate-fade-in">
          {Object.entries(subpages).map(([pageType, data]) => (
            <div key={pageType}>
              <div className="flex items-baseline gap-2 mb-2">
                <p className="text-xs font-semibold text-gray-300">
                  {PAGE_LABELS[pageType] ?? pageType}
                </p>
                <a
                  href={data.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-gray-600 hover:text-blue-400 transition-colors truncate"
                >
                  {data.url}
                </a>
              </div>
              <div className="space-y-1.5 pl-3 border-l border-white/[0.06]">
                {Object.entries(data)
                  .filter(([k]) => k !== "url")
                  .map(([key, res]) => {
                    const cls =
                      res.pass === true  ? "text-green-400"
                      : res.pass === null ? "text-amber-400"
                      : "text-red-400";
                    const icon = res.pass === true ? "✓" : res.pass === null ? "⚠" : "✕";
                    return (
                      <div key={key}>
                        <span className={`text-xs font-semibold ${cls}`}>
                          {icon} {CHECK_LABELS[key] ?? key}
                        </span>
                        <p className="text-xs text-gray-500 ml-4 leading-relaxed">{res.detail}</p>
                      </div>
                    );
                  })}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
