# Supabase 데이터베이스 설정 가이드

## 개요

이 프로젝트는 Supabase를 데이터베이스로 사용합니다. Supabase는 PostgreSQL 기반의 오픈소스 Firebase 대체제로, 실시간 데이터베이스, 인증, 스토리지 등을 제공합니다.

## 설정 단계

### 1. Supabase 프로젝트 생성

1. [Supabase](https://supabase.com)에 접속
2. 계정 생성 또는 로그인
3. "New Project" 클릭
4. 프로젝트 이름, 데이터베이스 비밀번호, 지역 선택
5. 프로젝트 생성 완료 (약 2분 소요)

### 2. 데이터베이스 스키마 적용

1. Supabase 대시보드에서 **SQL Editor** 선택
2. `database/supabase_schema.sql` 파일의 내용을 복사
3. SQL Editor에 붙여넣기
4. **Run** 버튼 클릭하여 실행

생성되는 테이블:
- `proposals`: 과거 제안서 저장소
- `personnel`: 인력 정보 관리
- `references`: 참고 자료
- `documents`: 문서 메타데이터

### 3. API 키 확인

1. Supabase 대시보드에서 **Settings** → **API** 선택
2. 다음 정보를 복사:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon public key**: 클라이언트 사이드용 공개 키
   - **service_role key**: 서버 사이드용 비밀 키 (⚠️ 노출 주의)

### 4. 환경 변수 설정

프로젝트 루트의 `.env` 파일을 수정:

```env
# Supabase 설정
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your-anon-public-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

⚠️ **주의사항**:
- `.env` 파일은 절대 Git에 커밋하지 마세요
- `SUPABASE_SERVICE_ROLE_KEY`는 서버 환경에서만 사용
- 공개 저장소에 업로드 금지

### 5. 의존성 설치

```bash
uv sync
```

이 명령어는 `pyproject.toml`의 `supabase>=2.0.0` 패키지를 설치합니다.

## 데이터베이스 구조

### proposals 테이블
```sql
id              UUID PRIMARY KEY
title           TEXT NOT NULL
client          TEXT NOT NULL
year            INTEGER NOT NULL
pages           INTEGER
status          TEXT
key_messages    TEXT[]
sections        JSONB
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

### personnel 테이블
```sql
id              UUID PRIMARY KEY
name            TEXT NOT NULL
grade           TEXT NOT NULL
role            TEXT NOT NULL
expertise       TEXT[]
available       BOOLEAN DEFAULT TRUE
projects        INTEGER DEFAULT 0
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

### references 테이블
```sql
id              UUID PRIMARY KEY
title           TEXT NOT NULL
content         TEXT
topics          TEXT[]
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

### documents 테이블
```sql
id              UUID PRIMARY KEY
filename        TEXT NOT NULL
path            TEXT
size            INTEGER
metadata        JSONB
created_at      TIMESTAMP
updated_at      TIMESTAMP
```

## 샘플 데이터

스키마 파일에는 다음 샘플 데이터가 포함되어 있습니다:

- **제안서**: 2건 (삼성전자, 현대모비스)
- **인력**: 4명 (PM, CTO, 개발리더, QA)
- **참고 자료**: 4건 (AWS, Kubernetes, AI, 컴플라이언스)

## 폴백 모드

Supabase 연결이 실패하거나 설정되지 않은 경우, 자동으로 메모리 기반 폴백 모드로 전환됩니다.

```python
# MCP 서버는 자동으로 폴백 처리
mcp_server = MCPServer(use_supabase=True)
# Supabase 연결 실패 시 → 메모리 모드로 전환
```

## 보안 설정

### Row Level Security (RLS)

모든 테이블에 RLS가 활성화되어 있습니다:

- **인증된 사용자**: 모든 작업 가능
- **Service Role**: 모든 작업 가능
- **익명 사용자**: 접근 불가

### 추가 보안 설정

1. **API Rate Limiting**: Supabase 대시보드에서 설정
2. **Database Backups**: 자동 백업 활성화 권장
3. **Monitoring**: Supabase 대시보드에서 로그 확인

## 문제 해결

### 연결 오류

```
RuntimeError: Supabase client not initialized
```

**해결방법**:
1. `.env` 파일에 `SUPABASE_URL`과 `SUPABASE_KEY` 설정 확인
2. Supabase 프로젝트가 활성 상태인지 확인
3. API 키가 올바른지 확인

### 스키마 적용 오류

```
ERROR: relation "proposals" already exists
```

**해결방법**:
- 이미 테이블이 존재하는 경우 정상입니다
- 테이블을 다시 생성하려면 먼저 삭제:
  ```sql
  DROP TABLE IF EXISTS proposals CASCADE;
  DROP TABLE IF EXISTS personnel CASCADE;
  DROP TABLE IF EXISTS references CASCADE;
  DROP TABLE IF EXISTS documents CASCADE;
  ```

## 추가 리소스

- [Supabase 공식 문서](https://supabase.com/docs)
- [Supabase Python Client](https://supabase.com/docs/reference/python/introduction)
- [PostgreSQL 문서](https://www.postgresql.org/docs/)
