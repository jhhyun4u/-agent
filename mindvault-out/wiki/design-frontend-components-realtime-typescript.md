# Design: Frontend Components — Realtime 전환 & typescript
Cohesion: 0.13 | Nodes: 18

## Key Nodes
- **Design: Frontend Components — Realtime 전환** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-components\frontend-components.design.md) -- 9 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[4]]
  - -> contains -> [[5]]
  - -> contains -> [[6]]
  - -> contains -> [[7]]
  - -> contains -> [[8]]
  - -> contains -> [[9]]
- **typescript** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-components\frontend-components.design.md) -- 4 connections
  - <- has_code_example <- [[idpagetsx-polling]]
  - <- has_code_example <- [[31-usephasestatus]]
  - <- has_code_example <- [[32-idpagetsx]]
  - <- has_code_example <- [[realtime]]
- **3. 설계 (변경 후)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-components\frontend-components.design.md) -- 3 connections
  - -> contains -> [[31-usephasestatus]]
  - -> contains -> [[32-idpagetsx]]
  - <- contains <- [[design-frontend-components-realtime]]
- **4. 의존성 확인** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-components\frontend-components.design.md) -- 3 connections
  - -> contains -> [[supabase-realtime]]
  - -> contains -> [[proposalstatus]]
  - <- contains <- [[design-frontend-components-realtime]]
- **1. 변경 범위** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-components\frontend-components.design.md) -- 2 connections
  - -> contains -> [[yagni]]
  - <- contains <- [[design-frontend-components-realtime]]
- **2. 현재 구현 (변경 전)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-components\frontend-components.design.md) -- 2 connections
  - -> contains -> [[idpagetsx-polling]]
  - <- contains <- [[design-frontend-components-realtime]]
- **3.1 usePhaseStatus 훅** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-components\frontend-components.design.md) -- 2 connections
  - -> has_code_example -> [[typescript]]
  - <- contains <- [[3]]
- **3.2 `[id]/page.tsx` 변경 사항** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-components\frontend-components.design.md) -- 2 connections
  - -> has_code_example -> [[typescript]]
  - <- contains <- [[3]]
- **5. 엣지 케이스** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-components\frontend-components.design.md) -- 2 connections
  - -> contains -> [[realtime]]
  - <- contains <- [[design-frontend-components-realtime]]
- **`[id]/page.tsx` 현재 polling 패턴** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-components\frontend-components.design.md) -- 2 connections
  - -> has_code_example -> [[typescript]]
  - <- contains <- [[2]]
- **Realtime 연결 실패 폴백 (선택 구현)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-components\frontend-components.design.md) -- 2 connections
  - -> has_code_example -> [[typescript]]
  - <- contains <- [[5]]
- **6. 구현 순서** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-components\frontend-components.design.md) -- 1 connections
  - <- contains <- [[design-frontend-components-realtime]]
- **7. 파일 변경 전체 요약** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-components\frontend-components.design.md) -- 1 connections
  - <- contains <- [[design-frontend-components-realtime]]
- **8. 성공 기준** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-components\frontend-components.design.md) -- 1 connections
  - <- contains <- [[design-frontend-components-realtime]]
- **9. 다음 단계** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-components\frontend-components.design.md) -- 1 connections
  - <- contains <- [[design-frontend-components-realtime]]
- **ProposalStatus_ 타입 확인** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-components\frontend-components.design.md) -- 1 connections
  - <- contains <- [[4]]
- **Supabase Realtime 전제 조건** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-components\frontend-components.design.md) -- 1 connections
  - <- contains <- [[4]]
- **변경 없는 파일 (YAGNI)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-components\frontend-components.design.md) -- 1 connections
  - <- contains <- [[1]]

## Internal Relationships
- 1. 변경 범위 -> contains -> 변경 없는 파일 (YAGNI) [EXTRACTED]
- 2. 현재 구현 (변경 전) -> contains -> `[id]/page.tsx` 현재 polling 패턴 [EXTRACTED]
- 3. 설계 (변경 후) -> contains -> 3.1 usePhaseStatus 훅 [EXTRACTED]
- 3. 설계 (변경 후) -> contains -> 3.2 `[id]/page.tsx` 변경 사항 [EXTRACTED]
- 3.1 usePhaseStatus 훅 -> has_code_example -> typescript [EXTRACTED]
- 3.2 `[id]/page.tsx` 변경 사항 -> has_code_example -> typescript [EXTRACTED]
- 4. 의존성 확인 -> contains -> Supabase Realtime 전제 조건 [EXTRACTED]
- 4. 의존성 확인 -> contains -> ProposalStatus_ 타입 확인 [EXTRACTED]
- 5. 엣지 케이스 -> contains -> Realtime 연결 실패 폴백 (선택 구현) [EXTRACTED]
- Design: Frontend Components — Realtime 전환 -> contains -> 1. 변경 범위 [EXTRACTED]
- Design: Frontend Components — Realtime 전환 -> contains -> 2. 현재 구현 (변경 전) [EXTRACTED]
- Design: Frontend Components — Realtime 전환 -> contains -> 3. 설계 (변경 후) [EXTRACTED]
- Design: Frontend Components — Realtime 전환 -> contains -> 4. 의존성 확인 [EXTRACTED]
- Design: Frontend Components — Realtime 전환 -> contains -> 5. 엣지 케이스 [EXTRACTED]
- Design: Frontend Components — Realtime 전환 -> contains -> 6. 구현 순서 [EXTRACTED]
- Design: Frontend Components — Realtime 전환 -> contains -> 7. 파일 변경 전체 요약 [EXTRACTED]
- Design: Frontend Components — Realtime 전환 -> contains -> 8. 성공 기준 [EXTRACTED]
- Design: Frontend Components — Realtime 전환 -> contains -> 9. 다음 단계 [EXTRACTED]
- `[id]/page.tsx` 현재 polling 패턴 -> has_code_example -> typescript [EXTRACTED]
- Realtime 연결 실패 폴백 (선택 구현) -> has_code_example -> typescript [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Design: Frontend Components — Realtime 전환, typescript, 3. 설계 (변경 후)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 frontend-components.design.md이다.

### Key Facts
- ```typescript // 현재: 3초 interval polling const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
- Supabase Realtime 전제 조건
- `[id]/page.tsx` 현재 polling 패턴
- ```typescript // frontend/lib/hooks/usePhaseStatus.ts "use client";
- **제거**: ```typescript // 삭제 대상 const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null); const [status, setStatus] = useState<ProposalStatus_ | null>(null); const fetchStatus = useCallback(async () => { ... }, [id]);
