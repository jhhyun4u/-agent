# Vault Chat Phase 2 — 대화 문맥 유지 & 권한 기반 응답 & Teams 통합

**Version**: 2.0  
**Initiated**: 2026-04-20  
**Target Completion**: 2026-05-04  
**Estimated Duration**: 2주 (14일)  
**Status**: PLANNING  

---

## Executive Summary

Vault Chat Phase 1에서 구축한 기본 의미 검색과 다중 회전 대화 시스템을 확장하여 **대화 문맥 유지**, **조직 역할 기반 응답 필터링**, **다국어 지원**, **Teams 채널 봇 통합**을 추가한다. 

내부 지식베이스를 학습한 AI 어시스턴트가 조직 전사원(모든 직급 및 팀)을 대상으로 실시간 Q&A를 제공하며, Teams 알림 통합으로 조직 생산성을 극대화한다.

---

## 비즈니스 가치

### 1. 대화 문맥 유지 (Conversation Context)
- **문제**: Phase 1에서 각 질문이 독립적으로 처리되어 "이전 답변을 기반으로..."와 같은 연속 질문 불가능
- **해결책**: 최근 6-8 회전의 대화 이력을 벡터 임베딩과 함께 컨텍스트 윈도우에 주입
- **효과**: 
  - 사용자 경험 향상 (자연스러운 대화 흐름)
  - 복잡한 쿼리 분해 가능 ("이 팀의 시장 현황은?" → "지난 분석과 비교하면?")
  - 회사 내부 지식 탐색 효율 20-30% 증가

### 2. 조직 역할 기반 응답 필터링 (Permission-Based Response Filtering)
- **문제**: 현재 모든 사용자가 동일한 지식베이스에 접근 → 임직원 급여, 수주 전략, 기밀 경쟁사 정보 노출 위험
- **해결책**: 
  - 각 지식 문서에 최소 접근 역할(member/lead/director/executive/admin) 메타데이터 설정
  - 응답 생성 후 사용자 역할 검증: 제외 콘텐츠는 제거 후 재응답 또는 "접근 권한 없음" 안내
  - 감시 로깅: 누가 어떤 정보 접근 시도
- **효과**:
  - 보안 리스크 제거 (GDPR, 내부 정보 유출 방지)
  - 신뢰도 증가 (감사 추적 자동화)
  - 관리자 부담 감소 (자동 권한 검증)

### 3. 다국어 지원 (Multi-language Support)
- **문제**: Phase 1은 한국어 중심 → 글로벌 팀/발주처 정보 활용 제한
- **해결책**:
  - 사용자 언어 자동 감지 (쿼리 언어로 추론)
  - 벡터 임베딩 다국어 모델 (OpenAI text-embedding-3-large는 다국어 지원)
  - 응답 언어 자동 조정 (사용자 선호도 저장 후 유지)
  - 문서 다국어 인덱싱: 동일 내용의 영문/중문/일문 버전 병렬 임베딩
- **효과**:
  - 제안 팀의 국제 프로젝트 수주율 향상
  - 글로벌 고객사 정보 활용 (영문 공고/법규 자동 번역)
  - 사용자 만족도 증가 (모국어 응답)

### 4. Teams 채널 봇 통합 (Teams Channel Bot Integration)
- **문제**: 현재 Vault는 웹 인터페이스만 제공 → 업무 흐름 방해 (별도 탭 전환)
- **해결책**:
  - Teams 채널 봇 3가지 시나리오:
    1. **적응형 봇**: 채널 멘션 감지 (`@Vault [질문]`) → 답변 + 소스 직접 포스트
    2. **일일 다이제스트**: 팀별 정기 모니터링 키워드 (G2B 공고, 경쟁사 뉴스) 요약 → 매일 아침 발송
    3. **프로젝트 자동 알림**: 새 RFP 수집 후 유사 내부 경험 자동 제시
  - Incoming Webhook 활용 (기존 teams_webhook_url 확장)
- **효과**:
  - Teams 사용 시간 내 AI 지식 활용 (흐름 방해 최소화)
  - 팀의 의사결정 속도 향상 (관련 정보 자동 푸시)
  - 입찰 대응 시간 단축 (조기 인식 → 조기 준비)

---

## 요구사항 명세

### FR1: 대화 문맥 유지

