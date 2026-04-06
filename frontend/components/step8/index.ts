/**
 * STEP 8 Component Exports
 *
 * All UI components for STEP 8A-8F node displays
 */

export { CustomerProfileCard } from "./CustomerProfileCard";
export type { CustomerProfileCardProps } from "./CustomerProfileCard";

export { ValidationReportCard } from "./ValidationReportCard";
export type { ValidationReportCardProps } from "./ValidationReportCard";

export { ConsolidatedProposalCard } from "./ConsolidatedProposalCard";
export type { ConsolidatedProposalCardProps } from "./ConsolidatedProposalCard";

export { MockEvalCard } from "./MockEvalCard";
export type { MockEvalCardProps } from "./MockEvalCard";

export { FeedbackSummaryCard } from "./FeedbackSummaryCard";
export type { FeedbackSummaryCardProps } from "./FeedbackSummaryCard";

export { RewriteHistoryCard } from "./RewriteHistoryCard";
export type { RewriteHistoryCardProps } from "./RewriteHistoryCard";

export { ReviewPanelEnhanced } from "./ReviewPanelEnhanced";
export type { ReviewPanelEnhancedProps } from "./ReviewPanelEnhanced";

export { NodeStatusDashboard } from "./NodeStatusDashboard";
export type { NodeStatusDashboardProps } from "./NodeStatusDashboard";

export { VersionHistoryViewer } from "./VersionHistoryViewer";
export type {
  VersionHistoryViewerProps,
  VersionMetadata,
  VersionComparisonData,
} from "./VersionHistoryViewer";

/**
 * Usage:
 *
 * import { CustomerProfileCard, ValidationReportCard } from "@/components/step8";
 *
 * <CustomerProfileCard
 *   data={customerProfile}
 *   isLoading={isLoading}
 *   error={error}
 *   onRevalidate={() => refetch()}
 * />
 */
