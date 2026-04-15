# Document Ingestion 배포 준비도 평가 (Deployment Readiness Assessment) & python
Cohesion: 0.12 | Nodes: 22

## Key Nodes
- **Document Ingestion 배포 준비도 평가 (Deployment Readiness Assessment)** (C:\project\tenopa proposer\-agent-master\docs\04-report\DEPLOYMENT_READINESS.md) -- 19 connections
  - -> contains -> [[1-excellent]]
  - -> contains -> [[2-excellent]]
  - -> contains -> [[3-api-complete]]
  - -> contains -> [[4-good]]
  - -> contains -> [[5-robust]]
  - -> contains -> [[6-configured]]
  - -> contains -> [[1-dev-mode-critical]]
  - -> contains -> [[2-high]]
  - -> contains -> [[3-high]]
  - -> contains -> [[4-medium]]
  - -> contains -> [[5-cors-medium]]
  - -> contains -> [[phase-1-e2e-supabase]]
  - -> contains -> [[phase-2]]
  - -> contains -> [[phase-3]]
  - -> contains -> [[pre-deployment]]
  - -> contains -> [[deployment]]
  - -> contains -> [[post-deployment-1]]
  - -> contains -> [[railway]]
  - -> contains -> [[docker]]
- **python** (C:\project\tenopa proposer\-agent-master\docs\04-report\DEPLOYMENT_READINESS.md) -- 5 connections
  - <- has_code_example <- [[6-configured]]
  - <- has_code_example <- [[1-dev-mode-critical]]
  - <- has_code_example <- [[2-high]]
  - <- has_code_example <- [[3-high]]
  - <- has_code_example <- [[5-cors-medium]]
- **bash** (C:\project\tenopa proposer\-agent-master\docs\04-report\DEPLOYMENT_READINESS.md) -- 3 connections
  - <- has_code_example <- [[4-medium]]
  - <- has_code_example <- [[railway]]
  - <- has_code_example <- [[docker]]
- **1. Dev Mode 비활성화 🔴 CRITICAL** (C:\project\tenopa proposer\-agent-master\docs\04-report\DEPLOYMENT_READINESS.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[document-ingestion-deployment-readiness-assessment]]
- **2. 필수 환경변수 검증 🟡 HIGH** (C:\project\tenopa proposer\-agent-master\docs\04-report\DEPLOYMENT_READINESS.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[document-ingestion-deployment-readiness-assessment]]
- **3. 헬스 체크 엔드포인트 추가 🟡 HIGH** (C:\project\tenopa proposer\-agent-master\docs\04-report\DEPLOYMENT_READINESS.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[document-ingestion-deployment-readiness-assessment]]
- **4. 로깅 포맷 프로덕션화 🟡 MEDIUM** (C:\project\tenopa proposer\-agent-master\docs\04-report\DEPLOYMENT_READINESS.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[document-ingestion-deployment-readiness-assessment]]
- **5. CORS 설정 업데이트 🟡 MEDIUM** (C:\project\tenopa proposer\-agent-master\docs\04-report\DEPLOYMENT_READINESS.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[document-ingestion-deployment-readiness-assessment]]
- **6. 환경 설정 ✅ CONFIGURED** (C:\project\tenopa proposer\-agent-master\docs\04-report\DEPLOYMENT_READINESS.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[document-ingestion-deployment-readiness-assessment]]
- **Docker 배포 (예시)** (C:\project\tenopa proposer\-agent-master\docs\04-report\DEPLOYMENT_READINESS.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[document-ingestion-deployment-readiness-assessment]]
- **Railway 배포 (예시)** (C:\project\tenopa proposer\-agent-master\docs\04-report\DEPLOYMENT_READINESS.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[document-ingestion-deployment-readiness-assessment]]
- **1. 코드 품질 ✅ EXCELLENT** (C:\project\tenopa proposer\-agent-master\docs\04-report\DEPLOYMENT_READINESS.md) -- 1 connections
  - <- contains <- [[document-ingestion-deployment-readiness-assessment]]
- **2. 데이터베이스 ✅ EXCELLENT** (C:\project\tenopa proposer\-agent-master\docs\04-report\DEPLOYMENT_READINESS.md) -- 1 connections
  - <- contains <- [[document-ingestion-deployment-readiness-assessment]]
