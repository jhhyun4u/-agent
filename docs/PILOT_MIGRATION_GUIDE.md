# 파일럿 마이그레이션 가이드 (MSSQL → Supabase)

## 목표

MSSQL 인트라넷 프로젝트 데이터를 Supabase PostgreSQL로 성공적으로 마이그레이션하고, 벡터 검색 기능이 정상 작동하는지 검증합니다.

**단계:**
1. **파일럿 (10개 프로젝트)** → 검색 & 사용성 검증
2. **전체 마이그레이션** → 모든 프로젝트 이동

---

## 파일럿 마이그레이션 실행 방법

### 전제 조건

```bash
# 필수 환경 변수 설정 (.env 파일)
MSSQL_HOST=10.1.3.251
MSSQL_USER=sa
MSSQL_PASSWORD=<your-password>
MSSQL_DATABASE=intranet

SUPABASE_URL=https://inuuyaxddgbxexljfykg.supabase.co
SUPABASE_KEY=<anon-key>
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>

OPENAI_API_KEY=<your-openai-key>  # 임베딩 생성용
```

### 1단계: 데이터 미리보기 (DRY-RUN)

```bash
cd /c/project/tenopa\ proposer/-agent-master

# 스크립트 1: 실제 MSSQL에서 가져오기
python scripts/pilot_migration_10projects.py --dry-run

# 또는 스크립트 2: 테스트 데이터로 데모
python scripts/pilot_migration_demo.py --dry-run
```

**출력:**
```
[DRY RUN] 10개 프로젝트 미리보기:

1. AI 기반 제안서 자동 작성 플랫폼 개발
   발주처: 국방부
   예산: 500,000,000
   팀: AI팀

2. 대용량 데이터 분석 및 시각화 시스템 구축
   ...
```

### 2단계: 실제 마이그레이션 실행

```bash
# 스크립트 1: MSSQL 연결 가능할 경우
python scripts/pilot_migration_10projects.py --execute

# 스크립트 2: 테스트 데이터로 데모 실행
python scripts/pilot_migration_demo.py --execute
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

...

======================================================================
파일럿 마이그레이션 완료 리포트
======================================================================
프로젝트 삽입 성공: 10건
프로젝트 삽입 실패: 0건
임베딩 생성: 10건
임베딩 실패: 0건
======================================================================
```

### 3단계: 벡터 검색 테스트

마이그레이션 실행 후 자동으로 검색 테스트가 진행됩니다.

**테스트 쿼리:**
```
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
  ...
```

---

## Supabase 데이터 구조

### intranet_projects 테이블

```sql
CREATE TABLE intranet_projects (
  id UUID PRIMARY KEY,
  org_id TEXT NOT NULL,
  legacy_idx INTEGER,              -- MSSQL의 idx_no
  legacy_code TEXT,                -- MSSQL의 pr_code
  project_name TEXT NOT NULL,
  client_name TEXT,                -- 발주처
  keywords TEXT[],                 -- 키워드 배열
  start_date DATE,
  end_date DATE,
  budget_krw BIGINT,               -- 예산 (원)
  manager TEXT,                    -- 담당자
  team_name TEXT,                  -- 팀명
  status TEXT,                     -- 프로젝트 상태
  file_count INTEGER DEFAULT 0,    -- 업로드된 파일 수
  migration_status TEXT,           -- pending|extracting|completed|failed
  embedding vector(1536),          -- OpenAI 임베딩 (텍스트 검색용)
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- RLS 정책: org_id 기반 필터링 (조직별 격리)
ALTER TABLE intranet_projects ENABLE ROW LEVEL SECURITY;

CREATE POLICY org_isolation ON intranet_projects
  USING (org_id = current_setting('app.org_id'));
```

### 벡터 검색 RPC 함수

```sql
CREATE OR REPLACE FUNCTION search_projects_by_embedding(
  query_embedding vector(1536),
  org_id TEXT,
  limit INT DEFAULT 5,
  similarity_threshold FLOAT DEFAULT 0.5
) RETURNS TABLE (
  id UUID,
  project_name TEXT,
  client_name TEXT,
  similarity FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    p.id,
    p.project_name,
    p.client_name,
    1 - (p.embedding <=> query_embedding) AS similarity
  FROM intranet_projects p
  WHERE p.org_id = search_projects_by_embedding.org_id
    AND p.embedding IS NOT NULL
    AND (1 - (p.embedding <=> query_embedding)) > similarity_threshold
  ORDER BY similarity DESC
  LIMIT search_projects_by_embedding.limit;
END;
$$ LANGUAGE plpgsql;
```

---

## 마이그레이션 프로세스 상세

### 1. 데이터 추출 (MSSQL)

```python
# MSSQL Project_List 테이블에서 조회
SELECT TOP 10
  idx_no, pr_code, pr_title, pr_com, pr_key,
  pr_start_yy, pr_start_mm, pr_start_dd,
  pr_end_yy, pr_end_mm, pr_end_dd,
  pr_account, pr_status, pr_team, pr_manager
FROM Project_List
WHERE pr_status != 'SKIP'
ORDER BY pr_start_yy DESC
```

