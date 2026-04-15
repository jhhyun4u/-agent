# Plan: 플랫폼 자가검증 시스템 (Self-Verification) & 3. 검증 항목 설계
Cohesion: 0.09 | Nodes: 23

## Key Nodes
- **Plan: 플랫폼 자가검증 시스템 (Self-Verification)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\self-verification.plan.md) -- 11 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[4]]
  - -> contains -> [[5]]
  - -> contains -> [[6-db]]
  - -> contains -> [[7]]
  - -> contains -> [[8]]
  - -> contains -> [[9]]
  - -> contains -> [[10]]
  - -> contains -> [[11]]
- **3. 검증 항목 설계** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\self-verification.plan.md) -- 5 connections
  - -> contains -> [[3-1-5]]
  - -> contains -> [[3-2-30]]
  - -> contains -> [[3-3-1]]
  - -> contains -> [[3-4-api-1]]
  - <- contains <- [[plan-self-verification]]
- **5. 핵심 모듈** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\self-verification.plan.md) -- 5 connections
  - -> contains -> [[5-1-appserviceshealthcheckerpy]]
  - -> contains -> [[5-2-appservicesalertmanagerpy]]
  - -> contains -> [[5-3-scheduledmonitorpy]]
  - -> contains -> [[5-4-api-mainpy]]
  - <- contains <- [[plan-self-verification]]
- **python** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\self-verification.plan.md) -- 2 connections
  - <- has_code_example <- [[5-1-appserviceshealthcheckerpy]]
  - <- has_code_example <- [[5-2-appservicesalertmanagerpy]]
- **5-1. `app/services/health_checker.py` (신규)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\self-verification.plan.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[5]]
- **5-2. `app/services/alert_manager.py` (신규)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\self-verification.plan.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[5]]
- **6. DB 스키마** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\self-verification.plan.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[plan-self-verification]]
- **7. 알림 형식** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\self-verification.plan.md) -- 2 connections
  - -> contains -> [[teams-adaptive-card]]
  - <- contains <- [[plan-self-verification]]
- **sql** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\self-verification.plan.md) -- 1 connections
  - <- has_code_example <- [[6-db]]
- **1. 개요** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\self-verification.plan.md) -- 1 connections
  - <- contains <- [[plan-self-verification]]
- **10. 제약 사항 및 결정** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\self-verification.plan.md) -- 1 connections
  - <- contains <- [[plan-self-verification]]
- **11. 성공 기준** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\self-verification.plan.md) -- 1 connections
  - <- contains <- [[plan-self-verification]]
- **2. 기존 인프라 활용** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\self-verification.plan.md) -- 1 connections
  - <- contains <- [[plan-self-verification]]
- **3-1. 인프라 레이어 (매 5분)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\self-verification.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **3-2. 데이터 정합성 (매 30분)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\self-verification.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **3-3. 외부 서비스 (매 1시간)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\self-verification.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **3-4. API 스모크 테스트 (매 1시간)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\self-verification.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **4. 아키텍처** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\self-verification.plan.md) -- 1 connections
  - <- contains <- [[plan-self-verification]]
- **5-3. 스케줄러 확장 (`scheduled_monitor.py`)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\self-verification.plan.md) -- 1 connections
  - <- contains <- [[5]]
- **5-4. API 엔드포인트 (`main.py` 또는 별도 라우터)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\self-verification.plan.md) -- 1 connections
  - <- contains <- [[5]]
- **8. 구현 순서** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\self-verification.plan.md) -- 1 connections
  - <- contains <- [[plan-self-verification]]
- **9. 의존성** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\self-verification.plan.md) -- 1 connections
  - <- contains <- [[plan-self-verification]]
- **Teams Adaptive Card** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\self-verification.plan.md) -- 1 connections
  - <- contains <- [[7]]

