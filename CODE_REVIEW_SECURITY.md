# 코드 품질 검토 보고서
**검토 대상**: routes_g2b.py, deps.py, config.py
**검토 일시**: 2026-04-09
**심각도**: 7개 HIGH 이슈, 12개 MEDIUM 이슈, 5개 LOW 이슈

---

## 1. 에러 메시지 처리 - 민감정보 누출 예방

### 1.1 HIGH: 예외 메시지 직접 노출
**위치**: routes_g2b.py:138, 172, 427 등
**문제**:
```python
# ❌ 나쁜 예: 예외 전체를 사용자에게 노출
except Exception as e:
    logger.error(f"bid-search 오류: {e}")
    raise G2BServiceError("나라장터 API 호출 중 오류가 발생했습니다.")
```

예외 객체 `e`를 직접 로깅하면:
- 내부 구조 정보 노출 가능
- 데이터베이스 연결 정보 누설 위험
- 타사 API 키 또는 경로 정보 유출 가능

**권장 사항**:
```python
# ✓ 좋은 예: 타입과 로그ID만 기록, 민감정보는 필터링
except Exception as e:
    error_id = f"ERR-{int(time.time())}-{random.randint(1000, 9999)}"
    logger.error(
        f"bid-search 처리 실패",
        extra={
            "error_id": error_id,
            "error_type": type(e).__name__,
            # 예외 메시지는 로깅하지 않음 (민감정보 포함 가능)
        }
    )
    raise G2BServiceError(
        f"요청 처리 중 오류가 발생했습니다 (오류코드: {error_id})"
    )
```

### 1.2 HIGH: 배경 작업에서 예외 메시지 노출
**위치**: routes_g2b.py:231, 244
**문제**:
```python
# ❌ 나쁜 예
logger.error(f"✗ 공고 분석 문서 생성 실패: {type(e).__name__}: {str(e)[:100]}")
```
배경 작업에서도 예외 메시지 일부가 로그에 남음.

**개선안**:
```python
# ✓ 좋은 예
logger.error(
    "배경 작업 실패",
    extra={
        "error_type": type(e).__name__,
        "bid_no": bid_no,
        "task": "generate_bid_analysis_documents"
    }
)
```

---

## 2. 환경변수 검증 - 누락 시 에러 처리

### 2.1 HIGH: 불완전한 개발 환경 검증
**위치**: deps.py:40-45
**문제**:
```python
def _init_dev_user():
    """환경변수에서 개발 모드 사용자 정보 읽기."""
    global _DEV_USER_ID, _DEV_USER_EMAIL, _DEV_USER_ORG_ID, _DEV_USER_TEAM_ID
    if settings.dev_mode:
        if not settings.dev_user_id or not settings.dev_user_org_id:
            raise RuntimeError(
                "DEV_MODE=true일 때 DEV_USER_ID, DEV_USER_EMAIL, "
                "DEV_USER_ORG_ID, DEV_USER_TEAM_ID 환경변수는 필수입니다."
            )
```

**문제점**:
1. `dev_user_email` 검증 없음 (라인 43에서 기본값 설정)
2. 런타임 에러 → 서버 시작 중 세션 런타임 예외 (BAD_UX)
3. 에러 메시지 구체성 부족 (어느 변수가 누락? 정확한 이름?)

**권장 사항**:
```python
# ✓ 좋은 예: 구체적인 검증 + 명확한 에러 메시지
def _init_dev_user():
    """개발 모드 사용자 정보 검증 및 초기화."""
    global _DEV_USER_ID, _DEV_USER_EMAIL, _DEV_USER_ORG_ID, _DEV_USER_TEAM_ID

    if not settings.dev_mode:
        return

    # 필수 필드 검증
    required_vars = {
        "DEV_USER_ID": settings.dev_user_id,
        "DEV_USER_ORG_ID": settings.dev_user_org_id,
    }

    missing = [k for k, v in required_vars.items() if not v]
    if missing:
        raise ValueError(
            f"DEV_MODE=true에서 필수 환경변수 누락: {', '.join(missing)}\n"
            f"설정 위치: ~/.env 또는 환경변수 직접 설정"
        )

    # 선택 필드 기본값
    _DEV_USER_ID = settings.dev_user_id
    _DEV_USER_EMAIL = settings.dev_user_email or "dev@tenopa.co.kr"
    _DEV_USER_ORG_ID = settings.dev_user_org_id
    _DEV_USER_TEAM_ID = settings.dev_user_team_id or ""

    logger.warning(
        f"개발 모드 활성화: Mock 사용자 [{_DEV_USER_ID}] 사용중"
    )
```

