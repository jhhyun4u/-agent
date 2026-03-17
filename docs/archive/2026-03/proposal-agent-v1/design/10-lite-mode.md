# 간이 모드 (Lite Mode)

> **소속**: proposal-agent-v1 설계 문서 v3.5
> **관련 파일**: [08-api-endpoints.md](08-api-endpoints.md), [03-graph-definition.md](03-graph-definition.md)
> **원본 섹션**: §14

---

## 14. 간이 모드 (Lite Mode) — U-1 해결

> **역량 DB 없이도 즉시 시작 가능.** 이 경우 AI가 역량 DB 자동 검색을 건너뛰고 사용자 수동 입력에 의존.

```python
# 간이 모드 프로젝트 생성
# POST /api/proposals
{
  "name": "AI 플랫폼 구축",
  "client": "과학기술부",
  "mode": "lite",         # ← lite 모드
  "rfp_file": <UploadFile> # ★ RFP 파일로 기본 정보 자동 추출 (U-3)
}
```

### 14-1. 모드별 동작 차이

| 항목 | Lite (간이) | Full (정규) |
|------|------------|------------|
| 역량 DB 필수 | 아니오 | 예 |
| STEP 0 공고 검색 | 가능 (키워드 검색만, 적합도 점수 간소화) | AI 공고 검색·추천 + 역량 기반 적합도 |
| STEP 1-② 포지셔닝 | 사용자 직접 선택 (AI 추천 없이) | AI 자동 판정 + 사용자 확정 |
| STEP 1-② 수주 가능성 점수 | 생략 | 산출 |
| STEP 2 Win Theme 생성 | 사용자 입력 역량 기반 | 역량 DB 자동 검색 기반 |
| STEP 4 실적 자동 인용 | 불가 (수동 입력) | 자동 |

### 14-2. RFP 업로드로 기본 정보 자동 추출 (U-3)

```python
# POST /api/proposals/from-rfp
async def create_from_rfp(rfp_file: UploadFile, mode: str = "lite"):
    """
    RFP 파일을 업로드하면:
    1. 파싱하여 사업명·발주기관·기한 자동 추출
    2. 프로젝트 생성
    3. rfp_raw에 파싱된 텍스트 저장
    → STEP 0 건너뛰고 STEP 1(RFP 분석)부터 직접 시작
    """
    text = await parse_rfp_file(rfp_file)
    basic_info = await extract_basic_info(text)  # Claude로 기본 정보 추출

    project = create_project(
        name=basic_info["project_name"],
        client=basic_info["client"],
        deadline=basic_info["deadline"],
        mode=mode,
    )

    # 그래프 초기 상태에 rfp_raw 포함 → STEP 1에서 재파싱 불필요
    await start_graph(project.id, initial_state={
        "rfp_raw": text,
        "project_name": basic_info["project_name"],
        "mode": mode,
    })

    return project
```

### 14-3. 공고번호 직접 지정 — from-search (U-2)

```python
# POST /api/proposals/from-search
async def create_from_search(bid_no: str, mode: str = "full"):
    """
    워크플로 밖에서 이미 알고 있는 공고번호로 프로젝트 생성.
    STEP 0(검색)을 건너뛰고 rfp_fetch(G2B 상세 수집 + RFP 업로드)부터 시작.
    """
    project = create_project(name=f"공고 {bid_no}", mode=mode)

    await start_graph(project.id, initial_state={
        "picked_bid_no": bid_no,  # → route_start에서 "direct_fetch" 분기
        "mode": mode,
    })

    return project
```

---
