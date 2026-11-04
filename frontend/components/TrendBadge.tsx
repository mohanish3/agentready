"use client";
import { useEffect, useState } from "react";
import { fetchTrend, type TrendData } from "@/lib/api";

interface Props {
  url: string;
}

/**
 * Compact trend indicator rendered beside the score gauge.
 *
 * Shows an arrow comparing the most recent scan to the previous one:
 *   - green up arrow   +N vs last scan  (score rose)
 *   - red down arrow   -N vs last scan  (score fell)
 *   - gray dash         no change / no prior scan
 *
 * Fetches the time series from GET /api/trend and hides itself silently
 * when the request fails so it never blocks the main scan view.
 */
export default function TrendBadge({ url }: Props) {
  const [trend, setTrend] = useState<TrendData | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let active = true;
    setTrend(null);
    setFailed(false);

    fetchTrend(url, 5)
      .then((data) => {
        if (active) setTrend(data);
      })
      .catch(() => {
        if (active) setFailed(true);
      });

    return () => {
      active = false;
    };
  }, [url]);

  if (failed || trend === null) return null;

  const { delta } = trend;
  // Flat when there is no prior scan (delta is null) or the score did not move.
  const flat = delta === null || delta === 0;

  if (flat) {
    return (
      <span
        className="inline-flex items-center gap-1 text-xs text-gray-500"
        title="No change vs last scan"
      >
        <span aria-hidden>&#8226;</span>
        <span>no change vs last scan</span>
      </span>
    );
  }

  const up = delta > 0;
  const color = up ? "text-green-400" : "text-red-400";
  const arrow = up ? "↑" : "↓";
  const magnitude = Math.abs(delta);

  return (
    <span
      className={`inline-flex items-center gap-1 text-xs font-semibold ${color}`}
      title={`Score changed by ${delta > 0 ? "+" : ""}${delta} vs last scan`}
    >
      <span aria-hidden>{arrow}</span>
      <span className="tabular-nums">
        {delta > 0 ? "+" : ""}
        {delta} vs last scan
      </span>
      {/* keep magnitude referenced for readability in the a11y label */}
      <span className="sr-only">{magnitude} points</span>
    </span>
  );
}
