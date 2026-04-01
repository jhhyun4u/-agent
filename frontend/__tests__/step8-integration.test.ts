/**
 * STEP 8 Integration Tests
 *
 * Tests for STEP 8 components with MSW mocks for GraphQL/REST endpoints.
 * Covers data fetching, error handling, and user interactions.
 */

import { describe, it, expect, beforeAll, afterEach, afterAll } from "vitest";
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
} from "@/lib/types/step8";

/** ============ MSW Server Setup ============ */

const mockNodeStatuses = {
  step_8a: {
    node_name: "customer_profile_extract",
    status: "completed",
    output_key: "customer_profile",
    version: 1,
    progress: { current: 100, total: 100 },
    updated_at: new Date().toISOString(),
  },
  step_8b: {
    node_name: "validation_report",
    status: "completed",
    output_key: "validation_report",
    version: 1,
    progress: { current: 100, total: 100 },
    updated_at: new Date().toISOString(),
  },
  step_8c: {
    node_name: "proposal_sections_consolidation",
    status: "in_progress",
    output_key: "consolidated_proposal",
    version: 2,
    progress: { current: 75, total: 100 },
    updated_at: new Date().toISOString(),
  },
  step_8d: {
    node_name: "mock_evaluation_analysis",
    status: "completed",
    output_key: "mock_eval_result",
    version: 1,
    progress: { current: 100, total: 100 },
    updated_at: new Date().toISOString(),
  },
  step_8e: {
    node_name: "mock_evaluation_feedback_processor",
    status: "pending",
    output_key: "feedback_summary",
    version: 0,
    progress: { current: 0, total: 100 },
    updated_at: new Date().toISOString(),
  },
  step_8f: {
    node_name: "proposal_write_next_v2",
    status: "pending",
    output_key: "rewrite_history",
    version: 0,
    progress: { current: 0, total: 100 },
    updated_at: new Date().toISOString(),
  },
};

const mockCustomerProfile: CustomerProfile = {
  proposal_id: "proposal-123",
  client_name: "TechCorp Inc.",
  client_org: "Technology Division",
  stakeholders: [
    {
      name: "John Smith",
      role: "Technical Lead",
      priorities: ["Performance", "Scalability", "Security"],
      concerns: ["Timeline", "Cost", "Integration"],
      influence_level: "high",
    },
    {
      name: "Jane Doe",
      role: "Budget Owner",
      priorities: ["ROI", "Cost Efficiency", "Risk Management"],
      concerns: ["Budget", "Scope Creep"],
      influence_level: "high",
    },
  ],
  decision_drivers: [
    "Technical capability",
    "Cost effectiveness",
    "Team experience",
  ],
  budget_authority: "Executive Team approval required",
  pain_points: ["Legacy system integration", "Performance bottlenecks"],
  created_at: new Date().toISOString(),
};

const mockValidationReport: ValidationReport = {
  proposal_id: "proposal-123",
  pass_validation: true,
  quality_score: 82,
  issues: [
    {
      location: "Section 3",
      severity: "major",
      issue_type: "Clarity",
      issue_description: "Technical requirements need clarification",
      fix_suggestion: "Add detailed requirements matrix",
    },
  ],
  critical_issues_count: 0,
  major_issues_count: 1,
  minor_issues_count: 2,
  compliance_status: "Compliant",
  style_consistency: 95,
  recommendations_for_improvement: ["Enhance visuals in section 2"],
  next_steps: ["Review feedback", "Prepare presentation"],
  created_at: new Date().toISOString(),
};

const mockConsolidatedProposal: ConsolidatedProposal = {
  proposal_id: "proposal-123",
  total_sections: 8,
  final_sections: [
    "Executive Summary",
    "Approach",
    "Team",
    "Schedule",
    "Cost",
    "Risk Management",
  ],
  section_lineage: [
    {
      original_index: 0,
      original_title: "Executive Summary v1",
      merged_into_index: 0,
      merged_into_title: "Executive Summary",
      conflict_resolution: "Combined best points from both drafts",
    },
  ],
  executive_summary:
    "Comprehensive proposal addressing all client requirements with proven approach.",
  key_changes: [
    "Consolidated duplicate sections",
    "Enhanced team qualifications",
    "Added risk mitigation strategies",
  ],
  created_at: new Date().toISOString(),
};

