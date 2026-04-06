"""레거시 호환 래퍼 — 실제 구현: app.services.bidding.pricing.cost_estimator"""
import importlib as _importlib
import sys as _sys
_real = _importlib.import_module("app.services.bidding.pricing.cost_estimator")
_sys.modules[__name__] = _real
