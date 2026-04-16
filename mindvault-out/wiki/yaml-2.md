# yaml & 2. 영향도 분석
Cohesion: 0.13 | Nodes: 18

## Key Nodes
- **yaml** (C:\project\tenopa proposer\PRE_RESTRUCTURING_DIAGNOSIS.md) -- 5 connections
  - <- has_code_example <- [[backend-ciyml]]
  - <- has_code_example <- [[frontend-ciyml]]
  - <- has_code_example <- [[docker-composeyml]]
  - <- has_code_example <- [[41-cicd-backend-ciyml]]
  - <- has_code_example <- [[42-docker-composeyml]]
- **2. 영향도 분석** (C:\project\tenopa proposer\PRE_RESTRUCTURING_DIAGNOSIS.md) -- 5 connections
  - -> contains -> [[21-python]]
  - -> contains -> [[22-github-actions-cicd]]
  - -> contains -> [[23-docker]]
  - -> contains -> [[24-pyprojecttoml]]
  - -> contains -> [[25-env]]
- **2.2 GitHub Actions CI/CD 워크플로우** (C:\project\tenopa proposer\PRE_RESTRUCTURING_DIAGNOSIS.md) -- 3 connections
  - -> contains -> [[backend-ciyml]]
  - -> contains -> [[frontend-ciyml]]
  - <- contains <- [[2]]
- **2.3 Docker 설정** (C:\project\tenopa proposer\PRE_RESTRUCTURING_DIAGNOSIS.md) -- 3 connections
  - -> contains -> [[dockerfile]]
  - -> contains -> [[docker-composeyml]]
  - <- contains <- [[2]]
- **4. 상세 변경 체크리스트** (C:\project\tenopa proposer\PRE_RESTRUCTURING_DIAGNOSIS.md) -- 3 connections
  - -> contains -> [[41-cicd-backend-ciyml]]
  - -> contains -> [[42-docker-composeyml]]
  - -> contains -> [[43-gitignore]]
- **2.4 pyproject.toml 빌드 설정** (C:\project\tenopa proposer\PRE_RESTRUCTURING_DIAGNOSIS.md) -- 2 connections
  - -> has_code_example -> [[toml]]
  - <- contains <- [[2]]
- **4.1 CI/CD 워크플로우 (backend-ci.yml)** (C:\project\tenopa proposer\PRE_RESTRUCTURING_DIAGNOSIS.md) -- 2 connections
  - -> has_code_example -> [[yaml]]
  - <- contains <- [[4]]
- **4.2 docker-compose.yml 경로 업데이트** (C:\project\tenopa proposer\PRE_RESTRUCTURING_DIAGNOSIS.md) -- 2 connections
  - -> has_code_example -> [[yaml]]
  - <- contains <- [[4]]
- **4.3 .gitignore 업데이트** (C:\project\tenopa proposer\PRE_RESTRUCTURING_DIAGNOSIS.md) -- 2 connections
  - -> has_code_example -> [[gitignore]]
  - <- contains <- [[4]]
- **backend-ci.yml (⚠️ 중요)** (C:\project\tenopa proposer\PRE_RESTRUCTURING_DIAGNOSIS.md) -- 2 connections
  - -> has_code_example -> [[yaml]]
  - <- contains <- [[22-github-actions-cicd]]
- **docker-compose.yml (⚠️ 상대 경로 의존)** (C:\project\tenopa proposer\PRE_RESTRUCTURING_DIAGNOSIS.md) -- 2 connections
  - -> has_code_example -> [[yaml]]
  - <- contains <- [[23-docker]]
- **Dockerfile (⚠️ 상대 경로 의존)** (C:\project\tenopa proposer\PRE_RESTRUCTURING_DIAGNOSIS.md) -- 2 connections
  - -> has_code_example -> [[dockerfile]]
  - <- contains <- [[23-docker]]
- **frontend-ci.yml (✅ 안전)** (C:\project\tenopa proposer\PRE_RESTRUCTURING_DIAGNOSIS.md) -- 2 connections
  - -> has_code_example -> [[yaml]]
  - <- contains <- [[22-github-actions-cicd]]
