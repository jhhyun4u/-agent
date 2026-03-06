# Design: 제안서작성 서비스 플랫폼 v1

## 메타 정보

| 항목 | 내용 |
|------|------|
| Feature | proposal-platform-v1 |
| 작성일 | 2026-03-05 |
| 최종 수정 | 2026-03-06 (8개 이슈 수정 v10 반영 — 최종 감리 완료) |
| 기반 Plan | docs/01-plan/features/proposal-platform-v1.plan.md |

---

## 1. 시스템 아키텍처

```
[Browser] Next.js 14 App Router
  /login  /proposals  /proposals/:id  /admin
     | JWT Bearer Token (Supabase Access Token)
[FastAPI 백엔드]  -- CORSMiddleware 필수, uvicorn --workers 1
  /api/v3.1/*      5-Phase 파이프라인  (Depends(get_current_user) 적용)
  /api/team/*      팀 CRUD, 댓글, 상태 (Depends(get_current_user) 적용)
  /api/g2b/*       나라장터 API 프록시 (Depends(get_current_user) 적용)
  -- 별도 /auth/* 라우터 없음. 인증은 Depends(get_current_user) 미들웨어로 처리 --
     |                    |
[Supabase]          [나라장터 Open API]
  DB + Auth + Storage + Realtime + Edge Functions
     |
[asyncio.create_task()]  -- Phase 실행 (uvicorn --workers 1 고정)
```

### 작업 실행 방식 결정 (v1 제약 사항)

FastAPI BackgroundTasks는 워커 프로세스 안에서 실행되므로,
서버 재시작 시 실행 중인 Phase 작업이 소리 없이 종료됨.

v1 대응: uvicorn --workers 1 고정 + DB 기반 세션 복원
  -> 재시작 시 running 상태 proposals를 failed로 마킹
  -> 사용자가 execute?start_phase=N 으로 재시작 가능 (UI 버튼 제공)

v2 목표: Celery + Redis 또는 pg_notify + 별도 worker 프로세스로 분리

---

## 2. DB 스키마 (Supabase)

### teams
```sql
CREATE TABLE teams (
  id         UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name       TEXT NOT NULL,
  created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

### team_members
```sql
CREATE TABLE team_members (
  id        UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  team_id   UUID REFERENCES teams(id) ON DELETE CASCADE,
  user_id   UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  role      TEXT CHECK (role IN ('admin','member','viewer')) DEFAULT 'member',
  joined_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(team_id, user_id)
);
```

### invitations (팀 초대 흐름용)
```sql
CREATE TABLE invitations (
  id         UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  team_id    UUID REFERENCES teams(id) ON DELETE CASCADE,
  email      TEXT NOT NULL,
  role       TEXT CHECK (role IN ('admin','member','viewer')) DEFAULT 'member',
  invited_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  status     TEXT CHECK (status IN ('pending','accepted','expired')) DEFAULT 'pending',
  created_at TIMESTAMPTZ DEFAULT now(),
  expires_at TIMESTAMPTZ DEFAULT now() + INTERVAL '7 days',
  UNIQUE(team_id, email)
);
-- 재초대 시 UNIQUE(team_id, email) 충돌 방지:
-- API 레이어에서 upsert 사용:
--   on_conflict="team_id,email" → status=pending, expires_at 갱신, invited_by 갱신
```

### proposals
```sql
CREATE TABLE proposals (
  id                    UUID DEFAULT gen_random_uuid() PRIMARY KEY,  -- UUID4 사용
  team_id               UUID REFERENCES teams(id) ON DELETE SET NULL,
  owner_id              UUID NOT NULL REFERENCES auth.users(id) ON DELETE RESTRICT,
  -- ON DELETE RESTRICT: 해당 유저 proposals 존재 시 계정 삭제 불가 (v2에서 soft-delete 예정)
  title                 TEXT NOT NULL,
  rfp_filename          TEXT,
  rfp_content           TEXT,
  rfp_content_truncated BOOLEAN DEFAULT false,
  status                TEXT CHECK (status IN (
                          'pending','running','completed','failed',
                          'reviewing','approved'
                        )) DEFAULT 'pending',
  current_phase         TEXT DEFAULT 'pending',
  phases_completed      INTEGER DEFAULT 0,
  failed_phase          INTEGER,
  storage_path_docx     TEXT,
  storage_path_pptx     TEXT,
  storage_path_rfp      TEXT,
  storage_upload_failed BOOLEAN DEFAULT false,  -- Storage 업로드 실패 플래그
  win_result            TEXT CHECK (win_result IN ('won','lost','pending')) DEFAULT 'pending',
  bid_amount            BIGINT,
  notes                 TEXT,
  created_at            TIMESTAMPTZ DEFAULT now(),
  updated_at            TIMESTAMPTZ DEFAULT now()
);

-- updated_at 자동 갱신 트리거
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER proposals_updated_at
  BEFORE UPDATE ON proposals
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- 서버 재시작 시 running -> failed 마킹
CREATE OR REPLACE FUNCTION mark_stale_running_proposals()
RETURNS void AS $$
BEGIN
  UPDATE proposals SET status = 'failed', current_phase = 'interrupted'
  WHERE status = 'running';
END;
$$ LANGUAGE plpgsql;

-- 제목 검색 인덱스 (ILIKE '%q%' 대소문자 무시 부분일치)
-- text_pattern_ops는 LIKE 'prefix%' 전용 → 부분일치에는 pg_trgm + gin_trgm_ops 필요
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX proposals_title_trgm ON proposals USING GIN (title gin_trgm_ops);

