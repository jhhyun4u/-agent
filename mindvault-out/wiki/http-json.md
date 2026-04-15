# http & json
Cohesion: 0.26 | Nodes: 14

## Key Nodes
- **http** (C:\project\tenopa proposer\-agent-master\docs\api\documents_api.md) -- 7 connections
  - <- has_code_example <- [[1]]
  - <- has_code_example <- [[2]]
  - <- has_code_example <- [[3]]
  - <- has_code_example <- [[4]]
  - <- has_code_example <- [[5]]
  - <- has_code_example <- [[6]]
  - <- has_code_example <- [[processingstatus]]
- **json** (C:\project\tenopa proposer\-agent-master\docs\api\documents_api.md) -- 6 connections
  - <- has_code_example <- [[1]]
  - <- has_code_example <- [[2]]
  - <- has_code_example <- [[3]]
  - <- has_code_example <- [[4]]
  - <- has_code_example <- [[5]]
  - <- has_code_example <- [[6]]
- **6. 문서 삭제** (C:\project\tenopa proposer\-agent-master\docs\api\documents_api.md) -- 6 connections
  - -> has_code_example -> [[http]]
  - -> has_code_example -> [[json]]
  - -> contains -> [[processingstatus]]
  - -> contains -> [[curl]]
  - -> contains -> [[python-httpx]]
  - <- contains <- [[api]]
- **문서 관리 API 명세서** (C:\project\tenopa proposer\-agent-master\docs\api\documents_api.md) -- 6 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[4]]
  - -> contains -> [[5]]
  - -> contains -> [[6]]
- **1. 문서 업로드** (C:\project\tenopa proposer\-agent-master\docs\api\documents_api.md) -- 3 connections
  - -> has_code_example -> [[http]]
  - -> has_code_example -> [[json]]
  - <- contains <- [[api]]
- **2. 문서 목록 조회** (C:\project\tenopa proposer\-agent-master\docs\api\documents_api.md) -- 3 connections
  - -> has_code_example -> [[http]]
  - -> has_code_example -> [[json]]
  - <- contains <- [[api]]
- **3. 문서 상세 조회** (C:\project\tenopa proposer\-agent-master\docs\api\documents_api.md) -- 3 connections
  - -> has_code_example -> [[http]]
  - -> has_code_example -> [[json]]
  - <- contains <- [[api]]
- **4. 문서 재처리** (C:\project\tenopa proposer\-agent-master\docs\api\documents_api.md) -- 3 connections
  - -> has_code_example -> [[http]]
  - -> has_code_example -> [[json]]
  - <- contains <- [[api]]
- **5. 문서 청크 조회** (C:\project\tenopa proposer\-agent-master\docs\api\documents_api.md) -- 3 connections
  - -> has_code_example -> [[http]]
  - -> has_code_example -> [[json]]
  - <- contains <- [[api]]
- **cURL** (C:\project\tenopa proposer\-agent-master\docs\api\documents_api.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[6]]
- **`processing_status` 값** (C:\project\tenopa proposer\-agent-master\docs\api\documents_api.md) -- 2 connections
  - -> has_code_example -> [[http]]
  - <- contains <- [[6]]
- **Python (httpx)** (C:\project\tenopa proposer\-agent-master\docs\api\documents_api.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[6]]
- **bash** (C:\project\tenopa proposer\-agent-master\docs\api\documents_api.md) -- 1 connections
  - <- has_code_example <- [[curl]]
- **python** (C:\project\tenopa proposer\-agent-master\docs\api\documents_api.md) -- 1 connections
  - <- has_code_example <- [[python-httpx]]

## Internal Relationships
- 1. 문서 업로드 -> has_code_example -> http [EXTRACTED]
- 1. 문서 업로드 -> has_code_example -> json [EXTRACTED]
- 2. 문서 목록 조회 -> has_code_example -> http [EXTRACTED]
- 2. 문서 목록 조회 -> has_code_example -> json [EXTRACTED]
- 3. 문서 상세 조회 -> has_code_example -> http [EXTRACTED]
- 3. 문서 상세 조회 -> has_code_example -> json [EXTRACTED]
- 4. 문서 재처리 -> has_code_example -> http [EXTRACTED]
- 4. 문서 재처리 -> has_code_example -> json [EXTRACTED]
- 5. 문서 청크 조회 -> has_code_example -> http [EXTRACTED]
- 5. 문서 청크 조회 -> has_code_example -> json [EXTRACTED]
- 6. 문서 삭제 -> has_code_example -> http [EXTRACTED]
- 6. 문서 삭제 -> has_code_example -> json [EXTRACTED]
- 6. 문서 삭제 -> contains -> `processing_status` 값 [EXTRACTED]
- 6. 문서 삭제 -> contains -> cURL [EXTRACTED]
- 6. 문서 삭제 -> contains -> Python (httpx) [EXTRACTED]
- 문서 관리 API 명세서 -> contains -> 1. 문서 업로드 [EXTRACTED]
- 문서 관리 API 명세서 -> contains -> 2. 문서 목록 조회 [EXTRACTED]
- 문서 관리 API 명세서 -> contains -> 3. 문서 상세 조회 [EXTRACTED]
- 문서 관리 API 명세서 -> contains -> 4. 문서 재처리 [EXTRACTED]
- 문서 관리 API 명세서 -> contains -> 5. 문서 청크 조회 [EXTRACTED]
- 문서 관리 API 명세서 -> contains -> 6. 문서 삭제 [EXTRACTED]
- cURL -> has_code_example -> bash [EXTRACTED]
- `processing_status` 값 -> has_code_example -> http [EXTRACTED]
- Python (httpx) -> has_code_example -> python [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 http, json, 6. 문서 삭제를 중심으로 has_code_example 관계로 연결되어 있다. 주요 소스 파일은 documents_api.md이다.

### Key Facts
- ```http POST /api/documents/upload Content-Type: multipart/form-data
- **콘텐츠 타입**: `application/json` (응답), `multipart/form-data` (업로드)
- ```bash 1. 문서 업로드 curl -X POST http://localhost:3000/api/documents/upload \ -H "Authorization: Bearer $JWT_TOKEN" \ -F "file=@proposal.pdf" \ -F "doc_type=제안서"
- | 상태 | 설명 | 다음 상태 | |------|------|---------| | `pending` | 대기 중 | `extracting` | | `extracting` | 텍스트 추출 중 | `chunking` | | `chunking` | 청크 분할 중 | `embedding` | | `embedding` | 임베딩 생성 중 | `completed` | | `completed` | 완료 | - | | `failed` | 실패 | `extracting` (재처리 시) |
- ```python import httpx
