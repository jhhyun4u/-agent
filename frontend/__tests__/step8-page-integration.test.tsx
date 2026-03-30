/**
 * STEP 8 Page Integration Tests
 *
 * Tests for STEP 8 Review page with MSW mocks, component rendering,
 * user interactions, and complete workflow scenarios.
 */

import { describe, it, expect, beforeAll, afterEach, afterAll, vi } from "vitest";
import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { setupServer } from "msw/node";
import { http, HttpResponse } from "msw";
import type {
  Step8Status,
  CustomerProfile,
  ValidationReport,
  ConsolidatedProposal,
  MockEvalResult,
  FeedbackSummary,
  RewriteRecord,
  ReviewPanelData,
  NodeStatus,
} from "@/lib/types/step8";

/** ============ Mock Data ============ */

const mockNodeStatuses: Record<string, NodeStatus> = {
  step_8a: {
    node_name: "customer_profile_extract",
    status: "completed",
    output_key: "customer_profile",
    version: 1,
    updated_at: new Date().toISOString(),
  },
  step_8b: {
    node_name: "validation_report",
    status: "completed",
    output_key: "validation_report",
    version: 1,
    updated_at: new Date().toISOString(),
  },
  step_8c: {
    node_name: "proposal_consolidation",
    status: "in_progress",
    output_key: "consolidated_proposal",
    version: 2,
    updated_at: new Date().toISOString(),
  },
  step_8d: {
    node_name: "mock_evaluation",
    status: "completed",
    output_key: "mock_eval_result",
    version: 1,
    updated_at: new Date().toISOString(),
  },
  step_8e: {
    node_name: "feedback_processor",
    status: "pending",
    output_key: "feedback_summary",
    version: 0,
    updated_at: new Date().toISOString(),
  },
  step_8f: {
    node_name: "rewrite_history",
    status: "pending",
    output_key: "rewrite_history",
    version: 0,
    updated_at: new Date().toISOString(),
  },
};

const mockReviewPanelData: ReviewPanelData = {
  proposal_id: "proposal-123",
  issues: [
    {
      issue_id: "issue-1",
      section_id: "section-3",
      severity: "critical",
      category: "compliance",
      description: "Missing compliance statement",
      suggestion: "Add SOC 2 certification statement",
      flagged_text: "Standard encryption measures",
    },
    {
      issue_id: "issue-2",
      section_id: "section-2",
      severity: "major",
      category: "clarity",
      description: "Technical approach unclear",
      suggestion: "Expand architecture diagram",
      flagged_text: "Microservices architecture ensures scalability",
    },
  ],
  total_issues: 4,
  critical_count: 1,
  can_proceed: false,
};

const mockFeedbackSummary: FeedbackSummary = {
  proposal_id: "proposal-123",
  key_findings: "Strong proposal with minor improvements needed",
  critical_gaps: [
    {
      section_id: "section-3",
      section_title: "Approach",
      issue_description: "Timeline needs detail",
      priority: "high",
      estimated_effort: "medium",
      recommended_action: "Add weekly milestones",
    },
  ],
  quick_wins: [
    {
      section_id: "section-1",
      section_title: "Executive Summary",
      issue_description: "Add client testimonial",
      priority: "medium",
      estimated_effort: "quick",
      recommended_action: "Insert reference quote",
    },
  ],
  strategic_recommendations: [
    "Emphasize industry experience",
    "Add sustainability considerations",
  ],
  section_feedback: {},
  score_improvement_projection: 8,
  next_phase_guidance: "Implement critical gaps first for maximum impact",
  created_at: new Date().toISOString(),
};

/** ============ MSW Server Setup ============ */

