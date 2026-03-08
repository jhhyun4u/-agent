# 제안발표 자료 자동 생성 — 설계서

- **Plan 참조**: `docs/01-plan/features/presentation-generator.plan.md`
- **작성일**: 2026-03-08

---

## 1. 컴포넌트 구조

```text
app/
├── api/
│   ├── routes.py                          # 수정: routes_presentation 등록
│   └── routes_presentation.py             # 신규
├── services/
│   ├── presentation_generator.py          # 신규
│   └── presentation_pptx_builder.py       # 신규
├── templates/
│   └── presentation/
│       ├── government_blue.pptx           # 표준 템플릿 1: 정부/공공기관 스타일
│       ├── corporate_modern.pptx          # 표준 템플릿 2: 기업 현대적 스타일
│       └── minimal_clean.pptx             # 표준 템플릿 3: 심플/미니멀
```

---

## 2. routes_presentation.py

### 2.1 엔드포인트 전체

```python
router = APIRouter(prefix="/v3.1", tags=["presentation"])

GET    /presentation/templates                          # 표준 템플릿 목록 조회
POST   /proposals/{proposal_id}/presentation            # 발표 자료 생성 요청
GET    /proposals/{proposal_id}/presentation/status     # 진행 상태 조회
GET    /proposals/{proposal_id}/presentation/download   # PPTX 파일 다운로드
```

### 2.2 GET `/presentation/templates`

표준 템플릿 목록 반환 (인증 불필요):

```json
{
  "templates": [
    {
      "id": "government_blue",
      "name": "정부/공공기관 스타일",
      "description": "공공입찰 발표에 적합한 블루 계열 공식 스타일",
      "preview_color": "#1F497D",
      "slide_count_example": 8
    },
    {
      "id": "corporate_modern",
      "name": "기업 현대적 스타일",
      "description": "깔끔한 모던 디자인, SI/컨설팅 발표에 적합",
      "preview_color": "#2E4057",
      "slide_count_example": 10
    },
    {
      "id": "minimal_clean",
      "name": "심플/미니멀",
      "description": "텍스트 중심, 내용 전달에 집중하는 미니멀 스타일",
      "preview_color": "#444444",
      "slide_count_example": 8
    }
  ]
}
```

### 2.3 POST `/proposals/{proposal_id}/presentation`

**요청 파라미터**

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `template_mode` | str | `"standard"` | `"standard"` \| `"sample"` \| `"scratch"` |
| `template_id` | str (선택) | `"government_blue"` | `standard` 모드일 때 사용할 템플릿 ID |
| `sample_storage_path` | str (선택) | `None` | `sample` 모드일 때 Supabase Storage 경로 |

**template_mode 별 동작**

| 모드 | 설명 | PPTX 빌더 동작 |
|------|------|---------------|
| `standard` | `app/templates/presentation/{template_id}.pptx` 로드 | 기존 슬라이드 제거 후 Slide Master 유지 |
| `sample` | Supabase Storage에서 사용자 샘플 다운로드 | 기존 슬라이드 제거 후 Slide Master 유지 |
| `scratch` | python-pptx 기본값 | `Presentation()` 빈 파일로 시작 |

**전처리 (동기)**

1. `session_manager.get_session(proposal_id)` → 없으면 404
2. `session.get("phases_completed", 0) < 5` → 400 "제안서 생성이 완료되지 않았습니다"
3. `session.get("presentation_status") == "processing"` → 409 "이미 생성 중입니다"
4. `template_mode == "standard"` 이고 template 파일 없으면 400
5. `template_mode == "sample"` 이고 `sample_storage_path` 없으면 400
6. 세션에 `presentation_status = "processing"` 업데이트

**백그라운드 실행**

```python
background_tasks.add_task(
    _run_presentation,
    proposal_id,
    template_mode,
    template_id,
    sample_storage_path,
)
```

**응답**

```json
{
  "proposal_id": "...",
  "status": "processing",
  "template_mode": "standard",
  "template_id": "government_blue",
  "message": "발표 자료 생성을 시작합니다"
}
```

### 2.4 GET `.../presentation/status`

세션에서 읽어 반환:

```json
{
  "proposal_id": "...",
  "status": "idle | processing | done | error",
  "pptx_url": "https://...",
  "eval_coverage": { "기술이해도": "slide_3", "수행방법론": "slide_4" },
  "error": ""
}
```

### 2.5 GET `.../presentation/download`

