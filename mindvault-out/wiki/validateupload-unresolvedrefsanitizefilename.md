# validate_upload & __unresolved__::ref::sanitize_filename
Cohesion: 0.50 | Nodes: 4

## Key Nodes
- **validate_upload** (C:\project\tenopa proposer\app\utils\file_utils.py) -- 4 connections
  - -> calls -> [[unresolvedrefsanitizefilename]]
  - -> calls -> [[unresolvedrefvalidateextension]]
  - -> calls -> [[unresolvedrefvalidatefilesize]]
  - <- contains <- [[fileutils]]
- **__unresolved__::ref::sanitize_filename** () -- 1 connections
  - <- calls <- [[validateupload]]
- **__unresolved__::ref::validate_extension** () -- 1 connections
  - <- calls <- [[validateupload]]
- **__unresolved__::ref::validate_file_size** () -- 1 connections
  - <- calls <- [[validateupload]]

## Internal Relationships
- validate_upload -> calls -> __unresolved__::ref::sanitize_filename [EXTRACTED]
- validate_upload -> calls -> __unresolved__::ref::validate_extension [EXTRACTED]
- validate_upload -> calls -> __unresolved__::ref::validate_file_size [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 validate_upload, __unresolved__::ref::sanitize_filename, __unresolved__::ref::validate_extension를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 file_utils.py이다.

### Key Facts
- def validate_upload(filename: str | None, content: bytes, category: str, max_mb: int | None = None) -> tuple[str, str]: """파일명 + 확장자 + 크기 통합 검증. (safe_filename, extension) 반환.""" safe = sanitize_filename(filename) ext = validate_extension(safe, category) validate_file_size(content, max_mb) return…
