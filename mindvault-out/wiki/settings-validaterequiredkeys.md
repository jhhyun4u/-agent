# Settings & validate_required_keys
Cohesion: 0.67 | Nodes: 3

## Key Nodes
- **Settings** (C:\project\tenopa proposer\app\config.py) -- 3 connections
  - -> extends -> [[unresolvedrefbasesettings]]
  - -> contains -> [[validaterequiredkeys]]
  - <- contains <- [[config]]
- **validate_required_keys** (C:\project\tenopa proposer\app\config.py) -- 2 connections
  - -> calls -> [[unresolvedrefappend]]
  - <- contains <- [[settings]]
- **__unresolved__::ref::basesettings** () -- 1 connections
  - <- extends <- [[settings]]

## Internal Relationships
- Settings -> extends -> __unresolved__::ref::basesettings [EXTRACTED]
- Settings -> contains -> validate_required_keys [EXTRACTED]

## Cross-Community Connections
- validate_required_keys -> calls -> __unresolved__::ref::append (-> [[unresolvedrefget-unresolvedrefexecute]])

## Context
이 커뮤니티는 Settings, validate_required_keys, __unresolved__::ref::basesettings를 중심으로 extends 관계로 연결되어 있다. 주요 소스 파일은 config.py이다.

### Key Facts
- from pydantic_settings import BaseSettings from pydantic import Field from typing import Literal
- def validate_required_keys(self) -> list[str]: """필수 API 키 누락 여부 확인. 누락된 키 이름 목록 반환.""" missing = [] if not self.anthropic_api_key: missing.append("ANTHROPIC_API_KEY") if not self.supabase_url: missing.append("SUPABASE_URL") if not self.supabase_key: missing.append("SUPABASE_KEY") if not…