- `presentation_pptx_path` 없으면 404
- `FileResponse(path, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation")`

### 2.6 `_run_presentation` 백그라운드 함수

```python
async def _run_presentation(
    proposal_id: str,
    template_mode: str = "standard",
    template_id: str = "government_blue",
    sample_storage_path: Optional[str] = None,
):
    session = await session_manager.aget_session(proposal_id)

    # Artifact 로드
    phase2 = Phase2Artifact(**session["phase_artifact_2"])
    phase3 = Phase3Artifact(**session["phase_artifact_3"])
    phase4 = Phase4Artifact(**session["phase_artifact_4"])
    rfp_data = RFPData(**session["phase_artifact_1"]["rfp_data"])

    # 슬라이드 JSON 생성
    slides_json = await generate_presentation_slides(phase2, phase3, phase4, rfp_data)

    # 템플릿 경로 결정
    template_path = _resolve_template_path(template_mode, template_id, sample_storage_path)

    # PPTX 빌드
    output_path = Path(f"/tmp/{proposal_id}/presentation.pptx")
    build_presentation_pptx(slides_json, output_path, rfp_data.project_name, template_path)

    # Supabase Storage 업로드
    pptx_url = await _upload_presentation(proposal_id, str(output_path))

    # 세션 업데이트
    session_manager.update_session(proposal_id, {
        "presentation_status": "done",
        "presentation_pptx_path": str(output_path),
        "presentation_pptx_url": pptx_url,
        "presentation_eval_coverage": slides_json.get("eval_coverage", {}),
        "presentation_template_mode": template_mode,
        "presentation_template_id": template_id,
    })
```

### 2.7 `_resolve_template_path` 헬퍼

```python
def _resolve_template_path(
    mode: str,
    template_id: str,
    sample_storage_path: Optional[str],
) -> Optional[Path]:
    """template_mode → 실제 파일 경로 반환. 없으면 None (scratch)"""
    if mode == "standard":
        path = Path("app/templates/presentation") / f"{template_id}.pptx"
        return path if path.exists() else None   # 없으면 scratch fallback

    if mode == "sample" and sample_storage_path:
        # Supabase Storage에서 로컬로 다운로드 (동기 처리)
        local = Path(f"/tmp/sample_template_{template_id}.pptx")
        # 실제 구현: asyncio.to_thread + client.storage.from_().download()
        return local if local.exists() else None

    return None   # scratch
```

---

## 3. presentation_generator.py

### 3.1 설계 원칙: 2-step 파이프라인

발표 자료 생성은 **목차 설계 → 스토리보드 작성 → PPTX 빌드** 순서로 진행한다.
단일 API 호출로 모든 슬라이드를 생성하면 목차 논리와 본문 내용이 혼재되어 품질이 저하된다.

```text
Phase 2/3/4 Artifacts
        │
        ▼
[Step 1] TOC 생성 (Claude API #1)
  입력: section_plan(score_weight순), evaluation_weights, win_theme
  출력: toc[] — 슬라이드 번호, 제목, 레이아웃, eval_badge, 대상 섹션명
        │
        ▼
[Step 2] 스토리보드 생성 (Claude API #2)
  입력: toc + proposal_sections + evaluator_perspective + win_theme + differentiation_strategy
  출력: slides[] — bullets(본문 근거), phases, speaker_notes
        │
        ▼
[Step 3] PPTX 빌드 (presentation_pptx_builder)
  입력: {slides, total_slides, eval_coverage}
  출력: .pptx 파일
```

**Step 1 — TOC (목차 설계)**

- proposal_sections 없이 호출 → 빠른 응답
- 배점 규칙 적용: score_weight ≥ 15 → 전용 슬라이드, ≤ 9 → 병합
- 고정 슬라이드: 표지(cover), 이기는전략(key_message), 마무리(closing)
- 각 TOC 항목: `slide_num, layout, title, eval_badge, target_section, score_weight`

**Step 2 — 스토리보드 (슬라이드별 본문)**

- TOC 확정 후 본문(proposal_sections) 참조
- evaluator_check_points 순서로 bullet 작성
- 정량 수치 최소 1개/슬라이드 강제
- speaker_notes: "평가위원이 이 항목에서 확인하는 것은" 형식

### 3.2 공개 인터페이스