| 항목 | 상세 |
|------|------|
| **목표** | 다중 회전 대화 시 이전 맥락을 자동으로 주입하여 자연스러운 연속 질문 지원 |
| **입력** | 사용자 새로운 질문 + conversation_id (기존) |
| **처리** | 1. DB에서 마지막 6-8 회전 메시지 조회 2. 각 메시지를 벡터 임베딩 3. 컨텍스트 윈도우에 주입 4. 쿼리 라우팅 및 응답 생성 |
| **출력** | 이전 대화 이력을 고려한 개선된 응답 + 새로운 메시지 저장 |
| **성공 기준** | - 연속 질문 3회 이상 정확도 > 85% - 문맥 고려 여부 테스트 케이스 통과 |
| **기술 스택** | PostgreSQL (vault_messages), VaultContextManager (확장), Claude API (context injection) |

### FR2: 조직 역할 기반 응답 필터링

| 항목 | 상세 |
|------|------|
| **목표** | 사용자 역할에 따라 접근 가능 정보만 응답에 포함 |
| **입력** | 사용자 role + 응답 텍스트 + 소스 목록 |
| **처리** | 1. vault_documents 메타데이터에 min_required_role 저장 2. 응답 생성 후 출처 검증 3. 권한 없는 소스 제거 4. 필요시 재응답 또는 경고 |
| **출력** | 역할별 필터링된 응답 + 제외 이유 (선택) |
| **역할 계층** | member < lead < director < executive < admin |
| **성공 기준** | - 역할별 필터링 테스트 100% 통과 - 감사 로그 기록율 100% |
| **기술 스택** | vault_documents (메타데이터 확장), vault_audit_logs, RLS (강화) |

### FR3: 다국어 지원

| 항목 | 상세 |
|------|------|
| **목표** | 영문, 중문, 일문 쿼리 자동 감지 및 응답 (한국어 기본) |
| **입력** | 사용자 쿼리 (다국어) |
| **처리** | 1. langdetect로 언어 감지 2. 감지 언어로 임베딩 검색 3. 응답 생성 4. 필요시 번역 |
| **출력** | 사용자 언어로 응답 + 소스는 원문 유지 |
| **지원 언어** | 한국어(KO), 영어(EN), 중문(ZH), 일어(JA) |
| **성공 기준** | - 4개 언어 쿼리 테스트 통과 - 번역 품질 평가 > 4/5 |
| **기술 스택** | langdetect, OpenAI embeddings (다국어), Claude API (번역) |

### FR4: Teams 채널 봇 통합

| 항목 | 상세 |
|------|------|
| **목표** | Teams 채널에서 직접 AI 지식베이스 활용 가능 |
| **통합 방식** | 1. 적응형 봇: 채널 멘션 → 실시간 응답 2. 일일 다이제스트: 정기 키워드 모니터링 → 정해진 시간 요약 발송 3. 프로젝트 알림: RFP 수집 → 자동 매칭 및 추천 |
| **API** | Incoming Webhook (기존) + 정기 스케줄러 (새) |
| **성공 기준** | - 봇 응답 시간 < 5초 - 메시지 포스트 성공률 > 98% - 사용자 피드백 > 4/5 |
| **기술 스택** | Teams Webhook, FastAPI, APScheduler, Claude API |

### NFR1: 성능 & 확장성

| 항목 | 요구사항 |
|------|---------|
| **대화 로드** | 동시 50명 사용자, 분당 100 쿼리 처리 가능 |
| **응답 시간** | 컨텍스트 주입 포함 평균 < 2초 (P95 < 4초) |
| **메모리** | 컨텍스트 윈도우 (6-8 턴) 메모리 오버헤드 < 100KB/대화 |
| **저장소** | 월 100만 메시지 × 평균 500B = 500GB (1년에 6TB, 보관 정책 적용) |

### NFR2: 보안

| 항목 | 요구사항 |
|------|---------|
| **접근 제어** | RLS + 애플리케이션 레이어 역할 검증 이중화 |
| **감시 로깅** | 모든 조회 + 제외된 정보 접근 시도 기록 |
| **암호화** | 전송 TLS, 저장소 AEAD 암호화 (Supabase 기본) |
| **규정** | GDPR, ISO 27001 감사 대비 (로그 보존 1년) |