- **dockerfile** (C:\project\tenopa proposer\PRE_RESTRUCTURING_DIAGNOSIS.md) -- 1 connections
  - <- has_code_example <- [[dockerfile]]
- **gitignore** (C:\project\tenopa proposer\PRE_RESTRUCTURING_DIAGNOSIS.md) -- 1 connections
  - <- has_code_example <- [[43-gitignore]]
- **toml** (C:\project\tenopa proposer\PRE_RESTRUCTURING_DIAGNOSIS.md) -- 1 connections
  - <- has_code_example <- [[24-pyprojecttoml]]
- **2.1 Python 임포트 경로 의존성** (C:\project\tenopa proposer\PRE_RESTRUCTURING_DIAGNOSIS.md) -- 1 connections
  - <- contains <- [[2]]
- **2.5 설정 파일 및 .env** (C:\project\tenopa proposer\PRE_RESTRUCTURING_DIAGNOSIS.md) -- 1 connections
  - <- contains <- [[2]]

## Internal Relationships
- 2. 영향도 분석 -> contains -> 2.1 Python 임포트 경로 의존성 [EXTRACTED]
- 2. 영향도 분석 -> contains -> 2.2 GitHub Actions CI/CD 워크플로우 [EXTRACTED]
- 2. 영향도 분석 -> contains -> 2.3 Docker 설정 [EXTRACTED]
- 2. 영향도 분석 -> contains -> 2.4 pyproject.toml 빌드 설정 [EXTRACTED]
- 2. 영향도 분석 -> contains -> 2.5 설정 파일 및 .env [EXTRACTED]
- 2.2 GitHub Actions CI/CD 워크플로우 -> contains -> backend-ci.yml (⚠️ 중요) [EXTRACTED]
- 2.2 GitHub Actions CI/CD 워크플로우 -> contains -> frontend-ci.yml (✅ 안전) [EXTRACTED]
- 2.3 Docker 설정 -> contains -> Dockerfile (⚠️ 상대 경로 의존) [EXTRACTED]
- 2.3 Docker 설정 -> contains -> docker-compose.yml (⚠️ 상대 경로 의존) [EXTRACTED]
- 2.4 pyproject.toml 빌드 설정 -> has_code_example -> toml [EXTRACTED]
- 4. 상세 변경 체크리스트 -> contains -> 4.1 CI/CD 워크플로우 (backend-ci.yml) [EXTRACTED]
- 4. 상세 변경 체크리스트 -> contains -> 4.2 docker-compose.yml 경로 업데이트 [EXTRACTED]
- 4. 상세 변경 체크리스트 -> contains -> 4.3 .gitignore 업데이트 [EXTRACTED]
- 4.1 CI/CD 워크플로우 (backend-ci.yml) -> has_code_example -> yaml [EXTRACTED]
- 4.2 docker-compose.yml 경로 업데이트 -> has_code_example -> yaml [EXTRACTED]
- 4.3 .gitignore 업데이트 -> has_code_example -> gitignore [EXTRACTED]
- backend-ci.yml (⚠️ 중요) -> has_code_example -> yaml [EXTRACTED]
- docker-compose.yml (⚠️ 상대 경로 의존) -> has_code_example -> yaml [EXTRACTED]
- Dockerfile (⚠️ 상대 경로 의존) -> has_code_example -> dockerfile [EXTRACTED]
- frontend-ci.yml (✅ 안전) -> has_code_example -> yaml [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 yaml, 2. 영향도 분석, 2.2 GitHub Actions CI/CD 워크플로우를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 PRE_RESTRUCTURING_DIAGNOSIS.md이다.

### Key Facts
- backend-ci.yml (⚠️ 중요) ```yaml Line 7-8, 15-16: 트리거 경로 on: push: paths: - "app/**"           ← ❌ 수정 필요 - "tests/**"         ← ❌ 수정 필요 ```
- 2.1 Python 임포트 경로 의존성
- **파일**: `.github/workflows/*.yml`
- Dockerfile (⚠️ 상대 경로 의존) ```dockerfile Line 12: 의존성 복사 COPY pyproject.toml uv.lock ./
- 4.1 CI/CD 워크플로우 (backend-ci.yml)