### 2. 데이터 변환

| MSSQL 필드 | → | Supabase 필드 | 변환 로직 |
|-----------|---|-------------|---------|
| idx_no | → | legacy_idx | 그대로 |
| pr_code | → | legacy_code | 그대로 |
| pr_title | → | project_name | 제목 |
| pr_com | → | client_name | 발주처 |
| pr_key | → | keywords | 쉼표로 구분 후 배열 |
| pr_account | → | budget_krw | 정수로 변환 |
| pr_team | → | team_name | 팀명 |
| pr_manager | → | manager | 담당자명 |
| pr_status | → | status | 프로젝트 상태 |
| (자동 생성) | → | embedding | title + client_name → OpenAI 임베딩 |

### 3. Supabase 삽입

```python
# 프로젝트 메타 삽입
project = await client.table("intranet_projects").insert({
  "id": uuid4(),
  "org_id": "tenopa-default",
  "legacy_idx": 1,
  "project_name": "AI 기반 제안서 자동 작성 플랫폼...",
  "client_name": "국방부",
  "keywords": ["AI", "NLP", "자동화"],
  "budget_krw": 500000000,
  "manager": "김철수",
  "team_name": "AI팀",
  "status": "COMPLETE"
}).execute()

project_id = project.data[0]["id"]
```

### 4. 임베딩 생성

```python
# OpenAI API로 임베딩 생성
embedding = openai_client.embeddings.create(
  model="text-embedding-3-small",
  input="AI 기반 제안서 자동 작성 플랫폼... 국방부"
).data[0].embedding  # 1536-dim vector

# Supabase에 업데이트
await client.table("intranet_projects").update({
  "embedding": embedding
}).eq("id", project_id).execute()
```

---

## 검증 체크리스트

### ✅ 삽입 검증

```sql
-- Supabase에서 확인
SELECT COUNT(*) as total, COUNT(embedding) as with_embedding
FROM intranet_projects
WHERE org_id = 'tenopa-default';

-- 결과: 10개 모두 임베딩 포함
-- total: 10
-- with_embedding: 10
```

### ✅ 벡터 검색 검증

```sql
-- 샘플 검색 쿼리 테스트
SELECT * FROM search_projects_by_embedding(
  (SELECT embedding FROM intranet_projects LIMIT 1),
  'tenopa-default',
  5,
  0.5
);
```

### ✅ 사용성 검증

- [ ] 프로젝트 목록 조회 성공
- [ ] 벡터 검색 결과 정확도 검증
- [ ] 관련 문서 업로드 및 검색 동작 확인
- [ ] RLS 정책이 조직별로 올바르게 적용됨

---

## 마이그레이션 후 다음 단계

### 전체 마이그레이션 (모든 프로젝트)

파일럿 마이그레이션 검증 완료 후:

```bash
# 제한 없이 모든 프로젝트 마이그레이션
python scripts/pilot_migration_10projects.py --execute --count 5000
```

### 증분 동기화 (매월 자동)

```bash
# 1개월 이내 수정된 프로젝트만 업데이트
python scripts/pilot_migration_10projects.py --execute --incremental
```

---

## 트러블슈팅

### MSSQL 연결 오류

```
Error: DB-Lib error message 20009, severity 9
Unable to connect: Adaptive Server is unavailable
```

**해결:**
- MSSQL 서버 접근 가능성 확인 (10.1.3.251:1433)
- 네트워크/방화벽 설정 확인
- 자격증명(사용자명, 비밀번호) 재확인

### Supabase 연결 오류

```
Error: Unauthorized (401)
```

**해결:**
- `SUPABASE_SERVICE_ROLE_KEY` 환경 변수 확인
- Supabase 대시보드에서 key 재발급

### OpenAI 임베딩 오류

```
Error: Invalid API key
```

**해결:**
- `OPENAI_API_KEY` 유효성 확인
- OpenAI 크레딧 잔액 확인
- API 사용 한도 확인

### 낮은 검색 유사도

**원인:** 쿼리와 프로젝트 이름이 너무 다름

**해결:**
- 유사도 임계값 (threshold) 낮추기
- 더 명확한 쿼리 입력
- 프로젝트 메타데이터 검토

---

## 성능 지표

| 메트릭 | 목표 | 실제 |
|-------|------|------|
| 프로젝트 삽입 속도 | <1초/건 | - |
| 임베딩 생성 속도 | <2초/건 | - |
| 벡터 검색 응답시간 | <500ms | - |
| 검색 정확도 (top-3) | >80% | - |

---

## 참고 문서

- [Supabase 벡터 검색](https://supabase.com/docs/guides/ai/vector-columns)
- [OpenAI 임베딩 API](https://platform.openai.com/docs/guides/embeddings)
- [pgvector 유사도 검색](https://github.com/pgvector/pgvector)

---

**마이그레이션 시작일:** 2026-04-11  
**파일럿 규모:** 10개 프로젝트  
**담당자:** 사용자
