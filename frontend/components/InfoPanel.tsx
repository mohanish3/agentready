"use client";
import { useState } from "react";

export default function InfoPanel() {
  const [open, setOpen] = useState(false);

  return (
    <div className="border-t border-white/[0.06] pt-6">
      <button
        onClick={() => setOpen(!open)}
        className="text-xs text-gray-600 hover:text-gray-400 transition-colors flex items-center gap-1.5"
      >
        <span className="text-[10px]">{open ? "▲" : "▼"}</span>
        <span>About agentready</span>
      </button>

      {open && (
        <div className="mt-6 grid sm:grid-cols-3 gap-6 animate-fade-in">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-blue-400 mb-2">Why it matters</p>
            <p className="text-3xl font-black text-white leading-none">40%</p>
            <p className="text-xs text-gray-400 mt-2 leading-relaxed">
              of enterprise apps will embed AI procurement agents by end of 2026.
            </p>
            <p className="text-xs text-gray-400 mt-2 leading-relaxed">
              Sites that score poorly get{" "}
              <strong className="text-red-400">filtered out</strong> before a human ever reviews them.
            </p>
          </div>

          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-blue-400 mb-2">How it&apos;s different</p>
            <div className="space-y-2">
              {[
                ["Profound / Peec AI", "Brand mentions"],
                ["Google Lighthouse",  "Human UX"],
              ].map(([tool, focus]) => (
                <div key={tool} className="flex justify-between text-xs">
                  <span className="text-gray-400">{tool}</span>
                  <span className="text-gray-600">{focus}</span>
                </div>
              ))}
              <div className="flex justify-between text-xs border-t border-white/[0.06] pt-2">
                <span className="text-green-400 font-semibold">agentready ✓</span>
                <span className="text-green-400 font-semibold">Agent actionability</span>
              </div>
            </div>
          </div>

          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-blue-400 mb-2">Methodology</p>
            <p className="text-xs text-gray-400 leading-relaxed">
              Fully <strong className="text-white">deterministic</strong> — no LLM involved.
              Fetches static HTML + robots.txt and runs{" "}
              <strong className="text-white">12 rule-based checks</strong>.
              Every result is reproducible and explainable.
            </p>
          </div>
        </div>
      )}

      <p className="text-[11px] text-gray-700 mt-6">by Mohanish · MIT License</p>
    </div>
  );
}