- **3. API 엔드포인트 ✅ COMPLETE** (C:\project\tenopa proposer\-agent-master\docs\04-report\DEPLOYMENT_READINESS.md) -- 1 connections
  - <- contains <- [[document-ingestion-deployment-readiness-assessment]]
- **4. 보안 설정 ✅ GOOD** (C:\project\tenopa proposer\-agent-master\docs\04-report\DEPLOYMENT_READINESS.md) -- 1 connections
  - <- contains <- [[document-ingestion-deployment-readiness-assessment]]
- **5. 에러 처리 ✅ ROBUST** (C:\project\tenopa proposer\-agent-master\docs\04-report\DEPLOYMENT_READINESS.md) -- 1 connections
  - <- contains <- [[document-ingestion-deployment-readiness-assessment]]
- **Deployment** (C:\project\tenopa proposer\-agent-master\docs\04-report\DEPLOYMENT_READINESS.md) -- 1 connections
  - <- contains <- [[document-ingestion-deployment-readiness-assessment]]
- **Phase 1: E2E 테스트 (실제 Supabase)** (C:\project\tenopa proposer\-agent-master\docs\04-report\DEPLOYMENT_READINESS.md) -- 1 connections
  - <- contains <- [[document-ingestion-deployment-readiness-assessment]]
- **Phase 2: 성능 테스트** (C:\project\tenopa proposer\-agent-master\docs\04-report\DEPLOYMENT_READINESS.md) -- 1 connections
  - <- contains <- [[document-ingestion-deployment-readiness-assessment]]
- **Phase 3: 부하 테스트** (C:\project\tenopa proposer\-agent-master\docs\04-report\DEPLOYMENT_READINESS.md) -- 1 connections
  - <- contains <- [[document-ingestion-deployment-readiness-assessment]]
- **Post-Deployment (배포 후 1시간)** (C:\project\tenopa proposer\-agent-master\docs\04-report\DEPLOYMENT_READINESS.md) -- 1 connections
  - <- contains <- [[document-ingestion-deployment-readiness-assessment]]
- **Pre-Deployment (배포 전)** (C:\project\tenopa proposer\-agent-master\docs\04-report\DEPLOYMENT_READINESS.md) -- 1 connections
  - <- contains <- [[document-ingestion-deployment-readiness-assessment]]

