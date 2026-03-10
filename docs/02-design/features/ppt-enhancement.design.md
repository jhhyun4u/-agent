# Design: ppt-enhancement

> Plan 참조: `docs/01-plan/features/ppt-enhancement.plan.md`

---

## 변경 파일 목록

| 파일 | 변경 유형 | FR |
|------|----------|-----|
| `app/services/presentation_generator.py` | 수정 | FR-01, FR-02, FR-03, FR-06 |
| `app/services/presentation_pptx_builder.py` | 수정 | FR-04 |
| `app/api/routes_presentation.py` | 수정 | FR-05 |

---

## FR-01 / FR-02: comparison·team 레이아웃 프롬프트 추가

### 문제
`STORYBOARD_USER` 프롬프트 예시에 `comparison`과 `team` 레이아웃 JSON 구조가 없어
Claude가 해당 필드(`table`, `team_rows`)를 생성하지 않음 → 항상 bullets fallback

### 설계: `STORYBOARD_USER` 예시 JSON 추가

`presentation_generator.py` — `STORYBOARD_USER` 문자열에 아래 예시 블록 추가:

```
# comparison 예시 (FR-01)
{{
    "slide_num": 5,
    "layout": "comparison",
    "title": "당사 기술은 경쟁사 대비 처리 속도 40% 우위를 갖춤",
    "eval_badge": "TOC의 eval_badge 그대로",
    "table": [
        {{"dimension": "응답 속도", "competitor": "평균 3초", "ours": "평균 1.8초 (40% 향상)"}},
        {{"dimension": "정확도", "competitor": "92%", "ours": "97% (5pp 향상)"}},
        {{"dimension": "운영 비용", "competitor": "월 500만원", "ours": "월 320만원 (36% 절감)"}}
    ],
    "speaker_notes": "평가위원이 이 항목에서 확인하는 것은 기술 차별성의 실질적 근거입니다. ..."
}},

# team 예시 (FR-02)
{{
    "slide_num": 6,
    "layout": "team",
    "title": "검증된 전문 인력 5명으로 납기 내 완수 체계를 갖춤",
    "eval_badge": "TOC의 eval_badge 그대로",
    "team_rows": [
        {{"role": "PM", "grade": "특급", "duration": "12개월", "task": "전체 일정·품질 관리"}},
        {{"role": "수석 개발자", "grade": "고급", "duration": "10개월", "task": "핵심 모듈 설계·구현"}},
        {{"role": "UI/UX", "grade": "중급", "duration": "6개월", "task": "화면 설계 및 사용성 검증"}}
    ],
    "speaker_notes": "평가위원이 이 항목에서 확인하는 것은 투입 인력의 적정성입니다. ..."
}}
```

### 데이터 출처 지시 추가 (STORYBOARD_SYSTEM)

```
7. comparison 레이아웃: table 필드를 반드시 포함하라.
   dimension/competitor/ours 값은 differentiation_strategy에서 추출하라.
8. team 레이아웃: team_rows 필드를 반드시 포함하라.
   role/grade/duration/task 값은 team_plan에서 추출하라.
   team_plan이 없으면 proposal_sections의 인력투입계획 섹션을 참조하라.
```

---

## FR-03: Action Title 규칙 추가

### 문제
슬라이드 제목이 토픽("사업 이해도")으로 생성됨.
McKinsey 원칙상 제목은 완결 주장 문장이어야 함.

### 설계

#### TOC_SYSTEM 마지막에 규칙 추가
```
8. 슬라이드 title은 반드시 "주어 + 서술어" 형식의 완결 주장 문장(assertion)으로 작성하라.
   예: ❌ "사업 이해도" → ✅ "당사는 현장 경험 5년으로 발주처 핵심 요구사항을 정확히 이해함"
   예: ❌ "기술 역량"   → ✅ "3개 특허 기반 고유 기술로 경쟁사 대비 처리 속도 40% 우위 확보"
   단, cover(표지)와 closing 슬라이드 title은 예외 (사업명, "왜 우리인가" 유지)
```

