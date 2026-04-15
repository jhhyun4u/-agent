# 9. 권장 조치 요약 (v2.0) & 즉시 조치 (HIGH) — 1건 (인프라)
Cohesion: 0.50 | Nodes: 4

## Key Nodes
- **9. 권장 조치 요약 (v2.0)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-gaps\frontend.analysis.md) -- 3 connections
  - -> contains -> [[high-1]]
  - -> contains -> [[v10-highmedium]]
  - -> contains -> [[mediumlow-8]]
- **즉시 조치 (HIGH) — 1건 (인프라)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-gaps\frontend.analysis.md) -- 1 connections
  - <- contains <- [[9-v20]]
- **향후 개선 (MEDIUM/LOW) — 8건 잔여** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-gaps\frontend.analysis.md) -- 1 connections
  - <- contains <- [[9-v20]]
- **~~해소 완료 (v1.0 HIGH/MEDIUM)~~ ✅** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-gaps\frontend.analysis.md) -- 1 connections
  - <- contains <- [[9-v20]]

## Internal Relationships
- 9. 권장 조치 요약 (v2.0) -> contains -> 즉시 조치 (HIGH) — 1건 (인프라) [EXTRACTED]
- 9. 권장 조치 요약 (v2.0) -> contains -> ~~해소 완료 (v1.0 HIGH/MEDIUM)~~ ✅ [EXTRACTED]
- 9. 권장 조치 요약 (v2.0) -> contains -> 향후 개선 (MEDIUM/LOW) — 8건 잔여 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 9. 권장 조치 요약 (v2.0), 즉시 조치 (HIGH) — 1건 (인프라), 향후 개선 (MEDIUM/LOW) — 8건 잔여를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 frontend.analysis.md이다.

### Key Facts
- 즉시 조치 (HIGH) — 1건 (인프라)
- | # | 항목 | 예상 공수 | 비고 | |---|------|-----------|------| | 1 | Azure AD SSO 로그인 연동 | 1일 | 프로덕션 배포 전 필수. 코드 갭이 아닌 인프라 설정 |
- | # | 항목 | 우선순위 | |---|------|:--------:| | 1 | artifacts.diff 클라이언트 메서드 (SS12-4 M2) | MEDIUM | | 2 | 대시보드 팀장 전용 결재대기/마감임박 위젯 분리 | MEDIUM | | 3 | 결재선 현황 컴포넌트 (SS13-8-3) | LOW | | 4 | 역량 DB 인라인 편집 모달 (SS13-9) | LOW | | 5 | 노임단가/낙찰가 CSV import/export | LOW | | 6 | 병렬 진행 미리보기 버튼 (SS13-7) | LOW | | 7 |…
- | # | 항목 | 해소 일자 | |---|------|-----------| | ~~1~~ | ~~v3.1 레거시 API 경로~~ | Phase 5 Act-1 (2026-03-17) | | ~~2~~ | ~~3가지 진입 경로 UI~~ | Phase 5 Act-1 (2026-03-17) | | ~~3~~ | ~~대시보드 역할별 API 연동~~ | 2026-03-18 | | ~~4~~ | ~~성과 추적 API 연동~~ | 2026-03-18 | | ~~5~~ | ~~Go/No-Go 패널 상세 점수~~ | 기존 구현 확인 | |…
