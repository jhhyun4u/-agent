# 디렉토리 구조 정리 전 종합 진단 보고서

**작성일**: 2026-04-16  
**상태**: 진단 완료 - 구조화 전 사전 검증 단계  
**평가**: ✅ 안전하게 구조화 가능 (조건부)

---

## 1. 현재 상황 분석

### 1.1 폴더 구조 문제점
```
c:\project\tenopa proposer\
├── -agent-master\           ← 모든 소스코드와 설정이 여기 있음
│   ├── app\                 ← Python 백엔드
│   ├── frontend\            ← Next.js 프론트엔드
│   ├── tests\               ← 테스트
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── .github\workflows\   ← CI/CD
│   └── ...
├── mindvault-out\           ← 임시 출력 (1.2GB)
├── output\                  ← 임시 출력
├── tmp_screenshots\         ← 임시 스크린샷
└── (루트 파일들 없음)
```

**문제점**:
- 모든 소스코드가 `-agent-master/` 폴더에 격리됨
- 루트 레벨에 임시 폴더 3개로 지저분함
- 표준 프로젝트 구조와 맞지 않음

---

## 2. 영향도 분석

### 2.1 Python 임포트 경로 의존성

**현재 상태**: `from app.main import app` / `from app.api.routes_* import *`

**스캔 결과**:
- 전체 Python 파일 약 930+ 줄에서 `from app` / `import app` 패턴 사용
- 분류:
  - `app/main.py`: 23개 라우터 임포트 (모두 `from app.api.routes_*` 패턴)
  - `app/graph/`: 40+ 노드 정의 (모두 `from app.` 패턴)
  - `app/api/`: 라우터 간 의존성 (`from app.services`, `from app.models`)
  - `app/services/`: 약 15+ 파일에서 `from app.` 임포트
  - 테스트: `tests/` 약 100+ 파일에서 `from app.` 임포트

**구조 변경 영향**:
- ✅ **파일 이동 후에도 임포트 경로 유지됨** (상대 위치 변경 없음)
  - 예: `from app.api.routes_proposal import router`
  - `-agent-master/` 내에서 `app/` 구조가 유지되면 임포트 경로 동일
- ⚠️ **단, Docker/CI에서 작업 디렉토리 변경 필요** (아래 2.3 참고)

### 2.2 GitHub Actions CI/CD 워크플로우

**파일**: `.github/workflows/*.yml`

#### backend-ci.yml (⚠️ 중요)
```yaml
# Line 7-8, 15-16: 트리거 경로
on:
  push:
    paths:
      - "app/**"           ← ❌ 수정 필요
      - "tests/**"         ← ❌ 수정 필요
```

**변경 필요**:
- `"app/**"` → `"-agent-master/app/**"` 또는 `".github/workflows/backend-ci.yml"` 수정 안 함
- `"tests/**"` → `"-agent-master/tests/**"` (동일)

**다른 명령어들**:
```yaml
# Line 68: ruff check
run: uv run ruff check app tests
# Line 78: pytest
run: uv run pytest tests/ -v --cov=app
# Line 236: bandit
run: bandit -r app
```

**평가**: ✅ 상대 경로이므로 GitHub Actions 실행 디렉토리가 `-agent-master/`이면 자동으로 작동

#### frontend-ci.yml (✅ 안전)
```yaml
# Line 23, 64: working-directory 설정
defaults:
  run:
    working-directory: ./frontend
```

**평가**: ✅ `working-directory`가 명시적으로 `./frontend` 설정 → 상대 경로 사용 → 안전

### 2.3 Docker 설정

#### Dockerfile (⚠️ 상대 경로 의존)
```dockerfile
# Line 12: 의존성 복사
COPY pyproject.toml uv.lock ./

# Line 16: 소스 복사
COPY app/ ./app/

# Line 30: 실행
CMD ["sh", "-c", "uv run uvicorn app.main:app ..."]
```

**현재 상태**: Dockerfile은 `-agent-master/` 내에 있음
- `COPY app/` → `-agent-master/app/` 상대 참조
- `COPY pyproject.toml` → `-agent-master/pyproject.toml` 상대 참조

**구조화 후**:
- ✅ Dockerfile 위치 그대로이면 상대 경로 유지됨
- ✅ `docker build .` 실행 시 자동으로 올바른 경로 참조

#### docker-compose.yml (⚠️ 상대 경로 의존)
```yaml
# Line 16: 스키마 마운트
- ./database/schema_v3.4.sql:/docker-entrypoint-initdb.d/01_schema.sql:ro

# Line 37: app 볼륨
- ./app:/app/app:ro

# Line 54: frontend 볼륨
- ./frontend:/app
```

