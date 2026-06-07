import assert from "node:assert/strict";
import test from "node:test";

import { selectNextStep } from "../lib/nextStep.js";

test("selectNextStep chooses highest points_lost recommendation", () => {
  const result = {
    recommendations: [
      {
        key: "contact_parsability",
        check: "Contact Info Parsability",
        status: "fail",
        points_lost: 10,
        action: "Add plaintext email.",
        effort_level: "Easy",
        effort_time: "30 min",
      },
      {
        key: "structured_data",
        check: "Structured Data",
        status: "warning",
        points_lost: 20,
        action: "Add Product JSON-LD.",
        effort_level: "Medium",
        effort_time: "2-4 hours",
      },
    ],
  };

  const next = selectNextStep(result);

  assert.equal(next.key, "structured_data");
  assert.equal(next.pointsGain, 20);
  assert.equal(next.label, "Structured Data");
  assert.equal(next.cta, "Apply this fix first");
});

test("selectNextStep returns complete state when no recommendations remain", () => {
  const next = selectNextStep({ recommendations: [] });

  assert.equal(next.key, "complete");
  assert.equal(next.label, "No fixes left");
  assert.equal(next.pointsGain, 0);
});