## Internal Relationships
- 3. 검증 항목 설계 -> contains -> 3-1. 인프라 레이어 (매 5분) [EXTRACTED]
- 3. 검증 항목 설계 -> contains -> 3-2. 데이터 정합성 (매 30분) [EXTRACTED]
- 3. 검증 항목 설계 -> contains -> 3-3. 외부 서비스 (매 1시간) [EXTRACTED]
- 3. 검증 항목 설계 -> contains -> 3-4. API 스모크 테스트 (매 1시간) [EXTRACTED]
- 5. 핵심 모듈 -> contains -> 5-1. `app/services/health_checker.py` (신규) [EXTRACTED]
- 5. 핵심 모듈 -> contains -> 5-2. `app/services/alert_manager.py` (신규) [EXTRACTED]
- 5. 핵심 모듈 -> contains -> 5-3. 스케줄러 확장 (`scheduled_monitor.py`) [EXTRACTED]
- 5. 핵심 모듈 -> contains -> 5-4. API 엔드포인트 (`main.py` 또는 별도 라우터) [EXTRACTED]
- 5-1. `app/services/health_checker.py` (신규) -> has_code_example -> python [EXTRACTED]
- 5-2. `app/services/alert_manager.py` (신규) -> has_code_example -> python [EXTRACTED]
- 6. DB 스키마 -> has_code_example -> sql [EXTRACTED]
- 7. 알림 형식 -> contains -> Teams Adaptive Card [EXTRACTED]
- Plan: 플랫폼 자가검증 시스템 (Self-Verification) -> contains -> 1. 개요 [EXTRACTED]
- Plan: 플랫폼 자가검증 시스템 (Self-Verification) -> contains -> 2. 기존 인프라 활용 [EXTRACTED]
- Plan: 플랫폼 자가검증 시스템 (Self-Verification) -> contains -> 3. 검증 항목 설계 [EXTRACTED]
- Plan: 플랫폼 자가검증 시스템 (Self-Verification) -> contains -> 4. 아키텍처 [EXTRACTED]
- Plan: 플랫폼 자가검증 시스템 (Self-Verification) -> contains -> 5. 핵심 모듈 [EXTRACTED]
- Plan: 플랫폼 자가검증 시스템 (Self-Verification) -> contains -> 6. DB 스키마 [EXTRACTED]
- Plan: 플랫폼 자가검증 시스템 (Self-Verification) -> contains -> 7. 알림 형식 [EXTRACTED]
- Plan: 플랫폼 자가검증 시스템 (Self-Verification) -> contains -> 8. 구현 순서 [EXTRACTED]
- Plan: 플랫폼 자가검증 시스템 (Self-Verification) -> contains -> 9. 의존성 [EXTRACTED]
- Plan: 플랫폼 자가검증 시스템 (Self-Verification) -> contains -> 10. 제약 사항 및 결정 [EXTRACTED]
- Plan: 플랫폼 자가검증 시스템 (Self-Verification) -> contains -> 11. 성공 기준 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Plan: 플랫폼 자가검증 시스템 (Self-Verification), 3. 검증 항목 설계, 5. 핵심 모듈를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 self-verification.plan.md이다.

### Key Facts
- 5-1. `app/services/health_checker.py` (신규)
- ```python @dataclass class HealthResult: check_id: str           # "I-1", "D-3" 등 category: str           # "infra", "data", "external", "api" status: Literal["pass", "warn", "fail", "fixed"] message: str auto_recovered: bool = False duration_ms: float = 0
- ```python @dataclass class HealthResult: check_id: str           # "I-1", "D-3" 등 category: str           # "infra", "data", "external", "api" status: Literal["pass", "warn", "fail", "fixed"] message: str auto_recovered: bool = False duration_ms: float = 0
- ```python class AlertManager: # 중복 알림 억제: 같은 check_id fail이 30분 이내 반복 시 스킵 async def handle_results(results: list[HealthResult]) -> None async def send_alert(result: HealthResult) -> None async def log_to_db(result: HealthResult) -> None ```
- ```sql CREATE TABLE IF NOT EXISTS health_check_logs ( id UUID DEFAULT gen_random_uuid() PRIMARY KEY, check_id TEXT NOT NULL,          -- "I-1", "D-3" category TEXT NOT NULL,          -- "infra", "data", "external", "api" status TEXT NOT NULL,            -- "pass", "warn", "fail", "fixed" message…
