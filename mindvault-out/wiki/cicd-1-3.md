# CI/CD 배포 상태 검증 (1단계) & 3. 가능한 원인들
Cohesion: 0.18 | Nodes: 14

## Key Nodes
- **CI/CD 배포 상태 검증 (1단계)** (C:\project\tenopa proposer\-agent-master\CI_DEPLOYMENT_STATUS.md) -- 7 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[5]]
  - -> contains -> [[1-ci]]
  - -> contains -> [[github-actions]]
  - -> contains -> [[api]]
- **3. 가능한 원인들** (C:\project\tenopa proposer\-agent-master\CI_DEPLOYMENT_STATUS.md) -- 4 connections
  - -> contains -> [[1-ci]]
  - -> contains -> [[2]]
  - -> contains -> [[3-secret]]
  - <- contains <- [[cicd-1]]
- **즉시 실행 (5분)** (C:\project\tenopa proposer\-agent-master\CI_DEPLOYMENT_STATUS.md) -- 4 connections
  - -> contains -> [[a]]
  - -> contains -> [[b]]
  - -> contains -> [[c]]
  - <- contains <- [[cicd-1]]
- **bash** (C:\project\tenopa proposer\-agent-master\CI_DEPLOYMENT_STATUS.md) -- 3 connections
  - <- has_code_example <- [[1-ci]]
  - <- has_code_example <- [[2]]
  - <- has_code_example <- [[api]]
- **2. 최근 변경사항** (C:\project\tenopa proposer\-agent-master\CI_DEPLOYMENT_STATUS.md) -- 3 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[cicd-1]]
  - <- contains <- [[3]]
- **1단계: 로컬 CI 테스트 실행** (C:\project\tenopa proposer\-agent-master\CI_DEPLOYMENT_STATUS.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[cicd-1]]
- **프로덕션 API 직접 확인** (C:\project\tenopa proposer\-agent-master\CI_DEPLOYMENT_STATUS.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[cicd-1]]
- **1. 워크플로우 파일 확인** (C:\project\tenopa proposer\-agent-master\CI_DEPLOYMENT_STATUS.md) -- 1 connections
  - <- contains <- [[cicd-1]]
- **원인 1: 실제 CI 테스트 실패** (C:\project\tenopa proposer\-agent-master\CI_DEPLOYMENT_STATUS.md) -- 1 connections
  - <- contains <- [[3]]
- **원인 3: 환경 변수/Secret 문제** (C:\project\tenopa proposer\-agent-master\CI_DEPLOYMENT_STATUS.md) -- 1 connections
  - <- contains <- [[3]]
- **A) 로컬 테스트 통과하면** (C:\project\tenopa proposer\-agent-master\CI_DEPLOYMENT_STATUS.md) -- 1 connections
  - <- contains <- [[5]]
- **B) 로컬 테스트 실패하면** (C:\project\tenopa proposer\-agent-master\CI_DEPLOYMENT_STATUS.md) -- 1 connections
  - <- contains <- [[5]]
- **C) 워크플로우 파일 문제면** (C:\project\tenopa proposer\-agent-master\CI_DEPLOYMENT_STATUS.md) -- 1 connections
  - <- contains <- [[5]]
- **GitHub Actions 확인** (C:\project\tenopa proposer\-agent-master\CI_DEPLOYMENT_STATUS.md) -- 1 connections
  - <- contains <- [[cicd-1]]

## Internal Relationships
- 1단계: 로컬 CI 테스트 실행 -> has_code_example -> bash [EXTRACTED]
- 2. 최근 변경사항 -> has_code_example -> bash [EXTRACTED]
- 3. 가능한 원인들 -> contains -> 원인 1: 실제 CI 테스트 실패 [EXTRACTED]
- 3. 가능한 원인들 -> contains -> 2. 최근 변경사항 [EXTRACTED]
- 3. 가능한 원인들 -> contains -> 원인 3: 환경 변수/Secret 문제 [EXTRACTED]
- 즉시 실행 (5분) -> contains -> A) 로컬 테스트 통과하면 [EXTRACTED]
- 즉시 실행 (5분) -> contains -> B) 로컬 테스트 실패하면 [EXTRACTED]
- 즉시 실행 (5분) -> contains -> C) 워크플로우 파일 문제면 [EXTRACTED]
- 프로덕션 API 직접 확인 -> has_code_example -> bash [EXTRACTED]
- CI/CD 배포 상태 검증 (1단계) -> contains -> 1. 워크플로우 파일 확인 [EXTRACTED]
- CI/CD 배포 상태 검증 (1단계) -> contains -> 2. 최근 변경사항 [EXTRACTED]
- CI/CD 배포 상태 검증 (1단계) -> contains -> 3. 가능한 원인들 [EXTRACTED]
- CI/CD 배포 상태 검증 (1단계) -> contains -> 즉시 실행 (5분) [EXTRACTED]
- CI/CD 배포 상태 검증 (1단계) -> contains -> 1단계: 로컬 CI 테스트 실행 [EXTRACTED]
- CI/CD 배포 상태 검증 (1단계) -> contains -> GitHub Actions 확인 [EXTRACTED]
- CI/CD 배포 상태 검증 (1단계) -> contains -> 프로덕션 API 직접 확인 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 CI/CD 배포 상태 검증 (1단계), 3. 가능한 원인들, 즉시 실행 (5분)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 CI_DEPLOYMENT_STATUS.md이다.

### Key Facts
- 원인 1: 실제 CI 테스트 실패 ``` 가능성: ★★★★☆ (높음) 이유: - 최근 코드 변경으로 테스트 실패 - backend-test, frontend-build 중 하나 실패 가능성
- 1단계: 로컬 CI 테스트 실행 ```bash cd "C:\\project\\tenopa proposer\\-agent-master"
- Backend 린트 (ruff) uv run ruff check app/
- curl https://your-production-api.com/api/documents 응답: 200 OK = API 정상 작동 ```
- ✅ ci.yml: 구조 정상 - 69줄 완료 - 3개 작업 정의: backend-lint, backend-test, frontend-build - YAML 문법 정상 ```