-- Supabase Realtime을 위한 REPLICA IDENTITY 설정
-- UPDATE 이벤트 payload에 변경 전후 전체 row가 포함되어야 함
ALTER TABLE proposals REPLICA IDENTITY FULL;
-- 추가 배포 작업: Supabase Dashboard > Database > Replication > proposals 테이블 활성화 필요
```

### proposal_phases
```sql
CREATE TABLE proposal_phases (
  id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  proposal_id   UUID REFERENCES proposals(id) ON DELETE CASCADE,
  phase_num     INTEGER NOT NULL CHECK (phase_num BETWEEN 1 AND 5),
  phase_name    TEXT NOT NULL,
  artifact_json JSONB NOT NULL DEFAULT '{}',
  completed_at  TIMESTAMPTZ DEFAULT now(),
  UNIQUE(proposal_id, phase_num)
);
```

### comments
```sql
CREATE TABLE comments (
  id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  proposal_id UUID REFERENCES proposals(id) ON DELETE CASCADE,
  user_id     UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  section     TEXT,
  body        TEXT NOT NULL,
  resolved    BOOLEAN DEFAULT false,
  created_at  TIMESTAMPTZ DEFAULT now()
);
```

### usage_logs (비용 추적)
```sql
CREATE TABLE usage_logs (
  id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  proposal_id   UUID REFERENCES proposals(id) ON DELETE SET NULL,
  team_id       UUID REFERENCES teams(id) ON DELETE SET NULL,
  owner_id      UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  phase_num     INTEGER,
  model         TEXT NOT NULL,
  input_tokens  INTEGER NOT NULL DEFAULT 0,
  output_tokens INTEGER NOT NULL DEFAULT 0,
  created_at    TIMESTAMPTZ DEFAULT now()
);
-- team_id 출처: phase_executor가 session.get('team_id')로 가져옴 (create_session 시 저장)
```

### g2b_cache
```sql
CREATE TABLE g2b_cache (
  id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  query_hash  TEXT UNIQUE NOT NULL,
  query_type  TEXT NOT NULL,
  result_json JSONB NOT NULL,
  cached_at   TIMESTAMPTZ DEFAULT now(),
  expires_at  TIMESTAMPTZ DEFAULT now() + INTERVAL '24 hours'
);

CREATE OR REPLACE FUNCTION cleanup_expired_g2b_cache()
RETURNS void AS $$
BEGIN DELETE FROM g2b_cache WHERE expires_at < now(); END;
$$ LANGUAGE plpgsql;
```

### RLS 정책

```sql
ALTER TABLE proposals ENABLE ROW LEVEL SECURITY;
CREATE POLICY proposals_access ON proposals
  USING (
    owner_id = auth.uid()
    OR team_id IN (
      SELECT team_id FROM team_members WHERE user_id = auth.uid()
    )
  );

ALTER TABLE comments ENABLE ROW LEVEL SECURITY;
CREATE POLICY comments_access ON comments
  USING (proposal_id IN (
    SELECT p.id FROM proposals p
    JOIN team_members tm ON p.team_id = tm.team_id
    WHERE tm.user_id = auth.uid()
    UNION
    SELECT id FROM proposals WHERE owner_id = auth.uid()
  ));

ALTER TABLE proposal_phases ENABLE ROW LEVEL SECURITY;
CREATE POLICY phases_access ON proposal_phases
  USING (proposal_id IN (
    SELECT p.id FROM proposals p
    JOIN team_members tm ON p.team_id = tm.team_id
    WHERE tm.user_id = auth.uid()
    UNION
    SELECT id FROM proposals WHERE owner_id = auth.uid()
  ));

ALTER TABLE usage_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY usage_logs_access ON usage_logs
  USING (owner_id = auth.uid()
    OR team_id IN (SELECT team_id FROM team_members WHERE user_id = auth.uid()));

-- teams: 소속 팀 또는 직접 생성한 팀만 접근
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;
CREATE POLICY teams_access ON teams
  USING (
    id IN (SELECT team_id FROM team_members WHERE user_id = auth.uid())
    OR created_by = auth.uid()
  );

-- team_members: 같은 팀 소속 사용자만 접근
ALTER TABLE team_members ENABLE ROW LEVEL SECURITY;
CREATE POLICY team_members_access ON team_members
  USING (team_id IN (
    SELECT team_id FROM team_members WHERE user_id = auth.uid()
  ));

-- invitations: admin만 조회/관리 (초대 수락 콜백은 service_role_key 사용)
ALTER TABLE invitations ENABLE ROW LEVEL SECURITY;
CREATE POLICY invitations_access ON invitations
  USING (team_id IN (
    SELECT team_id FROM team_members
    WHERE user_id = auth.uid() AND role = 'admin'
  ));

-- comments INSERT: 본인이 작성하는 댓글 + 접근 권한 있는 proposal만 허용
CREATE POLICY comments_insert ON comments FOR INSERT
  WITH CHECK (
    user_id = auth.uid()
    AND proposal_id IN (
      SELECT p.id FROM proposals p
      JOIN team_members tm ON p.team_id = tm.team_id
      WHERE tm.user_id = auth.uid()
      UNION
      SELECT id FROM proposals WHERE owner_id = auth.uid()
    )
  );
```

---

## 3. 인증 미들웨어

### Supabase AsyncClient — asyncio.Lock 싱글턴 (race condition 방지)

supabase-py v2 기본 create_client()는 동기. async 환경에서는 AsyncClient 필수.
전역 변수 동시 초기화 방지를 위해 asyncio.Lock 사용.

```python
# app/utils/supabase_client.py
import asyncio
from supabase import acreate_client, AsyncClient  # public API (supabase-py v2)
# 주의: from supabase._async.client import ... 은 private 모듈 — 버전 업 시 경로 변경 위험

_async_client: AsyncClient | None = None
_lock = asyncio.Lock()

async def get_async_client() -> AsyncClient:
    global _async_client
    async with _lock:
        if _async_client is None:
            _async_client = await acreate_client(
                settings.supabase_url,
                settings.supabase_service_role_key or settings.supabase_key
            )
    return _async_client

