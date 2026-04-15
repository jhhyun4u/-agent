# 3. 구현 항목 상세 & deployment-infra Plan
Cohesion: 0.12 | Nodes: 17

## Key Nodes
- **3. 구현 항목 상세** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\deployment-infra.plan.md) -- 7 connections
  - -> contains -> [[di-01-github-actions-ci]]
  - -> contains -> [[di-02-github-actions-cd]]
  - -> contains -> [[di-03-docker-composeyml]]
  - -> contains -> [[di-04]]
  - -> contains -> [[di-05]]
  - -> contains -> [[di-06-envproductionexample]]
  - <- contains <- [[deployment-infra-plan]]
- **deployment-infra Plan** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\deployment-infra.plan.md) -- 7 connections
  - -> contains -> [[1]]
  - -> contains -> [[2-scope]]
  - -> contains -> [[3]]
  - -> contains -> [[4]]
  - -> contains -> [[5]]
  - -> contains -> [[6]]
  - -> contains -> [[7]]
- **2. 범위 (Scope)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\deployment-infra.plan.md) -- 3 connections
  - -> contains -> [[in-scope]]
  - -> contains -> [[out-of-scope]]
  - <- contains <- [[deployment-infra-plan]]
- **DI-03: docker-compose.yml** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\deployment-infra.plan.md) -- 2 connections
  - -> has_code_example -> [[yaml]]
  - <- contains <- [[3]]
- **yaml** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\deployment-infra.plan.md) -- 1 connections
  - <- has_code_example <- [[di-03-docker-composeyml]]
- **1. 배경 및 동기** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\deployment-infra.plan.md) -- 1 connections
  - <- contains <- [[deployment-infra-plan]]
- **4. 구현 순서** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\deployment-infra.plan.md) -- 1 connections
  - <- contains <- [[deployment-infra-plan]]
- **5. 기술 결정** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\deployment-infra.plan.md) -- 1 connections
  - <- contains <- [[deployment-infra-plan]]
- **6. 리스크** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\deployment-infra.plan.md) -- 1 connections
  - <- contains <- [[deployment-infra-plan]]
- **7. 완료 기준** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\deployment-infra.plan.md) -- 1 connections
  - <- contains <- [[deployment-infra-plan]]
- **DI-01: GitHub Actions CI** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\deployment-infra.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **DI-02: GitHub Actions CD** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\deployment-infra.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **DI-04: 시크릿 점검** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\deployment-infra.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **DI-05: 배포 문서** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\deployment-infra.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **DI-06: .env.production.example** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\deployment-infra.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **In-Scope** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\deployment-infra.plan.md) -- 1 connections
  - <- contains <- [[2-scope]]
- **Out-of-Scope** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\deployment-infra.plan.md) -- 1 connections
  - <- contains <- [[2-scope]]

## Internal Relationships
- 2. 범위 (Scope) -> contains -> In-Scope [EXTRACTED]
- 2. 범위 (Scope) -> contains -> Out-of-Scope [EXTRACTED]
- 3. 구현 항목 상세 -> contains -> DI-01: GitHub Actions CI [EXTRACTED]
- 3. 구현 항목 상세 -> contains -> DI-02: GitHub Actions CD [EXTRACTED]
- 3. 구현 항목 상세 -> contains -> DI-03: docker-compose.yml [EXTRACTED]
- 3. 구현 항목 상세 -> contains -> DI-04: 시크릿 점검 [EXTRACTED]
- 3. 구현 항목 상세 -> contains -> DI-05: 배포 문서 [EXTRACTED]
- 3. 구현 항목 상세 -> contains -> DI-06: .env.production.example [EXTRACTED]
- deployment-infra Plan -> contains -> 1. 배경 및 동기 [EXTRACTED]
- deployment-infra Plan -> contains -> 2. 범위 (Scope) [EXTRACTED]
- deployment-infra Plan -> contains -> 3. 구현 항목 상세 [EXTRACTED]
- deployment-infra Plan -> contains -> 4. 구현 순서 [EXTRACTED]
- deployment-infra Plan -> contains -> 5. 기술 결정 [EXTRACTED]
- deployment-infra Plan -> contains -> 6. 리스크 [EXTRACTED]
- deployment-infra Plan -> contains -> 7. 완료 기준 [EXTRACTED]
- DI-03: docker-compose.yml -> has_code_example -> yaml [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 3. 구현 항목 상세, deployment-infra Plan, 2. 범위 (Scope)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 deployment-infra.plan.md이다.

### Key Facts
- DI-01: GitHub Actions CI
- > CI/CD 파이프라인 + docker-compose + 시크릿 관리 + 배포 문서화
- **파일**: `docker-compose.yml` (프로젝트 루트)
- **서비스 구성**: ```yaml services: backend:     # Dockerfile 기반, .env 마운트, 포트 8000 postgres:    # postgres:16-alpine, 볼륨 영속화 frontend:    # node:20-alpine, npm run dev, 포트 3000 ```
- 배포 준비 점검 결과 백엔드(96%)·프론트엔드(95%)는 프로덕션 수준이나, **인프라/DevOps 영역(60%)** 에 주요 갭이 존재한다.
