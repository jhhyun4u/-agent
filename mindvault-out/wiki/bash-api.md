# bash & 단위 테스트만 실행 (API 키 불필요)
Cohesion: 1.00 | Nodes: 2

## Key Nodes
- **bash** (C:\project\tenopa proposer\-agent-master\tests\README.md) -- 1 connections
  - <- has_code_example <- [[api]]
- **단위 테스트만 실행 (API 키 불필요)** (C:\project\tenopa proposer\-agent-master\tests\README.md) -- 1 connections
  - -> has_code_example -> [[bash]]

## Internal Relationships
- 단위 테스트만 실행 (API 키 불필요) -> has_code_example -> bash [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 bash, 단위 테스트만 실행 (API 키 불필요)를 중심으로 has_code_example 관계로 연결되어 있다. 주요 소스 파일은 README.md이다.

### Key Facts
- 전체 테스트 실행 ```bash uv run pytest ```
- 통합 테스트 실행 (API 키 필요) ```bash uv run pytest tests/integration/ ```