# 대안: lifespan에서 단 1회 초기화하는 방식도 안전
# async with lifespan(app):
#     _async_client = await acreate_client(...)  # public API
```

### JWT 검증 (Supabase SDK — PyJWT 사용 금지)

Supabase JWT는 JWKS 엔드포인트 방식이므로 일반 PyJWT 디코딩 불가.
반드시 SDK의 auth.get_user() 사용.

```python
# app/middleware/auth.py
from fastapi import Header, HTTPException, Depends
from typing import Optional

async def get_current_user(authorization: Optional[str] = Header(None)):
    # Header(...) 사용 시 헤더 없으면 422 반환 → 401로 통일하기 위해 Optional + None 사용
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    token = authorization.removeprefix("Bearer ")
    try:
        client = await get_async_client()
        response = await client.auth.get_user(token)
        return response.user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
```

### 인증 적용 범위
- /api/v3.1/* : Depends(get_current_user) 추가
- /api/team/* : Depends(get_current_user) 추가
- /api/g2b/*  : Depends(get_current_user) 추가
- /health, /status, /docs : 인증 제외
- /api/v3.1/bid/calculate : 공개 유지 (내부 도구)
- 별도 /auth/* 라우터 없음 — Supabase Auth는 프론트엔드 SDK에서 직접 처리

### CORS (main.py)
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # ["http://localhost:3000", ...]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 서버 시작 시 초기화 (main.py lifespan)
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    client = await get_async_client()
    try:
        await client.rpc("mark_stale_running_proposals").execute()
        await client.rpc("cleanup_expired_g2b_cache").execute()
    except Exception as e:
        logger.warning(f"lifespan 초기화 경고 (무시): {e}")
    yield
```

---

## 4. proposal_id 생성 방식 변경

```python
# 현재 (충돌 위험)
proposal_id = f"prop_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# 변경 후
import uuid
proposal_id = str(uuid.uuid4())
```

파일 경로도 UUID 기반:
- 로컬 임시: output/{uuid}.docx
- Storage: proposals/{uuid}/proposal.docx

---

## 5. API 엔드포인트 설계

### 역할 기반 접근 권한 (팀 API)

| 엔드포인트 | viewer | member | admin | owner |
|-----------|:------:|:------:|:-----:|:-----:|
| GET /proposals (목록 조회) | O | O | O | O |
| POST /proposals/generate | - | O | O | O |
| PATCH /proposals/{id}/status | - | O | O | O |
| PATCH /proposals/{id}/win-result | - | - | O | O |
| GET /proposals/{id}/comments | O | O | O | O |
| POST /proposals/{id}/comments | - | O | O | O |
| PATCH /comments/{id}/resolve | - | 작성자만 | O | O |
| POST /teams/{id}/invite | - | - | O | - |
| DELETE /teams/{id}/members/{uid} | - | - | O | - |
| GET /usage | O | O | O | O |

권한 체크 패턴:
```python
# routes_team.py 공통 헬퍼
async def get_member_role(team_id, user_id, client) -> str | None:
    row = (await client.table("team_members")
           .select("role").eq("team_id", team_id)
           .eq("user_id", user_id).single().execute()).data
    return row["role"] if row else None

async def require_role(team_id, user, client, allowed: list[str]):
    role = await get_member_role(team_id, str(user.id), client)
    if role not in allowed:
        raise HTTPException(403, "권한이 없습니다")

async def require_role_or_owner(proposal_id, user, client, allowed: list[str]):
    """팀 역할 OR 제안서 소유자 둘 중 하나를 만족하면 허용.
    팀 없는 개인 소유자(team_id=NULL)도 자신의 제안서에 접근 가능.
    예: PATCH /proposals/{id}/win-result (admin 또는 owner만 가능)
    """
    row = (await client.table("proposals")
           .select("owner_id, team_id").eq("id", proposal_id)
           .single().execute()).data
    if not row:
        raise HTTPException(404, "제안서를 찾을 수 없습니다")
    if str(row["owner_id"]) == str(user.id):
        return  # 소유자는 무조건 허용
    if row["team_id"]:
        role = await get_member_role(row["team_id"], str(user.id), client)
        if role in allowed:
            return
    raise HTTPException(403, "권한이 없습니다")
```

### v3.1 기존 엔드포인트 변경

| Method | Path | 변경 |
|--------|------|------|
| POST | /api/v3.1/proposals/generate | owner_id(JWT), team_id(optional) 추가 |
| POST | /api/v3.1/proposals/{id}/execute | start_phase 파라미터 추가 |
| GET | /api/v3.1/proposals/{id}/download/{type} | Storage 서명 URL 리다이렉트 |

### 팀 API (/api/team/*)

| Method | Path | 설명 |
|--------|------|------|
| POST | /api/team/teams | 팀 생성 |
| GET | /api/team/teams/me | 내 팀 목록 |
| POST | /api/team/teams/{id}/invite | 팀원 초대 (admin만) + invitations upsert |
| GET | /api/team/invitations/accept | 초대 수락 콜백 → team_members INSERT |
| DELETE | /api/team/teams/{id}/members/{uid} | 팀원 제거 (admin만) |
| GET | /api/team/proposals | 팀 제안서 목록 (페이지네이션 + 검색) |
| PATCH | /api/team/proposals/{id}/status | 검토중/승인 (member 이상) |
| PATCH | /api/team/proposals/{id}/win-result | 수주결과 (owner/admin만) |
| GET | /api/team/proposals/{id}/comments | 댓글 목록 (viewer 이상) |
| POST | /api/team/proposals/{id}/comments | 댓글 작성 (member 이상) |
| PATCH | /api/team/comments/{id}/resolve | 해결 처리 (작성자 또는 admin) |
| GET | /api/team/usage | 토큰 사용량 조회 |

