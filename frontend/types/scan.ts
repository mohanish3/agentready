export type CheckStatus = "pass" | "warning" | "fail";

export interface CheckResult {
  check: string;
  key: string;
  status: CheckStatus;
  points_earned: number;
  points_max: number;
  points_lost: number;
  detail: string;
  action: string;
  effort_level: "Easy" | "Medium" | "Hard";
  effort_time: string;
}

export interface SubpageCheck {
  pass: boolean | null;
  detail: string;
  action?: string;
}

export interface SubpageResult {
  url: string;
  pricing_parsability?: SubpageCheck;
  contact_parsability?: SubpageCheck;
  js_rendering?: SubpageCheck;
  structured_data?: SubpageCheck;
}

export interface ScanResult {
  url: string;
  score: number;
  checks: CheckResult[];
  recommendations: CheckResult[];
  subpages: Record<string, SubpageResult>;
}

export type ScanPhase = "idle" | "scanning" | "complete" | "error";
export type ComparePhase = "idle" | "loading" | "complete";
