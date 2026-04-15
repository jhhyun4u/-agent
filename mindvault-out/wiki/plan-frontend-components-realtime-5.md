# Plan: Frontend Components 분리 & Realtime 전환 & 5. 작업 목록
Cohesion: 0.15 | Nodes: 13

## Key Nodes
- **Plan: Frontend Components 분리 & Realtime 전환** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-components\frontend-components.plan.md) -- 8 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[4]]
  - -> contains -> [[5]]
  - -> contains -> [[6-usephasestatus]]
  - -> contains -> [[7]]
  - -> contains -> [[8]]
- **5. 작업 목록** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-components\frontend-components.plan.md) -- 3 connections
  - -> contains -> [[phase-a-realtime]]
  - -> contains -> [[phase-b-useproposals]]
  - <- contains <- [[plan-frontend-components-realtime]]
- **2. 목표** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-components\frontend-components.plan.md) -- 2 connections
  - -> contains -> [[v11]]
  - <- contains <- [[plan-frontend-components-realtime]]
- **6. usePhaseStatus 설계** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-components\frontend-components.plan.md) -- 2 connections
  - -> has_code_example -> [[typescript]]
  - <- contains <- [[plan-frontend-components-realtime]]
- **typescript** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-components\frontend-components.plan.md) -- 1 connections
  - <- has_code_example <- [[6-usephasestatus]]
- **1. 현황 분석** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-components\frontend-components.plan.md) -- 1 connections
  - <- contains <- [[plan-frontend-components-realtime]]
- **3. 사용자 의도** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-components\frontend-components.plan.md) -- 1 connections
  - <- contains <- [[plan-frontend-components-realtime]]
- **4. 기술 결정사항** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-components\frontend-components.plan.md) -- 1 connections
  - <- contains <- [[plan-frontend-components-realtime]]
- **7. 성공 기준** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-components\frontend-components.plan.md) -- 1 connections
  - <- contains <- [[plan-frontend-components-realtime]]
- **8. 다음 단계** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-components\frontend-components.plan.md) -- 1 connections
  - <- contains <- [[plan-frontend-components-realtime]]
- **Phase A — Realtime 훅 구현** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-components\frontend-components.plan.md) -- 1 connections
  - <- contains <- [[5]]
- **Phase B — (선택) useProposals 훅 분리** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-components\frontend-components.plan.md) -- 1 connections
  - <- contains <- [[5]]
- **v1.1 목표 (이 사이클)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-components\frontend-components.plan.md) -- 1 connections
  - <- contains <- [[2]]

## Internal Relationships
- 2. 목표 -> contains -> v1.1 목표 (이 사이클) [EXTRACTED]
- 5. 작업 목록 -> contains -> Phase A — Realtime 훅 구현 [EXTRACTED]
- 5. 작업 목록 -> contains -> Phase B — (선택) useProposals 훅 분리 [EXTRACTED]
- 6. usePhaseStatus 설계 -> has_code_example -> typescript [EXTRACTED]
- Plan: Frontend Components 분리 & Realtime 전환 -> contains -> 1. 현황 분석 [EXTRACTED]
- Plan: Frontend Components 분리 & Realtime 전환 -> contains -> 2. 목표 [EXTRACTED]
- Plan: Frontend Components 분리 & Realtime 전환 -> contains -> 3. 사용자 의도 [EXTRACTED]
- Plan: Frontend Components 분리 & Realtime 전환 -> contains -> 4. 기술 결정사항 [EXTRACTED]
- Plan: Frontend Components 분리 & Realtime 전환 -> contains -> 5. 작업 목록 [EXTRACTED]
- Plan: Frontend Components 분리 & Realtime 전환 -> contains -> 6. usePhaseStatus 설계 [EXTRACTED]
- Plan: Frontend Components 분리 & Realtime 전환 -> contains -> 7. 성공 기준 [EXTRACTED]
- Plan: Frontend Components 분리 & Realtime 전환 -> contains -> 8. 다음 단계 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Plan: Frontend Components 분리 & Realtime 전환, 5. 작업 목록, 2. 목표를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 frontend-components.plan.md이다.

### Key Facts
- Phase A — Realtime 훅 구현 | 순서 | 파일 | 작업 | |------|------|------| | A1 | `frontend/lib/hooks/usePhaseStatus.ts` | Supabase Realtime 구독 훅 신규 구현 | | A2 | `frontend/app/proposals/[id]/page.tsx` | polling 제거, usePhaseStatus 적용 |
- ```typescript // frontend/lib/hooks/usePhaseStatus.ts import { useEffect, useState } from "react" import { createClient } from "@/lib/supabase/client"
- ```typescript // frontend/lib/hooks/usePhaseStatus.ts import { useEffect, useState } from "react" import { createClient } from "@/lib/supabase/client"
- 핵심 문제 1. **Realtime 지연**: 현재 polling(3초)은 설계 명세 위반. Supabase Realtime으로 즉시 업데이트 필요 2. **컴포넌트 재사용**: 향후 페이지 추가 시 인라인 코드 중복 발생 가능
- | 결정 | 내용 | 이유 | |------|------|------| | Realtime 우선 | polling 제거, Realtime 전환 | 설계 명세 + 서버 부하 감소 | | 컴포넌트 분리 보류 | 인라인 유지 (단일 사용처) | YAGNI — 실제 재사용 발생 시 분리 | | usePhaseStatus hook | Supabase postgres_changes 구독 | [id]/page.tsx proposals UPDATE 이벤트 |
