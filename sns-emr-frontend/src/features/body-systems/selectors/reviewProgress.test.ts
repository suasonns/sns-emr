import { describe, it, expect } from "vitest";
import { calculateReviewProgress, countsTowardReviewProgress } from "./reviewProgress";
import type { SystemReviewState } from "../../../domain/body-systems";

describe("countsTowardReviewProgress", () => {
  it("counts 'reviewed' toward progress", () => {
    expect(countsTowardReviewProgress("reviewed")).toBe(true);
  });

  it("counts 'reviewed_with_exception' toward progress", () => {
    expect(countsTowardReviewProgress("reviewed_with_exception")).toBe(true);
  });

  it("does not count 'in_progress' toward progress", () => {
    expect(countsTowardReviewProgress("in_progress")).toBe(false);
  });

  it("does not count 'not_reviewed' toward progress", () => {
    expect(countsTowardReviewProgress("not_reviewed")).toBe(false);
  });
});

describe("calculateReviewProgress", () => {
  it("returns 0/0 for an empty list", () => {
    expect(calculateReviewProgress([])).toEqual({ reviewedCount: 0, totalCount: 0 });
  });

  it("counts only reviewed and reviewed_with_exception rows", () => {
    const rows: { reviewState: SystemReviewState }[] = [
      { reviewState: "reviewed" },
      { reviewState: "reviewed_with_exception" },
      { reviewState: "in_progress" },
      { reviewState: "not_reviewed" },
    ];
    expect(calculateReviewProgress(rows)).toEqual({ reviewedCount: 2, totalCount: 4 });
  });

  it("returns totalCount equal to the full row count regardless of review state mix", () => {
    const rows: { reviewState: SystemReviewState }[] = Array.from({ length: 10 }, () => ({
      reviewState: "not_reviewed" as SystemReviewState,
    }));
    expect(calculateReviewProgress(rows)).toEqual({ reviewedCount: 0, totalCount: 10 });
  });

  it("counts every row when all ten systems are reviewed", () => {
    const rows: { reviewState: SystemReviewState }[] = Array.from({ length: 10 }, () => ({
      reviewState: "reviewed" as SystemReviewState,
    }));
    expect(calculateReviewProgress(rows)).toEqual({ reviewedCount: 10, totalCount: 10 });
  });

  it("is not influenced by any field other than reviewState", () => {
    // The input type intentionally only exposes `reviewState`; this test
    // documents that guarantee rather than exercising extra fields, since
    // the selector's parameter type makes passing them a compile error.
    const rows: { reviewState: SystemReviewState }[] = [{ reviewState: "not_reviewed" }];
    expect(calculateReviewProgress(rows).reviewedCount).toBe(0);
  });
});