팀원 초대 흐름:
```
1. POST /invite (admin only)
   -> invitations upsert (on_conflict team_id,email → status=pending, expires_at 갱신)
   -> supabase.auth.admin.invite_user_by_email(
        email=target_email,
        redirectTo=f"{FRONTEND_URL}/invitations/accept?team_id={team_id}"
      )
2. 사용자 이메일 클릭 -> Supabase 인증 완료 -> redirectTo URL로 리다이렉트
3. GET /invitations/accept?team_id=...
   -> JWT에서 user.email 추출 (get_current_user)
   -> invitations 조회 (team_id=?, email=user.email, status='pending', expires_at > now())
      [조회 결과 없음/만료] → 400 {"detail": "초대장을 찾을 수 없거나 만료되었습니다"}
      [이미 team_members에 존재] → 200 {"message": "이미 팀원입니다"} (멱등성 보장)
   -> team_members INSERT ON CONFLICT (team_id, user_id) DO NOTHING
   -> invitations UPDATE status='accepted'
   -> 200 {"message": "팀 참여 완료", "team_id": "..."}
   [프론트엔드] 200 수신 → /proposals 리다이렉트
```
주의: ?token= 파라미터 사용 금지 — Supabase가 관리하는 내부 토큰과 혼동됨.
      team_id를 redirectTo에 포함하고, 이메일은 JWT(user.email)에서 추출.

팀 제안서 목록:
```
GET /api/team/proposals?page=1&limit=20&status=completed&sort=created_at:desc&q=검색어
응답: { items: [...], total: N, page: 1, pages: M }
q 파라미터: title ILIKE '%검색어%' (proposals_title_search 인덱스 활용)
```

### 나라장터 프록시 (/api/g2b/*)

| Method | Path | 설명 |
|--------|------|------|
| GET | /api/g2b/bid-search | 입찰공고 검색 |
| GET | /api/g2b/bid-results | 낙찰결과 조회 |
| GET | /api/g2b/contract-results | 계약결과 조회 |
| GET | /api/g2b/company-history | 업체 입찰이력 |
| GET | /api/g2b/competitors | 경쟁사 통합 분석 (4개 API 조합) |

---

## 6. 나라장터 API 연동

### API 주소 (_type=json 사용)
```
Base: https://apis.data.go.kr/1230000/

입찰공고 검색:   BidPublicInfoService04/getBidPblancListInfoServc
낙찰결과 조회:   BidPublicInfoService04/getBidResultListInfo   (낙찰업체명 필수)
계약결과 조회:   ContractInfoService/getContractResultListInfo
업체 입찰이력:   BidPublicInfoService04/getCmpnyBidInfoServc
```

### aiohttp ClientSession 생성 패턴

```python
# g2b_service.py
import aiohttp
from urllib.parse import quote  # serviceKey URL 인코딩 (함수 내부 import 금지)

class G2BService:
    def __init__(self):
        self.session: aiohttp.ClientSession | None = None
        self.base_url = "https://apis.data.go.kr/1230000"

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *_):
        if self.session:
            await self.session.close()

# 사용 패턴 (routes_g2b.py / phase_executor.py):
# async with G2BService() as g2b:
#     result = await g2b.search_competitors(rfp_title)
```

### Rate Limiting + Retry (공공 API 초당 10건 제한)

```python
# g2b_service.py
import asyncio, aiohttp

async def _call_api(self, endpoint: str, params: dict) -> list:
    # serviceKey는 URL 문자열에 직접 포함 — aiohttp params dict 사용 시 이중 인코딩 발생
    encoded_key = quote(settings.g2b_api_key, safe="")  # quote는 모듈 최상단에서 import
    url = f"{self.base_url}/{endpoint}?serviceKey={encoded_key}&_type=json"

    for attempt in range(3):
        await asyncio.sleep(0.1)  # 기본 Rate Limit 간격
        try:
            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 429:  # Too Many Requests
                    await asyncio.sleep(2 ** attempt)  # 1s, 2s, 4s backoff
                    continue
                resp.raise_for_status()
                data = await resp.json()
                # 나라장터 응답 구조: response.header.resultCode + response.body.items.item
                result = data.get("response", {})
                if result.get("header", {}).get("resultCode") != "00":
                    raise RuntimeError(f"G2B API 오류: {result.get('header', {}).get('resultMsg')}")
                items = result.get("body", {}).get("items") or {}
                raw = items.get("item", [])
                return raw if isinstance(raw, list) else [raw]  # 단건 응답 정규화
        except Exception as e:
            if attempt == 2:
                raise
            await asyncio.sleep(2 ** attempt)
    raise RuntimeError(f"G2B API 호출 실패: {endpoint}")
```

### 경쟁사 분석 흐름 (4단계)
```
1. getBidPblancListInfoServc  -> 유사 공고 목록
2. getBidResultListInfo       -> 낙찰업체명 + 낙찰금액 (필수)
3. getCmpnyBidInfoServc       -> 업체별 전체 수주이력
4. CompetitorProfile 생성    -> Phase 2 LLM 전달
```

### 캐싱
```
query_hash = SHA256(api_type + json.dumps(sorted(params.items())))
expires_at 이내: g2b_cache 반환
만료/미존재: 실제 API 호출 -> g2b_cache upsert
```

---

## 7. 세션 영속성 + phase_executor async 전환

### session_manager.py 전체 async 전환

파급 범위:
- routes_v31.py: create_session(1), get_session(4), update_session(1) = 6곳
- phase_executor.py: _update_status(5), _save_artifact(5), execute_all(2), execute_from_phase(3) = 15곳
- 합계: 21곳