```python
async def generate_presentation_slides(
    phase2: Phase2Artifact,
    phase3: Phase3Artifact,
    phase4: Phase4Artifact,
    rfp_data: Optional[RFPData] = None,
) -> dict:
    """
    2-step 파이프라인:
      1. _generate_toc(): 목차 설계
      2. _generate_storyboard(toc): 슬라이드별 본문 작성
    Returns: {slides, total_slides, eval_coverage}
    """
```

### 3.3 입력 조립 로직

```python
def _build_input(phase2, phase3, phase4, rfp_data) -> dict:
    sorted_plan = sorted(
        phase3.section_plan,
        key=lambda s: s.get("score_weight", 0) if isinstance(s, dict) else 0,
        reverse=True,
    )
    return {
        "project_name": (rfp_data.project_name if rfp_data else "") or "",
        "evaluation_weights": phase2.evaluation_weights,
        "evaluator_perspective": phase2.structured_data.get("evaluator_perspective", {}),
        "section_plan": sorted_plan,
        "win_theme": phase3.win_theme,
        "win_strategy": phase3.win_strategy,
        "differentiation_strategy": phase3.differentiation_strategy,
        "implementation_checklist": phase3.implementation_checklist,
        "proposal_sections": phase4.sections,
        "team_plan": phase3.team_plan,
    }
```

### 3.4 Step 1: TOC 생성 프롬프트

#### TOC_SYSTEM

```python
TOC_SYSTEM = """당신은 공공 입찰 발표 자료의 목차를 설계하는 전문가입니다.
평가위원이 배점표에 따라 채점하는 발표 심사를 위해 최적의 슬라이드 목차를 구성합니다.
응답은 반드시 JSON 형식으로만 제공합니다.

목차 설계 규칙:
1. 고정 슬라이드(표지, 이기는전략, 마무리)는 반드시 포함하라.
2. 평가항목 슬라이드는 score_weight 내림차순으로 배치하라.
3. score_weight >= 15점: 전용 슬라이드 1장
4. score_weight 10-14점: 전용 슬라이드 1장 (내용 압축)
5. score_weight <= 9점: 유사 섹션과 병합 (한 슬라이드에 2개)
6. 추진일정/타임라인은 timeline 레이아웃 사용
7. 인력투입계획은 team 레이아웃 사용"""
```

#### TOC_USER

```python
TOC_USER = """다음 정보를 바탕으로 발표 자료 목차를 설계해주세요.

## 사업명
{project_name}

## 평가항목 배점 (score_weight 내림차순 정렬됨)
{section_plan}

## Win Theme
{win_theme}

반드시 아래 JSON 형식으로 응답하세요:
{{
    "toc": [
        {{
            "slide_num": 1,
            "layout": "cover",
            "title": "사업명",
            "eval_badge": "",
            "target_section": "",
            "score_weight": 0
        }},
        {{
            "slide_num": 2,
            "layout": "key_message",
            "title": "이기는 전략",
            "eval_badge": "",
            "target_section": "",
            "score_weight": 0
        }},
        {{
            "slide_num": 3,
            "layout": "eval_section",
            "title": "슬라이드 제목 (평가항목 반영)",
            "eval_badge": "평가항목명 | XX점",
            "target_section": "phase3.section_plan의 section_name",
            "score_weight": 25
        }},
        {{
            "slide_num": 99,
            "layout": "closing",
            "title": "왜 우리인가",
            "eval_badge": "",
            "target_section": "",
            "score_weight": 0
        }}
    ],
    "total_slides": 8
}}

규칙:
- layout 값: cover | key_message | eval_section | comparison | timeline | team | closing
- slide_num은 1부터 연속 정수 (99 사용 금지)
- eval_badge: "평가항목명 | XX점" 형식 (eval_section/timeline/team만)
- target_section: section_plan의 section_name 값 그대로"""
```

### 3.5 Step 2: 스토리보드 생성 프롬프트

#### STORYBOARD_SYSTEM

```python
STORYBOARD_SYSTEM = """당신은 공공 입찰 발표 자료의 슬라이드 내용을 작성하는 전문가입니다.
확정된 목차(TOC)를 기반으로 각 슬라이드의 본문을 작성합니다.
응답은 반드시 JSON 형식으로만 제공합니다.

스토리보드 작성 규칙:
1. 모든 bullet의 근거는 반드시 proposal_sections에서 찾아라. 새 내용을 창작하지 말라.
2. 각 슬라이드의 bullet은 해당 섹션 evaluator_check_points를 순서대로 커버하라.
3. 정량 수치(%, 기간, 비용 절감액)가 포함된 bullet을 슬라이드당 최소 1개 포함하라.
4. win_theme.primary_message는 표지 subtitle, 슬라이드 2 headline, 마지막 슬라이드 headline에 명시하라.
5. 나머지 슬라이드의 speaker_notes 마지막 문장에서 Win Theme과 연결하라.
6. speaker_notes는 "평가위원이 이 항목에서 확인하는 것은" 형식으로 시작하라."""
```