### 2.2 MEDIUM: 중복된 환경변수 검증
**위치**: config.py:145-156, deps.py:37-50
**문제**:
- config.py에서 `validate_required_keys()` 체크
- deps.py에서 별도로 `_init_dev_user()` 체크
- 책임이 분산되어 있고 중복 로직 존재

**권장 사항**:
```python
# config.py에 통합 검증 로직 추가
class Settings(BaseSettings):
    # ... 기존 코드 ...

    def validate_dev_mode(self) -> list[str]:
        """개발 모드 필수 환경변수 검증."""
        if not self.dev_mode:
            return []

        missing = []
        if not self.dev_user_id:
            missing.append("DEV_USER_ID")
        if not self.dev_user_org_id:
            missing.append("DEV_USER_ORG_ID")

        return missing

# main.py 또는 app 초기화 시
_dev_missing = settings.validate_dev_mode()
if _dev_missing:
    raise RuntimeError(
        f"DEV_MODE=true 시 필수 환경변수 누락: {', '.join(_dev_missing)}"
    )
```

---

## 3. 타입 안전성 - None 체크, Optional 처리

### 3.1 HIGH: Optional 타입 누락으로 인한 None 참조 위험
**위치**: routes_g2b.py:80-90
**문제**:
```python
for item in items:
    bid_no = item.get("bid_no") or item.get("bidNo")
    if not bid_no:
        continue

    # bid_no가 None일 가능성이 있음 (이후 코드에서 안전하지 않음)
    try:
        result = await client.table("bid_announcements").select("id").eq(
            "org_id", current_user.org_id  # current_user.org_id: None 가능성?
        ).eq("bid_no", bid_no).execute()
```

**문제점**:
1. `current_user.org_id`가 None인 경우 미처리
2. `bid_no`가 문자열 타입 보장 안 됨 (빈 문자열, 정수 등)
3. RLS 필터링이 `org_id=None`으로 동작할 수 있음

**권장 사항**:
```python
# ✓ 좋은 예: 타입 검증 강화
def _validate_org_id(org_id: str | None) -> str:
    """조직 ID 검증."""
    if not org_id or not isinstance(org_id, str):
        raise ValueError("유효하지 않은 조직 ID")
    return org_id.strip()

def _validate_bid_no(bid_no: str | int | None) -> str:
    """공고 번호 검증."""
    if not bid_no:
        raise ValueError("공고 번호는 필수입니다")

    bid_no_str = str(bid_no).strip()
    if not bid_no_str or not bid_no_str.isalnum():
        raise ValueError(f"유효하지 않은 공고 번호: {bid_no}")

    return bid_no_str

# 사용
for item in items:
    try:
        bid_no = _validate_bid_no(item.get("bid_no") or item.get("bidNo"))
        org_id = _validate_org_id(current_user.org_id)

        result = await client.table("bid_announcements").select("id").eq(
            "org_id", org_id
        ).eq("bid_no", bid_no).execute()
        # ...
    except ValueError as e:
        logger.warning(f"데이터 검증 실패: {e}")
        continue
```

### 3.2 MEDIUM: 딕셔너리 키 접근 시 KeyError 위험
**위치**: routes_g2b.py:320-326
**문제**:
```python
primary = results[0]
return {
    "bid_no": bid_no,
    "status": "found",
    "award": {
        "winner": primary.get("bidwinnrNm", primary.get("sucsfBidderNm", "")),
        "amount": _parse_amount(primary.get("sucsfBidAmt", primary.get("presmptPrce"))),
        # primary가 dict가 아니면 AttributeError!
    },
```

**개선안**:
```python
# ✓ 좋은 예: 타입 검증
if not results or not isinstance(results[0], dict):
    return {
        "bid_no": bid_no,
        "status": "error",
        "message": "유효하지 않은 응답 형식",
    }

primary = results[0]
# 이후 안전한 접근 가능
```