**문제점**:
- `./database/schema_v3.4.sql` → 루트에서 `database/` 폴더 기대
- `./app` → 루트에서 `app/` 폴더 기대
- 현재: `-agent-master/` 내에 있으므로, 구조화 후 경로 수정 필요

**⚠️ 중요**: `docker-compose.yml`은 프로젝트 루트에서 실행 가정
- 현재: `-agent-master/docker-compose.yml`에서 실행 → 상대 경로가 `-agent-master/` 기준
- 구조화 후: `프로젝트루트/docker-compose.yml`로 이동 가능 → 절대 경로 수정 필요

### 2.4 pyproject.toml 빌드 설정

```toml
[tool.uv]
dev-dependencies = [...]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**평가**: ✅ Python 패키지 경로에 의존하지 않음 (상대적 영향 없음)

### 2.5 설정 파일 및 .env

- `.env.example`: ✅ 하드코딩된 경로 없음 (모두 환경변수)
- `app/config.py`: ✅ 모두 환경변수 참조

---

## 3. 제안된 구조화 방안

### 3.1 최종 구조
```
c:\project\tenopa proposer\
├── backend/          ← app/ 재명명 또는 그대로
│   ├── app/
│   ├── tests/
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── Dockerfile
│   └── ...
├── frontend/         ← 그대로 이동
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.ts
│   └── ...
├── database/         ← 루트 레벨로 이동
│   └── schema_v3.4.sql
├── .github/          ← 루트 레벨로 이동
│   └── workflows/
├── docker-compose.yml    ← 루트에서 실행 가정으로 이동
├── docker-compose.monitoring.yml
├── docker-compose.logging.yml
├── .gitignore        ← 임시 폴더 추가
└── (임시 폴더 정리)
```

**또는** (더 간단한 방식):
```
c:\project\tenopa proposer\
├── app/              ← 현재 -agent-master/app/
├── frontend/         ← 현재 -agent-master/frontend/
├── tests/            ← 현재 -agent-master/tests/
├── pyproject.toml    ← 현재 -agent-master/pyproject.toml
├── Dockerfile        ← 현재 -agent-master/Dockerfile
├── docker-compose.yml    ← 현재 -agent-master/docker-compose.yml
├── .github/          ← 현재 -agent-master/.github/
├── database/         ← 현재 -agent-master/database/
└── .gitignore
```

### 3.2 필수 수정 사항

| 파일 | 현재 경로 | 변경 사항 | 우선순위 |
|------|---------|---------|---------|
| backend-ci.yml | `.github/workflows/` | 경로 트리거 업데이트 (app/** → -agent-master/app/** 또는 상대경로 유지) | 🔴 중요 |
| frontend-ci.yml | `.github/workflows/` | ✅ 수정 불필요 (working-directory 설정됨) | ✅ 안전 |
| Dockerfile | -agent-master/ | ✅ 수정 불필요 (상대 경로 유지) | ✅ 안전 |
| docker-compose.yml | -agent-master/ | ⚠️ 루트로 이동 시 경로 업데이트 필요 | 🟡 조건부 |
| docker-compose.monitoring.yml | -agent-master/ | ⚠️ 루트로 이동 시 경로 업데이트 필요 | 🟡 조건부 |
| docker-compose.logging.yml | -agent-master/ | ⚠️ 루트로 이동 시 경로 업데이트 필요 | 🟡 조건부 |
| app/ Python 임포트 | 전체 | ✅ 수정 불필요 (상대 위치 변경 안 함) | ✅ 안전 |
| .gitignore | -agent-master/ | ⚠️ 루트로 이동 시 임시 폴더 제외 규칙 추가 | 🟡 조건부 |

---

## 4. 상세 변경 체크리스트

### 4.1 CI/CD 워크플로우 (backend-ci.yml)

**현재 코드**:
```yaml
on:
  push:
    branches: [main, develop]
    paths:
      - "app/**"
      - "tests/**"
      - "pyproject.toml"
      - "uv.lock"
      - ".github/workflows/backend-ci.yml"
```

**선택지**:

**옵션 A**: 절대 경로 (현재 -agent-master/ 구조 유지)
```yaml
paths:
  - "-agent-master/app/**"
  - "-agent-master/tests/**"
  - "-agent-master/pyproject.toml"
  - "-agent-master/uv.lock"
  - ".github/workflows/backend-ci.yml"
```

**옵션 B**: 루트 레벨로 완전 이동 (가장 깨끗함)
```yaml
paths:
  - "app/**"
  - "tests/**"
  - "pyproject.toml"
  - "uv.lock"
  - ".github/workflows/backend-ci.yml"