#### STORYBOARD_USER

```python
STORYBOARD_USER = """확정된 목차를 기반으로 각 슬라이드의 내용을 작성해주세요.

## 확정된 목차 (TOC)
{toc}

## Win Theme
{win_theme}

## 차별화 포인트
{differentiation_strategy}

## 평가위원 관점
{evaluator_perspective}

## 제안서 본문 (섹션별)
{proposal_sections}

## 추진 계획
{implementation_checklist}

반드시 아래 JSON 형식으로 응답하세요 (TOC의 모든 슬라이드 포함):
{{
    "slides": [
        {{
            "slide_num": 1,
            "layout": "cover",
            "title": "사업명",
            "subtitle": "win_theme.primary_message 그대로",
            "speaker_notes": "발표 시작 스크립트 (3문장 이상)"
        }},
        {{
            "slide_num": 2,
            "layout": "key_message",
            "title": "이기는 전략",
            "headline": "win_theme.primary_message 그대로",
            "bullets": ["근거 pillar 1", "근거 pillar 2", "근거 pillar 3"],
            "speaker_notes": "평가위원이 이 항목에서 확인하는 것은 우리의 핵심 강점입니다. ..."
        }},
        {{
            "slide_num": 3,
            "layout": "eval_section",
            "title": "TOC의 title 그대로",
            "eval_badge": "TOC의 eval_badge 그대로",
            "bullets": [
                "evaluator_check_point1 기반 압축 문장 (proposal_sections 근거)",
                "evaluator_check_point2 기반 압축 문장",
                "정량 수치 포함 문장 (처리 속도 40% 향상 등)"
            ],
            "speaker_notes": "평가위원이 이 항목에서 확인하는 것은 ~입니다. [근거]. [Win Theme 연결]"
        }},
        {{
            "slide_num": 7,
            "layout": "timeline",
            "title": "추진 계획",
            "eval_badge": "TOC의 eval_badge 그대로",
            "phases": [
                {{"name": "1단계", "duration": "1개월", "deliverables": ["산출물1", "산출물2"]}}
            ],
            "speaker_notes": "평가위원이 이 항목에서 확인하는 것은 일정 실현가능성입니다. ..."
        }},
        {{
            "slide_num": 8,
            "layout": "closing",
            "title": "왜 우리인가",
            "headline": "win_theme.primary_message 그대로",
            "bullets": ["차별화포인트1", "차별화포인트2", "차별화포인트3"],
            "speaker_notes": "..."
        }}
    ],
    "eval_coverage": {{
        "평가항목명1": "slide_3",
        "평가항목명2": "slide_4"
    }}
}}

규칙:
- TOC에 있는 모든 슬라이드를 포함하고 slide_num, layout, title, eval_badge는 TOC 값 그대로 유지
- bullets: 슬라이드당 3~5개, proposal_sections에서만 근거 추출
- eval_coverage: 각 평가항목명이 몇 번 슬라이드에서 다뤄지는지 매핑"""
```

### 3.6 Claude API 호출 흐름

```python
async def generate_presentation_slides(...) -> dict:
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    inp = _build_input(phase2, phase3, phase4, rfp_data)

    # Step 1: TOC 생성
    toc_response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=2048,
        system=TOC_SYSTEM,
        messages=[{"role": "user", "content": TOC_USER.format(
            project_name=inp["project_name"],
            section_plan=json.dumps(inp["section_plan"], ensure_ascii=False),
            win_theme=json.dumps(inp["win_theme"], ensure_ascii=False),
        )}],
    )
    toc_result = extract_json_from_response(toc_response.content[0].text)
    toc = toc_result.get("toc", [])

    # Step 2: 스토리보드 생성
    storyboard_response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=6000,
        system=STORYBOARD_SYSTEM,
        messages=[{"role": "user", "content": STORYBOARD_USER.format(
            toc=json.dumps(toc, ensure_ascii=False),
            win_theme=json.dumps(inp["win_theme"], ensure_ascii=False),
            differentiation_strategy=json.dumps(inp["differentiation_strategy"], ensure_ascii=False),
            evaluator_perspective=json.dumps(inp["evaluator_perspective"], ensure_ascii=False),
            proposal_sections=json.dumps(inp["proposal_sections"], ensure_ascii=False),
            implementation_checklist=json.dumps(inp["implementation_checklist"], ensure_ascii=False),
        )}],
    )
    storyboard = extract_json_from_response(storyboard_response.content[0].text)

    # total_slides는 TOC 기준
    storyboard["total_slides"] = toc_result.get("total_slides", len(toc))
    return storyboard
```

