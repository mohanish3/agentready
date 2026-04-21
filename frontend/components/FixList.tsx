import type { CheckResult } from "@/types/scan";

const EFFORT_COLOR: Record<string, string> = {
  Easy:   "text-green-500",
  Medium: "text-amber-500",
  Hard:   "text-red-500",
};

export default function FixList({ recs }: { recs: CheckResult[] }) {
  if (!recs.length) {
    return (
      <p className="text-sm text-green-400 leading-relaxed">
        All checks passed — your site is well-positioned for agentic commerce.
      </p>
    );
  }

  return (
    <div>
      <p className="text-xs text-gray-600 mb-4">Sorted by points available — highest ROI first.</p>
      <div>
        {recs.map((r, i) => (
          <div
            key={r.key}
            className="flex gap-3 py-3 border-b border-white/[0.05] last:border-0"
          >
            <span className="text-xs font-mono text-gray-700 mt-0.5 shrink-0 w-5 text-right">
              {i + 1}.
            </span>
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5 mb-1">
                <span className="text-sm font-semibold text-gray-100">{r.check}</span>
                <span className="text-xs text-gray-600">+{r.points_lost} pts</span>
                <span className={`text-xs font-semibold ${EFFORT_COLOR[r.effort_level]}`}>
                  {r.effort_level} · {r.effort_time}
                </span>
              </div>
              <p className="text-xs text-gray-400 leading-relaxed">{r.action}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