### 3.3 MEDIUM: 함수 반환 타입 미정의
**위치**: routes_g2b.py:453-464
**문제**:
```python
def _normalize_bid_detail(raw: dict) -> dict:
    """공고 상세 raw 데이터를 정규화."""
    return {
        "project_name": raw.get("bidNtceNm", ""),
        "client": raw.get("ntceInsttNm", raw.get("dminsttNm", "")),
        # ...
    }
```

**문제점**:
- `raw`가 dict이 아니면 `.get()` 호출 실패
- None 입력값 미처리

**개선안**:
```python
# ✓ 좋은 예
def _normalize_bid_detail(raw: dict | None) -> dict:
    """공고 상세 정보 정규화."""
    if not raw or not isinstance(raw, dict):
        return {
            "project_name": "",
            "client": "",
            "budget": None,
            "deadline": "",
            "bid_method": "",
            "contract_method": "",
        }

    return {
        "project_name": raw.get("bidNtceNm", ""),
        # ...
    }
```

---

## 4. 에러 처리 - try-except 커버리지

### 4.1 HIGH: 과도하게 광범위한 Exception 캐치
**위치**: routes_g2b.py 전반
**문제**:
```python
try:
    # 여러 라인의 코드
    async with G2BService() as g2b:
        items = await g2b.search_bid_announcements(...)

    # Supabase 작업
    client = await get_async_client()
    for item in items:
        # 저장 로직
except Exception as e:  # ❌ 너무 광범위!
    logger.error(f"bid-search 오류: {e}")
    raise G2BServiceError("나라장터 API 호출 중 오류가 발생했습니다.")
```

**문제점**:
1. 의도하지 않은 예외 (예: 메모리 부족, KeyboardInterrupt)도 캐치
2. 어느 라인에서 오류가 발생했는지 불명확
3. 복구 가능한 오류와 불가능한 오류 구분 없음

**권장 사항**:
```python
# ✓ 좋은 예: 세밀한 예외 처리
try:
    async with G2BService() as g2b:
        items = await g2b.search_bid_announcements(...)
except RuntimeError as e:
    raise _classify_g2b_error(e)
except Exception as e:
    logger.error(f"G2B 서비스 오류: {type(e).__name__}")
    raise G2BServiceError("나라장터 API 호출 중 오류가 발생했습니다.")

# Supabase 작업은 별도 try-except
client = await get_async_client()
saved_count = 0

for item in items:
    bid_no = item.get("bid_no") or item.get("bidNo")
    if not bid_no:
        continue

    try:
        # 저장 로직 (org 필터링)
        result = await client.table("bid_announcements").select("id").eq(
            "org_id", str(current_user.org_id)
        ).eq("bid_no", bid_no).execute()

        is_update = len(result.data) > 0
        data = {...}

        if is_update:
            bid_id = result.data[0]["id"]
            data.pop("created_by")
            await client.table("bid_announcements").update(data).eq(
                "id", bid_id
            ).execute()
        else:
            await client.table("bid_announcements").insert(data).execute()

        saved_count += 1
        logger.info(f"공고 저장됨: {bid_no}")

    except Exception as e:
        logger.warning(
            f"개별 공고 저장 실패: {bid_no}",
            extra={"error_type": type(e).__name__}
        )
        continue
```

### 4.2 MEDIUM: 백그라운드 작업의 예외 처리
**위치**: routes_g2b.py:210-231
**문제**:
```python
async def _analyze_documents():
    try:
        doc_paths = await generate_bid_analysis_documents(...)
        await client.table("bid_announcements").update({...}).eq("id", bid["id"]).execute()
        logger.info(f"✓ 공고 분석 문서 생성 완료")
    except Exception as e:
        logger.error(f"✗ 공고 분석 문서 생성 실패: {type(e).__name__}: {str(e)[:100]}")
```

**문제점**:
- 백그라운드 작업이 실패해도 사용자에게 알림 없음
- DB 업데이트 실패 여부 추적 불가
- 재시도 로직 없음

