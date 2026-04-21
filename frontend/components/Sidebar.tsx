export default function Sidebar() {
  return (
    <aside className="w-64 shrink-0 hidden lg:flex flex-col gap-3 pt-6">
      <div className="rounded-xl bg-blue-950/30 border border-blue-900/40 p-4">
        <p className="text-[10px] font-bold uppercase tracking-widest text-blue-400 mb-2">Why it matters</p>
        <p className="text-3xl font-black text-white leading-none">40%</p>
        <p className="text-xs text-gray-400 mt-1 leading-relaxed">
          of enterprise apps will embed AI procurement agents by end of 2026
        </p>
        <p className="text-xs text-gray-400 mt-2 leading-relaxed">
          Sites that score poorly get{" "}
          <strong className="text-red-400">filtered out</strong> before a human ever reviews them.
        </p>
      </div>

      <div className="rounded-xl bg-gray-900 border border-gray-800 p-4">
        <p className="text-[10px] font-bold uppercase tracking-widest text-blue-400 mb-3">How it&apos;s different</p>
        <div className="space-y-0 divide-y divide-gray-800">
          {[
            ["Profound / Peec AI", "Brand mentions"],
            ["Google Lighthouse",  "Human UX"],
          ].map(([tool, focus]) => (
            <div key={tool} className="flex justify-between items-center py-2 text-xs">
              <span className="text-gray-400">{tool}</span>
              <span className="text-gray-600">{focus}</span>
            </div>
          ))}
          <div className="flex justify-between items-center py-2 text-xs">
            <span className="text-green-400 font-semibold">agentready ✓</span>
            <span className="text-green-400 font-semibold">Agent actionability</span>
          </div>
        </div>
      </div>

      <div className="rounded-xl bg-gray-900 border border-gray-800 p-4">
        <p className="text-[10px] font-bold uppercase tracking-widest text-blue-400 mb-2">Methodology</p>
        <p className="text-xs text-gray-400 leading-relaxed">
          Fully <strong className="text-white">deterministic</strong> — no LLM involved.
          Fetches static HTML + robots.txt and runs{" "}
          <strong className="text-white">12 rule-based checks</strong>.
          Every result is reproducible and explainable.
        </p>
      </div>

      <p className="text-[11px] text-gray-600 text-center mt-auto pb-4">
        by Mohanish &nbsp;·&nbsp; MIT License
      </p>
    </aside>
  );
}
