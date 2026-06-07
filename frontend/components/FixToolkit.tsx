"use client";
import { useState } from "react";
import type { ScanResult } from "@/types/scan";

function CopyBlock({ title, code }: { title: string; code: string }) {
  const [copied, setCopied] = useState(false);

  const copy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs font-semibold text-gray-400">{title}</p>
        <button
          onClick={copy}
          className="text-xs text-gray-600 hover:text-blue-400 transition-colors"
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <pre className="text-xs text-gray-300 bg-white/[0.03] border border-white/[0.06] rounded-lg p-4 overflow-x-auto leading-relaxed whitespace-pre-wrap">
        {code}
      </pre>
    </div>
  );
}

export default function FixToolkit({ result }: { result: ScanResult }) {
  const [open, setOpen] = useState(false);

  const hasLlms = !!result.llms_txt_template;
  const hasJsonLd = !!result.json_ld_snippet;

  if (!hasLlms && !hasJsonLd) return null;

  const jsonLdFull = result.json_ld_snippet
    ? `<script type="application/ld+json">\n${result.json_ld_snippet}\n</script>`
    : null;

  return (
    <section>
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-gray-500 hover:text-gray-300 transition-colors mb-4"
      >
        <span>Fix Toolkit</span>
        <span className="font-normal normal-case tracking-normal text-xs text-gray-700">
          - copy-paste ready fixes
        </span>
        <span className="text-[8px] text-gray-700">{open ? "^" : "v"}</span>
      </button>

      {open && (
        <div className="space-y-6 animate-fade-in">
          {hasLlms && (
            <CopyBlock
              title="llms.txt template - save as /llms.txt at your domain root"
              code={result.llms_txt_template!}
            />
          )}
          {hasJsonLd && (
            <CopyBlock
              title="JSON-LD starter - paste into your <head> tag"
              code={jsonLdFull!}
            />
          )}
        </div>
      )}
    </section>
  );
}
