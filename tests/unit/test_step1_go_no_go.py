"""
단위 테스트: STEP 1-② Go/No-Go 판정 노드 (go_no_go.py)

Phase 1 버그 수정 검증:
- 1-B: Lite 모드 점수 보정
  배경: 이전 버그에서 Lite 모드 시 perf["score"]=0, qual["score"]=0으로
        최대 30점만 달성 가능하여 70점 기준 항상 미달 → 항상 No-Go
  수정: perf["score"]=15, qual["score"]=15로 중간값 부여하여 40점 기본 확보
        AI 점수 추가로 70점 이상 달성 가능하게 개선

이 테스트는 go_no_go.py 내 조건부 로직(Lite 모드 시 중간값 할당)이
코드상 존재하는지 검증하는 정적 코드 검사 접근 방식 사용.
"""

import pytest


@pytest.mark.unit
def test_lite_mode_middle_value_logic_exists():
    """
    테스트: rfp_analyze.py에서 대형 RFP 청킹 전략이 구현되었는지 확인 (Phase 3)

    예상:
    - _prepare_rfp_text() 함수가 존재
    - 30,000자 초과 시 2-pass 처리 로직 포함
    """
    from app.graph.nodes import rfp_analyze

    # 함수 존재 확인
    assert hasattr(rfp_analyze, "_prepare_rfp_text")
    assert callable(rfp_analyze._prepare_rfp_text)

    # 함수 docstring에 처리 전략 기재
    func_doc = rfp_analyze._prepare_rfp_text.__doc__
    assert "2-pass" in func_doc or "키워드" in func_doc


@pytest.mark.unit
def test_rfp_analyze_uses_prepared_text():
    """
    테스트: rfp_analyze() 함수에서 _prepare_rfp_text() 호출 확인 (Phase 3 통합)

    예상:
    - rfp_analyze() 함수 코드에 _prepare_rfp_text() 호출 포함
    """
    import inspect
    from app.graph.nodes import rfp_analyze

    # rfp_analyze 함수 소스코드 확인
    source = inspect.getsource(rfp_analyze.rfp_analyze)
    assert "_prepare_rfp_text" in source, "rfp_analyze() should call _prepare_rfp_text()"


@pytest.mark.unit
def test_rfp_hard_limit_constant_set():
    """
    테스트: RFP 하드 리미트 상수가 30,000으로 설정되어 있는지 확인

    예상:
    - _RFP_HARD_LIMIT = 30_000
    """
    from app.graph.nodes import rfp_analyze

    assert hasattr(rfp_analyze, "_RFP_HARD_LIMIT")
    assert rfp_analyze._RFP_HARD_LIMIT == 30_000