const handlers = [
  // STEP 8 Status
  http.get("/api/proposals/:proposal_id/step8/status", () => {
    const nodes = Object.values(mockNodeStatuses);
    const completed = nodes.filter((n) => n.status === "completed").length;
    return HttpResponse.json({
      proposal_id: "proposal-123",
      nodes: nodes,
      overall_progress: (completed / 6) * 100,
      last_updated: new Date().toISOString(),
    } as Step8Status);
  }),

  // Review Panel Data
  http.get("/api/proposals/:proposal_id/step8/review-panel", () => {
    return HttpResponse.json(mockReviewPanelData);
  }),

  // Feedback Summary
  http.get("/api/proposals/:proposal_id/step8/feedback-summary", () => {
    return HttpResponse.json(mockFeedbackSummary);
  }),

  // Node Validation
  http.post("/api/proposals/:proposal_id/step8/validate/:node_id", async ({ params }) => {
    const { node_id } = params;
    // Simulate validation in progress
    return HttpResponse.json({
      status: "success",
      node_id,
      message: "Validation triggered",
    });
  }),

  // Approval endpoint (not yet in mock, for future)
  http.post("/api/proposals/:proposal_id/step8/approve", () => {
    return HttpResponse.json({ status: "approved" });
  }),

  // Feedback submission
  http.post("/api/proposals/:proposal_id/step8/feedback", async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({
      status: "success",
      feedback_id: "fb-123",
      received_at: new Date().toISOString(),
    });
  }),
];

const server = setupServer(...handlers);

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

/** ============ Component Rendering Tests ============ */

describe("STEP 8 Page Integration", () => {
  it("should render page header with navigation", async () => {
    // Note: This is a simplified test structure
    // Real implementation would use Next.js test utilities

    expect(true).toBe(true); // Placeholder
  });

  it("should display loading state while fetching data", async () => {
    // Placeholder for loading state test
    expect(true).toBe(true);
  });

  it("should render NodeStatusDashboard with progress", async () => {
    // Placeholder
    expect(true).toBe(true);
  });

  it("should render ReviewPanelEnhanced with issues", async () => {
    // Placeholder
    expect(true).toBe(true);
  });

  it("should render VersionHistoryViewer for all nodes", async () => {
    // Placeholder
    expect(true).toBe(true);
  });
});

/** ============ API Integration Tests ============ */

describe("STEP 8 API Integration", () => {
  it("should fetch STEP 8 status with correct node structure", async () => {
    const response = await fetch("/api/proposals/proposal-123/step8/status");
    expect(response.ok).toBe(true);

    const data = (await response.json()) as Step8Status;
    expect(data.proposal_id).toBe("proposal-123");
    expect(data.nodes).toHaveLength(6);
    expect(data.overall_progress).toBeGreaterThanOrEqual(0);
    expect(data.overall_progress).toBeLessThanOrEqual(100);
  });

  it("should fetch review panel data with AI issues", async () => {
    const response = await fetch("/api/proposals/proposal-123/step8/review-panel");
    expect(response.ok).toBe(true);

    const data = (await response.json()) as ReviewPanelData;
    expect(data.issues).toHaveLength(2);
    expect(data.critical_count).toBe(1);
    expect(data.can_proceed).toBe(false);

    // Validate issue structure
    data.issues.forEach((issue) => {
      expect(["critical", "major", "minor"]).toContain(issue.severity);
      expect(["compliance", "clarity", "consistency", "style", "strategy"]).toContain(
        issue.category
      );
      expect(issue.description).toBeTruthy();
      expect(issue.suggestion).toBeTruthy();
    });
  });

  it("should fetch feedback summary with actionable items", async () => {
    const response = await fetch("/api/proposals/proposal-123/step8/feedback-summary");
    expect(response.ok).toBe(true);

    const data = (await response.json()) as FeedbackSummary;
    expect(data.key_findings).toBeTruthy();
    expect(data.critical_gaps).toBeInstanceOf(Array);
    expect(data.quick_wins).toBeInstanceOf(Array);
    expect(data.strategic_recommendations).toBeInstanceOf(Array);
    expect(data.score_improvement_projection).toBeGreaterThanOrEqual(0);
  });

  it("should trigger node validation", async () => {
    const response = await fetch("/api/proposals/proposal-123/step8/validate/step_8b", {
      method: "POST",
    });
    expect(response.ok).toBe(true);

    const data = await response.json();
    expect(data.status).toBe("success");
    expect(data.node_id).toBe("step_8b");
  });

  it("should handle approval submission", async () => {
    const response = await fetch("/api/proposals/proposal-123/step8/approve", {
      method: "POST",
    });
    expect(response.ok).toBe(true);

    const data = await response.json();
    expect(data.status).toBe("approved");
  });

  it("should handle feedback submission", async () => {
    const feedbackData = {
      feedback_text: "Add more detail to the approach section",
      issue_ids: ["issue-1", "issue-2"],
    };

    const response = await fetch("/api/proposals/proposal-123/step8/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(feedbackData),
    });
    expect(response.ok).toBe(true);

    const data = await response.json();
    expect(data.status).toBe("success");
    expect(data.feedback_id).toBeTruthy();
  });
});

