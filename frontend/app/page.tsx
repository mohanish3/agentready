"use client";
import { useState } from "react";
import ScanTab from "@/components/ScanTab";
import CompareTab from "@/components/CompareTab";
import InfoPanel from "@/components/InfoPanel";

type Tab = "scan" | "compare";

export default function Home() {
  const [tab, setTab] = useState<Tab>("scan");

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-white/[0.06] px-6 py-4">
        <div className="max-w-2xl mx-auto flex items-center gap-2">
          <span className="font-black tracking-tight text-white">agentready</span>
          <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-px" />
        </div>
      </header>

      <main className="flex-1 max-w-2xl mx-auto w-full px-4 sm:px-6 py-10 space-y-8">
        <div>
          <h1 className="text-3xl sm:text-4xl font-black tracking-tight mb-2 leading-tight">
            Is your site ready<br className="sm:hidden" /> for AI agents?
          </h1>
          <p className="text-sm text-gray-400 leading-relaxed max-w-sm">
            AI purchasing agents are evaluating your competitors right now.
            Find out if they can even find <em>you</em>.
          </p>
        </div>

        <div className="flex border-b border-white/[0.06]">
          {(["scan", "compare"] as Tab[]).map((id) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition-colors -mb-px ${
                tab === id
                  ? "border-blue-500 text-white"
                  : "border-transparent text-gray-500 hover:text-gray-300"
              }`}
            >
              {id === "scan" ? "Scan" : "Compare"}
            </button>
          ))}
        </div>

        {tab === "scan"    && <ScanTab />}
        {tab === "compare" && <CompareTab />}

        <InfoPanel />
      </main>
    </div>
  );
}
