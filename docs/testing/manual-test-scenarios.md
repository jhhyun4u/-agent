# 수동 테스트 시나리오 (Manual Test Scenarios)

**목적**: 구현된 핵심 기능의 정상 작동 여부를 사용자가 직접 확인  
**대상**: 개발자, PM, QA  
**작성일**: 2026-04-08  

---

## 📋 구현된 핵심 기능 리스트

### Phase 1: 문서 섭취 (Document Ingestion) ✅

| 기능 | 상태 | 파일 | 설명 |
|------|------|------|------|
| 파일 업로드 | ✅ | `routes_documents.py` | PDF/HWP/HWPX/DOCX/DOC 파일 Supabase Storage에 저장 |
| 문서 목록 조회 | ✅ | `routes_documents.py` | 필터링/정렬/페이지네이션 지원 |
| 문서 상세 조회 | ✅ | `routes_documents.py` | 메타데이터 + 추출된 텍스트 조회 |
| 자동 텍스트 추출 | ✅ | `document_ingestion.py` | PyPDF2, python-docx로 텍스트 자동 추출 |
| AI 청킹 & 임베딩 | ✅ | `document_ingestion.py` | Claude API로 의미 있는 단위로 분할 + pgvector 저장 |
| 문서 재처리 | ✅ | `routes_documents.py` | 실패한 문서 재시도 |
| 문서 삭제 | ✅ | `routes_documents.py` | Storage + DB에서 완전 삭제 |
| **프론트엔드 UI** | ✅ | `page.tsx` | 문서 업로드/목록/상세/삭제 페이지 |

### Phase 2: CI/CD 파이프라인 ✅

| 기능 | 상태 | 파일 | 설명 |
|------|------|------|------|
| 백엔드 CI | ✅ | `backend-ci.yml` | pytest + ruff + black + mypy + Codecov |
| 프론트엔드 CI | ✅ | `frontend-ci.yml` | ESLint + TypeScript + Next.js 빌드 |
| E2E 테스트 | ✅ | `test_documents_e2e.spec.ts` | Playwright 기반 15개 시나리오 |
| 성능 테스트 | ✅ | `test_documents_performance.py` | 응답시간, 메모리, 처리량 측정 |
| 자동 배포 | ✅ | `*-ci.yml` | develop/main → Railway/Vercel |
| 알림 | ✅ | `*-ci.yml` | Slack 배포 상태 알림 |

### Phase 3: 모니터링 & 로깅 ✅

| 기능 | 상태 | 파일 | 설명 |
|------|------|------|------|
| Prometheus 메트릭 수집 | ✅ | `docker-compose.monitoring.yml` | 15s 간격, 7개 job |
| Grafana 대시보드 | ✅ | `prometheus.yml` | 시스템, API, 데이터베이스 메트릭 시각화 |
| 자동 알림 (36개 규칙) | ✅ | `prometheus-alerts.yml` | Slack/PagerDuty 연동 |
| ELK Stack (로깅) | ✅ | `docker-compose.logging.yml` | Elasticsearch + Kibana |
| 로그 파싱 & 필터링 | ✅ | `logstash.conf` | 민감정보 마스킹, 구조화 |

### Phase 4: 백업 & 재해복구 ✅

| 기능 | 상태 | 파일 | 설명 |
|------|------|------|------|
| 자동 백업 | ✅ | `backup-disaster-recovery.md` | pg_dump, S3 크로스 리전, Git 미러 |
| 복구 절차 | ✅ | `backup-disaster-recovery.md` | 4가지 시나리오별 단계별 가이드 |
| RTO/RPO 목표 | ✅ | `backup-disaster-recovery.md` | 데이터베이스 RTO 1시간, RPO 15분 |

### Phase 5: 교육 & 문서 ✅

| 기능 | 상태 | 파일 | 설명 |
|------|------|------|------|
| 사용자 매뉴얼 | ✅ | `user-handbook.md` | AI 협업 6단계, FAQ, 문제 해결 |
| 관리자 가이드 | ✅ | `admin-guide.md` | 시스템 관리, 모니터링, 성능 튜닝 |
| API 문서 | ✅ | `documents_api.md` + `documents_openapi.yaml` | OpenAPI 3.1 스펙 |

---

## 🧪 테스트 시나리오 3가지

### 시나리오 1: 문서 업로드 & API 검증 (백엔드)

**목적**: Document Ingestion API의 정상 작동 확인  
**예상 시간**: 5분  
**준비물**: 
- Python 3.11+
- curl 또는 Postman
- 테스트 PDF 파일 (또는 샘플 생성)
- 로컬 백엔드 실행 (또는 Railway URL)