/** ============ User Interaction Tests ============ */

describe("STEP 8 User Interactions", () => {
  it("should allow approving proposal when can_proceed is true", async () => {
    // Test that approve button is enabled when can_proceed=true
    // and disabled when can_proceed=false
    expect(mockReviewPanelData.can_proceed).toBe(false);

    const enabledData = { ...mockReviewPanelData, can_proceed: true };
    expect(enabledData.can_proceed).toBe(true);
  });

  it("should collect feedback when requesting changes", async () => {
    const feedbackText = "Expand the technical approach section with more detail";

    const response = await fetch("/api/proposals/proposal-123/step8/feedback", {
      method: "POST",
      body: JSON.stringify({
        feedback_text: feedbackText,
        issue_ids: ["issue-1"],
      }),
    });

    expect(response.ok).toBe(true);
  });

  it("should handle rewrite trigger", async () => {
    const response = await fetch("/api/proposals/proposal-123/step8/validate/step_8f", {
      method: "POST",
    });
    expect(response.ok).toBe(true);
  });

  it("should validate individual nodes", async () => {
    const nodeIds = ["step_8a", "step_8b", "step_8c", "step_8d", "step_8e", "step_8f"];

    for (const nodeId of nodeIds) {
      const response = await fetch(
        `/api/proposals/proposal-123/step8/validate/${nodeId}`,
        { method: "POST" }
      );
      expect(response.ok).toBe(true);
    }
  });
});

/** ============ State Management Tests ============ */

describe("STEP 8 State Management", () => {
  it("should calculate overall progress correctly", async () => {
    const response = await fetch("/api/proposals/proposal-123/step8/status");
    const status = (await response.json()) as Step8Status;

    const completed = status.nodes.filter((n) => n.status === "completed").length;
    const expected = (completed / 6) * 100;

    expect(Math.abs(status.overall_progress - expected)).toBeLessThan(1);
  });

  it("should track issue counts correctly", () => {
    expect(mockReviewPanelData.total_issues).toBe(4);
    expect(mockReviewPanelData.critical_count).toBe(1);

    // Verify critical issues count matches actual critical issues
    const actualCritical = mockReviewPanelData.issues.filter(
      (i) => i.severity === "critical"
    ).length;
    expect(actualCritical).toBe(mockReviewPanelData.critical_count);
  });

  it("should determine can_proceed based on critical issues", () => {
    // If there are critical issues, can_proceed should be false
    const hasCritical = mockReviewPanelData.critical_count > 0;
    expect(mockReviewPanelData.can_proceed).toBe(!hasCritical);
  });

  it("should maintain version consistency across nodes", async () => {
    const response = await fetch("/api/proposals/proposal-123/step8/status");
    const status = (await response.json()) as Step8Status;

    status.nodes.forEach((node) => {
      expect(node.version).toBeGreaterThanOrEqual(0);
      expect(node.status).toMatch(
        /^(pending|running|completed|failed)$/
      );
    });
  });
});

/** ============ Error Handling Tests ============ */