## Internal Relationships
- 1. Dev Mode 비활성화 🔴 CRITICAL -> has_code_example -> python [EXTRACTED]
- 2. 필수 환경변수 검증 🟡 HIGH -> has_code_example -> python [EXTRACTED]
- 3. 헬스 체크 엔드포인트 추가 🟡 HIGH -> has_code_example -> python [EXTRACTED]
- 4. 로깅 포맷 프로덕션화 🟡 MEDIUM -> has_code_example -> bash [EXTRACTED]
- 5. CORS 설정 업데이트 🟡 MEDIUM -> has_code_example -> python [EXTRACTED]
- 6. 환경 설정 ✅ CONFIGURED -> has_code_example -> python [EXTRACTED]
- Docker 배포 (예시) -> has_code_example -> bash [EXTRACTED]
- Document Ingestion 배포 준비도 평가 (Deployment Readiness Assessment) -> contains -> 1. 코드 품질 ✅ EXCELLENT [EXTRACTED]
- Document Ingestion 배포 준비도 평가 (Deployment Readiness Assessment) -> contains -> 2. 데이터베이스 ✅ EXCELLENT [EXTRACTED]
- Document Ingestion 배포 준비도 평가 (Deployment Readiness Assessment) -> contains -> 3. API 엔드포인트 ✅ COMPLETE [EXTRACTED]
- Document Ingestion 배포 준비도 평가 (Deployment Readiness Assessment) -> contains -> 4. 보안 설정 ✅ GOOD [EXTRACTED]
- Document Ingestion 배포 준비도 평가 (Deployment Readiness Assessment) -> contains -> 5. 에러 처리 ✅ ROBUST [EXTRACTED]
- Document Ingestion 배포 준비도 평가 (Deployment Readiness Assessment) -> contains -> 6. 환경 설정 ✅ CONFIGURED [EXTRACTED]
- Document Ingestion 배포 준비도 평가 (Deployment Readiness Assessment) -> contains -> 1. Dev Mode 비활성화 🔴 CRITICAL [EXTRACTED]
- Document Ingestion 배포 준비도 평가 (Deployment Readiness Assessment) -> contains -> 2. 필수 환경변수 검증 🟡 HIGH [EXTRACTED]
- Document Ingestion 배포 준비도 평가 (Deployment Readiness Assessment) -> contains -> 3. 헬스 체크 엔드포인트 추가 🟡 HIGH [EXTRACTED]
- Document Ingestion 배포 준비도 평가 (Deployment Readiness Assessment) -> contains -> 4. 로깅 포맷 프로덕션화 🟡 MEDIUM [EXTRACTED]
- Document Ingestion 배포 준비도 평가 (Deployment Readiness Assessment) -> contains -> 5. CORS 설정 업데이트 🟡 MEDIUM [EXTRACTED]
- Document Ingestion 배포 준비도 평가 (Deployment Readiness Assessment) -> contains -> Phase 1: E2E 테스트 (실제 Supabase) [EXTRACTED]
- Document Ingestion 배포 준비도 평가 (Deployment Readiness Assessment) -> contains -> Phase 2: 성능 테스트 [EXTRACTED]
- Document Ingestion 배포 준비도 평가 (Deployment Readiness Assessment) -> contains -> Phase 3: 부하 테스트 [EXTRACTED]
- Document Ingestion 배포 준비도 평가 (Deployment Readiness Assessment) -> contains -> Pre-Deployment (배포 전) [EXTRACTED]
- Document Ingestion 배포 준비도 평가 (Deployment Readiness Assessment) -> contains -> Deployment [EXTRACTED]
- Document Ingestion 배포 준비도 평가 (Deployment Readiness Assessment) -> contains -> Post-Deployment (배포 후 1시간) [EXTRACTED]
- Document Ingestion 배포 준비도 평가 (Deployment Readiness Assessment) -> contains -> Railway 배포 (예시) [EXTRACTED]
- Document Ingestion 배포 준비도 평가 (Deployment Readiness Assessment) -> contains -> Docker 배포 (예시) [EXTRACTED]
- Railway 배포 (예시) -> has_code_example -> bash [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Document Ingestion 배포 준비도 평가 (Deployment Readiness Assessment), python, bash를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 DEPLOYMENT_READINESS.md이다.

### Key Facts
- **작성일**: 2026-04-02 **기능**: document_ingestion (인트라넷 문서 수집 파이프라인) **평가 대상**: CHECK 단계 완료 후 ACT 단계 진행 가능 여부
- 6. 환경 설정 ✅ CONFIGURED **파일**: `app/config.py` ```python ✅ 프로덕션 환경 감지: environment="production" ✅ 민감한 설정 환경변수로 분리: - anthropic_api_key - supabase_url, supabase_service_role_key - azure_ad_* (인증) ✅ 로깅 설정 분리 (JSON/text) ✅ CORS 설정 (localhost 기본값) ```
- 4. 로깅 포맷 프로덕션화 🟡 MEDIUM **현재**: `log_format: text` (개발 모드용) **프로덕션**: JSON 포맷으로 변경 ```bash .env (프로덕션) LOG_FORMAT=json LOG_LEVEL=INFO  # DEBUG에서 INFO로 변경 ```
- 2. 필수 환경변수 검증 🟡 HIGH **필요한 검증 추가**: ```python def validate_env_on_startup(): """프로덕션 환경에서 필수 환경변수 검증""" if settings.is_production: required = [ "ANTHROPIC_API_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "AZURE_AD_TENANT_ID", "AZURE_AD_CLIENT_ID", "AZURE_AD_CLIENT_SECRET", ] missing = [k for…
- 3. 헬스 체크 엔드포인트 추가 🟡 HIGH **필요함**: 배포 모니터링 및 로드 밸런서 상태 확인용 ```python @app.get("/health") async def health_check(): """헬스 체크 엔드포인트""" return { "status": "healthy", "service": "proposal-agent", "timestamp": datetime.now(timezone.utc).isoformat(), }