### create_session
```python
async def create_session(self, proposal_id, initial_data, session_type="v3.1"):
    rfp_content = initial_data.get("proposal_state", {}).get("rfp_content", "")
    truncated = len(rfp_content) > 100_000
    session_data = {
        **initial_data,
        "proposal_id": proposal_id,
        "created_at": datetime.now(),
        "status": "initialized"
    }
    # DB INSERT 먼저 — 성공 확인 후 인메모리 등록 (DB 실패 시 ghost session 방지)
    client = await get_async_client()
    await client.table("proposals").insert({
        "id": proposal_id,
        "title": initial_data.get("rfp_title", ""),
        "owner_id": initial_data.get("owner_id"),
        "team_id": initial_data.get("team_id"),        # ← session에 저장 → _log_usage에서 참조
        "rfp_filename": initial_data.get("rfp_filename"),  # 서버 재시작 후 복원용
        "rfp_content": rfp_content[:100_000],
        "rfp_content_truncated": truncated,
        "status": "pending"
    }).execute()
    self._sessions[proposal_id] = session_data
    return session_data
```

### get_session (서버 재시작 후 DB 복원)
```python
async def get_session(self, proposal_id):
    if proposal_id in self._sessions:
        return self._sessions[proposal_id]
    client = await get_async_client()
    row = (await client.table("proposals").select("*")
           .eq("id", proposal_id).single().execute()).data
    if not row:
        raise SessionNotFoundError(...)
    phases = (await client.table("proposal_phases").select("*")
              .eq("proposal_id", proposal_id).execute()).data
    artifacts = {f"phase_artifact_{p['phase_num']}": p["artifact_json"] for p in phases}
    session = {
        "proposal_id": proposal_id,
        "rfp_title": row["title"],
        "status": row["status"],
        "team_id": row["team_id"],              # ← _log_usage에서 사용
        "owner_id": row["owner_id"],
        "current_phase": row["current_phase"],
        "phases_completed": row["phases_completed"],
        "failed_phase": row["failed_phase"],
        # Storage 필드 복원 — download 엔드포인트가 서버 재시작 후에도 정상 동작하려면 필수
        "storage_path_docx": row["storage_path_docx"],
        "storage_path_pptx": row["storage_path_pptx"],
        "storage_path_rfp": row["storage_path_rfp"],
        "storage_upload_failed": row["storage_upload_failed"],
        "proposal_state": {"rfp_content": row["rfp_content"] or ""},
        **artifacts
    }
    self._sessions[proposal_id] = session
    return session
```

### update_session
```python
async def update_session(self, proposal_id, updates):
    session = await self.get_session(proposal_id)
    session.update(updates)
    db_fields = {}
    for key in ("status", "current_phase", "phases_completed", "failed_phase"):
        if key in updates:
            db_fields[key] = updates[key]
    if db_fields:
        client = await get_async_client()
        await client.table("proposals").update(db_fields).eq("id", proposal_id).execute()
    return session
```

### phase_executor.py async 전환 + 토큰 로깅

```python
async def _update_status(self, phase_name):
    await self.session_manager.update_session(
        self.proposal_id, {"current_phase": phase_name, "status": "running"}
    )  # DB 쓰기 -> Realtime 발동

async def _save_artifact(self, n, artifact):
    await self.session_manager.update_session(
        self.proposal_id,
        {f"phase_artifact_{n}": artifact.model_dump(), "phases_completed": n}
    )
    client = await get_async_client()
    await client.table("proposal_phases").upsert({
        "proposal_id": self.proposal_id,
        "phase_num": n,
        "phase_name": artifact.phase_name,
        "artifact_json": artifact.model_dump()
    }, on_conflict="proposal_id,phase_num").execute()

async def _log_usage(self, phase_num, usage):
    # team_id: create_session 시 session에 저장된 값 참조
    session = await self.session_manager.get_session(self.proposal_id)
    client = await get_async_client()
    await client.table("usage_logs").insert({
        "proposal_id": self.proposal_id,
        "team_id": session.get("team_id"),   # ← session에서 가져옴
        "owner_id": session.get("owner_id"),
        "phase_num": phase_num,
        "model": self.model,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens
    }).execute()

async def _handle_failure(self, phase_num, error):
    error_msg = str(error)[:500]  # 최대 500자 저장
    logger.error(f"Phase {phase_num} 실패 (proposal={self.proposal_id}): {error_msg}")
    await self.session_manager.update_session(
        self.proposal_id,
        {"status": "failed", "failed_phase": phase_num,
         "current_phase": f"phase{phase_num}_failed"}
    )
    # 에러 내용을 notes 컬럼에 저장 (추후 디버깅·재시도 판단용)
    client = await get_async_client()
    await client.table("proposals").update({
        "notes": f"[Phase {phase_num} error] {error_msg}"
    }).eq("id", self.proposal_id).execute()
```

---

## 8. 파일 저장소 (Supabase Storage)

```
Bucket: "proposals" (private)
경로:   proposals/{uuid}/proposal.docx
        proposals/{uuid}/proposal.pptx
        proposals/{uuid}/rfp_original.pdf

업로드 (phase5 완료 후):
  client.storage.from_("proposals").upload(path, file_bytes)

다운로드 (서명 URL, 1시간 유효):
  url = client.storage.from_("proposals").create_signed_url(path, 3600)
  return RedirectResponse(url)
```

### Storage 업로드 실패 처리