#### 단계 1: 테스트 PDF 생성
```bash
# 간단한 PDF 생성 (Python)
python3 << 'EOF'
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

c = canvas.Canvas("/tmp/test_document.pdf", pagesize=letter)
c.drawString(100, 750, "Test Proposal Document")
c.drawString(100, 730, "This is a sample document for testing.")
c.drawString(100, 710, "Created on 2026-04-08")
c.save()
print("PDF created: /tmp/test_document.pdf")
EOF
```

#### 단계 2: API를 통해 파일 업로드
```bash
# 환경 변수 설정
export API_URL="http://localhost:8000"  # 또는 Railway URL
export API_TOKEN="your_jwt_token"       # Supabase 인증 토큰

# 파일 업로드
curl -X POST "${API_URL}/api/documents/upload" \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/tmp/test_document.pdf" \
  -F "doc_type=제안서" \
  -F "doc_subtype=기술제안" \
  -v

# 응답 예시:
# {
#   "id": "doc-abc123",
#   "filename": "test_document.pdf",
#   "org_id": "org-001",
#   "processing_status": "pending",
#   "created_at": "2026-04-08T10:30:00Z"
# }
```

#### 단계 3: 업로드된 문서 목록 조회
```bash
# 문서 목록 조회
curl -X GET "${API_URL}/api/documents" \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -H "Content-Type: application/json" \
  -v

# 응답 필드 확인:
# {
#   "items": [
#     {
#       "id": "doc-abc123",
#       "filename": "test_document.pdf",
#       "processing_status": "extracting|chunking|completed",
#       "total_chars": 1250,
#       "chunk_count": 5
#     }
#   ],
#   "total": 1,
#   "limit": 20,
#   "offset": 0
# }
```

#### 단계 4: 상세 정보 조회
```bash
# 문서 상세 조회 (위에서 받은 document_id 사용)
DOC_ID="doc-abc123"
curl -X GET "${API_URL}/api/documents/${DOC_ID}" \
  -H "Authorization: Bearer ${API_TOKEN}" \
  -H "Content-Type: application/json" \
  -v

# 응답 확인 사항:
# ✓ extracted_text가 null이 아닌 값 포함 (텍스트 추출됨)
# ✓ processing_status가 "completed"
# ✓ chunk_count > 0 (청킹 완료)
```

#### ✅ 성공 기준
```
□ 단계 1: PDF 파일 생성됨
□ 단계 2: 업로드 응답 status 201 또는 200
□ 단계 3: 문서 목록에 업로드한 파일이 나타남
□ 단계 4: extracted_text에 문서 내용이 포함됨
□ 단계 4: processing_status = "completed"
□ 단계 4: chunk_count >= 1

모두 완료 시 → ✅ 시나리오 1 성공
```

---

### 시나리오 2: 프론트엔드 UI 테스트 (문서 관리 페이지)

**목적**: Next.js 프론트엔드 Document 관리 페이지의 정상 작동 확인  
**예상 시간**: 10분  
**준비물**:
- 브라우저 (Chrome, Firefox, Edge)
- 로컬 프론트엔드 실행: `npm run dev` (port 3000)
- 로그인 가능한 테스트 계정

#### 단계 1: 페이지 접속 및 로드 확인
```
1. 브라우저 열기 → http://localhost:3000
2. 로그인 (Azure AD 또는 이메일)
3. 좌측 메뉴 → "KB" → "문서 관리"
4. URL: http://localhost:3000/kb/documents

✓ 확인 항목:
  - 페이지 로드 완료 (흰색 빈 화면 아님)
  - 제목: "인트라넷 문서" 또는 "문서 관리" 표시
  - 버튼 보임: "새 문서 업로드", "필터", "정렬" 등
```

#### 단계 2: 파일 업로드 테스트
```
1. "새 문서 업로드" 또는 파일 업로드 버튼 클릭
2. 파일 선택 대화 열림
3. /tmp/test_document.pdf 선택
4. 문서 유형 선택: "제안서"
5. "업로드" 클릭

✓ 확인 항목:
  - 업로드 진행 표시 (프로그레스 바 또는 "처리 중...")
  - 완료 후 목록에 파일 나타남
  - 파일명: "test_document.pdf" 표시
  - 상태: "처리 중" → "완료" 변경 (몇 초 후)
```

#### 단계 3: 목록 조회 및 필터링
```
1. 문서 목록 페이지 (자동 새로고침)
2. 업로드한 "test_document.pdf" 카드 보임

✓ 확인 항목:
  - 문서 카드 표시 (제목, 상태, 날짜)
  - 상태 배지: "완료" (녹색) 또는 "처리 중" (파란색)
  - 파일 크기, 생성 날짜 표시

3. 필터 테스트 (있는 경우):
  - "상태" 필터 → "완료" 선택
  - 목록 업데이트 확인
  - 다른 문서는 필터링됨
```

