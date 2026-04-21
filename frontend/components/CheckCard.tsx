"use client";
import { useState } from "react";
import type { CheckResult } from "@/types/scan";

const STATUS = {
  pass:    { dot: "bg-green-500",  text: "text-green-400"  },
  warning: { dot: "bg-amber-500",  text: "text-amber-400"  },
  fail:    { dot: "bg-red-500",    text: "text-red-400"    },
};

const EFFORT_COLOR: Record<string, string> = {
  Easy:   "text-green-500",
  Medium: "text-amber-500",
  Hard:   "text-red-500",
};

export default function CheckCard({
  check,
  defaultOpen = false,
}: {
  check: CheckResult;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const s = STATUS[check.status];

  return (
    <div className="animate-slide-in">
      <button
        className="w-full text-left px-3 py-2.5 flex items-center gap-3 rounded-lg hover:bg-white/[0.03] transition-colors"
        onClick={() => setOpen(!open)}
      >
        <span className={`w-2 h-2 rounded-full shrink-0 ${s.dot}`} />
        <span className="text-sm text-gray-200 flex-1 min-w-0">{check.check}</span>
        <span className={`text-xs font-semibold tabular-nums shrink-0 ${s.text}`}>
          {check.points_earned}/{check.points_max}
        </span>
        <span className="text-gray-700 text-[10px] shrink-0">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div className="px-8 pb-3 pt-0.5 space-y-2">
          <p className="text-sm text-gray-300 leading-relaxed">{check.detail}</p>
          {check.status !== "pass" && check.action && (
            <p className="text-xs text-gray-500 leading-relaxed">
              <span className="text-gray-400 font-medium">Fix:</span> {check.action}
            </p>
          )}
          <div className="flex items-center gap-2 pt-0.5">
            <span className={`text-xs font-semibold ${EFFORT_COLOR[check.effort_level]}`}>
              {check.effort_level}
            </span>
            <span className="text-gray-700 text-xs">·</span>
            <span className="text-xs text-gray-500">{check.effort_time}</span>
          </div>
        </div>
      )}
    </div>
  );
}
