# RTO/RPO 목표 & bash
Cohesion: 0.15 | Nodes: 19

## Key Nodes
- **RTO/RPO 목표** (C:\project\tenopa proposer\-agent-master\docs\operations\backup-disaster-recovery.md) -- 11 connections
  - -> contains -> [[1-supabase-postgresql]]
  - -> contains -> [[2-supabase-storage]]
  - -> contains -> [[3-github-repository]]
  - -> contains -> [[4]]
  - -> contains -> [[scenario-a]]
  - -> contains -> [[scenario-b]]
  - -> contains -> [[scenario-c-storage]]
  - -> contains -> [[scenario-d]]
  - -> contains -> [[1]]
  - -> contains -> [[prometheus]]
  - <- contains <- [[dr]]
- **bash** (C:\project\tenopa proposer\-agent-master\docs\operations\backup-disaster-recovery.md) -- 9 connections
  - <- has_code_example <- [[pgdump]]
  - <- has_code_example <- [[s3]]
  - <- has_code_example <- [[mirrored-repository]]
  - <- has_code_example <- [[4]]
  - <- has_code_example <- [[scenario-a]]
  - <- has_code_example <- [[scenario-b]]
  - <- has_code_example <- [[scenario-c-storage]]
  - <- has_code_example <- [[scenario-d]]
  - <- has_code_example <- [[1]]
- **1. Supabase PostgreSQL 백업** (C:\project\tenopa proposer\-agent-master\docs\operations\backup-disaster-recovery.md) -- 3 connections
  - -> contains -> [[supabase]]
  - -> contains -> [[pgdump]]
  - <- contains <- [[rtorpo]]
- **월간 복구 테스트 (1차 목요일)** (C:\project\tenopa proposer\-agent-master\docs\operations\backup-disaster-recovery.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[rtorpo]]
- **2. Supabase Storage 백업** (C:\project\tenopa proposer\-agent-master\docs\operations\backup-disaster-recovery.md) -- 2 connections
  - -> contains -> [[s3]]
  - <- contains <- [[rtorpo]]
- **3. GitHub Repository 백업** (C:\project\tenopa proposer\-agent-master\docs\operations\backup-disaster-recovery.md) -- 2 connections
  - -> contains -> [[mirrored-repository]]
  - <- contains <- [[rtorpo]]
- **4. 애플리케이션 설정 백업** (C:\project\tenopa proposer\-agent-master\docs\operations\backup-disaster-recovery.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[rtorpo]]
- **백업 및 재해복구 (DR) 계획** (C:\project\tenopa proposer\-agent-master\docs\operations\backup-disaster-recovery.md) -- 2 connections
  - -> contains -> [[rtorpo]]
  - <- contains <- [[backup-disaster-recovery]]
- **Mirrored Repository** (C:\project\tenopa proposer\-agent-master\docs\operations\backup-disaster-recovery.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[3-github-repository]]
- **수동 백업 (pg_dump)** (C:\project\tenopa proposer\-agent-master\docs\operations\backup-disaster-recovery.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[1-supabase-postgresql]]
- **Prometheus 알림** (C:\project\tenopa proposer\-agent-master\docs\operations\backup-disaster-recovery.md) -- 2 connections
  - -> has_code_example -> [[yaml]]
  - <- contains <- [[rtorpo]]
- **S3 크로스 리전 복제** (C:\project\tenopa proposer\-agent-master\docs\operations\backup-disaster-recovery.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[2-supabase-storage]]
- **Scenario A: 데이터베이스 부분 손실** (C:\project\tenopa proposer\-agent-master\docs\operations\backup-disaster-recovery.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[rtorpo]]
- **Scenario B: 전체 데이터베이스 손실** (C:\project\tenopa proposer\-agent-master\docs\operations\backup-disaster-recovery.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[rtorpo]]
- **Scenario C: Storage 파일 손실** (C:\project\tenopa proposer\-agent-master\docs\operations\backup-disaster-recovery.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[rtorpo]]
- **Scenario D: 애플리케이션 서버 다운** (C:\project\tenopa proposer\-agent-master\docs\operations\backup-disaster-recovery.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[rtorpo]]
- **yaml** (C:\project\tenopa proposer\-agent-master\docs\operations\backup-disaster-recovery.md) -- 1 connections
  - <- has_code_example <- [[prometheus]]
