# Bidding 모듈 리스트럭처링 설계 & 3. `__init__.py` Re-export 정의
Cohesion: 0.11 | Nodes: 22

## Key Nodes
- **Bidding 모듈 리스트럭처링 설계** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bidding-restructure.design.md) -- 7 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3-initpy-re-export]]
  - -> contains -> [[4]]
  - -> contains -> [[5-import]]
  - -> contains -> [[6-8]]
  - -> contains -> [[7]]
- **3. `__init__.py` Re-export 정의** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bidding-restructure.design.md) -- 6 connections
  - -> contains -> [[31-appservicesbiddinginitpy]]
  - -> contains -> [[32-appservicesbiddingmonitorinitpy]]
  - -> contains -> [[33-appservicesbiddingsubmissioninitpy]]
  - -> contains -> [[34-appservicesbiddingartifactsinitpy]]
  - -> contains -> [[35-appservicesbiddingpricinginitpy]]
  - <- contains <- [[bidding]]
- **python** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bidding-restructure.design.md) -- 5 connections
  - <- has_code_example <- [[31-appservicesbiddinginitpy]]
  - <- has_code_example <- [[32-appservicesbiddingmonitorinitpy]]
  - <- has_code_example <- [[33-appservicesbiddingsubmissioninitpy]]
  - <- has_code_example <- [[34-appservicesbiddingartifactsinitpy]]
  - <- has_code_example <- [[42]]
- **4. 호환 래퍼 상세** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bidding-restructure.design.md) -- 4 connections
  - -> contains -> [[41-11]]
  - -> contains -> [[42]]
  - -> contains -> [[43-pricing]]
  - <- contains <- [[bidding]]
- **5. 내부 import 변경** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bidding-restructure.design.md) -- 4 connections
  - -> contains -> [[51-pricing-8]]
  - -> contains -> [[52-monitor-2]]
  - -> contains -> [[53-submission-1]]
  - <- contains <- [[bidding]]
- **1. 파일 이동 매핑** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bidding-restructure.design.md) -- 3 connections
  - -> contains -> [[11]]
  - -> contains -> [[12]]
  - <- contains <- [[bidding]]
- **3.1 `app/services/bidding/__init__.py`** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bidding-restructure.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[3-initpy-re-export]]
- **3.2 `app/services/bidding/monitor/__init__.py`** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bidding-restructure.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[3-initpy-re-export]]
- **3.3 `app/services/bidding/submission/__init__.py`** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bidding-restructure.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[3-initpy-re-export]]
- **3.4 `app/services/bidding/artifacts/__init__.py`** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bidding-restructure.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[3-initpy-re-export]]
- **4.2 래퍼 파일 형식** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bidding-restructure.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[4]]
- **1.1 전체 매핑 테이블** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bidding-restructure.design.md) -- 1 connections
  - <- contains <- [[1]]
- **1.2 이동하지 않는 파일** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bidding-restructure.design.md) -- 1 connections
  - <- contains <- [[1]]
- **2. 디렉토리 구조 상세** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bidding-restructure.design.md) -- 1 connections
  - <- contains <- [[bidding]]
- **3.5 `app/services/bidding/pricing/__init__.py`** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bidding-restructure.design.md) -- 1 connections
  - <- contains <- [[3-initpy-re-export]]
- **4.1 래퍼 파일 목록 (11개)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bidding-restructure.design.md) -- 1 connections
  - <- contains <- [[4]]
- **4.3 pricing/ 서브모듈 래퍼** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bidding-restructure.design.md) -- 1 connections
  - <- contains <- [[4]]
- **5.1 pricing/ 내부 (8건)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bidding-restructure.design.md) -- 1 connections
  - <- contains <- [[5-import]]
- **5.2 monitor/ 내부 (2건)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bidding-restructure.design.md) -- 1 connections
  - <- contains <- [[5-import]]
- **5.3 submission/ 내부 (1건)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bidding-restructure.design.md) -- 1 connections
  - <- contains <- [[5-import]]