**권장 사항**:
```python
# ✓ 좋은 예: 백그라운드 작업 복구 로직
async def _analyze_documents():
    max_retries = 2
    for attempt in range(max_retries):
        try:
            doc_paths = await generate_bid_analysis_documents(
                bid_no=bid["bid_no"],
                bid_title=bid["bid_title"],
                ...
            )

            await client.table("bid_announcements").update({
                "md_rfp_analysis_path": doc_paths["md_rfp_analysis_path"],
                "md_notice_path": doc_paths["md_notice_path"],
                "md_instruction_path": doc_paths["md_instruction_path"],
                "analysis_status": "analyzed",
            }).eq("id", bid["id"]).execute()

            logger.info(
                f"공고 분석 완료",
                extra={"bid_no": bid["bid_no"], "attempt": attempt + 1}
            )
            return

        except Exception as e:
            logger.warning(
                f"공고 분석 재시도 (시도 {attempt + 1}/{max_retries})",
                extra={
                    "bid_no": bid["bid_no"],
                    "error_type": type(e).__name__,
                    "attempt": attempt + 1,
                }
            )

            if attempt == max_retries - 1:
                # 최종 실패: DB에 오류 상태 기록
                try:
                    await client.table("bid_announcements").update({
                        "analysis_status": "failed",
                        "analysis_error": f"{type(e).__name__}",
                    }).eq("id", bid["id"]).execute()
                except Exception:
                    logger.error(f"오류 상태 업데이트 실패: {bid['bid_no']}")
                return

            await asyncio.sleep(2 ** attempt)  # 지수 백오프
```

---

## 5. 매직 스트링 - 상수화 가능한 문자열

### 5.1 MEDIUM: 분산된 매직 스트링
**위치**: routes_g2b.py 전반
**문제**:
```python
# 여러 곳에 "Go"/"No-Go" 하드코딩
if decision not in ["Go", "No-Go"]:
    raise G2BServiceError("의사결정은 'Go' 또는 'No-Go'만 가능합니다.")

# 여러 곳에 테이블명 하드코딩
await client.table("bid_announcements").select(...)
await client.table("bid_announcements").update(...)

# 상태값 하드코딩
"analysis_status": "pending"
"analysis_status": "analyzed"
"decision": "pending"
```

**권장 사항**:
```python
# ✓ 좋은 예: 상수 정의 (routes_g2b.py 최상단)
class BidConstants:
    """입찰 공고 관련 상수"""

    # 테이블명
    TABLE_BID_ANNOUNCEMENTS = "bid_announcements"
    TABLE_BID_RESULTS = "bid_results"
    TABLE_PROPOSALS = "proposals"

    # 의사결정 값
    DECISION_GO = "Go"
    DECISION_NO_GO = "No-Go"
    DECISION_VALID = {DECISION_GO, DECISION_NO_GO}

    # 분석 상태
    STATUS_PENDING = "pending"
    STATUS_ANALYZED = "analyzed"
    STATUS_FAILED = "failed"

    # 결정 상태
    DECISION_STATUS_PENDING = "pending"

    # 칼럼명
    COL_ORG_ID = "org_id"
    COL_BID_NO = "bid_no"
    COL_ID = "id"

# 사용
if decision not in BidConstants.DECISION_VALID:
    raise G2BServiceError(
        f"의사결정은 '{BidConstants.DECISION_GO}' 또는 "
        f"'{BidConstants.DECISION_NO_GO}'만 가능합니다."
    )

result = await client.table(BidConstants.TABLE_BID_ANNOUNCEMENTS).select(
    BidConstants.COL_ID
).eq(BidConstants.COL_ORG_ID, org_id).eq(
    BidConstants.COL_BID_NO, bid_no
).execute()
```

---

## 6. 함수 책임 - 단일 책임 원칙 (SRP)

### 6.1 HIGH: 함수가 너무 많은 책임을 가짐
**위치**: routes_g2b.py:49-139 (`bid_search` 함수)
**문제**:
```python
@router.get("/bid-search")
async def bid_search(...):
    """
    1. 나라장터 API 호출
    2. 결과 정규화
    3. Supabase에 저장
    4. 개별 저장 오류 처리
    5. 응답 포맷팅
    """
```

함수가 90줄 이상이고 5가지 책임을 수행 → 테스트 어려움, 유지보수성 떨어짐.