```python
# phase_executor.py — phase5 완료 후
async def _upload_to_storage(self, uuid, docx_bytes, pptx_bytes):
    client = await get_async_client()
    docx_path = f"proposals/{uuid}/proposal.docx"
    pptx_path = f"proposals/{uuid}/proposal.pptx"
    docx_ok = pptx_ok = False
    try:
        await client.storage.from_("proposals").upload(
            docx_path, docx_bytes,
            file_options={"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
        )
        docx_ok = True
        await client.storage.from_("proposals").upload(
            pptx_path, pptx_bytes,
            file_options={"content-type": "application/vnd.openxmlformats-officedocument.presentationml.presentation"}
        )
        pptx_ok = True
    except Exception as e:
        logger.error(f"Storage 업로드 실패: {e}")
    finally:
        # 개별 업로드 성공분은 저장 — 부분 실패 시에도 docx 경로 유실 방지
        update_fields = {
            "storage_path_docx": docx_path if docx_ok else None,
            "storage_path_pptx": pptx_path if pptx_ok else None,
            "storage_upload_failed": not (docx_ok and pptx_ok)
        }
        await client.table("proposals").update(update_fields).eq("id", uuid).execute()
        # 인메모리 세션도 동기화 — upload 직후 download 요청 시 404 방지
        await self.session_manager.update_session(uuid, update_fields)
        # 프론트엔드: storage_upload_failed=True 시 안내 메시지 표시

# /download 엔드포인트 — 로컬 폴백
async def download_document(...):
    session = await session_manager.get_session(proposal_id)
    if session.get("storage_upload_failed"):
        # 로컬 파일로 폴백 (서버에 파일이 있는 경우)
        return FileResponse(local_path)
    if file_type not in ("docx", "pptx"):
        raise HTTPException(400, "file_type은 docx 또는 pptx여야 합니다")
    # 검증 순서 중요: file_type 먼저 → 이후 storage_path 조회 (순서 반대 시 400 도달 불가)
    storage_path = session.get(f"storage_path_{file_type}")
    if not storage_path:
        raise HTTPException(404, "파일을 찾을 수 없습니다")
    client = await get_async_client()  # client 정의 (누락 시 NameError)
    res = await client.storage.from_("proposals").create_signed_url(storage_path, 3600)
    # supabase-py v2: AsyncClient.storage는 res.data["signedUrl"] 반환
    signed_url = res.data["signedUrl"] if hasattr(res, "data") else res["signedURL"]
    return RedirectResponse(signed_url)
```

변경 대상:
- docx_builder.py, pptx_builder.py: 반환값 (bytes, path) 튜플로 수정
- proposals 테이블: storage_upload_failed 컬럼 포함 (DDL에 포함)

---

## 9. 프론트엔드 실시간 상태 (Supabase Realtime)

proposals.current_phase, proposals.status가 DB에 쓰이므로
Realtime 이벤트가 실제로 발동됨 (_update_status -> DB 쓰기 연동).

### Phase 예상 소요 시간
```typescript
const PHASE_ESTIMATES = {
  phase1: { label: "RFP 분석", minutes: 2 },
  phase2: { label: "경쟁사 분석", minutes: 3 },
  phase3: { label: "전략 수립", minutes: 2 },
  phase4: { label: "제안서 작성", minutes: 5 },
  phase5: { label: "품질 검증", minutes: 2 },
} as const
```

### Realtime 구독 훅
```typescript
useEffect(() => {
  const channel = supabase
    .channel(`proposal-${proposalId}`)
    .on('postgres_changes', {
      event: 'UPDATE', schema: 'public', table: 'proposals',
      filter: `id=eq.${proposalId}`
    }, (payload) => {
      setStatus(payload.new.status)
      setCurrentPhase(payload.new.current_phase)
      setPhasesCompleted(payload.new.phases_completed)
      setFailedPhase(payload.new.failed_phase)
      setStorageUploadFailed(payload.new.storage_upload_failed)
    })
    .subscribe()
  return () => supabase.removeChannel(channel)
}, [proposalId])
```

### 완료 알림 (이메일 v1 포함)

```typescript
// supabase/functions/proposal-complete/index.ts
// Trigger: proposals UPDATE (DB Webhook) — status='completed' 변경 시에만 처리
const { id: proposal_id, title, owner_id, status } = event.record
// UPDATE 이벤트는 모든 컬럼 변경에 발동 → completed 아닌 경우 즉시 종료
if (status !== "completed") return new Response("skip", { status: 200 })

// owner 이메일 조회 (proposals 테이블에 email 컬럼 없으므로 admin API 사용)
const { data: ownerData } = await supabase.auth.admin.getUserById(owner_id)
const owner_email = ownerData?.user?.email
if (!owner_email) return new Response("no owner email", { status: 200 })

await resend.emails.send({
  from: "noreply@tenopa.ai",
  to: owner_email,
  subject: `[제안서 완료] ${title}`,
  html: `<p>제안서가 완료되었습니다.<br>
         <a href="${FRONTEND_URL}/proposals/${proposal_id}">결과 확인하기</a></p>`
})
// Resend 무료: 3,000건/월
```

### 댓글 알림 (team_id NULL 케이스 처리)
```typescript
// supabase/functions/comment-notify/index.ts
const comment = event.record  // DB Webhook 이벤트의 신규 행 (INSERT payload)
// Supabase JS 클라이언트는 { data: {...}, error: null } 구조를 반환
// proposal.team_id(X) → 구조분해 후 proposal.team_id(O) 접근
const { data: proposal, error: proposalErr } = await supabase
  .from("proposals").select("team_id, owner_id, title")
  .eq("id", comment.proposal_id).single()

// team_id가 NULL이면 개인 소유 제안서 → 알림 없음
if (!proposal?.team_id) return new Response("no team, skip", { status: 200 })

// 팀 멤버 조회 (작성자 제외)
const members = await supabase
  .from("team_members").select("user_id")
  .eq("team_id", proposal.team_id)
  .neq("user_id", comment.user_id)

// 각 멤버에게 이메일 발송
// auth.users 이메일은 admin API로 조회 (team_members에 email 컬럼 없음)
for (const member of members.data) {
  const { data: userData } = await supabase.auth.admin.getUserById(member.user_id)
  const member_email = userData?.user?.email
  if (!member_email) continue
  await resend.emails.send({ to: member_email, subject: "[댓글] ..." })
}
```

---

## 10. Next.js 프론트엔드