#### 단계 4: 문서 상세 보기
```
1. 문서 카드 클릭 또는 "상세보기" 버튼
2. 상세 페이지 열림

✓ 확인 항목:
  - 문서 정보 표시 (파일명, 상태, 생성일)
  - 추출된 텍스트 미리보기 (있는 경우)
  - 액션 버튼: "다운로드", "삭제", "재처리" 등
```

#### ✅ 성공 기준
```
□ 단계 1: 페이지 정상 로드, 제목 표시
□ 단계 2: 파일 업로드 완료, 목록에 나타남
□ 단계 2: 상태가 "처리 중" → "완료"로 변경
□ 단계 3: 문서 카드에 올바른 정보 표시
□ 단계 3: 필터링 정상 작동
□ 단계 4: 상세 페이지 로드, 정보 표시

모두 완료 시 → ✅ 시나리오 2 성공
```

---

### 시나리오 3: CI/CD 파이프라인 동작 확인

**목적**: GitHub Actions 자동 배포 파이프라인의 정상 작동 확인  
**예상 시간**: 15~30분 (배포 대기 시간 포함)  
**준비물**:
- GitHub 저장소 접근 권한
- 로컬 코드 변경 가능
- Railway/Vercel 대시보드 접근

#### 단계 1: 백엔드 CI/CD 테스트 (GitHub Actions)
```bash
# 1. 로컬에서 간단한 변경 (테스트용)
cd /project/tenopa\ proposer/-agent-master

# 2. 파일 수정 (예: 버전 업데이트)
echo "# Test run at $(date)" >> README.md

# 3. 변경 커밋
git add README.md
git commit -m "test: CI/CD pipeline verification"

# 4. develop 브랜치에 푸시
git push origin develop

# 5. GitHub Actions 모니터링
# GitHub → Actions → 최신 워크플로우 클릭
```

**GitHub Actions 진행 상황 확인**:
```
┌─────────────────────────────────────────┐
│ Backend CI/CD 워크플로우 진행 상황       │
├─────────────────────────────────────────┤
│ ✓ Checkout code (1-2초)                │
│ ✓ Set up Python (5-10초)               │
│ ✓ Install dependencies (30-60초)       │
│ ✓ Lint with ruff (10-20초)             │
│ ✓ Format check with black (10-20초)    │
│ ✓ Type check with mypy (20-30초)       │
│ ✓ Run pytest (60-120초)                │
│ ⏳ Build Docker image (60-90초)        │
│ ⏳ Deploy to Staging (30-60초)         │
│ ⏳ Slack notification (5초)             │
└─────────────────────────────────────────┘
```

#### 단계 2: 배포 결과 확인 (Railway)
```
1. Railway 대시보드 접속 (https://railway.app)
2. 프로젝트 선택 → Deployments
3. 최신 배포 보기

✓ 확인 항목:
  - Status: "Success" (녹색) 또는 "Failed" (빨간색)
  - Deployment 시간: 1-5분
  - Logs 탭: 배포 로그 확인
  - 마지막 줄: "Deployment successful" 또는 에러 메시지
```

#### 단계 3: API 헬스 체크
```bash
# 배포된 API 상태 확인
curl https://api.tenopa.io/health -v

# 응답 예시:
# {
#   "status": "healthy",
#   "version": "4.9.0",
#   "database": "connected",
#   "redis": "connected"
# }
```

#### 단계 4: Slack 알림 확인
```
1. Slack 워크스페이스 접속
2. #deployments 또는 #alerts 채널 확인
3. 최근 메시지 보기

✓ 확인 항목:
  - 배포 완료 알림 메시지
  - 커밋 정보 표시
  - 타임스탬프: 배포 시간과 일치
  - 상태: ✅ (성공) 또는 ❌ (실패)
```

#### 단계 5: 프론트엔드 CI/CD 테스트 (선택)
```bash
# 1. 프론트엔드 코드 수정
cd frontend
echo "// Test build at $(date)" >> app/layout.tsx

# 2. 커밋 및 푸시
git add app/layout.tsx
git commit -m "test: Frontend CI/CD verification"
git push origin develop

# 3. GitHub Actions 모니터링
# GitHub → Actions → frontend-ci.yml
```

**진행 상황 확인**:
```
✓ Lint (ESLint)
✓ Type check (TypeScript)
✓ Build (Next.js)
✓ E2E tests (Playwright)
⏳ Deploy to Vercel (Preview URL 생성)
```

