"use client";
import { useEffect, useState } from "react";

interface Props {
  score: number;
  animate?: boolean;
}

function scoreInfo(score: number): { color: string; label: string } {
  if (score >= 80) return { color: "#22c55e", label: "Agent-Ready" };
  if (score >= 60) return { color: "#16a34a", label: "Above Average" };
  if (score >= 40) return { color: "#f59e0b", label: "Average" };
  if (score >= 20) return { color: "#ef4444", label: "Below Average" };
  return { color: "#dc2626", label: "Not Ready" };
}

export default function ScoreGauge({ score, animate = true }: Props) {
  const [displayed, setDisplayed] = useState(animate ? 0 : score);
  const { color, label } = scoreInfo(score);

  useEffect(() => {
    if (!animate) { setDisplayed(score); return; }
    const t = setTimeout(() => setDisplayed(score), 80);
    return () => clearTimeout(t);
  }, [score, animate]);

  const r = 80;
  const cx = 100;
  const cy = 105;
  const arcLen = Math.PI * r; // ~251.33
  const offset = arcLen * (1 - displayed / 100);
  const arc = `M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`;

  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 200 115" className="w-full max-w-[220px]">
        {/* Track */}
        <path d={arc} fill="none" stroke="#1f2937" strokeWidth="10" strokeLinecap="round" />
        {/* Fill */}
        <path
          d={arc}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={arcLen}
          strokeDashoffset={offset}
          className="gauge-path"
        />
        {/* Score */}
        <text
          x={cx} y={cy - 14}
          textAnchor="middle"
          fontSize="42"
          fontWeight="800"
          fill={color}
          fontFamily="Inter, system-ui, sans-serif"
        >
          {displayed}
        </text>
        {/* /100 */}
        <text
          x={cx} y={cy + 4}
          textAnchor="middle"
          fontSize="12"
          fill="#6b7280"
          fontFamily="Inter, system-ui, sans-serif"
        >
          / 100
        </text>
      </svg>
      <span
        className="text-sm font-semibold mt-1"
        style={{ color }}
      >
        {label}
      </span>
    </div>
  );
}
