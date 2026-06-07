export default function Sidebar() {
  return (
    <aside className="w-64 shrink-0 hidden lg:flex flex-col gap-3 pt-6">
      <div className="rounded-xl bg-blue-950/30 border border-blue-900/40 p-4">
        <p className="text-[10px] font-bold uppercase tracking-widest text-blue-400 mb-2">Why it matters</p>
        <p className="text-xs text-gray-400 leading-relaxed">
          Crawlers and automated tools depend on raw HTML, robots.txt,
          structured data, sitemaps, and published API metadata.
        </p>
      </div>

      <div className="rounded-xl bg-gray-900 border border-gray-800 p-4">
        <p className="text-[10px] font-bold uppercase tracking-widest text-blue-400 mb-3">How it&apos;s different</p>
        <div className="space-y-0 divide-y divide-gray-800">
          {[
            ["Brand trackers", "Mentions"],
            ["Google Lighthouse", "Human UX"],
          ].map(([tool, focus]) => (
            <div key={tool} className="flex justify-between items-center py-2 text-xs">
              <span className="text-gray-400">{tool}</span>
              <span className="text-gray-600">{focus}</span>
            </div>
          ))}
          <div className="flex justify-between items-center py-2 text-xs">
            <span className="text-green-400 font-semibold">agentready</span>
            <span className="text-green-400 font-semibold">Technical readiness</span>
          </div>
        </div>
      </div>

      <div className="rounded-xl bg-gray-900 border border-gray-800 p-4">
        <p className="text-[10px] font-bold uppercase tracking-widest text-blue-400 mb-2">Methodology</p>
        <p className="text-xs text-gray-400 leading-relaxed">
          Deterministic scan. Fetches static HTML, robots.txt, discovery files,
          and key subpages, then runs <strong className="text-white">12 rule-based checks</strong>.
        </p>
      </div>

      <p className="text-[11px] text-gray-600 text-center mt-auto pb-4">
        by Mohanish - MIT License
      </p>
    </aside>
  );
}
