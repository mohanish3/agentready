export function selectNextStep(result) {
  const recs = [...(result.recommendations ?? [])].sort(
    (a, b) => (b.points_lost ?? 0) - (a.points_lost ?? 0)
  );

  if (recs.length === 0) {
    return {
      key: "complete",
      label: "No fixes left",
      detail: "Every check passed.",
      action: "Run another scan when the site changes.",
      pointsGain: 0,
      effort: "Done",
      cta: "Scan another page",
    };
  }

  const top = recs[0];
  return {
    key: top.key,
    label: top.check,
    detail: top.detail,
    action: top.action,
    pointsGain: top.points_lost ?? 0,
    effort: `${top.effort_level} - ${top.effort_time}`,
    source: top.research_source,
    confidence: top.confidence,
    cta: "Apply this fix first",
  };
}