#### STORYBOARD_SYSTEM 기존 규칙 보완
```
# 기존 규칙 1 뒤에 추가:
각 슬라이드의 title은 TOC의 assertion title을 그대로 유지하라. 임의로 변경 금지.
```

---

## FR-04: 슬라이드 번호 추가

### 설계: `presentation_pptx_builder.py`

#### 헬퍼 함수 추가 (기존 헬퍼 블록 하단)

```python
def _add_slide_number(slide, num: int):
    """슬라이드 우측 하단에 페이지 번호 표시 (표지 제외)"""
    _add_textbox(
        slide,
        Inches(12.5), Inches(6.9), Inches(0.6), Inches(0.35),
        text=str(num),
        font_size=14,
        color=COLOR_DARK_TEXT,
        align=PP_ALIGN.RIGHT,
    )
```

#### 각 레이아웃 렌더러 수정

`_render_slide()` 디스패처에서 슬라이드 번호를 일괄 주입하는 방식으로 구현
(각 renderer 개별 수정 대신 디스패처에서 처리 → 중앙화):

```python
def _render_slide(prs: Presentation, data: dict) -> None:
    layout = data.get("layout", "eval_section")
    renderer = _LAYOUT_MAP.get(layout, _render_eval_section)
    try:
        layout_idx = min(6, len(prs.slide_layouts) - 1)
        slide = prs.slides.add_slide(prs.slide_layouts[layout_idx])
        renderer(slide, data)
        # 표지(cover)를 제외한 모든 슬라이드에 번호 표시
        if layout != "cover":
            _add_slide_number(slide, data.get("slide_num", 0))
    except Exception as e:
        # ... 기존 fallback 유지
```

---

## FR-05: 파일 경로 OS 독립화

### 문제
`routes_presentation.py`:
```python
output_path = Path(f"/tmp/{proposal_id}/presentation.pptx")  # Windows 비호환
```

### 설계

`import tempfile` 추가 후:
```python
import tempfile

# 기존
output_path = Path(f"/tmp/{proposal_id}/presentation.pptx")

# 변경
output_path = Path(tempfile.gettempdir()) / proposal_id / "presentation.pptx"
```

`_download_sample_template()` 내 `/tmp/` 경로도 동일하게 수정:
```python
# 기존
local_path = Path(f"/tmp/sample_template_{fname}")

# 변경
local_path = Path(tempfile.gettempdir()) / f"sample_template_{fname}"
```

---

## FR-06: Step 2 토큰 증가

### 문제
`max_tokens=6000`으로 12장 슬라이드(speaker_notes 포함) 생성 시 JSON 잘림 위험

### 설계
```python
# 기존
max_tokens=6000,

# 변경
max_tokens=8192,
```

---

## 구현 순서

1. `presentation_generator.py` — FR-06 (1줄, 리스크 없음)
2. `routes_presentation.py` — FR-05 (`import tempfile` + 경로 2곳)
3. `presentation_pptx_builder.py` — FR-04 (헬퍼 추가 + `_render_slide` 수정)
4. `presentation_generator.py` — FR-03 (TOC_SYSTEM, STORYBOARD_SYSTEM 문자열 수정)
5. `presentation_generator.py` — FR-01 / FR-02 (STORYBOARD_USER 예시 JSON 추가)

---

## 검증 기준

| FR | 검증 방법 |
|----|----------|
| FR-01 | Claude 응답 JSON에 `table` 키 존재 + pptx_builder가 표를 렌더링 |
| FR-02 | Claude 응답 JSON에 `team_rows` 키 존재 + pptx_builder가 표를 렌더링 |
| FR-03 | 생성된 슬라이드 제목이 "주어+서술어" 형식 |
| FR-04 | 표지(slide 1) 제외 모든 슬라이드 우측 하단에 번호 존재 |
| FR-05 | Windows 로컬에서 PPTX 파일 경로 오류 없이 생성 완료 |
| FR-06 | 12장 슬라이드 생성 시 JSON 파싱 예외 없음 |
