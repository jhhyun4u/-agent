"""
Debug script to see exactly what Claude returns for STEP 2 prompt.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

import asyncio
import json
from app.services.core.claude_client import claude_generate

async def test_raw_response():
    """Call Claude directly and print raw response"""

    # Minimal test prompt
    test_prompt = """당신은 제안 전략 전문가입니다.

## MANDATORY: PURE JSON ONLY — NO MARKDOWN WRAPPERS

## POSITIONING 고정: offensive

Go/No-Go 단계에서 이미 포지셔닝이 결정되었습니다.
당신의 역할: offensive 전략 내에서 2+ 전술적 변형(alternatives)을 제시하는 것입니다.

당신이 생성할 2개의 alternatives는 같은 offensive 포지셔닝 내에서의 서로 다른 전술적 접근입니다.

**대안 A: Aggressive Innovation**
- 개념: 기술 혁신을 공격적으로 리드
- Ghost Theme 각도: 경쟁사의 매너리즘과 보수성 vs 우리의 혁신과 도전 정신

**대안 B: Smart Innovation**
- 개념: 신중한 혁신 (검증된 부분 + 차별화 부분 조화)
- Ghost Theme 각도: 경쟁사의 보수적 접근 vs 우리의 균형잡힌 혁신

## REQUIRED STRUCTURE

{{
  "positioning": "offensive",
  "positioning_rationale": "테스트 근거",
  "alternatives": [
    {{
      "alt_id": "A_Aggressive_Innovation",
      "alt_name": "Aggressive Innovation",
      "ghost_theme": "경쟁사는 기존 방식을 고수하고 있습니다.",
      "win_theme": "우리는 최신 기술 5가지를 도입하여 성능 50% 향상을 달성할 수 있습니다.",
      "action_forcing_event": "2026년 정부 정책 변화로 2027년까지 의사결정 필수",
      "key_messages": ["혁신으로 50% 성능 향상", "최신 기술 도입", "위험 최소화 전략", "비용 30% 절감"],
      "price_strategy": {{"approach": "innovation_premium", "target_ratio": 0.88, "rationale": "기술 혁신 정당화"}},
      "risk_assessment": {{"key_risks": ["기술 리스크"], "mitigation": ["단계적 도입"]}}
    }},
    {{
      "alt_id": "B_Smart_Innovation",
      "alt_name": "Smart Innovation",
      "ghost_theme": "경쟁사는 검증되지 않은 새 기술에만 집착합니다.",
      "win_theme": "우리는 검증된 기술과 혁신을 균형잡게 조합하여 리스크를 30% 감소시킵니다.",
      "action_forcing_event": "ISMS 인증 의무화로 2026.07까지 운영 체계 수립 필수",
      "key_messages": ["균형잡힌 혁신", "검증된 기술 활용", "리스크 30% 감소", "높은 신뢰도"],
      "price_strategy": {{"approach": "stability_premium", "target_ratio": 0.92, "rationale": "안정성과 혁신 조합"}},
      "risk_assessment": {{"key_risks": ["초기 비용"], "mitigation": ["분할 납부"]}}
    }}
  ],
  "focus_areas": [{{"area": "혁신", "weight": 50, "strategy": "신기술 도입"}}],
  "competitor_analysis": {{"swot_matrix": [], "scenarios": {{"best_case": "우리 강점", "base_case": "균형", "worst_case": "경쟁 강화"}}}},
  "research_framework": {{"research_questions": ["RQ1"], "methodology_rationale": ["방법론"]}}
}}

## FINAL CRITICAL REQUIREMENT

[최고 우선순위] alternatives 배열에 2+ 대안 포함:

1. 첫 번째 대안 (alt_id: "A_...")
2. 두 번째 대안 (alt_id: "B_...")

반드시 2개 이상의 완전한 대안을 생성하세요. 1개만 있으면 검증 실패합니다.
"""

    print("=" * 80)
    print("Claude 원본 응답 테스트")
    print("=" * 80)

    result = await claude_generate(
        test_prompt,
        max_tokens=2000,
        step_name="debug_step2"
    )

    print("\n[1] 파싱된 결과:")
    if "_parse_error" in result:
        print("[ERROR] JSON 파싱 실패!")
        text_content = result.get('text', '')
        print(f"응답 길이: {len(text_content)} 자")
        print(f"원본 텍스트 (마지막 1000자): ...{text_content[-1000:]}")

        # 응답이 어디서 끝나는지 확인
        if "alternatives" in text_content:
            alt_pos = text_content.find('"alternatives"')
            print(f"\nalternatives 시작 위치: {alt_pos}")
            print(f"alternatives 이후 내용 (마지막 500자): {text_content[alt_pos:][-500:]}")
    else:
        alternatives = result.get("alternatives", [])
        print(f"[OK] Alternatives 개수: {len(alternatives)}")
        for i, alt in enumerate(alternatives):
            print(f"  [{i+1}] alt_id={alt.get('alt_id')}, keys={list(alt.keys())}")
            if i < 2:  # 처음 2개만 상세 출력
                print(f"       win_theme 길이: {len(alt.get('win_theme', ''))}")
                print(f"       key_messages: {len(alt.get('key_messages', []))}개")


if __name__ == "__main__":
    asyncio.run(test_raw_response())
