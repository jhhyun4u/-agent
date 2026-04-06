/**
 * STEP 8A-8F: Node Type Definitions
 *
 * TypeScript interfaces for all STEP 8 node outputs.
 * Matches backend Pydantic models from app/graph/state.py
 */

/** ============ Core Models ============ */

export interface Stakeholder {
  name: string;
  role: string;
  priorities: string[];
  concerns: string[];
  influence_level: "high" | "medium" | "low";
}

export interface CustomerProfile {
  proposal_id: string;
  client_name: string;
  client_org: string;
  stakeholders: Stakeholder[];
  decision_drivers: string[];
  budget_authority: string;
  pain_points: string[];
  created_at: string;
}

/** ============ Validation ============ */

export interface ValidationIssue {
  location: string;
  severity: "critical" | "major" | "minor";
  issue_type: string;
  issue_description: string;
  fix_suggestion?: string;
}

export interface ValidationReport {
  proposal_id: string;
  pass_validation: boolean;
  quality_score: number; // 0-100
  issues: ValidationIssue[];
  critical_issues_count: number;
  major_issues_count: number;
  minor_issues_count: number;
  compliance_status: string;
  style_consistency: number; // percentage
  recommendations_for_improvement: string[];
  next_steps: string[];
  created_at: string;
}

/** ============ Consolidation ============ */

export interface SectionLineage {
  original_index: number;
  original_title: string;
  merged_into_index: number;
  merged_into_title: string;
  conflict_resolution: string;
}

export interface ConsolidatedProposal {
  proposal_id: string;
  total_sections: number;
  final_sections: string[]; // Section titles after consolidation
  section_lineage: SectionLineage[];
  executive_summary: string;
  key_changes: string[];
  created_at: string;
}

/** ============ Mock Evaluation ============ */

export interface ScoreComponent {
  dimension: string;
  score: number; // 0-100
  rationale: string;
  strengths: string[];
  weaknesses: string[];
}

export interface MockEvalResult {
  proposal_id: string;
  total_score: number; // 0-100
  dimensions: ScoreComponent[]; // 5 dimensions: technical, team, cost, schedule, risk
  win_probability: number; // 0-1 (0% to 100%)
  pass_fail_risk: "high" | "medium" | "low"; // Risk categorization
  key_differentiators: string[];
  competitive_risks: string[];
  created_at: string;
}

/** ============ Feedback ============ */

export interface FeedbackItem {
  section_id: string;
  section_title: string;
  issue_description: string;
  priority: "high" | "medium" | "low";
  estimated_effort: "quick" | "medium" | "complex";
  recommended_action: string;
}

export interface FeedbackSummary {
  proposal_id: string;
  key_findings: string;
  critical_gaps: FeedbackItem[];
  quick_wins: FeedbackItem[];
  strategic_recommendations: string[];
  section_feedback: Record<string, FeedbackItem[]>; // Keyed by section_id
  score_improvement_projection: number; // Expected score increase (0-100)
  next_phase_guidance: string;
  created_at: string;
}

/** ============ Rewrite History ============ */

export interface RewriteHistory {
  section_id: string;
  section_title: string;
  iteration: number;
  original_content: string;
  rewritten_content: string;
  feedback_used: string;
  created_at: string;
}

export interface RewriteRecord {
  proposal_id: string;
  current_section_index: number;
  rewrite_iteration_count: number;
  total_rewrites: number;
  history: RewriteHistory[];
  created_at: string;
}

/** ============ API Issue Flagging ============ */

export interface AIIssueFlag {
  issue_id: string;
  section_id: string;
  severity: "critical" | "major" | "minor";
  category: "compliance" | "clarity" | "consistency" | "style" | "strategy";
  description: string;
  suggestion: string;
  flagged_text?: string; // Inline highlight
}

export interface ReviewPanelData {
  proposal_id: string;
  issues: AIIssueFlag[];
  total_issues: number;
  critical_count: number;
  can_proceed: boolean;
}

/** ============ Version & Status ============ */

export interface ArtifactVersion {
  version: number;
  created_at: string;
  created_by: string;
  size_bytes: number;
  node_name: string;
}

export interface NodeStatus {
  node_name: string;
  status: "pending" | "running" | "completed" | "failed";
  output_key: string;
  version: number;
  progress?: Record<string, unknown>;
  error?: string;
}

export interface Step8Status {
  proposal_id: string;
  nodes: NodeStatus[];
  overall_progress: number; // 0-100
  last_updated: string;
}

/** ============ Node Display Props ============ */

export interface CardProps {
  data: unknown; // Specific to each card
  isLoading?: boolean;
  error?: Error | null;
  onRevalidate?: () => void;
}

export interface ReviewPanelProps {
  proposal_id: string;
  issues: AIIssueFlag[];
  onApprove?: () => void;
  onRequestChanges?: (feedback: string) => void;
  onRewrite?: () => void;
}