- **6. 구현 절차 (8단계)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bidding-restructure.design.md) -- 1 connections
  - <- contains <- [[bidding]]
- **7. 성공 기준** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bidding-restructure.design.md) -- 1 connections
  - <- contains <- [[bidding]]

## Internal Relationships
- 1. 파일 이동 매핑 -> contains -> 1.1 전체 매핑 테이블 [EXTRACTED]
- 1. 파일 이동 매핑 -> contains -> 1.2 이동하지 않는 파일 [EXTRACTED]
- 3.1 `app/services/bidding/__init__.py` -> has_code_example -> python [EXTRACTED]
- 3.2 `app/services/bidding/monitor/__init__.py` -> has_code_example -> python [EXTRACTED]
- 3.3 `app/services/bidding/submission/__init__.py` -> has_code_example -> python [EXTRACTED]
- 3.4 `app/services/bidding/artifacts/__init__.py` -> has_code_example -> python [EXTRACTED]
- 3. `__init__.py` Re-export 정의 -> contains -> 3.1 `app/services/bidding/__init__.py` [EXTRACTED]
- 3. `__init__.py` Re-export 정의 -> contains -> 3.2 `app/services/bidding/monitor/__init__.py` [EXTRACTED]
- 3. `__init__.py` Re-export 정의 -> contains -> 3.3 `app/services/bidding/submission/__init__.py` [EXTRACTED]
- 3. `__init__.py` Re-export 정의 -> contains -> 3.4 `app/services/bidding/artifacts/__init__.py` [EXTRACTED]
- 3. `__init__.py` Re-export 정의 -> contains -> 3.5 `app/services/bidding/pricing/__init__.py` [EXTRACTED]
- 4. 호환 래퍼 상세 -> contains -> 4.1 래퍼 파일 목록 (11개) [EXTRACTED]
- 4. 호환 래퍼 상세 -> contains -> 4.2 래퍼 파일 형식 [EXTRACTED]
- 4. 호환 래퍼 상세 -> contains -> 4.3 pricing/ 서브모듈 래퍼 [EXTRACTED]
- 4.2 래퍼 파일 형식 -> has_code_example -> python [EXTRACTED]
- 5. 내부 import 변경 -> contains -> 5.1 pricing/ 내부 (8건) [EXTRACTED]
- 5. 내부 import 변경 -> contains -> 5.2 monitor/ 내부 (2건) [EXTRACTED]
- 5. 내부 import 변경 -> contains -> 5.3 submission/ 내부 (1건) [EXTRACTED]
- Bidding 모듈 리스트럭처링 설계 -> contains -> 1. 파일 이동 매핑 [EXTRACTED]
- Bidding 모듈 리스트럭처링 설계 -> contains -> 2. 디렉토리 구조 상세 [EXTRACTED]
- Bidding 모듈 리스트럭처링 설계 -> contains -> 3. `__init__.py` Re-export 정의 [EXTRACTED]
- Bidding 모듈 리스트럭처링 설계 -> contains -> 4. 호환 래퍼 상세 [EXTRACTED]
- Bidding 모듈 리스트럭처링 설계 -> contains -> 5. 내부 import 변경 [EXTRACTED]
- Bidding 모듈 리스트럭처링 설계 -> contains -> 6. 구현 절차 (8단계) [EXTRACTED]
- Bidding 모듈 리스트럭처링 설계 -> contains -> 7. 성공 기준 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Bidding 모듈 리스트럭처링 설계, 3. `__init__.py` Re-export 정의, python를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 bidding-restructure.design.md이다.

### Key Facts
- > 날짜: 2026-03-24 > Plan 참조: `docs/01-plan/features/bidding-restructure.plan.md`
- 3.1 `app/services/bidding/__init__.py`
- ```python """Bidding 도메인 통합 패키지.
- 원래 위치에 남기는 래퍼 파일. 기존 import을 깨뜨리지 않으면서 점진적 마이그레이션 가능.
- 이동된 파일 내부에서 서로를 참조하는 import 수정.
