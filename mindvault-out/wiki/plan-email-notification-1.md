# Plan: 이메일 알림 + 개인 설정 (email-notification) & 1. 배경 및 목표
Cohesion: 0.08 | Nodes: 26

## Key Nodes
- **Plan: 이메일 알림 + 개인 설정 (email-notification)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\email-notification\email-notification.plan.md) -- 13 connections
  - -> contains -> [[1]]
  - -> contains -> [[2-12-4]]
  - -> contains -> [[3-microsoft-graph-api]]
  - -> contains -> [[4-notificationsettings-jsonb]]
  - -> contains -> [[5]]
  - -> contains -> [[6]]
  - -> contains -> [[7-configpy]]
  - -> contains -> [[8]]
  - -> contains -> [[9]]
  - -> contains -> [[10-v10v11]]
  - -> contains -> [[11-out-of-scope]]
  - -> contains -> [[12]]
  - -> contains -> [[version-history]]
- **1. 배경 및 목표** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\email-notification\email-notification.plan.md) -- 4 connections
  - -> contains -> [[11]]
  - -> contains -> [[12]]
  - -> contains -> [[13]]
  - <- contains <- [[plan-email-notification]]
- **5. 구현 범위** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\email-notification\email-notification.plan.md) -- 4 connections
  - -> contains -> [[51]]
  - -> contains -> [[52-settings]]
  - -> contains -> [[53-settings]]
  - <- contains <- [[plan-email-notification]]
- **2. 전체 알림 유형 (12종 → 4카테고리)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\email-notification\email-notification.plan.md) -- 3 connections
  - -> contains -> [[21]]
  - -> contains -> [[22-4]]
  - <- contains <- [[plan-email-notification]]
- **3. 기술 방식: Microsoft Graph API** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\email-notification\email-notification.plan.md) -- 3 connections
  - -> contains -> [[31]]
  - -> contains -> [[32-azure]]
  - <- contains <- [[plan-email-notification]]
- **4. `notification_settings` JSONB 재설계** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\email-notification\email-notification.plan.md) -- 2 connections
  - -> has_code_example -> [[json]]
  - <- contains <- [[plan-email-notification]]
- **7. config.py 설정** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\email-notification\email-notification.plan.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[plan-email-notification]]
- **json** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\email-notification\email-notification.plan.md) -- 1 connections
  - <- has_code_example <- [[4-notificationsettings-jsonb]]
- **python** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\email-notification\email-notification.plan.md) -- 1 connections
  - <- has_code_example <- [[7-configpy]]
- **10. 기존 구현 재활용 (v1.0~v1.1에서 이미 완료된 것)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\email-notification\email-notification.plan.md) -- 1 connections
  - <- contains <- [[plan-email-notification]]
- **11. 범위 외 (Out of Scope)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\email-notification\email-notification.plan.md) -- 1 connections
  - <- contains <- [[plan-email-notification]]
- **12. 리스크** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\email-notification\email-notification.plan.md) -- 1 connections
  - <- contains <- [[plan-email-notification]]
- **1.1 현재 상태** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\email-notification\email-notification.plan.md) -- 1 connections
  - <- contains <- [[1]]
- **1.2 목표** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\email-notification\email-notification.plan.md) -- 1 connections
  - <- contains <- [[1]]
- **1.3 대상 사용자** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\email-notification\email-notification.plan.md) -- 1 connections
  - <- contains <- [[1]]
- **2.1 알림 인벤토리** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\email-notification\email-notification.plan.md) -- 1 connections
  - <- contains <- [[2-12-4]]
- **2.2 4카테고리 매핑** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\email-notification\email-notification.plan.md) -- 1 connections
  - <- contains <- [[2-12-4]]
- **3.1 선택 이유** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\email-notification\email-notification.plan.md) -- 1 connections
  - <- contains <- [[3-microsoft-graph-api]]
- **3.2 사전 조건 (Azure 포털)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\email-notification\email-notification.plan.md) -- 1 connections
  - <- contains <- [[3-microsoft-graph-api]]
- **5.1 백엔드** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\email-notification\email-notification.plan.md) -- 1 connections
  - <- contains <- [[5]]
- **5.2 프론트엔드 — `/settings` 페이지 신설** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\email-notification\email-notification.plan.md) -- 1 connections
  - <- contains <- [[5]]
- **5.3 `/settings` 페이지 구조** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\email-notification\email-notification.plan.md) -- 1 connections
  - <- contains <- [[5]]
- **6. 알림 함수 ↔ 카테고리 매핑 (최종)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\email-notification\email-notification.plan.md) -- 1 connections
  - <- contains <- [[plan-email-notification]]
- **8. 의존성** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\email-notification\email-notification.plan.md) -- 1 connections
  - <- contains <- [[plan-email-notification]]
- **9. 구현 순서** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\email-notification\email-notification.plan.md) -- 1 connections
  - <- contains <- [[plan-email-notification]]