---

## 4. presentation_pptx_builder.py

### 4.1 공개 인터페이스

```python
def build_presentation_pptx(
    slides_json: dict,
    output_path: Path,
    project_name: str = "",
    template_path: Optional[Path] = None,   # None이면 scratch
) -> Path:
```

#### 템플릿 초기화 로직

```python
def _init_presentation(template_path: Optional[Path]) -> Presentation:
    if template_path and template_path.exists():
        prs = Presentation(str(template_path))
        # 기존 슬라이드 전부 제거 (Slide Master/디자인 유지)
        while len(prs.slides._sldIdLst) > 0:
            rId = prs.slides._sldIdLst[0].rId
            prs.part.drop_rel(rId)
            del prs.slides._sldIdLst[0]
    else:
        prs = Presentation()   # scratch: 기본 blank 템플릿
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)
    return prs
```

### 4.2 레이아웃별 렌더링 함수

```python
def _render_cover(slide, data: dict) -> None
def _render_key_message(slide, data: dict) -> None
def _render_eval_section(slide, data: dict) -> None    # eval_badge 포함
def _render_comparison(slide, data: dict) -> None      # 경쟁자 vs 우리 2컬럼 표
def _render_timeline(slide, data: dict) -> None        # eval_badge 포함
def _render_team(slide, data: dict) -> None            # 인력 구성 표
def _render_closing(slide, data: dict) -> None
```

### 4.3 eval_badge 렌더링 (`_render_eval_section`, `_render_timeline`)

슬라이드 우측 상단에 텍스트 박스 배치:

```python
# 위치: 우측 상단 (Inches(9.5), Inches(0.2), width=Inches(3.5), height=Inches(0.5))
txBox = slide.shapes.add_textbox(Inches(9.5), Inches(0.2), Inches(3.5), Inches(0.5))
tf = txBox.text_frame
tf.text = data.get("eval_badge", "")
tf.paragraphs[0].font.size = Pt(12)
tf.paragraphs[0].font.bold = True
tf.paragraphs[0].font.color.rgb = RGBColor(0x1F, 0x49, 0x7D)   # 진한 파랑
tf.paragraphs[0].alignment = PP_ALIGN.RIGHT
```

### 4.4 speaker_notes 추가

모든 레이아웃 공통:

```python
notes_slide = slide.notes_slide
notes_slide.notes_text_frame.text = data.get("speaker_notes", "")
```

### 4.5 timeline 레이아웃 (`_render_timeline`)

`implementation_checklist` 또는 `phases` 배열을 가로 배치:

```python
# 단계 수에 따라 width 균등 분배
# 각 단계: 박스(배경색) + 단계명 + 기간 + 산출물 bullet
col_width = Inches(10.5) / len(phases)
for i, phase in enumerate(phases):
    left = Inches(1.5) + col_width * i
    # 배경 사각형
    shape = slide.shapes.add_shape(MSO_SHAPE_TYPE.RECTANGLE, left, Inches(2.5), col_width - Inches(0.1), Inches(3.5))
    shape.text = f"{phase['name']}\n{phase['duration']}"
    for d in phase.get("deliverables", [])[:3]:
        p = shape.text_frame.add_paragraph()
        p.text = f"• {d}"
        p.font.size = Pt(11)
```

### 4.6 fallback 처리

**`_render_comparison` — 경쟁자 vs 우리 2컬럼 표**

```python
def _render_comparison(slide, data: dict) -> None:
    # eval_badge 표시 (있으면)
    # 제목 텍스트박스
    # 왼쪽 컬럼: "경쟁사" 헤더 + table[].competitor
    # 오른쪽 컬럼: "우리" 헤더 + table[].ours
    # dimension(구분 축) 행: table[].dimension
```

**`_render_team` — 인력 구성 표**

