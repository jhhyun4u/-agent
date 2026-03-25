"""레거시 호환 래퍼 — 실제 구현: app.services.bidding.artifacts.cost_sheet_builder

이 파일은 기존 import 경로 호환을 위해 유지됩니다.
새 코드에서는 app.services.bidding.artifacts.cost_sheet_builder 경로를 사용하세요.
"""
import importlib as _importlib
import sys as _sys

_real = _importlib.import_module("app.services.bidding.artifacts.cost_sheet_builder")
_sys.modules[__name__] = _real
