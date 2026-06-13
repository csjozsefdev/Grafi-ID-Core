import { describe, expect, it } from "vitest";

import {
  formatSidebarSummaryPreview,
  sidebarSummaryPreviewText,
  stripSidebarSummaryLineLabel,
  summaryPreviewText,
} from "./continuity";

describe("sidebar summary preview formatting", () => {
  it("prefers the first human line and appends a short next step", () => {
    const raw = [
      "Where you left off: Continuing sidebar regression fix after doc update.",
      "Suggested next step: review changes in app/(tabs)/_layout.tsx",
      "Session still open (started today).",
    ].join("\n");

    expect(formatSidebarSummaryPreview(raw)).toBe(
      "Continuing sidebar regression fix after doc update. · Next: review changes in app/(tabs)/_layout.tsx"
    );
  });

  it("strips repeated label prefixes per line without changing stored summary text", () => {
    const stored = "Where you left off: recent edits in src/a.ts\nSuggested next step: review changes in src/a.ts";
    expect(stored).toContain("Where you left off:");
    expect(stripSidebarSummaryLineLabel("Suggested next step: polish admin UI")).toBe(
      "polish admin UI"
    );
  });

  it("does not rewrite backend summary preview text", () => {
    const project = {
      summary_preview: {
        headline: "sidebar regression fix",
        summary_text:
          "Where you left off: Continuing sidebar regression fix.\nSuggested next step: finish tests.",
      },
      latest_session: null,
    };

    expect(summaryPreviewText(project)).toContain("Where you left off:");
    expect(sidebarSummaryPreviewText(project)).toBe(
      "Continuing sidebar regression fix. · Next: finish tests."
    );
  });
});