**권장 사항**:
```python
# ✓ 좋은 예: 책임 분리

# 1. 검색 책임만 담당
async def _search_bids(keyword: str, num_of_rows: int, page_no: int):
    """나라장터 검색 API 호출."""
    async with G2BService() as g2b:
        return await g2b.search_bid_announcements(
            keyword=keyword,
            num_of_rows=num_of_rows,
            page_no=page_no,
        )

# 2. 데이터 정규화 책임만 담당
async def _normalize_bid_item(item: dict, org_id: str, user_id: str):
    """검색 결과를 저장 가능한 형식으로 변환."""
    bid_no = item.get("bid_no") or item.get("bidNo")
    if not bid_no:
        return None

    return {
        "org_id": org_id,
        "bid_no": bid_no,
        "bid_title": item.get("bid_title") or item.get("bidTitle") or "제목 미정",
        "agency": item.get("agency") or item.get("agencyName"),
        "budget_amount": item.get("budget_amount") or item.get("budgetAmount"),
        "deadline_date": item.get("deadline_date") or item.get("deadlineDate"),
        "content_text": item.get("content_text", ""),
        "raw_data": item,
        "analysis_status": "pending",
        "decision": "pending",
        "created_by": user_id,
    }

# 3. 저장 책임만 담당
async def _save_bids(
    client,
    bids: list[dict],
    org_id: str,
) -> tuple[int, list[str]]:
    """공고 목록을 데이터베이스에 저장."""
    saved_count = 0
    errors = []

    for bid in bids:
        if not bid:
            continue

        bid_no = bid["bid_no"]
        try:
            result = await client.table("bid_announcements").select("id").eq(
                "org_id", org_id
            ).eq("bid_no", bid_no).execute()

            is_update = len(result.data) > 0

            if is_update:
                bid_id = result.data[0]["id"]
                bid.pop("created_by", None)
                await client.table("bid_announcements").update(bid).eq(
                    "id", bid_id
                ).execute()
            else:
                await client.table("bid_announcements").insert(bid).execute()

            saved_count += 1
            logger.info(f"공고 저장됨: {bid_no}")

        except Exception as e:
            errors.append(f"{bid_no}: {type(e).__name__}")
            logger.warning(f"공고 저장 실패: {bid_no}")

    return saved_count, errors

# 4. 엔드포인트는 조율만 담당
@router.get("/bid-search")
async def bid_search(
    keyword: str = Query(...),
    num_of_rows: int = Query(20, ge=1, le=100),
    page_no: int = Query(1, ge=1),
    current_user=Depends(get_current_user),
):
    """나라장터 공고 검색 및 저장."""
    try:
        # 1. 검색
        items = await _search_bids(keyword, num_of_rows, page_no)

        # 2. 정규화
        client = await get_async_client()
        normalized_bids = []
        for item in items:
            bid = await _normalize_bid_item(
                item,
                org_id=str(current_user.org_id),
                user_id=str(current_user.id),
            )
            if bid:
                normalized_bids.append(bid)

        # 3. 저장
        saved_count, errors = await _save_bids(
            client, normalized_bids, str(current_user.org_id)
        )

        logger.info(
            f"공고 검색 완료: {saved_count}/{len(items)} 저장됨"
        )

        return {
            "keyword": keyword,
            "page_no": page_no,
            "num_of_rows": num_of_rows,
            "total_count": len(items),
            "saved_count": saved_count,
            "items": items,
            "errors": errors if errors else None,
        }

    except RuntimeError as e:
        raise _classify_g2b_error(e)
    except Exception as e:
        logger.error(f"검색 요청 처리 실패", extra={"error_type": type(e).__name__})
        raise G2BServiceError("나라장터 검색 중 오류가 발생했습니다.")
```

### 6.2 MEDIUM: RLS 필터링 구현 불일치
**위치**: routes_g2b.py:87, 199-200
**문제**:
```python
# 라인 87: bid_announcements 쿼리에서 RLS 필터링
result = await client.table("bid_announcements").select("id").eq(
    "org_id", current_user.org_id
).eq("bid_no", bid_no).execute()

# 라인 199-200: RLS 필터링 수동으로 구현
result = await client.table("bid_announcements").select(
    "id, bid_no, bid_title, agency, budget_amount, deadline_date, raw_data"
).eq("org_id", str(current_user.org_id)).eq("bid_no", bid_no).maybe_single().execute()
```