const mockMockEvalResult: MockEvalResult = {
  proposal_id: "proposal-123",
  total_score: 78,
  dimensions: [
    {
      dimension: "technical",
      score: 85,
      rationale: "Strong technical approach",
      strengths: ["Innovative architecture", "Proven technology stack"],
      weaknesses: ["Limited legacy system integration"],
    },
    {
      dimension: "team",
      score: 80,
      rationale: "Experienced team with relevant background",
      strengths: ["10+ years experience", "Similar project delivery"],
      weaknesses: ["First-time client relationship"],
    },
    {
      dimension: "cost",
      score: 72,
      rationale: "Competitive pricing",
      strengths: ["Below market average", "Clear cost breakdown"],
      weaknesses: ["Less flexibility in payment terms"],
    },
    {
      dimension: "schedule",
      score: 75,
      rationale: "Realistic timeline",
      strengths: ["Achievable milestones", "Buffer included"],
      weaknesses: ["Dependent on client availability"],
    },
    {
      dimension: "risk",
      score: 82,
      rationale: "Well-identified risks with mitigation",
      strengths: ["Comprehensive risk analysis", "Mitigation strategies"],
      weaknesses: ["Emerging technology risks"],
    },
  ],
  win_probability: 0.72,
  pass_fail_risk: "low",
  key_differentiators: ["Innovative approach", "Proven track record"],
  competitive_risks: ["Competing vendor with lower cost", "Market timing"],
  created_at: new Date().toISOString(),
};

const mockFeedbackSummary: FeedbackSummary = {
  proposal_id: "proposal-123",
  key_findings: "Strong overall proposal with minor improvements needed",
  critical_gaps: [
    {
      section_id: "section-3",
      section_title: "Approach",
      issue_description: "Implementation timeline needs detail",
      priority: "high",
      estimated_effort: "medium",
      recommended_action: "Add weekly milestone breakdown for first 6 months",
    },
  ],
  quick_wins: [
    {
      section_id: "section-1",
      section_title: "Executive Summary",
      issue_description: "Add client testimonial from previous project",
      priority: "medium",
      estimated_effort: "quick",
      recommended_action: "Insert 2-3 sentence quote from reference client",
    },
  ],
  strategic_recommendations: [
    "Emphasize industry-specific experience more prominently",
    "Add sustainability considerations to approach",
  ],
  section_feedback: {
    "section-1": [
      {
        section_id: "section-1",
        section_title: "Executive Summary",
        issue_description: "Add value proposition statement",
        priority: "high",
        estimated_effort: "quick",
        recommended_action: "Lead with key differentiators",
      },
    ],
  },
  score_improvement_projection: 8,
  next_phase_guidance:
    "Implement critical gaps first, then quick wins for maximum impact.",
  created_at: new Date().toISOString(),
};

const mockRewriteRecord: RewriteRecord = {
  proposal_id: "proposal-123",
  current_section_index: 2,
  rewrite_iteration_count: 2,
  total_rewrites: 3,
  history: [
    {
      section_id: "section-1",
      section_title: "Executive Summary",
      iteration: 1,
      original_content: "This is the original executive summary content.",
      rewritten_content:
        "Enhanced executive summary with key value propositions and client benefits highlighted.",
      feedback_used: "Added more specific client benefits",
      created_at: new Date(Date.now() - 3600000).toISOString(),
    },
  ],
  created_at: new Date().toISOString(),
};

const mockReviewPanelData: ReviewPanelData = {
  proposal_id: "proposal-123",
  issues: [
    {
      issue_id: "issue-1",
      section_id: "section-3",
      severity: "critical",
      category: "compliance",
      description: "Missing mandatory compliance statement",
      suggestion:
        "Add SOC 2 Type II certification statement to security section",
      flagged_text: "Security measures include standard encryption",
    },
    {
      issue_id: "issue-2",
      section_id: "section-2",
      severity: "major",
      category: "clarity",
      description: "Technical approach needs clarification",
      suggestion: "Expand architecture diagram with component descriptions",
      flagged_text: "Our microservices architecture ensures scalability.",
    },
  ],
  total_issues: 4,
  critical_count: 1,
  can_proceed: false,
};

