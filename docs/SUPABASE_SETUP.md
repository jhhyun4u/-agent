# Supabase 설정 완료 가이드

## 📋 개요
PostgreSQL에서 Supabase로 성공적으로 마이그레이션 완료했습니다.

## ✅ 완료된 작업

### 1. 의존성 변경
- ❌ 제거: `asyncpg` (PostgreSQL 직접 연결)
- ✅ 추가: `supabase>=2.0.0` (Supabase 클라이언트)

### 2. 환경 변수 설정
`.env` 파일에 다음 값들이 설정되었습니다:
```bash
SUPABASE_URL=https://qrejgelizidpqakbkvmp.supabase.co
SUPABASE_KEY=eyJhbGci...  # anon key (클라이언트용)
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...  # service_role key (서버용, RLS 우회)
```

### 3. 데이터베이스 스키마
`database/supabase_schema.sql` 파일 실행 완료:
- ✅ `proposals` 테이블: 제안서 데이터 (2건 샘플)
- ✅ `personnel` 테이블: 인력 정보 (4명 샘플)
- ✅ `reference_materials` 테이블: 참고 자료 (4건 샘플)
- ✅ `documents` 테이블: 문서 메타데이터 (비어있음)

### 4. Supabase 클라이언트 구현
`app/utils/supabase_client.py`:
- 싱글톤 패턴으로 Supabase 클라이언트 관리
- **중요**: `service_role_key` 우선 사용 (RLS 정책 우회)
- 주요 메서드:
  - `get_proposals()` - 제안서 목록 조회
  - `search_proposals()` - 제안서 검색
  - `get_personnel()` - 인력 목록 조회
  - `search_personnel_by_skill()` - 기술별 인력 검색
  - `get_references()` - 참고 자료 조회
  - `search_references()` - 참고 자료 검색

### 5. MCP 서버 통합
`services/mcp_server.py`:
- Supabase 우선 사용, 실패 시 메모리로 자동 폴백
- 4가지 서비스 통합:
  1. ProposalDB - 과거 제안서 저장소
  2. PersonnelDB - 인력 정보 관리
  3. RAGServer - 참고 자료 검색
  4. DocumentStore - 생성된 문서 저장소

## 🔧 주요 이슈 해결

### 문제 1: RLS (Row Level Security) 정책으로 인한 접근 불가
**증상**:
- Supabase Table Editor에서는 데이터가 보이지만
- Python 클라이언트에서는 0건 조회됨

**원인**:
- `anon` 키는 RLS 정책의 제약을 받음
- RLS 정책이 `authenticated` 및 `service_role`만 허용

**해결책**:
```python
# app/utils/supabase_client.py
def __init__(self):
    if self._client is None and settings.supabase_url:
        # 서비스 롤 키 우선 사용 (RLS 우회)
        api_key = settings.supabase_service_role_key or settings.supabase_key
        if api_key:
            self._client = create_client(settings.supabase_url, api_key)
```

### 문제 2: SQL 예약어 충돌
**증상**: `ERROR: 42601: syntax error at or near 'references'`

**해결책**: 테이블명 변경 `references` → `reference_materials`

### 문제 3: PostgreSQL 텍스트 검색 설정
**증상**: `ERROR: 42704: text search configuration "korean" does not exist`

**해결책**: `to_tsvector('korean', ...)` → `to_tsvector('simple', ...)`

## ✅ 연결 테스트 결과

```bash
$ uv run python test_supabase_connection.py
```

**결과**:
- ✅ Supabase 클라이언트 초기화 성공
- ✅ 제안서 2건 조회 성공 (삼성전자, 현대모비스)
- ✅ 인력 4명 조회 성공 (김철수, 이영희, 박민준, 최수진)
- ✅ 참고 자료 4건 조회 성공
- ✅ 검색 기능 정상 작동 ('클라우드' 검색 → 1건)

## 📚 다음 단계

### 1. 전체 워크플로우 테스트
```bash
uv run pytest tests/integration/test_workflow.py
```

### 2. API 엔드포인트 테스트
```bash
# 서버 실행
uv run uvicorn app.main:app --reload

# 별도 터미널에서
uv run python tests/api/test_v31_endpoints.py
```

### 3. MCP 서버 실제 사용 테스트
에이전트들이 Supabase에서 실제 데이터를 가져와 제안서를 생성하는지 확인

## 🔑 보안 주의사항

1. **Service Role Key 보호**
   - `.env` 파일은 절대 Git에 커밋하지 말 것
   - Service Role Key는 모든 RLS 정책을 우회하므로 서버 사이드에서만 사용

2. **클라이언트 사이드에서는 Anon Key 사용**
   - 웹 프론트엔드나 모바일 앱에서는 `SUPABASE_KEY` (anon) 사용
   - RLS 정책을 통해 접근 제어

3. **프로덕션 환경**
   - 환경 변수는 시스템 환경 변수나 비밀 관리 시스템 사용
   - API 키 로테이션 정책 수립

## 📖 참고 자료

- [Supabase 공식 문서](https://supabase.com/docs)
- [Row Level Security 가이드](https://supabase.com/docs/guides/auth/row-level-security)
- [Python 클라이언트 라이브러리](https://supabase.com/docs/reference/python)