**문제점**:
- 일부는 `current_user.org_id` 직접 사용
- 일부는 `str(current_user.org_id)` 변환
- RLS 필터링이 완전하지 않을 수 있음 (row-level-security 정책 우회 위험)

**권장 사항**:
```python
# ✓ 좋은 예: 일관된 RLS 구현

class RLSFilter:
    """Row-Level Security 필터 헬퍼."""

    @staticmethod
    def org_id(org_id: str | None) -> str:
        """조직 ID 검증 및 문자열 변환."""
        if not org_id:
            raise ValueError("org_id는 필수입니다")
        return str(org_id).strip()

# 사용
org_id = RLSFilter.org_id(current_user.org_id)

result = await client.table("bid_announcements").select("id").eq(
    "org_id", org_id
).eq("bid_no", bid_no).execute()

# 프로덕션: Supabase RLS 정책 확인
# SELECT * FROM bid_announcements WHERE org_id = auth.user_id() 형태여야 함
```

---

## 7. 의존성 - 순환 참조나 강한 결합

### 7.1 MEDIUM: 순환 임포트 위험
**위치**: routes_g2b.py:16-24
**문제**:
```python
from app.api.deps import get_current_user  # deps.py
from app.exceptions import G2BExternalError  # exceptions.py
from app.services.g2b_service import G2BService  # services/g2b_service.py
from app.utils.supabase_client import get_async_client  # utils/supabase_client.py
```

**위험성**:
- `deps.py` → `config.py` (settings 읽음)
- `g2b_service.py` → `deps.py` 또는 다른 모듈 (순환 참조 가능)
- 강한 결합으로 인해 테스트 어려움

**권장 사항**:
```python
# ✓ 좋은 예: 의존성 주입으로 결합도 낮춤

# services/g2b_service.py
class G2BService:
    def __init__(self, client=None):
        self.client = client  # 주입 가능

# routes_g2b.py
@router.get("/bid-search")
async def bid_search(
    ...,
    g2b_service: G2BService = Depends(lambda: G2BService()),
):
    items = await g2b_service.search_bid_announcements(...)
```

### 7.2 MEDIUM: 전역 변수 사용
**위치**: deps.py:31-34, 46-49
**문제**:
```python
# ❌ 나쁜 예: 전역 변수
_DEV_USER_ID = None
_DEV_USER_EMAIL = None
_DEV_USER_ORG_ID = None
_DEV_USER_TEAM_ID = None

def _init_dev_user():
    global _DEV_USER_ID, _DEV_USER_EMAIL, ...
```

**문제점**:
- 스레드 안전성 문제
- 테스트에서 상태 격리 불가
- 전역 상태 추적 어려움

**권장 사항**:
```python
# ✓ 좋은 예: 클래스 기반 구현

class DevUserConfig:
    """개발 모드 사용자 설정."""

    _instance: "DevUserConfig | None" = None

    def __init__(self):
        self.user_id: str | None = None
        self.email: str | None = None
        self.org_id: str | None = None
        self.team_id: str | None = None

    @classmethod
    def get_instance(cls) -> "DevUserConfig":
        """싱글톤 인스턴스 반환."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def initialize(self, settings: Settings):
        """설정에서 초기화."""
        if not settings.dev_mode:
            return

        missing = []
        if not settings.dev_user_id:
            missing.append("DEV_USER_ID")
        if not settings.dev_user_org_id:
            missing.append("DEV_USER_ORG_ID")

        if missing:
            raise ValueError(
                f"필수 환경변수 누락: {', '.join(missing)}"
            )

        self.user_id = settings.dev_user_id
        self.email = settings.dev_user_email or "dev@tenopa.co.kr"
        self.org_id = settings.dev_user_org_id
        self.team_id = settings.dev_user_team_id or ""

    async def get_current_user(self) -> CurrentUser:
        """개발 모드 사용자 반환."""
        if not self.user_id:
            raise AuthTokenExpiredError()

        return CurrentUser(
            id=self.user_id,
            email=self.email,
            name="Dev User",
            role="lead",
            org_id=self.org_id,
            team_id=self.team_id,
            division_id=None,
            status="active",
        )

# main.py 또는 앱 초기화
dev_config = DevUserConfig.get_instance()
dev_config.initialize(settings)
```

