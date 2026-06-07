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
        <span className="text-[10px]">{open ? "^" : "v"}</span>
        <span>About agentready</span>
      </button>

      {open && (
        <div className="mt-6 grid sm:grid-cols-3 gap-6 animate-fade-in">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-blue-400 mb-2">Why it matters</p>
            <p className="text-xs text-gray-400 leading-relaxed">
              Crawlers and automated tools depend on raw HTML, robots.txt,
              structured data, sitemaps, and published API metadata. If those
              signals are missing, machines have to guess.
            </p>
          </div>

          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-blue-400 mb-2">How it&apos;s different</p>
            <div className="space-y-2">
              {[
                ["Brand trackers", "Mentions"],
                ["Google Lighthouse", "Human UX"],
              ].map(([tool, focus]) => (
                <div key={tool} className="flex justify-between text-xs">
                  <span className="text-gray-400">{tool}</span>
                  <span className="text-gray-600">{focus}</span>
                </div>
              ))}
              <div className="flex justify-between text-xs border-t border-white/[0.06] pt-2">
                <span className="text-green-400 font-semibold">agentready</span>
                <span className="text-green-400 font-semibold">Technical readiness</span>
              </div>
            </div>
          </div>

          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-blue-400 mb-2">Methodology</p>
            <p className="text-xs text-gray-400 leading-relaxed">
              Deterministic scan. Fetches static HTML, robots.txt, discovery files,
              and key subpages, then runs <strong className="text-white">12 rule-based checks</strong>.
              Results include source-backed rationale and are stored for audit.
            </p>
          </div>
        </div>
      )}

      <p className="text-[11px] text-gray-700 mt-6">by Mohanish - MIT License</p>
    </div>
  );
}
