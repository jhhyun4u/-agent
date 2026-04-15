# 15개 검증 항목 & PDCA Completion Report: 플랫폼 자가검증 시스템 (Self-Verification)
Cohesion: 0.20 | Nodes: 10

## Key Nodes
- **15개 검증 항목** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\self-verification.report.md) -- 6 connections
  - -> contains -> [[5]]
  - -> contains -> [[30]]
  - -> contains -> [[1]]
  - -> contains -> [[api-1]]
  - -> contains -> [[teams-adaptive-card]]
  - <- contains <- [[pdca-completion-report-self-verification]]
- **PDCA Completion Report: 플랫폼 자가검증 시스템 (Self-Verification)** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\self-verification.report.md) -- 4 connections
  - -> contains -> [[15]]
  - -> contains -> [[api]]
  - -> contains -> [[configpy]]
  - -> contains -> [[gap-analysis]]
- **외부 서비스 (매 1시간)** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\self-verification.report.md) -- 1 connections
  - <- contains <- [[15]]
- **데이터 정합성 (매 30분)** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\self-verification.report.md) -- 1 connections
  - <- contains <- [[15]]
- **인프라 (매 5분)** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\self-verification.report.md) -- 1 connections
  - <- contains <- [[15]]
- **관리자 API** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\self-verification.report.md) -- 1 connections
  - <- contains <- [[pdca-completion-report-self-verification]]
- **API 스모크 (매 1시간)** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\self-verification.report.md) -- 1 connections
  - <- contains <- [[15]]
- **설정 (config.py)** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\self-verification.report.md) -- 1 connections
  - <- contains <- [[pdca-completion-report-self-verification]]
- **Gap Analysis 결과** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\self-verification.report.md) -- 1 connections
  - <- contains <- [[pdca-completion-report-self-verification]]
- **Teams Adaptive Card 형식** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\self-verification.report.md) -- 1 connections
  - <- contains <- [[15]]

## Internal Relationships
- 15개 검증 항목 -> contains -> 인프라 (매 5분) [EXTRACTED]
- 15개 검증 항목 -> contains -> 데이터 정합성 (매 30분) [EXTRACTED]
- 15개 검증 항목 -> contains -> 외부 서비스 (매 1시간) [EXTRACTED]
- 15개 검증 항목 -> contains -> API 스모크 (매 1시간) [EXTRACTED]
- 15개 검증 항목 -> contains -> Teams Adaptive Card 형식 [EXTRACTED]
- PDCA Completion Report: 플랫폼 자가검증 시스템 (Self-Verification) -> contains -> 15개 검증 항목 [EXTRACTED]
- PDCA Completion Report: 플랫폼 자가검증 시스템 (Self-Verification) -> contains -> 관리자 API [EXTRACTED]
- PDCA Completion Report: 플랫폼 자가검증 시스템 (Self-Verification) -> contains -> 설정 (config.py) [EXTRACTED]
- PDCA Completion Report: 플랫폼 자가검증 시스템 (Self-Verification) -> contains -> Gap Analysis 결과 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 15개 검증 항목, PDCA Completion Report: 플랫폼 자가검증 시스템 (Self-Verification), 외부 서비스 (매 1시간)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 self-verification.report.md이다.

### Key Facts
- | ID | 검증 | 자동 복구 | |----|------|:---------:| | E-1 | G2B API 응답 확인 | - | | E-2 | Claude API 키 형식 확인 (호출 X, 비용 절약) | - | | E-3 | Teams Webhook 접근 확인 (HEAD, 메시지 X) | - |
- | ID | 검증 | 자동 복구 | |----|------|:---------:| | D-1 | 마감 경과 공고 days_remaining 불일치 → 재계산 | ✅ | | D-2 | 고아 추천 레코드 (공고 없는 bid_no) → 삭제 | ✅ | | D-3 | Stale 세션 (running >2시간) → stale 전환 | ✅ | | D-4 | MV 최신성 (>24시간) → REFRESH | ✅ | | D-5 | 파일 캐시-DB 불일치 → DB 기준 동기화 | ✅ |
- | ID | 검증 | 자동 복구 | |----|------|:---------:| | I-1 | DB 연결 (SELECT + 연결 풀 재생성) | ✅ | | I-2 | Supabase Storage 버킷 접근 | - | | I-3 | 메모리/CPU (psutil, 선택적) | - |
- | 엔드포인트 | 용도 | |-----------|------| | `GET /health` | 공개 — DB + 최근 검증 요약 (fail 건수, failing 목록) | | `GET /api/admin/health/detail?category=data&hours=24` | 관리자 — 최근 이력 상세 (필터링) | | `POST /api/admin/health/run?check_id=D-1` | 관리자 — 수동 즉시 실행 |
- | ID | 검증 | 자동 복구 | |----|------|:---------:| | A-1 | /health 내부 호출 | - | | A-2 | 모니터 API 응답 구조 + 필수 필드 검증 | - | | A-3 | 스코어링 함수 정상 작동 | - | | A-4 | proposals 테이블 접근 | - |
