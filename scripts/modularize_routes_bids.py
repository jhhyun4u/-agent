#!/usr/bin/env python3
"""
routes_bids.py를 app/api/bids/ 모듈로 자동 분해

구조:
- app/api/bids/utils.py      - 유틸 함수 + 상수
- app/api/bids/helpers.py    - 헬퍼 함수
- app/api/bids/handlers.py   - 라우트 핸들러 (21개)
- app/api/bids/routes.py     - 라우터 생성 및 엔드포인트 등록
- app/api/bids/__init__.py   - 모듈 export
"""

import re
from pathlib import Path

# ─────────────────────────────────────────────────────────
# 1. 파일 읽기
# ─────────────────────────────────────────────────────────

routes_bids_path = Path(__file__).parent.parent / "app" / "api" / "routes_bids.py"
content = routes_bids_path.read_text(encoding="utf-8")

# ─────────────────────────────────────────────────────────
# 2. 섹션 분리 (정규식 기반)
# ─────────────────────────────────────────────────────────

lines = content.split('\n')

# Imports 찾기 (처음부터 첫 함수 정의까지)
imports_end = 0
for i, line in enumerate(lines):
    if line.startswith('logger = '):
        imports_end = i
        break

imports_section = '\n'.join(lines[:imports_end + 1])

# 함수 시작 라인 찾기
func_lines = {}  # func_name -> line_number
for i, line in enumerate(lines):
    match = re.match(r'^(async )?def ([a-zA-Z_][a-zA-Z0-9_]*)\(', line)
    if match:
        func_name = match.group(2)
        func_lines[func_name] = i

# ─────────────────────────────────────────────────────────
# 3. 함수별 내용 추출
# ─────────────────────────────────────────────────────────

def extract_function(func_name: str, start_line: int) -> str:
    """함수 정의부터 다음 함수까지의 내용 추출"""
    func_start = start_line

    # 다음 함수 찾기
    func_end = len(lines)
    for fn, ln in func_lines.items():
        if ln > start_line:
            func_end = min(func_end, ln)

    # 함수 끝 찾기 (들여쓰기 기반)
    actual_end = func_start + 1
    if actual_end < len(lines):
        first_line = lines[func_start]
        if first_line.startswith('def ') or first_line.startswith('async def '):
            base_indent = len(first_line) - len(first_line.lstrip())
            for i in range(func_start + 1, func_end):
                stripped = lines[i].lstrip()
                if stripped and not lines[i].startswith(' ' * (base_indent + 1)) and not lines[i].startswith('\t'):
                    # 주석이나 빈 줄 확인
                    if not stripped.startswith('#'):
                        actual_end = i
                        break
                actual_end = i + 1

    return '\n'.join(lines[func_start:actual_end])

# ─────────────────────────────────────────────────────────
# 4. 함수 분류
# ─────────────────────────────────────────────────────────

# Utility functions (private helpers)
utils_funcs = [
    '_load_file_cache',
    '_save_file_cache',
    '_escape_like',
    '_extract_content_from_raw',
    '_check_analysis_cache',
    '_load_bid_content',
    '_load_teams_info',
    '_format_rfp_sections',
    '_format_notice_markdown',
]

# Helper functions (handler support)
helpers_funcs = [
    '_monitor_my',
    '_monitor_team_or_division',
    '_monitor_company',
    '_enrich_monitor_data',
    '_run_unified_analysis',
    '_save_recommendations',
    '_invalidate_recommendations_cache',
    '_get_preset_or_404',
    '_get_active_preset_or_422',
    '_get_profile_or_422',
    '_get_cached_recommendations',
    '_build_recommendations_response',
    '_run_fetch_and_analyze',
    '_queue_bid_analysis',
    '_analyze_bid_background',
    '_save_markdown_to_storage',
]

# Handler functions (public endpoints)
handlers_funcs = [
    'get_bid_profile',
    'upsert_bid_profile',
    'list_search_presets',
    'create_search_preset',
    'update_search_preset',
    'delete_search_preset',
    'activate_search_preset',
    'trigger_fetch',
    'get_recommendations',
    'list_announcements',
    'pipeline_status',
    'pipeline_trigger',
    'get_scored_bids',
    'manual_crawl',
    'get_monitored_bids',
    'update_bid_status',
    'analyze_bid_for_proposal',
    'toggle_bookmark',
    'get_bid_detail',
    'list_bid_attachments',
    'download_bid_attachment',
]

# ─────────────────────────────────────────────────────────
# 5. 섹션 내용 구축
# ─────────────────────────────────────────────────────────

# Constants와 imports 정리
const_lines = []
for i, line in enumerate(lines[imports_end:]):
    if i >= len(lines) - imports_end:
        break
    if any(fn in line for fn in utils_funcs + helpers_funcs + handlers_funcs):
        # 함수 시작 감지
        if re.match(r'^(async )?def ', line.lstrip()):
            const_lines = lines[imports_end:imports_end + i]
            break

# ─────────────────────────────────────────────────────────
# 6. 파일 생성 (간단한 방식: 섹션으로 분리)
# ─────────────────────────────────────────────────────────

bids_dir = Path(__file__).parent.parent / "app" / "api" / "bids"
bids_dir.mkdir(parents=True, exist_ok=True)

print("📦 routes_bids.py 분해 시작...")
print(f"  📍 Utils 함수: {len(utils_funcs)}개")
print(f"  📍 Helper 함수: {len(helpers_funcs)}개")
print(f"  📍 Handler 함수: {len(handlers_funcs)}개")
print()

# 원본 파일 읽기 (섹션 기반)
with open(routes_bids_path, 'r', encoding='utf-8') as f:
    full_content = f.read()

# 간단한 정규식 분해
# Constants 섹션 찾기
const_section_match = re.search(
    r'(logger = logging\.getLogger.*?)((?:^@router|^async def |^def ))',
    full_content,
    re.MULTILINE | re.DOTALL
)

if const_section_match:
    const_section = const_section_match.group(1)
else:
    const_section = ""

print("✅ 분석 완료")
print("📝 파일 생성 준비 중...")

# 상세 정보 출력
print(f"\nImports 섹션: ~{len(imports_section)} 글자")
print(f"Constants 섹션: ~{len(const_section)} 글자")
print(f"총 함수: {len(func_lines)}개")
print(f"  - Utils: {sum(1 for f in func_lines if f in utils_funcs)}개")
print(f"  - Helpers: {sum(1 for f in func_lines if f in helpers_funcs)}개")
print(f"  - Handlers: {sum(1 for f in func_lines if f in handlers_funcs)}개")

print(f"\n📂 대상: {bids_dir}")
print("✅ 준비 완료 - manual split 필요")