- **backup-disaster-recovery** (C:\project\tenopa proposer\-agent-master\docs\operations\backup-disaster-recovery.md) -- 1 connections
  - -> contains -> [[dr]]
- **자동 백업 (Supabase 관리)** (C:\project\tenopa proposer\-agent-master\docs\operations\backup-disaster-recovery.md) -- 1 connections
  - <- contains <- [[1-supabase-postgresql]]

## Internal Relationships
- backup-disaster-recovery -> contains -> 백업 및 재해복구 (DR) 계획 [EXTRACTED]
- 월간 복구 테스트 (1차 목요일) -> has_code_example -> bash [EXTRACTED]
- 1. Supabase PostgreSQL 백업 -> contains -> 자동 백업 (Supabase 관리) [EXTRACTED]
- 1. Supabase PostgreSQL 백업 -> contains -> 수동 백업 (pg_dump) [EXTRACTED]
- 2. Supabase Storage 백업 -> contains -> S3 크로스 리전 복제 [EXTRACTED]
- 3. GitHub Repository 백업 -> contains -> Mirrored Repository [EXTRACTED]
- 4. 애플리케이션 설정 백업 -> has_code_example -> bash [EXTRACTED]
- 백업 및 재해복구 (DR) 계획 -> contains -> RTO/RPO 목표 [EXTRACTED]
- Mirrored Repository -> has_code_example -> bash [EXTRACTED]
- 수동 백업 (pg_dump) -> has_code_example -> bash [EXTRACTED]
- Prometheus 알림 -> has_code_example -> yaml [EXTRACTED]
- RTO/RPO 목표 -> contains -> 1. Supabase PostgreSQL 백업 [EXTRACTED]
- RTO/RPO 목표 -> contains -> 2. Supabase Storage 백업 [EXTRACTED]
- RTO/RPO 목표 -> contains -> 3. GitHub Repository 백업 [EXTRACTED]
- RTO/RPO 목표 -> contains -> 4. 애플리케이션 설정 백업 [EXTRACTED]
- RTO/RPO 목표 -> contains -> Scenario A: 데이터베이스 부분 손실 [EXTRACTED]
- RTO/RPO 목표 -> contains -> Scenario B: 전체 데이터베이스 손실 [EXTRACTED]
- RTO/RPO 목표 -> contains -> Scenario C: Storage 파일 손실 [EXTRACTED]
- RTO/RPO 목표 -> contains -> Scenario D: 애플리케이션 서버 다운 [EXTRACTED]
- RTO/RPO 목표 -> contains -> 월간 복구 테스트 (1차 목요일) [EXTRACTED]
- RTO/RPO 목표 -> contains -> Prometheus 알림 [EXTRACTED]
- S3 크로스 리전 복제 -> has_code_example -> bash [EXTRACTED]
- Scenario A: 데이터베이스 부분 손실 -> has_code_example -> bash [EXTRACTED]
- Scenario B: 전체 데이터베이스 손실 -> has_code_example -> bash [EXTRACTED]
- Scenario C: Storage 파일 손실 -> has_code_example -> bash [EXTRACTED]
- Scenario D: 애플리케이션 서버 다운 -> has_code_example -> bash [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 RTO/RPO 목표, bash, 1. Supabase PostgreSQL 백업를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 backup-disaster-recovery.md이다.

### Key Facts
- 1. [개요](#개요) 2. [RTO/RPO 목표](#rtorpo-목표) 3. [백업 전략](#백업-전략) 4. [복구 절차](#복구-절차) 5. [테스트 계획](#테스트-계획) 6. [모니터링](#모니터링) 7. [체크리스트](#체크리스트)
- 수동 백업 (pg_dump) ```bash !/bin/bash 일일 수동 백업 스크립트 export PGPASSWORD="${SUPABASE_PASSWORD}"
- 자동 백업 (Supabase 관리) ``` 빈도: 일일 (자동) 보관 기간: 7일 복구 시점 선택(PITR): 지난 7일 내 임의 시점 ```
- set -e DATE=$(date +%Y%m%d) TEST_DIR="/tmp/dr-test-${DATE}"
- 자동 스냅샷 ``` 빈도: 일일 보관 기간: 14일 버킷: tenopa-proposer/documents ```