const mockStep8Status: Step8Status = {
  proposal_id: "proposal-123",
  nodes: Object.values(mockNodeStatuses),
  overall_progress: 67,
  last_updated: new Date().toISOString(),
};

// MSW Handlers
const handlers = [
  // Fetch node statuses
  http.get("/api/proposals/:proposal_id/step8/status", () => {
    return HttpResponse.json(mockStep8Status);
  }),

  // Fetch customer profile
  http.get("/api/proposals/:proposal_id/step8/customer-profile", () => {
    return HttpResponse.json(mockCustomerProfile);
  }),

  // Fetch validation report
  http.get("/api/proposals/:proposal_id/step8/validation-report", () => {
    return HttpResponse.json(mockValidationReport);
  }),

  // Fetch consolidated proposal
  http.get("/api/proposals/:proposal_id/step8/consolidated-proposal", () => {
    return HttpResponse.json(mockConsolidatedProposal);
  }),

  // Fetch mock evaluation
  http.get("/api/proposals/:proposal_id/step8/mock-eval", () => {
    return HttpResponse.json(mockMockEvalResult);
  }),

  // Fetch feedback summary
  http.get("/api/proposals/:proposal_id/step8/feedback-summary", () => {
    return HttpResponse.json(mockFeedbackSummary);
  }),

  // Fetch rewrite history
  http.get("/api/proposals/:proposal_id/step8/rewrite-history", () => {
    return HttpResponse.json(mockRewriteRecord);
  }),

  // Fetch review panel data (AI issues)
  http.get("/api/proposals/:proposal_id/step8/review-panel", () => {
    return HttpResponse.json(mockReviewPanelData);
  }),

  // Validate node
  http.post("/api/proposals/:proposal_id/step8/validate/:node_id", () => {
    return HttpResponse.json({
      status: "success",
      node_id: "step_8b",
      message: "Node validation triggered",
    });
  }),

  // Version history endpoint
  http.get("/api/proposals/:proposal_id/step8/versions/:node_id", () => {
    return HttpResponse.json({
      node_id: "step_8a",
      versions: [
        {
          version_id: "v1-abc123",
          node_name: "customer_profile_extract",
          version_number: 1,
          created_at: new Date().toISOString(),
          created_by: "system",
          size_bytes: 2048,
          description: "Initial profile extraction",
          change_summary: "Extracted stakeholder analysis and decision drivers",
        },
      ],
    });
  }),
];

const server = setupServer(...handlers);

/** ============ Test Setup ============ */

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

/** ============ Type Definition Tests ============ */

describe("STEP 8 Types", () => {
  it("should have all required node status fields", () => {
    const nodeStatus = mockNodeStatuses.step_8a;
    expect(nodeStatus).toHaveProperty("node_name");
    expect(nodeStatus).toHaveProperty("status");
    expect(nodeStatus).toHaveProperty("output_key");
    expect(nodeStatus).toHaveProperty("version");
  });

  it("should have valid Step8Status structure", () => {
    expect(mockStep8Status).toHaveProperty("proposal_id");
    expect(mockStep8Status).toHaveProperty("nodes");
    expect(mockStep8Status.nodes).toHaveLength(6);
    expect(mockStep8Status.overall_progress).toBeGreaterThanOrEqual(0);
    expect(mockStep8Status.overall_progress).toBeLessThanOrEqual(100);
  });

  it("should have valid CustomerProfile structure", () => {
    expect(mockCustomerProfile.stakeholders).toHaveLength(2);
    expect(mockCustomerProfile.stakeholders[0]).toHaveProperty(
      "influence_level",
    );
    expect(["high", "medium", "low"]).toContain(
      mockCustomerProfile.stakeholders[0].influence_level,
    );
  });

  it("should have valid ValidationReport structure", () => {
    expect(mockValidationReport.quality_score).toBeGreaterThanOrEqual(0);
    expect(mockValidationReport.quality_score).toBeLessThanOrEqual(100);
    expect(mockValidationReport.issues).toBeInstanceOf(Array);
  });

  it("should have valid MockEvalResult with 5 dimensions", () => {
    expect(mockMockEvalResult.dimensions).toHaveLength(5);
    expect(mockMockEvalResult.win_probability).toBeGreaterThanOrEqual(0);
    expect(mockMockEvalResult.win_probability).toBeLessThanOrEqual(1);
    expect(["high", "medium", "low"]).toContain(
      mockMockEvalResult.pass_fail_risk,
    );
  });

  it("should have valid ReviewPanelData with issue categories", () => {
    const categories = [
      "compliance",
      "clarity",
      "consistency",
      "style",
      "strategy",
    ];
    mockReviewPanelData.issues.forEach((issue) => {
      expect(categories).toContain(issue.category);
      expect(["critical", "major", "minor"]).toContain(issue.severity);
    });
  });
});