```
frontend/
  middleware.ts                 ← 인증 보호 라우트 (필수)
  app/
    layout.tsx                  # Supabase Auth Provider
    login/page.tsx              # 이메일 로그인
    onboarding/page.tsx         # 신규 가입자 온보딩
    proposals/
      page.tsx                  # 목록 (검색, 필터, 페이지네이션, EmptyState)
      new/page.tsx              # RFP 업로드 폼
      [id]/page.tsx             # 진행상태 + 결과 뷰어 + 댓글
    admin/page.tsx              # 팀원 관리
    invitations/accept/page.tsx # 초대 수락 콜백
  components/
    PhaseProgress.tsx           # 5단계 진행 바 + 예상 시간
    PhaseRetryButton.tsx        # 실패 시 재시작 버튼
    ResultViewer.tsx            # artifact_json 웹 뷰어
    FileUploadZone.tsx          # 드래그앤드롭 + 제약 안내
    CommentThread.tsx           # 댓글 스레드
    TeamInviteModal.tsx         # 초대 모달
    EmptyState.tsx              # 재사용 빈 상태 컴포넌트
  lib/
    supabase.ts                 # createBrowserClient (브라우저용)
    supabase-server.ts          # createServerClient (서버 컴포넌트용, @supabase/ssr)
    api.ts                      # FastAPI 호출 + Authorization 헤더 자동 주입
    hooks/
      useProposals.ts           # SWR + 페이지네이션 + 검색
      usePhaseStatus.ts         # Supabase Realtime 구독
```

### middleware.ts — 인증 보호 라우트

```typescript
// frontend/middleware.ts
import { createServerClient } from "@supabase/ssr"
import { NextResponse, type NextRequest } from "next/server"

const PUBLIC_PATHS = ["/login", "/invitations/accept"]

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  if (PUBLIC_PATHS.some(p => pathname.startsWith(p))) {
    return NextResponse.next()
  }

  const response = NextResponse.next()
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get: (name) => request.cookies.get(name)?.value,
        set: (name, value, options) => {
          // middleware에서는 response에 쿠키를 써야 Next.js가 전파함
          response.cookies.set({ name, value, ...options })
        },
        remove: (name, options) => {
          response.cookies.set({ name, value: "", ...options })
        }
      }
    }
  )
  // getSession()은 쿠키를 그대로 읽을 뿐 JWT 서버 검증을 하지 않음
  // 보안을 위해 getUser()로 Supabase Auth 서버에 검증 요청
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    return NextResponse.redirect(new URL("/login", request.url))
  }
  return response
}

export const config = { matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"] }
```

### 세션 만료 처리 (lib/api.ts)
```typescript
// 401 응답 시 자동 로그아웃 + 리다이렉트
if (response.status === 401) {
  await supabase.auth.signOut()
  window.location.href = "/login"
  throw new Error("세션이 만료되었습니다. 다시 로그인해주세요.")
}
```

---

## 11. UX 설계 세부 사항

### 11-1. 온보딩 플로우
```
가입 완료 -> /onboarding
  -> "팀으로 사용" / "혼자 사용" 선택
  -> 팀 선택: 팀 이름 입력 -> 팀원 초대(선택) -> /proposals
  -> 개인 선택: /proposals
```

### 11-2. 빈 상태 (EmptyState)
| 화면 | 메시지 | 액션 |
|------|--------|------|
| /proposals (없음) | "첫 제안서를 만들어보세요" | "새 제안서 작성" |
| /proposals (검색 결과 없음) | "{q}에 해당하는 제안서가 없습니다" | "검색어 지우기" |
| /admin (팀원 없음) | "팀원을 초대하면 함께 검토할 수 있습니다" | "팀원 초대" |

### 11-3. 실패 복구 UI (PhaseRetryButton)
```
status='failed' 시:
  -> "Phase {failed_phase}에서 오류가 발생했습니다"
  -> [Phase {failed_phase}부터 재시작] 버튼
     -> POST /api/v3.1/proposals/{id}/execute?start_phase={failed_phase}

status='failed', current_phase='interrupted' (서버 재시작):
  -> "서버 재시작으로 중단된 제안서입니다"
  -> [Phase {phases_completed+1}부터 재시작] 버튼

storage_upload_failed=true 시:
  -> "파일 저장 중 일시적인 오류가 발생했습니다. 다운로드 버튼을 클릭하면 파일을 받을 수 있습니다."
  -> /download 엔드포인트가 로컬 파일로 자동 폴백 (사용자 개입 불필요)
```

### 11-4. RFP 업로드 (FileUploadZone)
```
지원 형식: PDF, DOCX, TXT
HWP: 미지원 — "HWP 파일은 PDF/DOCX로 변환 후 업로드해주세요" (클라이언트 즉시 거부)
최대 크기: 10MB — 초과 시 즉시 오류 (서버 요청 전)
드래그앤드롭 + 파일 선택 버튼
업로드 진행 바 (%)
파일 선택 후 파일명 → rfp_title 기본값 자동 채움
```

### 11-5. 진행 상태 (PhaseProgress)
```
Phase별: 완료 체크 / 진행중 스피너+예상시간 / 대기 / 실패 X아이콘
진행 중: "예상 남은 시간: 약 N분" + 경과 시간 카운터
```

### 11-6. ResultViewer
```
Phase 1: RFP 요약 카드 (발주처, 예산, 기간, 핵심 요구사항)
Phase 2: 경쟁사 테이블 (업체명, 낙찰금액, 수주횟수)
Phase 3: 전략 카드 (차별화 포인트, 가격 전략)
Phase 4: 제안서 섹션별 본문 (아코디언)
Phase 5: 품질 점수 + 수정 항목

다운로드 버튼: storage_upload_failed=true → 안내 메시지
서명 URL: 만료(1h) 후 재클릭 → 새 서명 URL 자동 요청
```

---

## 12. 구현 순서