---

## 8. 추가 발견사항

### 8.1 MEDIUM: 로깅 레벨 일관성 부재
**위치**: routes_g2b.py 전반
**문제**:
```python
logger.info(f"✓ bid_announcements 저장: {bid_no}")  # 개별 저장
logger.info(f"[analyze] ✓ 공고 분석 시작됨")        # 시작 메시지
logger.error(f"bid-search 오류: {e}")              # 에러
```

**권장 사항**:
```python
# ✓ 좋은 예: 구조화된 로깅
logger.info(
    "공고 저장됨",
    extra={"bid_no": bid_no, "count": 1}
)

logger.info(
    "공고 분석 시작",
    extra={"bid_no": bid_no, "stage": "analysis"}
)

logger.error(
    "공고 분석 실패",
    extra={"bid_no": bid_no, "error_type": type(e).__name__}
)
```

### 8.2 MEDIUM: API 응답 일관성
**위치**: routes_g2b.py:237-241
**문제**:
```python
# 엔드포인트마다 다른 응답 형식
return {
    "bid_no": bid_no,
    "status": "pending",
    "message": "...",
}

# vs

return {
    "keyword": keyword,
    "page_no": page_no,
    "total_count": len(items),
    "items": items,
}
```

**권장 사항**:
```python
# ✓ 좋은 예: 일관된 응답 포맷 (patterns.md 참고)

class APIResponse(BaseModel):
    """표준 API 응답."""
    success: bool
    status: str  # ok, pending, error
    message: str | None = None
    data: dict | list | None = None
    error_code: str | None = None
    errors: list[str] | None = None

# 사용
return APIResponse(
    success=True,
    status="pending",
    message="공고 분석이 백그라운드에서 처리 중입니다",
    data={"bid_no": bid_no},
).dict()
```

### 8.3 LOW: 데코레이터 중복
**위치**: routes_g2b.py:56, 151
**문제**:
```python
# 모든 엔드포인트에서 반복되는 패턴
current_user=Depends(get_current_user),

# 하지만 사용하지 않는 경우도 있음
@router.post("/bid-results/bulk-sync")
async def bulk_sync(
    current_user=Depends(get_current_user),  # 사용 안 됨!
):
```

**권장 사항**:
```python
# ✓ 좋은 예: 데코레이터 활용
from functools import wraps

def require_auth(func):
    """인증 필수 데코레이터."""
    @wraps(func)
    async def wrapper(*args, current_user=Depends(get_current_user), **kwargs):
        return await func(*args, current_user=current_user, **kwargs)
    return wrapper

# 또는 RouterDepends 사용
router = APIRouter(
    prefix="/g2b",
    tags=["g2b"],
    dependencies=[Depends(get_current_user)],
)
```

---

## 요약 및 우선순위

### 즉시 수정 필요 (CRITICAL)
1. **예외 메시지 필터링**: 민감정보 노출 방지 (1.1, 1.2)
2. **환경변수 검증**: 명확한 에러 메시지 (2.1, 2.2)
3. **타입 검증**: None 참조 방지 (3.1, 3.2)

### 1주일 내 수정 (HIGH)
4. **함수 책임 분리**: 코드 품질 개선 (6.1, 6.2)
5. **백그라운드 작업 복구**: 안정성 향상 (4.2)

### 필요시 수정 (MEDIUM)
6. 매직 스트링 상수화
7. 로깅 구조화
8. API 응답 일관성

---

## 검증 체크리스트
- [ ] 예외 메시지에 민감정보 필터링 추가
- [ ] 환경변수 검증 통합 (config.py)
- [ ] None 체크 및 타입 검증 강화
- [ ] 함수 책임 분리 (routes_g2b.py)
- [ ] 상수 정의 클래스 생성
- [ ] 구조화된 로깅 적용
- [ ] RLS 필터링 일관성 확인
- [ ] 전역 변수 제거 및 클래스 기반 구현
- [ ] 테스트 커버리지 80% 이상 확인