#### ✅ 성공 기준
```
□ 단계 1: Git 푸시 완료
□ 단계 2: GitHub Actions 워크플로우 시작 및 완료
□ 단계 2: 모든 단계 ✅ 완료 (실패 없음)
□ 단계 3: Railway 배포 상태 "Success"
□ 단계 4: API 헬스 체크 응답 "healthy"
□ 단계 5: Slack 알림 수신 (배포 완료 메시지)

모두 완료 시 → ✅ 시나리오 3 성공
```

---

## 📊 테스트 결과 기록 양식

테스트 실행 후 아래 양식을 작성하여 저장하세요:

```markdown
# 테스트 실행 결과 (2026-04-08)

## 시나리오 1: 문서 업로드 & API 검증
- 실행 시간: 14:30 ~ 14:35 (5분)
- 결과: ✅ 성공 / ❌ 실패
- 완료된 체크리스트:
  - ✅ PDF 파일 생성
  - ✅ API 업로드 성공
  - ✅ 목록 조회 정상
  - ✅ 상세 정보 조회 정상
  - ✅ extracted_text 확인
- 이슈 사항: (있으면 기록)
- 메모: (추가 사항)

## 시나리오 2: 프론트엔드 UI 테스트
- 실행 시간: 14:35 ~ 14:45 (10분)
- 결과: ✅ 성공 / ❌ 실패
- 완료된 체크리스트:
  - ✅ 페이지 로드 정상
  - ✅ 파일 업로드 정상
  - ✅ 상태 변경 정상 (처리중 → 완료)
  - ✅ 필터링 정상
  - ✅ 상세 보기 정상
- 이슈 사항: (있으면 기록)
- 메모: (추가 사항)

## 시나리오 3: CI/CD 파이프라인
- 실행 시간: 14:45 ~ 15:15 (30분)
- 결과: ✅ 성공 / ❌ 실패
- 완료된 체크리스트:
  - ✅ GitHub Actions 시작
  - ✅ 모든 단계 완료
  - ✅ Railway 배포 성공
  - ✅ API 헬스 체크 통과
  - ✅ Slack 알림 수신
- 이슈 사항: (있으면 기록)
- 메모: (추가 사항)

## 총평
- 전체 결과: ✅ 성공 / ❌ 일부 실패
- 발견된 버그: (있으면 기록)
- 개선 제안: (있으면 기록)
```

---

## 🆘 문제 발생 시

### 시나리오 1 실패 케이스

**문제**: "401 Unauthorized"
```
해결: API_TOKEN이 유효한지 확인
- Supabase 콘솔 → Authentication
- JWT 토큰 복사 (또는 새로 발급)
- curl 명령에서 Bearer 토큰 확인
```

**문제**: "415 Unsupported Media Type"
```
해결: Content-Type 확인
- 올바른 방식:
  curl -F "file=@..." (자동으로 multipart/form-data 설정)
- 잘못된 방식:
  curl -H "Content-Type: application/json" (JSON으로 파일 전송 불가)
```

### 시나리오 2 실패 케이스

**문제**: "페이지가 로드되지 않음 (흰색 화면)"
```
해결:
1. 브라우저 콘솔 확인 (F12 → Console)
2. 에러 메시지 확인
3. npm run dev 로그 확인
4. 환경변수 확인 (.env.local)
```

**문제**: "문서가 업로드되지 않음"
```
해결:
1. 파일 크기 확인 (최대 500MB)
2. 파일 형식 확인 (PDF, HWP, DOCX 등)
3. 네트워크 요청 모니터링 (F12 → Network)
4. API 로그 확인 (백엔드 터미널)
```

### 시나리오 3 실패 케이스

**문제**: "GitHub Actions 실패"
```
해결:
1. GitHub Actions 로그 확인 (상세 단계별 에러)
2. 일반적 원인:
   - 의존성 설치 실패 → pip/npm 업데이트
   - 테스트 실패 → pytest 로그 확인
   - 빌드 실패 → Docker 로그 확인
```

**문제**: "Railway 배포 실패"
```
해결:
1. Railway 대시보드 → Deployments → 실패한 배포 클릭
2. Logs 탭에서 에러 메시지 확인
3. 환경변수 확인 (Variables 탭)
4. Railway 상태 페이지 확인 (https://status.railway.app)
```

---

## 📞 추가 지원

테스트 중 문제가 발생하면:

| 문제 종류 | 연락처 | 응답 시간 |
|---------|--------|---------|
| API 관련 | ops-support@tenopa.io | 2시간 |
| 프론트엔드 | frontend-team@tenopa.io | 1시간 |
| CI/CD | devops@tenopa.io | 30분 |
| 긴급 (24/7) | Slack: #ops-oncall | 15분 |

---

**마지막 수정**: 2026-04-08  
**버전**: 1.0