```python
def _render_team(slide, data: dict) -> None:
    # eval_badge 표시 (있으면)
    # team_rows: [ {role, grade, person_months} ] 형태의 표 렌더링
    # 또는 bullets 리스트를 bullet 형태로 렌더링 (fallback)
```

#### fallback 처리

```python
def _render_slide(prs, data: dict) -> None:
    layout_map = {
        "cover": _render_cover,
        "key_message": _render_key_message,
        "eval_section": _render_eval_section,
        "comparison": _render_comparison,
        "timeline": _render_timeline,
        "team": _render_team,
        "closing": _render_closing,
    }
    layout = data.get("layout", "eval_section")
    renderer = layout_map.get(layout, _render_eval_section)
    try:
        slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank layout
        renderer(slide, data)
    except Exception as e:
        logger.warning(f"슬라이드 렌더링 실패 ({layout}), fallback 적용: {e}")
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        slide.shapes.title.text = data.get("title", "")
        if data.get("bullets"):
            slide.placeholders[1].text = "\n".join(data["bullets"])
```

---

## 5. Storage 업로드 (`_upload_presentation`)

기존 `_upload_to_storage` 패턴 동일하게 적용:

```python
async def _upload_presentation(proposal_id: str, local_path: str) -> str:
    client = await get_async_client()
    bucket = "proposal-files"
    storage_path = f"{proposal_id}/presentation.pptx"
    file_bytes = await asyncio.to_thread(lambda: open(local_path, "rb").read())
    await client.storage.from_(bucket).upload(
        path=storage_path,
        file=file_bytes,
        file_options={
            "content-type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "upsert": "true",
        },
    )
    return client.storage.from_(bucket).get_public_url(storage_path)
```

---

## 6. routes.py 수정

```python
# 기존 import 목록에 추가
from . import routes_presentation

# router.include_router() 목록에 추가
router.include_router(routes_presentation.router)
```

---

## 7. 세션 상태 키 (session_manager)

| 키 | 타입 | 설명 |
|----|------|------|
| `presentation_status` | str | `"idle"` \| `"processing"` \| `"done"` \| `"error"` |
| `presentation_pptx_path` | str | 로컬 임시 파일 경로 |
| `presentation_pptx_url` | str | Supabase Storage 공개 URL |
| `presentation_eval_coverage` | dict | `{ "평가항목명": "slide_N" }` |
| `presentation_template_mode` | str | `"standard"` \| `"sample"` \| `"scratch"` |
| `presentation_template_id` | str | 사용된 표준 템플릿 ID (standard 모드만) |
| `presentation_error` | str | 오류 메시지 (error 상태일 때) |

---

## 8. 오류 처리 정책

| 상황 | HTTP 코드 | 메시지 |
|------|:--------:|--------|
| proposal_id 세션 없음 | 404 | "제안서를 찾을 수 없습니다" |
| phases_completed < 5 | 400 | "제안서 생성이 완료되지 않았습니다" |
| 이미 processing 중 | 409 | "발표 자료를 생성 중입니다" |
| standard 모드인데 template 파일 없음 | 400 | "존재하지 않는 템플릿입니다: {template_id}" |
| sample 모드인데 sample_storage_path 없음 | 400 | "sample 모드에는 sample_storage_path가 필요합니다" |
| 다운로드 파일 없음 | 404 | "발표 자료가 아직 생성되지 않았습니다" |
| standard/sample 템플릿 로드 실패 (백그라운드) | — | scratch로 자동 fallback 후 계속 |
| 백그라운드 전체 실패 | — | 세션 `presentation_status="error"`, `presentation_error=msg` |

---

## 9. Fallback 체인

```text
section_plan[].score_weight 없음
  → phase2.evaluation_weights에서 target_criteria로 배점 조회

phase4.sections[섹션명] 없음
  → phase3.section_plan[].approach 텍스트로 bullet 구성

phase3.win_theme 비어있음
  → phase3.win_strategy 텍스트를 headline으로 사용

phase3.evaluator_check_points 비어있음
  → evaluation_weights 항목명으로 generic bullet 구성

PPTX 슬라이드 렌더링 오류
  → blank layout + title + bullet 텍스트 fallback
```

---

## 10. 구현 순서

1. `presentation_pptx_builder.py` — PPTX 빌더 (레이아웃 6종)
2. `presentation_generator.py` — Claude API 호출 + 입력 조립
3. `routes_presentation.py` — 3개 엔드포인트 + 백그라운드 함수
4. `routes.py` — 라우터 등록
