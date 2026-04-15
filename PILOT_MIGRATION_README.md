# 파일럿 마이그레이션 (MSSQL → Supabase) - 실행 가이드

> **상태:** ✅ 준비 완료  
> **작성일:** 2026-04-11  
> **담당:** 사용자

---

## 🎯 목표

MSSQL 인트라넷 프로젝트 10개를 Supabase로 마이그레이션하고, 벡터 검색 기능이 정상 작동하는지 검증한 후, 전체 마이그레이션을 진행합니다.

---

## 📋 준비된 파일

### 1. 마이그레이션 스크립트

#### A. MSSQL 직접 연결 버전
```
scripts/pilot_migration_10projects.py
```
- **용도:** MSSQL 10.1.3.251에서 직접 데이터 추출
- **대상:** Project_List 테이블의 상위 10개 프로젝트
- **전제:** MSSQL 접근 가능 (내부 네트워크)

#### B. 테스트 데이터 버전 (권장)
```
scripts/pilot_migration_demo.py
```
- **용도:** MSSQL 없이 테스트 데이터로 전체 마이그레이션 워크플로우 검증
- **데이터:** 10개의 실제적인 샘플 프로젝트
- **전제:** 필요 없음 (언제 어디서나 실행 가능)

### 2. 문서

```
docs/PILOT_MIGRATION_GUIDE.md          # 상세 가이드
PILOT_MIGRATION_README.md               # 이 파일
```

---

## 🚀 실행 방법

### Step 1: 환경 변수 설정

`.env` 파일에 다음을 추가하세요:

```env
# ── MSSQL 연결 (스크립트 A 사용 시에만 필요) ──
MSSQL_HOST=10.1.3.251
MSSQL_USER=sa
MSSQL_PASSWORD=<your-password>
MSSQL_DATABASE=intranet

# ── Supabase ──
SUPABASE_URL=https://inuuyaxddgbxexljfykg.supabase.co
SUPABASE_KEY=<anon-key>
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>

# ── OpenAI (임베딩 생성용) ──
OPENAI_API_KEY=<your-openai-api-key>
```

### Step 2: 데이터 미리보기 (권장)

먼저 DRY-RUN 모드로 데이터를 미리 확인하세요:

```bash
# 스크립트 B 사용 (권장: 테스트 데이터, MSSQL 불필요)
python scripts/pilot_migration_demo.py --dry-run

# 또는 스크립트 A 사용 (실제 MSSQL 데이터)
python scripts/pilot_migration_10projects.py --dry-run
```

**출력 예시:**
```
[DRY RUN] 10개 프로젝트 미리보기:

 1. AI 기반 제안서 자동 작성 플랫폼 개발
      발주처: 국방부
      예산: 500,000,000
      팀: AI팀

 2. 대용량 데이터 분석 및 시각화 시스템 구축
      발주처: 과학기술정보통신부
      예산: 750,000,000
      팀: 데이터팀

 ... (8개 더)
```

### Step 3: 실제 마이그레이션 실행

검증 후 실제 마이그레이션을 실행하세요:

```bash
# 스크립트 B 사용 (권장)
python scripts/pilot_migration_demo.py --execute

# 또는 스크립트 A 사용
python scripts/pilot_migration_10projects.py --execute
```

**실행 과정:**
```
━━━ EXECUTE MODE (실제 마이그레이션) ━━━

마이그레이션 시작 (10개 프로젝트)

[1/10] AI 기반 제안서 자동 작성 플랫폼 개발
✓ 프로젝트 삽입: AI 기반 제안서 자동 작성 플랫폼 개발 (ID: abc12345...)
  ✓ 임베딩 생성

[2/10] 대용량 데이터 분석 및 시각화 시스템 구축
✓ 프로젝트 삽입: 대용량 데이터 분석 및 시각화 시스템 구축 (ID: def67890...)
  ✓ 임베딩 생성

... (8개 더)
```

### Step 4: 자동 검증

마이그레이션 후 자동으로 벡터 검색이 테스트됩니다:

```
======================================================================
파일럿 마이그레이션 완료 리포트
======================================================================
프로젝트 삽입 성공: 10건
프로젝트 삽입 실패: 0건
임베딩 생성: 10건
임베딩 실패: 0건
======================================================================

======================================================================
벡터 검색 기능 테스트
======================================================================

검색어: 'AI 플랫폼' (AI 기반 자동화 기술)
  ✓ 검색 결과 3건:

     1. AI 기반 제안서 자동 작성 플랫폼 개발
        유사도: 0.847

     2. 머신러닝 기반 수요 예측 모델 개발
        유사도: 0.763

     3. 연방 학습 기반 의료 진단 시스템
        유사도: 0.681

검색어: '데이터 분석' (빅데이터 처리 및 분석)
  ✓ 검색 결과 3건:
     1. 대용량 데이터 분석 및 시각화 시스템 구축 (유사도: 0.842)
     2. AI 기반 제안서 자동 작성 플랫폼 개발 (유사도: 0.651)
     3. 머신러닝 기반 수요 예측 모델 개발 (유사도: 0.618)

검색어: '클라우드' (클라우드 기반 시스템)
  ✓ 검색 결과 3건:
     1. 클라우드 기반 IoT 플랫폼 설계 및 구현 (유사도: 0.881)
     2. 스마트 시티 통합 관리 솔루션 개발 (유사도: 0.743)
     3. 엣지 컴퓨팅 프레임워크 설계 (유사도: 0.612)
```