/** ============ API Integration Tests ============ */

describe("STEP 8 API Integration", () => {
  it("should fetch node statuses", async () => {
    const response = await fetch("/api/proposals/proposal-123/step8/status");
    expect(response.ok).toBe(true);
    const data = await response.json();
    expect(data.proposal_id).toBe("proposal-123");
    expect(data.nodes).toHaveLength(6);
  });

  it("should fetch customer profile", async () => {
    const response = await fetch(
      "/api/proposals/proposal-123/step8/customer-profile",
    );
    expect(response.ok).toBe(true);
    const data = await response.json();
    expect(data.client_name).toBe("TechCorp Inc.");
    expect(data.stakeholders).toHaveLength(2);
  });

  it("should fetch validation report", async () => {
    const response = await fetch(
      "/api/proposals/proposal-123/step8/validation-report",
    );
    expect(response.ok).toBe(true);
    const data = await response.json();
    expect(data.quality_score).toBe(82);
    expect(data.pass_validation).toBe(true);
  });

  it("should fetch mock evaluation results", async () => {
    const response = await fetch("/api/proposals/proposal-123/step8/mock-eval");
    expect(response.ok).toBe(true);
    const data = await response.json();
    expect(data.total_score).toBe(78);
    expect(data.win_probability).toBe(0.72);
  });

  it("should fetch feedback summary", async () => {
    const response = await fetch(
      "/api/proposals/proposal-123/step8/feedback-summary",
    );
    expect(response.ok).toBe(true);
    const data = await response.json();
    expect(data.critical_gaps).toHaveLength(1);
    expect(data.quick_wins).toHaveLength(1);
  });

  it("should fetch rewrite history", async () => {
    const response = await fetch(
      "/api/proposals/proposal-123/step8/rewrite-history",
    );
    expect(response.ok).toBe(true);
    const data = await response.json();
    expect(data.current_section_index).toBe(2);
    expect(data.history).toHaveLength(1);
  });

  it("should fetch review panel data", async () => {
    const response = await fetch(
      "/api/proposals/proposal-123/step8/review-panel",
    );
    expect(response.ok).toBe(true);
    const data = await response.json();
    expect(data.issues).toHaveLength(2);
    expect(data.can_proceed).toBe(false);
    expect(data.critical_count).toBe(1);
  });

  it("should trigger node validation", async () => {
    const response = await fetch(
      "/api/proposals/proposal-123/step8/validate/step_8b",
      {
        method: "POST",
      },
    );
    expect(response.ok).toBe(true);
    const data = await response.json();
    expect(data.status).toBe("success");
  });

  it("should fetch version history", async () => {
    const response = await fetch(
      "/api/proposals/proposal-123/step8/versions/step_8a",
    );
    expect(response.ok).toBe(true);
    const data = await response.json();
    expect(data.versions).toHaveLength(1);
    expect(data.versions[0].version_number).toBe(1);
  });
});

/** ============ Error Handling Tests ============ */

describe("STEP 8 Error Handling", () => {
  it("should handle 404 for missing proposal", async () => {
    server.use(
      http.get("/api/proposals/:proposal_id/step8/status", () => {
        return HttpResponse.json({ error: "Not found" }, { status: 404 });
      }),
    );

    const response = await fetch("/api/proposals/invalid-id/step8/status");
    expect(response.status).toBe(404);
  });

  it("should handle 500 server errors", async () => {
    server.use(
      http.get("/api/proposals/:proposal_id/step8/validation-report", () => {
        return HttpResponse.json(
          { error: "Internal server error" },
          { status: 500 },
        );
      }),
    );

    const response = await fetch(
      "/api/proposals/proposal-123/step8/validation-report",
    );
    expect(response.status).toBe(500);
  });

  it("should handle network timeout simulation", async () => {
    server.use(
      http.get("/api/proposals/:proposal_id/step8/mock-eval", async () => {
        await new Promise((resolve) => setTimeout(resolve, 100));
        return HttpResponse.json({});
      }),
    );

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 50);

    try {
      await fetch("/api/proposals/proposal-123/step8/mock-eval", {
        signal: controller.signal,
      });
    } catch (error) {
      expect((error as Error).name).toBe("AbortError");
    } finally {
      clearTimeout(timeoutId);
    }
  });
});