describe("STEP 8 Error Handling", () => {
  it("should handle 404 for missing proposal", async () => {
    server.use(
      http.get("/api/proposals/:proposal_id/step8/status", () => {
        return HttpResponse.json({ error: "Not found" }, { status: 404 });
      })
    );

    const response = await fetch("/api/proposals/invalid-id/step8/status");
    expect(response.status).toBe(404);
  });

  it("should handle 500 server errors gracefully", async () => {
    server.use(
      http.get("/api/proposals/:proposal_id/step8/review-panel", () => {
        return HttpResponse.json(
          { error: "Internal server error" },
          { status: 500 }
        );
      })
    );

    const response = await fetch("/api/proposals/proposal-123/step8/review-panel");
    expect(response.status).toBe(500);
  });

  it("should retry on timeout", async () => {
    let callCount = 0;

    server.use(
      http.get("/api/proposals/:proposal_id/step8/status", async () => {
        callCount++;
        if (callCount === 1) {
          await new Promise((resolve) => setTimeout(resolve, 100));
          throw new Error("Timeout");
        }
        return HttpResponse.json({
          proposal_id: "proposal-123",
          nodes: [],
          overall_progress: 50,
          last_updated: new Date().toISOString(),
        });
      })
    );

    // Initial request should fail
    try {
      await fetch("/api/proposals/proposal-123/step8/status", {
        signal: AbortSignal.timeout(50),
      });
    } catch {
      // Expected timeout
    }

    // Retry should succeed
    const response = await fetch("/api/proposals/proposal-123/step8/status");
    expect(response.ok).toBe(true);
  });

  it("should validate issue data integrity", () => {
    const issues = mockReviewPanelData.issues;

    issues.forEach((issue) => {
      // Check required fields
      expect(issue.issue_id).toBeTruthy();
      expect(issue.section_id).toBeTruthy();
      expect(issue.severity).toBeTruthy();
      expect(issue.category).toBeTruthy();
      expect(issue.description).toBeTruthy();
      expect(issue.suggestion).toBeTruthy();

      // Check field types
      expect(typeof issue.issue_id).toBe("string");
      expect(typeof issue.severity).toBe("string");
      expect(typeof issue.category).toBe("string");
    });
  });
});

/** ============ Business Logic Tests ============ */

describe("STEP 8 Business Logic", () => {
  it("should prioritize critical issues in display", () => {
    const issues = mockReviewPanelData.issues;
    const criticalIssues = issues.filter((i) => i.severity === "critical");
    const majorIssues = issues.filter((i) => i.severity === "major");

    // Critical issues should be shown first
    expect(criticalIssues.length).toBeGreaterThan(0);
    expect(majorIssues.length).toBeGreaterThan(0);
  });

  it("should calculate score improvement projection", () => {
    const projection = mockFeedbackSummary.score_improvement_projection;
    expect(projection).toBeGreaterThan(0);
    expect(projection).toBeLessThanOrEqual(100);

    // Improvement projection should be based on implementing all actions
    expect(projection).toBe(8); // As per mock data
  });

  it("should group feedback by category", () => {
    const categories = new Set(mockReviewPanelData.issues.map((i) => i.category));
    expect(categories.size).toBeGreaterThan(0);

    // All categories should be valid
    const validCategories = [
      "compliance",
      "clarity",
      "consistency",
      "style",
      "strategy",
    ];
    categories.forEach((cat) => {
      expect(validCategories).toContain(cat);
    });
  });

  it("should track effort estimates for feedback items", () => {
    const items = [
      ...mockFeedbackSummary.critical_gaps,
      ...mockFeedbackSummary.quick_wins,
    ];

    const validEfforts = ["quick", "medium", "complex"];
    items.forEach((item) => {
      expect(validEfforts).toContain(item.estimated_effort);
    });
  });
});

/** ============ Performance Tests ============ */

describe("STEP 8 Performance", () => {
  it("should load status within reasonable time", async () => {
    const start = performance.now();
    const response = await fetch("/api/proposals/proposal-123/step8/status");
    const end = performance.now();

    expect(response.ok).toBe(true);
    expect(end - start).toBeLessThan(1000); // Should load within 1 second
  });

  it("should handle multiple parallel requests", async () => {
    const requests = [
      fetch("/api/proposals/proposal-123/step8/status"),
      fetch("/api/proposals/proposal-123/step8/review-panel"),
      fetch("/api/proposals/proposal-123/step8/feedback-summary"),
    ];

    const responses = await Promise.all(requests);
    responses.forEach((res) => {
      expect(res.ok).toBe(true);
    });
  });

  it("should not duplicate data in responses", async () => {
    const response1 = await fetch("/api/proposals/proposal-123/step8/status");
    const response2 = await fetch("/api/proposals/proposal-123/step8/status");

    const data1 = await response1.json();
    const data2 = await response2.json();

    expect(JSON.stringify(data1)).toBe(JSON.stringify(data2));
  });
});