### NFR3: 가용성

| 항목 | 요구사항 |
|------|---------|
| **SLA** | 99.5% uptime (월 3.6시간 다운타임 허용) |
| **재해복구** | 데이터 자동 백업 (일일), RTO 1시간, RPO 24시간 |
| **모니터링** | 실시간 대시보드 (응답시간, 에러율, 데이터 신선도) |

---

## 기능 명세 (Detailed Feature Specification)

### FEATURE-2.1: Conversation Context Storage & Retrieval

**설명**: 대화 이력을 효율적으로 검색하고 LLM 컨텍스트로 주입

**DB 스키마 변경**:
```sql
ALTER TABLE vault_messages ADD COLUMN 
  context_embedding VECTOR(1536);  -- 컨텍스트용 임베딩
ALTER TABLE vault_messages ADD COLUMN 
  is_question BOOLEAN DEFAULT true;  -- Q/A 구분
CREATE INDEX idx_vault_messages_context 
  ON vault_messages(conversation_id, created_at DESC);
```

**API Endpoint** (신규):
- `GET /api/vault/conversations/{id}/context` - 마지막 N 회전 조회
- `POST /api/vault/conversations/{id}/search-history` - 대화 이력 검색

**프롬프트 주입 예시**:
```
[이전 대화 맥락]
사용자: "당사의 정부 프로젝트 성공 사례는?"
어시스턴트: "2024년 환경부 프로젝트 2건, 낙찰률 80% 달성..."

[새 질문]
사용자: "그 중에서 예산이 가장 컸던 것은?"
→ 어시스턴트: (이전 맥락 이용) "당사가 수주한 환경부 프로젝트 중 OOO이 가장 크며..."
```

---

### FEATURE-2.2: Permission-Based Response Filtering

**설명**: 역할 기반 접근 제어로 민감 정보 자동 보호

**DB 스키마 변경**:
```sql
ALTER TABLE vault_documents ADD COLUMN
  min_required_role TEXT DEFAULT 'member'
  CHECK (min_required_role IN ('member','lead','director','executive','admin'));
  
ALTER TABLE vault_audit_logs ADD COLUMN
  action_denied BOOLEAN DEFAULT false;  -- 거부된 접근 추적
ALTER TABLE vault_audit_logs ADD COLUMN
  denied_reason TEXT;
```

**필터링 로직**:
```
응답 생성 (Claude API)
  ↓
소스 문서 추출 (citation_service)
  ↓
사용자 역할 vs 문서 min_required_role 비교
  ↓
권한 없음 → 제거 또는 재응답 ("이 정보는 director 이상만 접근 가능합니다")
  ↓
감시 로그 기록 (attempted_access 플래그)
  ↓
최종 응답 반환
```

**역할 정의**:
| 역할 | 접근 가능 정보 | 예시 |
|------|---|---|
| member | 공개 프로젝트, 외부 정보 | 낙찰 사례, 정부 공고 |
| lead | 팀 내부 노하우, 팀별 실적 | 팀 낙찰률, 팀원 정보 |
| director | 전사 전략, 경쟁사 분석 | 수주전략, 경쟁사 가격 분석 |
| executive | 매출, 수익성, 인사 정보 | 팀 매출, 직원 급여, M&A 정보 |
| admin | 전체 (제한 없음) | 모든 정보 |

---

### FEATURE-2.3: Multi-language Support

**설명**: 다국어 쿼리 자동 감지 및 응답

**구현**:
1. **언어 감지**: langdetect로 쿼리 언어 추론
2. **다국어 임베딩**: OpenAI text-embedding-3-large (다국어 지원)
3. **응답 언어**: 감지 언어로 생성, 사용자 선호도 저장
4. **문서 번역**: 중요 문서 (정부 공고, 경쟁사 분석) 다국어 버전 유지

**DB 스키마**:
```sql
ALTER TABLE vault_documents ADD COLUMN
  language TEXT DEFAULT 'ko'
  CHECK (language IN ('ko', 'en', 'zh', 'ja'));
ALTER TABLE vault_documents ADD COLUMN
  translated_from UUID REFERENCES vault_documents(id);  -- 원본 문서 링크

ALTER TABLE users ADD COLUMN
  preferred_language TEXT DEFAULT 'ko';  -- 사용자 언어 선호도

ALTER TABLE vault_conversations ADD COLUMN
  primary_language TEXT DEFAULT 'ko';  -- 대화 주 언어
```

