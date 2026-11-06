import type { ScanResult, ScanSummary } from "@/types/scan";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function scanUrl(url: string): Promise<ScanResult> {
  const res = await fetch(`${API}/api/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `Scan failed (${res.status})`);
  }
  return res.json();
}

export async function compareUrls(urls: string[]): Promise<ScanResult[]> {
  const res = await fetch(`${API}/api/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ urls }),
  });
  if (!res.ok) throw new Error(`Compare failed (${res.status})`);
  return res.json();
}

export async function downloadReport(
  result: ScanResult,
  type: "txt" | "pdf"
): Promise<void> {
  const res = await fetch(`${API}/api/report/${type}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(result),
  });
  if (!res.ok) throw new Error(`Report generation failed`);
  const blob = await res.blob();
  const blobUrl = URL.createObjectURL(blob);
  const safe = result.url.replace(/https?:\/\//, "").replace(/\//g, "_");
  const a = document.createElement("a");
  a.href = blobUrl;
  a.download = `agentready_${safe}.${type}`;
  a.click();
  URL.revokeObjectURL(blobUrl);
}

export async function downloadGeneratedFile(
  result: ScanResult,
  type: "llms-txt" | "json-ld"
): Promise<void> {
  const res = await fetch(`${API}/api/generate/${type}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(result),
  });
  if (!res.ok) throw new Error(`Generate failed (${res.status})`);
  const blob = await res.blob();
  const blobUrl = URL.createObjectURL(blob);
  const safe = result.url.replace(/https?:\/\//, "").replace(/\//g, "_");
  const ext = type === "llms-txt" ? "txt" : "json";
  const a = document.createElement("a");
  a.href = blobUrl;
  a.download = `${type === "llms-txt" ? "llms" : "schema"}_${safe}.${ext}`;
  a.click();
  URL.revokeObjectURL(blobUrl);
}

export function streamScan(
  url: string,
  onCheck: (check: object) => void,
  onComplete: (result: ScanResult) => void,
  onError: (msg: string) => void
): () => void {
  const encoded = encodeURIComponent(url);
  const es = new EventSource(`${API}/api/scan/stream?url=${encoded}`);

  es.onmessage = (e) => {
    if (e.data === "[DONE]") {
      es.close();
      return;
    }
    try {
      const data = JSON.parse(e.data);
      if (data.type === "check") onCheck(data);
      else if (data.type === "complete") { onComplete(data); es.close(); }
      else if (data.type === "error") { onError(data.error); es.close(); }
    } catch {
      // ignore parse errors
    }
  };

  es.onerror = () => {
    onError("Connection to scanner lost. Is the backend running?");
    es.close();
  };

  return () => es.close();
}

export async function listScans(limit = 50): Promise<ScanSummary[]> {
  const res = await fetch(`${API}/api/scans?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to load scan history');
  return res.json();
}

export async function getScanById(id: number): Promise<ScanResult> {
  const res = await fetch(`${API}/api/scans/${id}`);
  if (!res.ok) {
    if (res.status === 404) throw new Error('Scan not found');
    throw new Error('Failed to load scan');
  }
  return res.json();
}
