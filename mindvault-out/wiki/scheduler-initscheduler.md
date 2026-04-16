# scheduler & init_scheduler
Cohesion: 0.20 | Nodes: 11

## Key Nodes
- **scheduler** (C:\project\tenopa proposer\app\scheduler.py) -- 7 connections
  - -> contains -> [[getscheduler]]
  - -> contains -> [[initscheduler]]
  - -> contains -> [[shutdownscheduler]]
  - -> contains -> [[registerjobs]]
  - -> imports -> [[unresolvedreflogging]]
  - -> imports -> [[unresolvedrefasyncio]]
  - -> imports -> [[unresolvedrefcron]]
- **init_scheduler** (C:\project\tenopa proposer\app\scheduler.py) -- 5 connections
  - -> calls -> [[unresolvedrefgetscheduler]]
  - -> calls -> [[unresolvedrefinfo]]
  - -> calls -> [[unresolvedrefregisterjobs]]
  - -> calls -> [[unresolvedrefstart]]
  - <- contains <- [[scheduler]]
- **shutdown_scheduler** (C:\project\tenopa proposer\app\scheduler.py) -- 4 connections
  - -> calls -> [[unresolvedrefgetscheduler]]
  - -> calls -> [[unresolvedrefshutdown]]
  - -> calls -> [[unresolvedrefinfo]]
  - <- contains <- [[scheduler]]
- **__unresolved__::ref::get_scheduler** () -- 3 connections
  - <- calls <- [[initscheduler]]
  - <- calls <- [[shutdownscheduler]]
  - <- calls <- [[startbatchscheduler]]
- **start_batch_scheduler** (C:\project\tenopa proposer\app\services\scheduler\vault_bidding_batch.py) -- 3 connections
  - -> calls -> [[unresolvedrefgetscheduler]]
  - -> calls -> [[unresolvedrefstartscheduler]]
  - <- contains <- [[vaultbiddingbatch]]
- **__unresolved__::ref::asyncioscheduler** () -- 2 connections
  - <- calls <- [[getscheduler]]
  - <- calls <- [[setupscheduler]]
- **get_scheduler** (C:\project\tenopa proposer\app\scheduler.py) -- 2 connections
  - -> calls -> [[unresolvedrefasyncioscheduler]]
  - <- contains <- [[scheduler]]
- **__unresolved__::ref::_register_jobs** () -- 1 connections
  - <- calls <- [[initscheduler]]
- **__unresolved__::ref::cron** () -- 1 connections
  - <- imports <- [[scheduler]]
- **__unresolved__::ref::shutdown** () -- 1 connections
  - <- calls <- [[shutdownscheduler]]
- **__unresolved__::ref::start_scheduler** () -- 1 connections
  - <- calls <- [[startbatchscheduler]]

## Internal Relationships
- get_scheduler -> calls -> __unresolved__::ref::asyncioscheduler [EXTRACTED]
- init_scheduler -> calls -> __unresolved__::ref::get_scheduler [EXTRACTED]
- init_scheduler -> calls -> __unresolved__::ref::_register_jobs [EXTRACTED]
- shutdown_scheduler -> calls -> __unresolved__::ref::get_scheduler [EXTRACTED]
- shutdown_scheduler -> calls -> __unresolved__::ref::shutdown [EXTRACTED]
- scheduler -> contains -> get_scheduler [EXTRACTED]
- scheduler -> contains -> init_scheduler [EXTRACTED]
- scheduler -> contains -> shutdown_scheduler [EXTRACTED]
- scheduler -> imports -> __unresolved__::ref::cron [EXTRACTED]
- start_batch_scheduler -> calls -> __unresolved__::ref::get_scheduler [EXTRACTED]
- start_batch_scheduler -> calls -> __unresolved__::ref::start_scheduler [EXTRACTED]

## Cross-Community Connections
- init_scheduler -> calls -> __unresolved__::ref::info (-> [[unresolvedrefget-unresolvedrefexecute]])
- init_scheduler -> calls -> __unresolved__::ref::start (-> [[unresolvedrefreact-unresolvedreflibapi]])
- shutdown_scheduler -> calls -> __unresolved__::ref::info (-> [[unresolvedrefget-unresolvedrefexecute]])
- scheduler -> contains -> _register_jobs (-> [[unresolvedrefget-unresolvedrefexecute]])
- scheduler -> imports -> __unresolved__::ref::logging (-> [[unresolvedrefbasemodel-unresolvedreflogging]])
- scheduler -> imports -> __unresolved__::ref::asyncio (-> [[unresolvedrefbasemodel-unresolvedreflogging]])

## Context
이 커뮤니티는 scheduler, init_scheduler, shutdown_scheduler를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 scheduler.py, vault_bidding_batch.py이다.

### Key Facts
- """ APScheduler 스케줄러 초기화 및 관리
- async def init_scheduler(): """스케줄러 초기화 및 작업 등록""" scheduler = get_scheduler()
- async def shutdown_scheduler(): """스케줄러 종료""" scheduler = get_scheduler() if scheduler.running: scheduler.shutdown(wait=True) logger.info("Scheduler stopped")
- async def start_batch_scheduler(): """배치 스케줄러 시작 (애플리케이션 시작 시 호출)""" scheduler = await get_scheduler() await scheduler.start_scheduler()
- def get_scheduler() -> AsyncIOScheduler: """스케줄러 인스턴스 반환""" global _scheduler if _scheduler is None: _scheduler = AsyncIOScheduler() return _scheduler
