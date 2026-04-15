# Code Style & Conventions & Error Handling
Cohesion: 0.33 | Nodes: 6

## Key Nodes
- **Code Style & Conventions** (C:\project\tenopa proposer\-agent-master\.serena\memories\code_style_conventions.md) -- 5 connections
  - -> contains -> [[python]]
  - -> contains -> [[file-organization]]
  - -> contains -> [[error-handling]]
  - -> contains -> [[key-patterns]]
  - -> contains -> [[post-edit-checklist]]
- **Error Handling** (C:\project\tenopa proposer\-agent-master\.serena\memories\code_style_conventions.md) -- 1 connections
  - <- contains <- [[code-style-conventions]]
- **File Organization** (C:\project\tenopa proposer\-agent-master\.serena\memories\code_style_conventions.md) -- 1 connections
  - <- contains <- [[code-style-conventions]]
- **Key Patterns** (C:\project\tenopa proposer\-agent-master\.serena\memories\code_style_conventions.md) -- 1 connections
  - <- contains <- [[code-style-conventions]]
- **Post-Edit Checklist** (C:\project\tenopa proposer\-agent-master\.serena\memories\code_style_conventions.md) -- 1 connections
  - <- contains <- [[code-style-conventions]]
- **Python** (C:\project\tenopa proposer\-agent-master\.serena\memories\code_style_conventions.md) -- 1 connections
  - <- contains <- [[code-style-conventions]]

## Internal Relationships
- Code Style & Conventions -> contains -> Python [EXTRACTED]
- Code Style & Conventions -> contains -> File Organization [EXTRACTED]
- Code Style & Conventions -> contains -> Error Handling [EXTRACTED]
- Code Style & Conventions -> contains -> Key Patterns [EXTRACTED]
- Code Style & Conventions -> contains -> Post-Edit Checklist [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Code Style & Conventions, Error Handling, File Organization를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 code_style_conventions.md이다.

### Key Facts
- Python - PEP 8 compliance - Type annotations on all functions - Pydantic v2 models for schemas - async/await patterns (FastAPI) - Error handling: TenopAPIError base class (standard error codes) - Docstrings: Korean language - Use `from dataclasses import dataclass` for immutable structures
- Python - PEP 8 compliance - Type annotations on all functions - Pydantic v2 models for schemas - async/await patterns (FastAPI) - Error handling: TenopAPIError base class (standard error codes) - Docstrings: Korean language - Use `from dataclasses import dataclass` for immutable structures
- Error Handling - Handle errors explicitly at every level - Use TenopAPIError for consistency - HTTPException gradually replaced with TenopAPIError
- Post-Edit Checklist - Run linting/formatting - Verify type hints - Check against similar patterns in codebase - Update CLAUDE.md if architecture changes
- Post-Edit Checklist - Run linting/formatting - Verify type hints - Check against similar patterns in codebase - Update CLAUDE.md if architecture changes