```
Step 1: DB + 기반 인프라
  database/schema.sql              전체 DDL (storage_upload_failed, 검색 인덱스 포함)
  app/utils/supabase_client.py     AsyncClient + asyncio.Lock
  app/config.py                    G2B_API_KEY, cors_origins, .hwp 제거
  app/main.py                      CORSMiddleware + lifespan
  app/middleware/auth.py           Supabase SDK JWT 검증 (별도 /auth/* 라우터 없음)

Step 2: 세션 영속성 + 파이프라인
  app/services/session_manager.py  전체 async + Supabase DB 연동 (team_id 저장 포함)
  app/services/phase_executor.py   async 전환 + _save_artifact + _log_usage + _handle_failure
  app/api/routes_v31.py            UUID4, await, start_phase, Storage URL

Step 3: 파일 저장소
  app/services/docx_builder.py     (bytes, path) 튜플 반환
  app/services/pptx_builder.py     (bytes, path) 튜플 반환
  app/services/phase_executor.py   Storage 업로드 + storage_upload_failed 처리

Step 4: G2B 실제 API
  app/services/g2b_service.py      4단계 + Rate Limiting (asyncio.sleep + retry)
  app/api/routes_g2b.py            G2B 프록시 라우터

Step 5: 팀 협업 API
  app/api/routes_team.py           역할 기반 권한 + 초대 upsert + 페이지네이션 + 검색
  supabase/functions/              proposal-complete, comment-notify (team_id NULL 처리)
  Supabase Dashboard               Edge Function Secrets (RESEND_API_KEY)
  Supabase Dashboard               Database Webhooks 설정 (Edge Function 트리거)
    proposals INSERT/UPDATE → proposal-complete 함수 연결
    comments INSERT → comment-notify 함수 연결
    방법: Dashboard > Database > Webhooks > Create a new hook

Step 6: 프론트엔드
  Next.js 초기화 + @supabase/ssr
  middleware.ts (인증 보호)
  페이지 + 컴포넌트 구현
  Realtime 훅 + 세션 만료 처리
```

---

## 13. 파일 변경 전체 요약

| 파일 | 유형 | 핵심 변경 |
|------|------|----------|
| database/schema.sql | 신규 | 8개 테이블 + 13개 RLS + REPLICA IDENTITY + 검색 인덱스 |
| app/config.py | 수정 | G2B_API_KEY, cors_origins, .hwp 제거 |
| app/main.py | 수정 | CORSMiddleware(settings.cors_origins) + lifespan |
| app/utils/supabase_client.py | 수정 | AsyncClient + asyncio.Lock |
| app/middleware/auth.py | 신규 | JWT 검증 (별도 /auth/* 라우터 없음) |
| app/services/session_manager.py | 수정 | 전체 async + Supabase DB + team_id/owner_id 저장 |
| app/services/phase_executor.py | 수정 | async + _log_usage(team_id from session) + _handle_failure + Storage |
| app/services/g2b_service.py | 신규 | 실제 4단계 API + Rate Limiting + retry |
| app/services/docx_builder.py | 수정 | (bytes, path) 튜플 반환 |
| app/services/pptx_builder.py | 수정 | (bytes, path) 튜플 반환 |
| app/api/routes_v31.py | 수정 | UUID4, await, start_phase, Storage URL |
| app/api/routes_team.py | 신규 | 역할 기반 권한 + 초대 upsert + 검색 |
| app/api/routes_g2b.py | 신규 | G2B 프록시 |
| app/api/routes.py | 수정 | 신규 라우터 등록 |
| supabase/functions/proposal-complete/ | 신규 | 완료 이메일 |
| supabase/functions/comment-notify/ | 신규 | 댓글 알림 (team_id NULL 처리) |
| frontend/ | 신규 | Next.js 앱 전체 (middleware.ts 포함) |

---

## 14. 성공 기준

| 기준 | 검증 방법 |
|------|----------|
| UUID4 proposal_id | DB proposals.id 형식 확인 |
| JWT 인증 | Bearer 없는 요청 -> 401 |
| 세션 영속성 | /execute 후 서버 재시작 -> /status 200 복원 |
| Realtime 동작 | Phase 진행 시 proposals.current_phase DB 변경 확인 |
| G2B 실제 데이터 | Phase 2 결과에 실제 업체명 + 낙찰금액 포함 |
| G2B Rate Limit | 429 오류 없이 4단계 순차 호출 성공 |
| 파일 영속성 | 서버 재시작 후 /download 서명 URL 정상 |
| Storage 실패 처리 | Storage 오류 시 storage_upload_failed=true 기록 + 로컬 폴백 |
| 팀 초대 흐름 | 초대 -> 수락 -> team_members 자동 생성 |
| 재초대 | 만료된 초대 재전송 시 409 없이 갱신 |
| 역할 권한 | viewer가 win-result 수정 시 403 |
| 토큰 로깅 | usage_logs 제안서 1건당 5개 행 + team_id 포함 |
| 페이지네이션 | /proposals?page=2 정상 응답 |
| 검색 | /proposals?q=키워드 제목 필터 동작 |
| CORS | Next.js localhost:3000 -> FastAPI 정상 통신 |
| 실패 복구 UI | Phase 실패 후 재시작 버튼 -> 해당 Phase부터 재실행 |
| 완료 이메일 | Phase5 완료 후 owner 이메일 수신 |
| 댓글 알림 | 팀 있는 제안서: 팀원 이메일 수신 / 팀 없는 제안서: 알림 없음 |
| 빈 상태 | 제안서 0개 상태 EmptyState 표시 |
| HWP 차단 | .hwp 선택 시 즉시 오류 (서버 요청 전) |
| 세션 만료 처리 | 401 -> /login 리다이렉트 |
| 인증 보호 라우트 | 비로그인 /proposals 접근 -> /login 리다이렉트 |
| middleware.ts | Next.js middleware 동작 확인 |