**API Endpoint** (신규):
- `POST /api/vault/chat` (기존, 언어 자동 감지 추가)
- `PUT /api/users/preferences` - 언어 선호도 설정

**테스트 케이스**:
- 영문 쿼리: "What are the government projects completed in 2024?"
- 중문 쿼리: "2024年完成的政府项目有哪些?"
- 일문 쿼리: "2024年に完了した政府プロジェクトは?"

---

### FEATURE-2.4: Teams Channel Bot Integration

**설명**: Teams에서 직접 Vault AI 활용 가능한 3가지 봇 모드

**모드 1: 적응형 봇 (Adaptive Bot)**
- 트리거: 채널 멘션 (`@Vault [질문]`)
- 응답: 실시간 AI 답변 (Thread로 포스트)
- 구현: Teams Incoming Webhook → FastAPI → Vault API
- SLA: 5초 이내 응답

**모드 2: 일일 다이제스트 (Daily Digest)**
- 트리거: 매일 오전 9시 (정기)
- 내용: 팀별 모니터링 키워드 검색 결과 요약
- 예: "G2B 신규 공고 3건, 경쟁사 입찰 현황, 기술 동향"
- 구현: APScheduler + Vault Search + Teams Webhook
- 빈도: 평일 08:00~18:00 매시 정각

**모드 3: 프로젝트 자동 추천 (Project Matching)**
- 트리거: 새 RFP 수집 (G2B 또는 수동 업로드)
- 추천: "당사 유사 프로젝트 3건 발견: 낙찰 가능성 85% (Team A), 70% (Team B)..."
- 구현: RFP 수집 → 의미 검색 (Vault) → Teams Webhook
- 효과: 조기 대응 → 입찰 준비 시간 증가

**DB 스키마**:
```sql
CREATE TABLE IF NOT EXISTS teams_bot_config (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id UUID REFERENCES teams(id) NOT NULL UNIQUE,
  webhook_url TEXT NOT NULL,
  bot_enabled BOOLEAN DEFAULT true,
  bot_modes TEXT[] DEFAULT ARRAY['adaptive', 'digest'],  -- 활성 모드
  digest_time TIME DEFAULT '09:00',  -- 다이제스트 발송 시간
  digest_keywords TEXT[] DEFAULT '{}',  -- 모니터링 키워드
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS teams_bot_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id UUID REFERENCES teams(id) NOT NULL,
  conversation_id UUID REFERENCES vault_conversations(id),
  query TEXT NOT NULL,
  response TEXT NOT NULL,
  message_id TEXT,  -- Teams message ID
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**API Endpoints** (신규):
- `POST /api/teams/bot/query` - 적응형 봇 쿼리
- `GET /api/teams/bot/config/{team_id}` - 봇 설정 조회
- `PUT /api/teams/bot/config/{team_id}` - 봇 설정 변경
- `POST /api/teams/bot/digest` - 수동 다이제스트 발송 (테스트용)

**프롬프트 예시**:
```
[적응형 봇]
@Vault 당사의 2024년 환경부 프로젝트 실적은?
→ (Vault가 검색 후) 스레드 답변: "2024년 환경부 프로젝트 2건 낙찰, 총 예산 OOO억원..."