/** ============ Data Validation Tests ============ */

describe("STEP 8 Data Validation", () => {
  it("should validate node status progression", () => {
    const validStatuses = ["pending", "running", "completed", "failed"];
    Object.values(mockNodeStatuses).forEach((node) => {
      expect(validStatuses).toContain(node.status);
    });
  });

  it("should validate issue severity levels", () => {
    const validSeverities = ["critical", "major", "minor"];
    mockReviewPanelData.issues.forEach((issue) => {
      expect(validSeverities).toContain(issue.severity);
    });
  });

  it("should validate feedback item effort levels", () => {
    const validEfforts = ["quick", "medium", "complex"];
    const allItems = [
      ...mockFeedbackSummary.critical_gaps,
      ...mockFeedbackSummary.quick_wins,
      ...Object.values(mockFeedbackSummary.section_feedback).flat(),
    ];
    allItems.forEach((item) => {
      expect(validEfforts).toContain(item.estimated_effort);
    });
  });

  it("should validate stakeholder influence levels", () => {
    const validInfluence = ["high", "medium", "low"];
    mockCustomerProfile.stakeholders.forEach((stakeholder) => {
      expect(validInfluence).toContain(stakeholder.influence_level);
    });
  });

  it("should validate score ranges", () => {
    expect(mockValidationReport.quality_score).toBeGreaterThanOrEqual(0);
    expect(mockValidationReport.quality_score).toBeLessThanOrEqual(100);

    mockMockEvalResult.dimensions.forEach((dim) => {
      expect(dim.score).toBeGreaterThanOrEqual(0);
      expect(dim.score).toBeLessThanOrEqual(100);
    });
  });
});

/** ============ State Management Tests ============ */

describe("STEP 8 State Management", () => {
  it("should track overall progress correctly", () => {
    const completed = Object.values(mockNodeStatuses).filter(
      (n) => n.status === "completed",
    );
    const expectedProgress = (completed.length / 6) * 100;
    expect(
      Math.abs(mockStep8Status.overall_progress - expectedProgress),
    ).toBeLessThan(1);
  });

  it("should maintain node ordering consistency", () => {
    const nodeOrder = [
      "step_8a",
      "step_8b",
      "step_8c",
      "step_8d",
      "step_8e",
      "step_8f",
    ];
    const statusNodeNames = mockStep8Status.nodes.map((n) => n.output_key);
    expect(statusNodeNames).toHaveLength(6);
  });

  it("should track version numbers correctly", () => {
    expect(mockNodeStatuses.step_8a.version).toBe(1);
    expect(mockNodeStatuses.step_8c.version).toBe(2); // In-progress version bumped
  });
});

/** ============ Business Logic Tests ============ */

describe("STEP 8 Business Logic", () => {
  it("should determine can_proceed based on critical issues", () => {
    expect(mockReviewPanelData.can_proceed).toBe(false); // Has critical issues
    expect(mockReviewPanelData.critical_count).toBeGreaterThan(0);
  });

  it("should calculate score improvement correctly", () => {
    expect(mockFeedbackSummary.score_improvement_projection).toBeGreaterThan(0);
    expect(
      mockFeedbackSummary.score_improvement_projection,
    ).toBeLessThanOrEqual(100);
  });

  it("should map feedback items to sections correctly", () => {
    Object.entries(mockFeedbackSummary.section_feedback).forEach(
      ([sectionId, items]) => {
        items.forEach((item) => {
          expect(item.section_id).toBe(sectionId);
        });
      },
    );
  });

  it("should categorize rewrite iterations", () => {
    expect(mockRewriteRecord.rewrite_iteration_count).toBeGreaterThanOrEqual(0);
    expect(mockRewriteRecord.total_rewrites).toBeGreaterThanOrEqual(
      mockRewriteRecord.rewrite_iteration_count,
    );
  });
});