```

**권장**: **옵션 B** (전체 프로젝트를 루트로 정리)

### 4.2 docker-compose.yml 경로 업데이트

**현재 (루트에서 `-agent-master/docker-compose.yml` 실행 경우)**:
```yaml
volumes:
  - ./database/schema_v3.4.sql:/docker-entrypoint-initdb.d/01_schema.sql:ro
  - ./app:/app/app:ro
  - ./frontend:/app
```

**수정 후 (루트에서 `docker-compose.yml` 실행)**:
```yaml
volumes:
  - ./database/schema_v3.4.sql:/docker-entrypoint-initdb.d/01_schema.sql:ro
  - ./app:/app/app:ro
  - ./frontend:/app
```

✅ **변경 없음** (상대 경로가 자동으로 맞춰짐)

### 4.3 .gitignore 업데이트

**추가할 규칙**:
```gitignore
# 임시 폴더
/mindvault-out/
/output/
/tmp_screenshots/

# 개발 환경
.venv/
.env.local
*.pyc
__pycache__/
node_modules/
.next/

# OS
.DS_Store
Thumbs.db
```

---

## 5. 위험도 평가

### 5.1 사전 체크 결과

| 항목 | 위험도 | 설명 |
|------|--------|------|
| **Python 임포트 경로** | ✅ 낮음 | 상대 위치 변경 없음 → 임포트 경로 자동 유지 |
| **Docker 빌드** | ✅ 낮음 | Dockerfile이 app/ 같은 레벨에 있으면 상대 경로 유지 |
| **docker-compose 실행** | ⚠️ 중간 | 루트에서 실행 시 경로 수정 필요 (간단함) |
| **CI/CD 트리거** | 🔴 높음 | backend-ci.yml 경로 반드시 수정 필요 (안 하면 테스트 미실행) |
| **pytest 실행** | ✅ 낮음 | 상대 경로 사용 → 실행 디렉토리가 올바르면 작동 |
| **Node.js 빌드** | ✅ 낮음 | working-directory 명시 → 안전 |

### 5.2 가장 주의할 점

1. **backend-ci.yml 경로 트리거 (필수)**
   - 수정하지 않으면 CI/CD가 트리거되지 않음
   - 결과: main/develop 푸시 시 테스트/빌드 미실행

2. **docker-compose.yml 실행 방식 (선택사항)**
   - 현재: `-agent-master/` 내에서 실행
   - 구조화 후: 루트에서 실행 시 경로 수정 필요

---

## 6. 구현 로드맵

### Phase 1: 안전성 검증 (현재 단계 - ✅ 완료)
- ✅ Python 임포트 패턴 930+ 줄 스캔
- ✅ CI/CD 워크플로우 5개 파일 분석
- ✅ Docker/docker-compose 설정 검증
- ✅ 상대 경로 의존성 매핑
- ✅ 영향도 평가 및 위험도 산정

### Phase 2: 사용자 승인 (다음 단계)
- **사용자 결정 필요**:
  1. 옵션 A: `-agent-master/` 폴더명 유지, CI/CD만 수정
  2. 옵션 B: 전체 루트 레벨로 정리 (권장)

### Phase 3: 자동화 변경 (사용자 승인 후)
- 선택한 옵션에 따라 파일 이동
- CI/CD 워크플로우 경로 업데이트
- docker-compose 경로 업데이트 (필요시)
- .gitignore 생성/업데이트

### Phase 4: 검증 (최종)
- 모든 파일 이동 완료 확인
- GitHub Actions 트리거 테스트
- Docker 빌드 테스트
- docker-compose 실행 테스트
- 각 서비스 헬스체크

---

## 7. 최종 결론

### ✅ 구조화 가능 판정

**기술적 안전성**: **높음 (90%+)**

현재 코드 구조는 상대 경로 중심이므로 파일을 이동해도 대부분의 import/reference가 자동으로 유지됩니다.

### 필수 수정 사항 (구현 전)

1. **backend-ci.yml** - 경로 트리거 업데이트 (필수)
2. **docker-compose.yml** - 루트 이동 시 경로 확인 (조건부)
3. **.gitignore** - 임시 폴더 제외 규칙 추가 (권장)

### 권장 최종 구조

```
c:\project\tenopa proposer\
├── app/
├── frontend/
├── tests/
├── database/
├── .github/workflows/
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── .gitignore
└── (임시 폴더 정리)
```

**예상 효과**:
- ✅ 프로젝트 루트 정리 (임시 폴더 3개 제거)
- ✅ 표준 프로젝트 구조 준수
- ✅ 개발자 접근성 향상
- ✅ CI/CD 가독성 개선

---

## 8. 다음 단계

**사용자 결정 필요**:
- [ ] **옵션 A**: `-agent-master/` 폴더 유지, CI/CD만 수정
- [ ] **옵션 B**: 전체 루트 레벨로 정리 (권장 ⭐)

선택 후 자동화 구현을 진행하겠습니다.