- **Version History** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\email-notification\email-notification.plan.md) -- 1 connections
  - <- contains <- [[plan-email-notification]]

## Internal Relationships
- 1. 배경 및 목표 -> contains -> 1.1 현재 상태 [EXTRACTED]
- 1. 배경 및 목표 -> contains -> 1.2 목표 [EXTRACTED]
- 1. 배경 및 목표 -> contains -> 1.3 대상 사용자 [EXTRACTED]
- 2. 전체 알림 유형 (12종 → 4카테고리) -> contains -> 2.1 알림 인벤토리 [EXTRACTED]
- 2. 전체 알림 유형 (12종 → 4카테고리) -> contains -> 2.2 4카테고리 매핑 [EXTRACTED]
- 3. 기술 방식: Microsoft Graph API -> contains -> 3.1 선택 이유 [EXTRACTED]
- 3. 기술 방식: Microsoft Graph API -> contains -> 3.2 사전 조건 (Azure 포털) [EXTRACTED]
- 4. `notification_settings` JSONB 재설계 -> has_code_example -> json [EXTRACTED]
- 5. 구현 범위 -> contains -> 5.1 백엔드 [EXTRACTED]
- 5. 구현 범위 -> contains -> 5.2 프론트엔드 — `/settings` 페이지 신설 [EXTRACTED]
- 5. 구현 범위 -> contains -> 5.3 `/settings` 페이지 구조 [EXTRACTED]
- 7. config.py 설정 -> has_code_example -> python [EXTRACTED]
- Plan: 이메일 알림 + 개인 설정 (email-notification) -> contains -> 1. 배경 및 목표 [EXTRACTED]
- Plan: 이메일 알림 + 개인 설정 (email-notification) -> contains -> 2. 전체 알림 유형 (12종 → 4카테고리) [EXTRACTED]
- Plan: 이메일 알림 + 개인 설정 (email-notification) -> contains -> 3. 기술 방식: Microsoft Graph API [EXTRACTED]
- Plan: 이메일 알림 + 개인 설정 (email-notification) -> contains -> 4. `notification_settings` JSONB 재설계 [EXTRACTED]
- Plan: 이메일 알림 + 개인 설정 (email-notification) -> contains -> 5. 구현 범위 [EXTRACTED]
- Plan: 이메일 알림 + 개인 설정 (email-notification) -> contains -> 6. 알림 함수 ↔ 카테고리 매핑 (최종) [EXTRACTED]
- Plan: 이메일 알림 + 개인 설정 (email-notification) -> contains -> 7. config.py 설정 [EXTRACTED]
- Plan: 이메일 알림 + 개인 설정 (email-notification) -> contains -> 8. 의존성 [EXTRACTED]
- Plan: 이메일 알림 + 개인 설정 (email-notification) -> contains -> 9. 구현 순서 [EXTRACTED]
- Plan: 이메일 알림 + 개인 설정 (email-notification) -> contains -> 10. 기존 구현 재활용 (v1.0~v1.1에서 이미 완료된 것) [EXTRACTED]
- Plan: 이메일 알림 + 개인 설정 (email-notification) -> contains -> 11. 범위 외 (Out of Scope) [EXTRACTED]
- Plan: 이메일 알림 + 개인 설정 (email-notification) -> contains -> 12. 리스크 [EXTRACTED]
- Plan: 이메일 알림 + 개인 설정 (email-notification) -> contains -> Version History [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Plan: 이메일 알림 + 개인 설정 (email-notification), 1. 배경 및 목표, 5. 구현 범위를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 email-notification.plan.md이다.

### Key Facts
- > **Version**: 2.0 > **Date**: 2026-03-26 > **Status**: Plan > **Priority**: HIGH
- 1.1 현재 상태 - 알림 채널: **Teams Webhook + 인앱** (2가지만 구현) - 이메일 발송 기능: **미구현** - `users.notification_settings`: `{"teams": true, "in_app": true}` — email 키 없음 - 알림 발송 시 `notification_settings` 확인 로직 **미적용** (항상 발송) - 개인 설정 페이지 **없음** — 알림 설정이 팀 설정(`/monitoring/settings`)에 혼재 - 알림 함수 12종이 3개 파일에 산재…
- 3.1 선택 이유 - TENOPA가 이미 Azure AD (MS365) 사용 중 → 추가 비용 없음 - Outlook 보낸편지함에 기록 → 감사 추적 가능 - 기존 `azure_ad_tenant_id`, `azure_ad_client_id`, `azure_ad_client_secret` 재활용
- ```json // Before {"teams": true, "in_app": true}
- ```python 이메일 알림 (Microsoft Graph API) — 이미 구현됨 email_enabled: bool = False email_sender: str = "" email_graph_scope: str = "https://graph.microsoft.com/.default" ```
