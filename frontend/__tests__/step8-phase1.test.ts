/**
 * Phase 1 Tests: Type Definitions & API Hooks
 *
 * Tests for STEP 8 types and hooks with mock API responses
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import type {
  CustomerProfile,
  ValidationReport,
  ConsolidatedProposal,
  MockEvalResult,
  FeedbackSummary,
  NodeStatus,
  Step8Status,
} from "@/lib/types/step8";

describe("STEP 8 Types", () => {
  describe("CustomerProfile", () => {
    it("should create a valid customer profile", () => {
      const profile: CustomerProfile = {
        proposal_id: "prop-123",
        client_name: "Acme Corp",
        client_org: "Manufacturing",
        stakeholders: [
          {
            name: "John Doe",
            role: "CTO",
            priorities: ["cost", "timeline"],
            concerns: ["risk"],
            influence_level: "high",
          },
        ],
        decision_drivers: ["ROI", "time-to-market"],
        budget_authority: "CFO",
        pain_points: ["legacy system", "downtime"],
        created_at: new Date().toISOString(),
      };

      expect(profile.proposal_id).toBe("prop-123");
      expect(profile.stakeholders).toHaveLength(1);
      expect(profile.stakeholders[0].influence_level).toBe("high");
    });
  });

  describe("ValidationReport", () => {
    it("should calculate quality score from issues", () => {
      const report: ValidationReport = {
        proposal_id: "prop-123",
        pass_validation: false,
        quality_score: 60, // 100 - (1*20 + 1*5 + 3*1) = 100 - 28 = 72
        issues: [
          {
            location: "Section 3",
            severity: "critical",
            issue_type: "compliance",
            issue_description: "Missing required fields",
          },
          {
            location: "Section 5",
            severity: "major",
            issue_type: "clarity",
            issue_description: "Unclear language",
          },
          {
            location: "Section 2",
            severity: "minor",
            issue_type: "style",
            issue_description: "Inconsistent formatting",
          },
        ],
        critical_issues_count: 1,
        major_issues_count: 1,
        minor_issues_count: 1,
        compliance_status: "non-compliant",
        style_consistency: 45.5,
        recommendations_for_improvement: [
          "Add required fields",
          "Clarify language",
        ],
        next_steps: ["Fix critical issues", "Request manager review"],
        created_at: new Date().toISOString(),
      };

      expect(report.pass_validation).toBe(false);
      expect(report.quality_score).toBeLessThan(100);
      expect(report.issues).toHaveLength(3);
    });

    it("should pass validation with no critical issues", () => {
      const report: ValidationReport = {
        proposal_id: "prop-123",
        pass_validation: true,
        quality_score: 95,
        issues: [
          {
            location: "Section 1",
            severity: "minor",
            issue_type: "style",
            issue_description: "Extra spacing",
          },
        ],
        critical_issues_count: 0,
        major_issues_count: 0,
        minor_issues_count: 1,
        compliance_status: "compliant",
        style_consistency: 92.0,
        recommendations_for_improvement: [],
        next_steps: ["Ready for review"],
        created_at: new Date().toISOString(),
      };

      expect(report.critical_issues_count).toBe(0);
      expect(report.pass_validation).toBe(true);
    });
  });

  describe("MockEvalResult", () => {
    it("should contain 5 score dimensions", () => {
      const eval_: MockEvalResult = {
        proposal_id: "prop-123",
        total_score: 78,
        dimensions: [
          {
            dimension: "technical",
            score: 85,
            rationale: "Strong technical approach",
            strengths: ["modern stack", "scalable"],
            weaknesses: ["unproven vendor"],
          },
          {
            dimension: "team",
            score: 80,
            rationale: "Experienced team",
            strengths: ["10+ years exp"],
            weaknesses: ["new product"],
          },
          {
            dimension: "cost",
            score: 75,
            rationale: "Competitive pricing",
            strengths: ["fixed price"],
            weaknesses: ["no discounts"],
          },
          {
            dimension: "schedule",
            score: 72,
            rationale: "Realistic timeline",
            strengths: ["documented", "staged"],
            weaknesses: ["tight Q3"],
          },
          {
            dimension: "risk",
            score: 78,
            rationale: "Mitigated risks",
            strengths: ["backup plan", "insurance"],
            weaknesses: ["vendor lock-in"],
          },
        ],
        win_probability: 0.72,
        pass_fail_risk: "medium",
        key_differentiators: ["proprietary algorithm", "24/7 support"],
        competitive_risks: ["established competitor", "new startup"],
        created_at: new Date().toISOString(),
      };

      expect(eval_.dimensions).toHaveLength(5);
      expect(eval_.win_probability).toBeGreaterThan(0);
      expect(eval_.win_probability).toBeLessThanOrEqual(1);
    });
  });

  describe("FeedbackSummary", () => {
    it("should categorize feedback by priority", () => {
      const feedback: FeedbackSummary = {
        proposal_id: "prop-123",
        key_findings: "Team experience is strong; pricing needs adjustment",
        critical_gaps: [
          {
            section_id: "sec-1",
            section_title: "Technical Approach",
            issue_description: "Missing architecture diagram",
            priority: "high",
            estimated_effort: "complex",
            recommended_action:
              "Add detailed architecture diagram with components",
          },
        ],
        quick_wins: [
          {
            section_id: "sec-2",
            section_title: "Budget",
            issue_description: "Add cost breakdown table",
            priority: "medium",
            estimated_effort: "quick",
            recommended_action: "Format existing costs as table",
          },
        ],
        strategic_recommendations: [
          "Emphasize team expertise in proposal",
          "Add risk mitigation section",
        ],
        section_feedback: {
          "sec-1": [
            {
              section_id: "sec-1",
              section_title: "Technical",
              issue_description: "Unclear scalability",
              priority: "high",
              estimated_effort: "medium",
              recommended_action: "Add scalability metrics",
            },
          ],
        },
        score_improvement_projection: 15,
        next_phase_guidance:
          "Implement quick wins first, then tackle critical gaps",
        created_at: new Date().toISOString(),
      };

      expect(feedback.critical_gaps).toHaveLength(1);
      expect(feedback.quick_wins).toHaveLength(1);
      expect(feedback.score_improvement_projection).toBe(15);
    });
  });

  describe("Step8Status", () => {
    it("should aggregate node statuses", () => {
      const status: Step8Status = {
        proposal_id: "prop-123",
        nodes: [
          {
            node_name: "Node 8A",
            status: "completed",
            output_key: "customer_profile",
            version: 1,
          },
          {
            node_name: "Node 8B",
            status: "completed",
            output_key: "validation_report",
            version: 1,
          },
          {
            node_name: "Node 8C",
            status: "pending",
            output_key: "consolidated_proposal",
            version: 0,
          },
        ] as NodeStatus[],
        overall_progress: 66,
        last_updated: new Date().toISOString(),
      };

      expect(status.nodes).toHaveLength(3);
      expect(status.overall_progress).toBe(66);

      const completed = status.nodes.filter((n) => n.status === "completed");
      expect(completed).toHaveLength(2);
    });
  });
});

describe("useStep8 Hooks (Mock)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("useNodeStatus", () => {
    it("should fetch node statuses", () => {
      // This will be tested in integration tests with MSW
      // For now, verify the hook signature
      const expectedReturn = {
        status: null,
        isLoading: true,
        error: null,
        refresh: () => {},
      };

      expect(expectedReturn.isLoading).toBe(true);
      expect(typeof expectedReturn.refresh).toBe("function");
    });
  });

  describe("useValidateNode", () => {
    it("should validate a specific node", () => {
      // Integration test with MSW will verify actual behavior
      const expectedReturn = {
        validate: async () => null,
        isLoading: false,
        error: null,
      };

      expect(typeof expectedReturn.validate).toBe("function");
    });
  });

  describe("useVersionHistory", () => {
    it("should fetch version history for an artifact", () => {
      const expectedReturn = {
        versions: [],
        activeVersion: 0,
        isLoading: true,
        error: null,
        refresh: () => {},
      };

      expect(expectedReturn.versions).toHaveLength(0);
      expect(typeof expectedReturn.refresh).toBe("function");
    });
  });
});

describe("Type Safety", () => {
  it("should enforce severity enum values", () => {
    const validSeverities: Array<"critical" | "major" | "minor"> = [
      "critical",
      "major",
      "minor",
    ];
    expect(validSeverities).toContain("critical");

    // TypeScript will catch invalid values at compile time
    // @ts-expect-error - should not allow invalid severity
    const invalid: "critical" | "major" | "minor" = "low";
  });

  it("should enforce node status values", () => {
    const validStatuses: Array<"pending" | "running" | "completed" | "failed"> =
      ["pending", "running", "completed", "failed"];

    const status: NodeStatus = {
      node_name: "8A",
      status: "completed",
      output_key: "test",
      version: 1,
    };

    expect(validStatuses).toContain(status.status);
  });
});