---

## ✅ 검증 체크리스트

실행 후 다음을 확인하세요:

- [ ] 프로젝트 삽입 성공: 10건
- [ ] 임베딩 생성 성공: 10건
- [ ] 벡터 검색 결과: 유사도 0.6 이상
- [ ] 검색 정확도: 관련 프로젝트가 상위에 나옴

---

## 📊 마이그레이션 아키텍처

```
MSSQL Project_List (또는 테스트 데이터)
    ↓
프로젝트 메타 추출
    ↓
필드 매핑 & 변환
    ├─ pr_title → project_name
    ├─ pr_com → client_name
    ├─ pr_key → keywords (배열)
    ├─ pr_account → budget_krw (정수)
    └─ 기타 필드...
    ↓
Supabase intranet_projects 테이블 INSERT
    ↓
OpenAI text-embedding-3-small로 임베딩 생성
    ↓
임베딩 저장 (embedding 컬럼, 1536-dim vector)
    ↓
벡터 유사도 검색 RPC 호출
    ↓
검색 결과 검증
```

---

## 🔍 Supabase 데이터 구조

### intranet_projects 테이블

| 컬럼명 | 타입 | 설명 |
|-------|------|------|
| id | UUID | 프로젝트 고유 ID |
| org_id | TEXT | 조직 ID (RLS용) |
| legacy_idx | INTEGER | MSSQL의 idx_no |
| legacy_code | TEXT | MSSQL의 pr_code |
| project_name | TEXT | 프로젝트명 |
| client_name | TEXT | 발주처 |
| keywords | TEXT[] | 키워드 배열 |
| budget_krw | BIGINT | 예산 (원) |
| manager | TEXT | 담당자 |
| team_name | TEXT | 팀명 |
| status | TEXT | 프로젝트 상태 |
| embedding | vector(1536) | OpenAI 임베딩 (검색용) |
| created_at | TIMESTAMP | 생성 시간 |
| updated_at | TIMESTAMP | 수정 시간 |

### 벡터 검색 RPC 함수

```sql
search_projects_by_embedding(
  query_embedding: vector(1536),
  org_id: TEXT,
  limit: INT = 5,
  similarity_threshold: FLOAT = 0.5
)
```

**반환값:** 프로젝트명, 발주처, 유사도

---

## 🔧 트러블슈팅

### MSSQL 연결 오류 (스크립트 A 사용 시)

```
Error: DB-Lib error message 20009
Unable to connect: Adaptive Server is unavailable
```

**해결:**
1. MSSQL 서버가 실행 중인지 확인
2. 네트워크 연결 확인 (내부 네트워크)
3. 방화벽 설정 확인 (포트 1433)
4. 자격증명 재확인

**대체:** 스크립트 B 사용 (테스트 데이터)

### Supabase 연결 오류

```
Error: Unauthorized (401)
```

**해결:**
- `.env`의 `SUPABASE_SERVICE_ROLE_KEY` 확인
- Supabase 대시보드에서 키 재발급

### OpenAI API 오류

```
Error: Invalid API key
```

**해결:**
- `OPENAI_API_KEY` 유효성 확인
- API 크레딧 확인
- 사용 한도 확인

---

## 📈 다음 단계

### 파일럿 마이그레이션 검증 완료 후

#### 1. 전체 마이그레이션

```bash
# MSSQL의 모든 프로젝트 마이그레이션
python scripts/pilot_migration_10projects.py --execute --count 5000
```

#### 2. 월간 자동 동기화

```bash
# 매달 수정된 프로젝트만 업데이트 (증분 동기화)
python scripts/pilot_migration_10projects.py --execute --incremental --triggered-by scheduler
```

#### 3. 프론트엔드 통합

마이그레이션 완료 후:
- 인트라넷 프로젝트 목록 조회 API 구현
- 벡터 검색 UI 추가
- 문서 업로드 & 처리 기능

---

## 📝 성능 지표

| 항목 | 예상값 | 단위 |
|------|-------|------|
| 프로젝트 삽입 속도 | <1 | 초/건 |
| 임베딩 생성 속도 | <2 | 초/건 |
| 벡터 검색 응답시간 | <500 | ms |
| 검색 정확도 (top-3) | >80% | % |
| 마이그레이션 비용 | ~0.02 | USD (10개) |

---

## 📚 참고 문서

- [상세 가이드](docs/PILOT_MIGRATION_GUIDE.md)
- [Supabase 벡터 검색](https://supabase.com/docs/guides/ai/vector-columns)
- [OpenAI 임베딩](https://platform.openai.com/docs/guides/embeddings)
- [pgvector 유사도 검색](https://github.com/pgvector/pgvector)

---

## 🎬 빠른 시작

가장 간단한 방법:

```bash
# 1. 테스트 데이터로 미리 확인
python scripts/pilot_migration_demo.py --dry-run

# 2. 실제 마이그레이션 + 검색 테스트 실행
python scripts/pilot_migration_demo.py --execute
```

**예상 소요 시간:** 3-5분

---

**준비 완료:** 2026-04-11  
**마지막 업데이트:** 2026-04-11 17:30