[일일 다이제스트]
"[09:00] 오늘의 Vault 다이제스트
- G2B 신규공고: 환경부 스마트팩토리 (적격성 점수 88%)
- 경쟁사 입찰: OOO사 환경기술 프로젝트 낙찰
- 기술 동향: AI 기반 탄소관리 시스템"
```

---

## 구현 계획 (Implementation Roadmap)

### Phase 2 Timeline

| 주차 | 일정 | Task | 담당 | 산출물 |
|------|------|------|------|--------|
| **W1** | 04/20~04/26 | PLAN + DESIGN | Agent | design.md + schema.sql |
| **W1-2** | 04/20~04/30 | DO: Context + Permission + L10n | Engineer | 400줄 코드 + 15 테스트 |
| **W2** | 05/01~05/04 | DO: Teams Bot + E2E 테스트 | Engineer | 300줄 코드 + 20 테스트 |
| **W2** | 05/01~05/04 | CHECK: 통합 테스트 + 성능 검증 | QA | 35 테스트 통과 |

### 주차별 상세 계획

#### Week 1 (04/20 ~ 04/26)
**목표**: PLAN & DESIGN 완료, DO 50% 진행

1. **Day 1 (04/20)**: PLAN & DESIGN
   - 요구사항 명세서 작성 (완료: 이 문서)
   - DB 스키마 설계
   - API 사양 정의
   - 테스트 케이스 작성 (25개)
   - 산출물: design.md (1,200줄) + schema.sql

2. **Day 2-3 (04/21-22)**: Context Manager 구현
   - `VaultContextManager` 확장 (context_embedding 저장/조회)
   - `POST /api/vault/conversations/{id}/context` 엔드포인트
   - 단위 테스트 5개 + 통합 테스트 3개
   - 산출물: 80줄 코드 + 8 테스트

3. **Day 3-4 (04/22-23)**: Permission Filtering 구현
   - `vault_documents` 메타데이터 확장 (min_required_role)
   - `VaultResponseFilter` 새로운 서비스 클래스 (100줄)
   - 응답 생성 후 필터링 로직
   - 감시 로깅 (denied_reason 기록)
   - 산출물: 100줄 코드 + 6 테스트

4. **Day 5 (04/26)**: Multi-language 구현 (초기)
   - `langdetect` 통합
   - 언어 감지 + 로깅
   - 다국어 임베딩 모델 (OpenAI 3-large) 테스트
   - 산출물: 150줄 코드 + 6 테스트

**산출물 요약**:
- design.md (1,200줄)
- schema.sql (신규 테이블 5개)
- 330줄 신규 코드
- 23개 테스트 (15 unit + 8 integration)

#### Week 2 (04/27 ~ 05/04)
**목표**: DO 100% + CHECK 완료 + 배포 준비

1. **Day 6-7 (04/27-28)**: Teams Bot 구현 - 적응형 봇
   - Teams Webhook 핸들러
   - `/api/teams/bot/query` 엔드포인트
   - Thread 기반 응답 포스트
   - 산출물: 120줄 코드 + 8 테스트

2. **Day 7-8 (04/28-29)**: Teams Bot 구현 - 다이제스트 & 추천
   - APScheduler 통합 (매시 정각 실행)
   - Digest 생성 로직 (키워드 기반 요약)
   - RFP 매칭 로직 (프로젝트 추천)
   - 산출물: 180줄 코드 + 12 테스트

3. **Day 9 (05/01)**: E2E 테스트 & 성능 검증
   - 통합 E2E 테스트 15개 작성
   - 성능 벤치마크 (응답시간, 메모리)
   - 스트레스 테스트 (100명 동시 사용자)
   - 산출물: 35 통합 테스트, 성능 보고서

4. **Day 10 (05/02)**: CHECK Phase 검증
   - 모든 테스트 통과율 검증
   - 설계-구현 일치도 검증 (95% 목표)
   - 갭 분석 및 버그 수정
   - 산출물: CHECK 보고서

5. **Day 11-14 (05/03-04)**: 미세 조정 & 배포 준비
   - 버그 수정 및 성능 최적화
   - 스테이징 배포
   - 24시간 모니터링
   - 배포 문서 작성
   - 산출물: 배포 준비 완료, ACT 계획

**산출물 요약**:
- 400줄 신규 코드
- 35개 통합 테스트
- 성능 벤치마크 보고서
- 배포 가이드

---

## 성공 기준 (Success Criteria)

### Functional Acceptance Criteria

| 기능 | 수용 기준 | 검증 방법 |
|------|---------|---------|
| **Context** | 연속 3회 질문 정확도 > 85% | 테스트 케이스 (Q1→Q2→Q3 시나리오) |
| **Permission** | 역할별 필터링 100% 정확도 | 5개 역할 × 10개 문서 = 50가지 조합 검증 |
| **L10n** | 4개 언어 모두 > 80% 품질 | 각 언어 20개 쿼리 수동 검증 |
| **Teams** | 응답 시간 < 5초, 성공률 > 98% | Teams 테스트 채널에서 실시간 검증 |

### Performance Metrics

| 메트릭 | 목표 | 측정 도구 |
|--------|------|---------|
| P50 응답시간 | < 1.5초 | CloudWatch / Prometheus |
| P95 응답시간 | < 3초 | CloudWatch / Prometheus |
| 메모리 (컨텍스트) | < 150KB/대화 | Python memory_profiler |
| 저장소 증가율 | 월 500GB | DB 디스크 모니터링 |

### Quality Metrics

| 메트릭 | 목표 |
|--------|------|
| 코드 커버리지 | ≥ 85% |
| 테스트 통과율 | 100% |
| 설계 일치도 | ≥ 95% |
| 문서화 완성도 | 100% |

---

## 리스크 & 완화책 (Risk Management)

| 리스크 | 영향 | 가능성 | 완화책 |
|--------|------|--------|--------|
| **다국어 임베딩 품질 저하** | 의미 검색 정확도 하락 | 중간 | 프로토타이핑 early (week 1), 벤치마크 (text-embedding-3-small vs large) |
| **Teams API 레이트 제한** | 봇 응답 지연/실패 | 높음 | 메시지 배치 및 재시도 로직, 큐잉 시스템 |
| **대화 이력 데이터 폭증** | 저장소 비용, 쿼리 성능 저하 | 중간 | 자동 아카이빙 (90일), 컨텍스트 윈도우 제한 (8턴) |
| **권한 검증 로직 버그** | 정보 유출 또는 사용성 저하 | 낮음 | 화이트박스 테스트 (20개 케이스), 코드 리뷰 (2인 검증) |
| **Teams 다이제스트 키워드 오류** | 유관 정보 누락 또는 스팸 | 중간 | 관리자 UI (키워드 수정 가능), 초기 수동 큐레이션 |

---

## 기술 스택 & 의존성

### 신규 라이브러리
```
langdetect>=1.0.9          # 언어 감지
python-dateutil>=2.8       # 시간대 처리 (Teams 타임존)
pytz>=2024.1               # 타임존 (다이제스트 스케줄)
```

### 기존 활용 (확장)
- PostgreSQL (vault_messages, vault_documents 확장)
- OpenAI Embeddings (text-embedding-3-large로 업그레이드)
- Claude API (context injection 프롬프트 튜닝)
- Teams Webhook (기존 + 새로운 메시지 형식)
- APScheduler (정기 다이제스트)

---

## 예상 결과물

### 코드 (총 ~700줄)
- Context Manager 확장: 80줄
- Permission Filter Service: 100줄
- Multi-language Handler: 150줄
- Teams Bot Service: 300줄
- API Endpoints: 70줄

### 테스트 (총 ~50개)
- Unit Tests: 15개
- Integration Tests: 20개
- E2E Tests: 15개

### 문서
- Phase 2 Design Document: 1,200줄
- 배포 가이드: 200줄
- API 문서: 300줄

---

## 예산 & 리소스

| 항목 | 비용 | 비고 |
|------|------|------|
| **엔지니어 인력** | 240시간 (3명 × 2주) | 개발 + 테스트 |
| **QA 인력** | 40시간 (1명) | 통합 테스트 + 성능 검증 |
| **클라우드 인프라** | +$200/월 | 저장소 증가 (500GB/월) + 벡터 검색 |
| **Teams API** | 무료 | Webhook 사용 (무료) |
| **OpenAI API** | +$500/월 | text-embedding-3-large (다국어) |
| **총예산** | ~$13,500 | 2주 개발 + 운영비 3개월 |

---

## 다음 단계 (Next Steps)

1. **지금 (2026-04-20)**: 이 PLAN 문서 승인
2. **내일 (2026-04-21)**: design.md 작성 시작 (parallel)
3. **04/22**: 스키마 검증 및 마이그레이션 준비
4. **04/23**: 개발 환경 셋업 (langdetect, Teams sandbox)
5. **04/27**: Week 2 DO Phase 시작

---

## 승인 & 추적

| 역할 | 이름 | 서명 | 날짜 |
|------|------|------|------|
| PM | (담당자) | [ ] | 2026-04-20 |
| 기술리드 | (엔지니어) | [ ] | 2026-04-20 |
| 운영 | (DevOps) | [ ] | 2026-04-20 |

---

**Document Version**: 2.0  
**Last Updated**: 2026-04-20 20:00 KST  
**Next Review**: 2026-04-27 (DO Phase 점검)
