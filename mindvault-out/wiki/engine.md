# engine
Cohesion: 1.00 | Nodes: 1

## Key Nodes
- **engine** (C:\project\tenopa proposer\app\services\pricing\engine.py) -- 0 connections

## Internal Relationships

## Cross-Community Connections

## Context
이 커뮤니티는 engine를 중심으로 related 관계로 연결되어 있다. 주요 소스 파일은 engine.py이다.

### Key Facts
- """레거시 호환 래퍼 — 실제 구현: app.services.bidding.pricing.engine""" import importlib as _importlib import sys as _sys _real = _importlib.import_module("app.services.bidding.pricing.engine") _sys.modules[__name__] = _real
