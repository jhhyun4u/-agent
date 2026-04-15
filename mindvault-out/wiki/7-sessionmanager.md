# 7. 세션 상태 키 (session_manager)
Cohesion: 1.00 | Nodes: 1

## Key Nodes
- **7. 세션 상태 키 (session_manager)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\presentation-generator\presentation-generator.design.md) -- 0 connections

## Internal Relationships

## Cross-Community Connections

## Context
이 커뮤니티는 7. 세션 상태 키 (session_manager)를 중심으로 related 관계로 연결되어 있다. 주요 소스 파일은 presentation-generator.design.md이다.

### Key Facts
- | 키 | 타입 | 설명 | |----|------|------| | `presentation_status` | str | `"idle"` \| `"processing"` \| `"done"` \| `"error"` | | `presentation_pptx_path` | str | 로컬 임시 파일 경로 | | `presentation_pptx_url` | str | Supabase Storage 공개 URL | | `presentation_eval_coverage` | dict | `{ "평가항목명": "slide_N" }` |…
