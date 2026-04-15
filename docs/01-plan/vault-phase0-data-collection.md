# Vault Phase 0 — 데이터 수집 계획서

**프로젝트**: TENOPA 자료저장소 (Vault) 통합
**기간**: 3-4주 (Phase 0)
**목표**: 8개 섹션의 초기 데이터 로드 + AI Chat 정확성 검증

---

## 1. Vault 아키텍처 개요

### 1.1 8개 섹션 및 데이터 소스

| # | 섹션 | 설명 | 주요 파일 유형 | 데이터 소스 | 보관 정책 |
|---|---|---|---|---|---|
| 1 | **종료프로젝트** | 마스터파일(메타데이터), 제안서, PPT, 최종보고서 | DOCX, PPTX, PDF, MD | proposals 테이블 | 영구 |
| 2 | **회사내부자료** | 회사소개서, 조직도, 인력정보(경력기술서), 재무재표, 인증자료 | DOCX, PDF, XLS, MD | intranet_migration, team_members | 영구 |
| 3 | **실적증명서** | 마스터파일(수행과제 목록), 실적증명서, 계약서 원본/사본 | DOCX, PDF, HWP | completed_projects, contracts | 영구 |
| 4 | **정부지침/제출서류** | 인건비 단가, 예산편성지침, 출장비 규정, 보안각서, 서식 | DOCX, XLS, PDF | government_guidelines, form_templates | 영구 |
| 5 | **경쟁사 정보** | 유사과제 수행기관 분석, 경쟁력 분석 | MD, PDF | completed_projects (분석) | 영구 |
| 6 | **성공사례 & 시사점** | 발표자료, Q&A, 성공사례 학습자료 | PPTX, MD, PDF | project_archive, lessons | 영구 |
| 7 | **발주처 정보** | 고객사 관계DB, 담당자, 성공/실패 경험 | MD, XLSX | clients_db (신규 테이블) | 영구 |
| 8 | **리서치 자료** | 기술 동향, 산업 보고서, 특허/논문 | PDF, MD | research_archive | 3개월 TTL |

### 1.2 핵심 메타데이터 필드

**모든 Vault 자료에 포함**:
```
- id: 자료 고유ID
- section: 섹션명
- title: 제목
- description: 설명
- tags: 태그 (검색용)
- source_proposal_id: 출처 제안 프로젝트 (있으면)
- source_completed_project_id: 출처 수행 프로젝트 (있으면)
- owner_id: 소유자
- team_id: 팀
- created_at: 생성일
- updated_at: 수정일
- retention_policy: 보관 정책 (영구 / TTL)
- ttl_expires_at: 만료일 (리서치 자료만)
- file_path: 스토리지 경로
- file_format: 파일 형식
- is_searchable: 검색 가능 여부
```

---

## 2. 섹션별 데이터 수집 상세 계획

### 2.1 섹션 1: 종료프로젝트

**데이터 소스**: `proposals` 테이블 (status = "completed" or "closed")

**수집 항목**:
- 기본정보: id, title, client_name, deadline
- 결과: status, win_result, bid_amount, budget
- 팀/인력: team_name, participants[], owner_name
- 성과분석: elapsed_seconds, total_token_cost, lessons
- 저장파일: storage_path_docx, storage_path_pptx, storage_path_hwpx

**마스터파일 생성**:
```markdown
# [프로젝트명]

## 기본정보
- 발주처: {client_name}
- 공고번호: {bid_no}
- 종료일: {deadline}

## 결과
- 수주결과: {win_result}
- 낙찰가: {bid_amount}
- 예산: {budget}
- 낙찰율: {bid_amount/budget*100}%

## 참여
- PM: {project_manager}
- PL: {project_leader}
- 팀: {team_name}
- 참여인력: {participants}

## 성과
- 작업시간: {elapsed_seconds}
- 토큰비용: ${total_token_cost}
- 주요성과: {lessons_summary}
```

**파일 저장 위치**: `vault/종료프로젝트/{proposal_id}/`

---

### 2.2 섹션 2: 회사내부자료

**데이터 소스**: 
- 인트라넷 마이그레이션 데이터
- `team_members` 테이블
- `company_assets` 테이블

**수집 항목**:

#### 2.2.1 회사소개서 & 조직도
- 최신 회사소개서 (DOCX)
- 조직도 (PDF)
- 주요 부서 소개

#### 2.2.2 인력정보 (경력기술서)
**구조**:
```
인력정보 인덱스
├─ 이름: {name}
├─ 소속팀: {team}
├─ 소속컨설턴트: {consultant}
├─ 주요이력: {summary}
└─ 상세이력 (MD 파일)
```

**경력기술서 MD 파일** (개인별):
```markdown
# {이름} 경력기술서

## 기본정보
- 소속: {team}
- 직급: {position}
- 경력: {experience_years}년

## 주요경력
1. {프로젝트A명} (2023.01-03, {역할})
   - 수행내용: {description}
   - 담당분야: {domain}
   
2. {프로젝트B명} (2023.04-06, {역할})
   ...

## 주요역량
- {skill1}
- {skill2}
```

**통합생성 기능**:
- 실적증명서 섹션 > 인력 클릭 > "통합생성" 버튼
- 해당 인력의 모든 참여 프로젝트 추출
- 경력기술서 자동 생성 (MD → DOCX 변환 가능)

#### 2.2.3 재무재표 & 인증자료
- 최신 재무제표 (XLS)
- ISO 인증서 (PDF)
- 기술 인증서 (PDF)

---

### 2.3 섹션 3: 실적증명서

**데이터 소스**: 
- `completed_projects` 테이블 (신규 필요)
- 기존 수행과제 기록
- 계약서 아카이브

**수집 항목**:

#### 3.1 마스터파일 (수행과제 목록)
```markdown
# TENOPA 수행실적 목록 (최근 3년)

| 연도 | 과제명 | 발주처 | 계약금액 | 계약기간 | 수행팀 | 참여인력 |
|------|--------|--------|---------|---------|--------|---------|
| 2024 | {과제명} | {발주처} | {금액} | {시작}-{종료} | {팀} | {인력} |
| 2023 | ... | ... | ... | ... | ... | ... |
```

#### 3.2 실적증명서 파일
- 발주기관 발행 증명서 (PDF)
- 계약서 원본 (HWP/PDF)
- 사본 (스캔본)

**저장 구조**: `vault/실적증명서/{completed_project_id}/`

---

### 2.4 섹션 4: 정부지침/제출서류

**데이터 소스**: 
- 기존 정부지침 문서
- 공공기관 표준 지침
- 사내 정책 & 서식

**수집 항목**:

#### 4.1 인건비 단가
```
파일: ingunbi-dangka-{year}.xlsx
내용:
- 연도별 인건비 기준 (정부 공시가)
- 급여 등급별 (1급-10급)
- 직급별 (연구원, 수석, 책임)
- 각 분야별 계수
```

#### 4.2 예산편성지침
```
파일: budget-guideline-{year}.docx
내용:
- 예산 구성 방법
- 항목별 상한액
- 증빙서류 요건
```

#### 4.3 출장비 규정
```
파일: travel-regulation.docx
내용:
- 숙박료 기준
- 식사료 기준
- 교통비 기준
```

#### 4.4 제출서류 서식
```
파일: template-{종류}-{년도}.docx
예:
- template-proposal-2024.docx
- template-receipt-2024.hwp
- template-security-agreement.docx
```

---

### 2.5 섹션 5: 경쟁사 정보

**데이터 소스**: 완료된 프로젝트 분석

**수집 항목**:

#### 5.1 유사과제 수행기관 목록
```markdown
# AI 솔루션 분야 유사과제 수행기관

## 최근 3년 수행 기관
1. {기관명A} (프로젝트 3건)
   - 2024: {프로젝트명}
   - 2023: {프로젝트명}
   - 2022: {프로젝트명}

2. {기관명B} (프로젝트 2건)
   ...
```

#### 5.2 경쟁력 분석
```markdown
# 경쟁사 비교분석

| 기관 | 최근3년경험 | 핵심인력 | 기술우위 | 가격경쟁력 |
|------|----------|---------|---------|-----------|
| {경쟁사} | ... | ... | ... | ... |
```

---

### 2.6 섹션 6: 성공사례 & 시사점

**데이터 소스**: 
- 완료된 프로젝트 (win_result = "won")
- 발표자료 아카이브
- 프로젝트 교훈

**수집 항목**:

#### 6.1 성공사례 정리
```markdown
# 클라우드 마이그레이션 프로젝트 성공사례

## 프로젝트 개요
- 발주처: {기관명}
- 기간: {기간}
- 규모: {규모}
- 결과: 수주

## 성공요인
1. {요인1}
2. {요인2}
3. {요인3}

## 주요 성과
- {성과1}
- {성과2}

## 시사점
- {배운점1}
- {배운점2}
```

#### 6.2 발표자료 & Q&A
- 발주처 발표 PPT (수주 사례)
- 질의응답 기록
- 프레젠테이션 전략 (성공 요인)

---

### 2.7 섹션 7: 발주처 정보

**데이터 소스**: 신규 테이블 필요 (`clients_db`)

**수집 항목**:

#### 7.1 발주처 기본정보
```markdown
# {발주기관명}

## 기본정보
- 기관코드: {code}
- 소속: {parent_organization}
- 담당자: {contact_person}
- 연락처: {phone} / {email}

## TENOPA 거래이력
- 수주: {수주건수}건, {총금액}원
- 낙선: {낙선건수}건
- 성공률: {success_rate}%

## 최근거래
- 2024-01: {프로젝트} (수주)
- 2023-09: {프로젝트} (낙선)

## 관계상태
- 관계: {신규/기존}
- 담당자 변경: {변경이력}
```

#### 7.2 발주처 관계 DB
- CSV/XLSX: 모든 발주처 목록
- 관계 상태 (신규/기존)
- 성공 경험 여부
- 담당자 정보

---

### 2.8 섹션 8: 리서치 자료

**데이터 소스**: 진행 중인 제안 프로젝트의 리서치 산출물

**수집 항목**:

#### 8.1 기술/산업 동향
- 최근 기술 보고서 (PDF)
- 산업 분석 자료 (MD)
- 특허/논문 요약 (MD)

#### 8.2 프로젝트별 리서치
```markdown
# {프로젝트명} 리서치 자료

## 기술 동향
- {기술A}: {요약}
- {기술B}: {요약}

## 경쟁 상황
- {경쟁사A}: {분석}
- {경쟁사B}: {분석}

## 시장 규모
- TAM: ${규모}
- 성장률: {%}
```

**보관 정책**:
- win_result = "won" → 영구 보관
- win_result = "lost" → created_at + 3개월 후 자동 삭제
- 자동 삭제: DB 트리거 또는 Cron Job

---

## 3. Phase 0 타임라인 (3주)

### Week 1: 인트라넷 데이터 마이그레이션 & 인력 정보

**목표**: 섹션 2 (회사내부자료), 섹션 3 (실적증명서) 기초 데이터 준비

**Task**:
1. **T1-1** (Day 1-2): 인트라넷에서 조직도, 회사소개서, 재무제표 추출
2. **T1-2** (Day 2-3): 기존 수행과제 목록 (3년) Supabase 마이그레이션
   - 테이블: `completed_projects` (project_id, name, client, contract_amount, start_date, end_date, team_id, participants)
3. **T1-3** (Day 3-4): TENOPA 전체 인력 목록 추출 (team, position, experience)
4. **T1-4** (Day 4-5): 개인별 경력기술서 MD 파일 생성 (템플릿 기반)
   - 각 인력별: `{name}-career.md`
   - 저장: `vault/회사내부자료/인력정보/`
5. **T1-5** (Day 5): 실적증명서 (계약서, 증명서) 파일 수집 & 분류
   - 저장: `vault/실적증명서/{project_id}/`

**산출물**:
- ✅ `completed_projects` 테이블 (100+ 레코드)
- ✅ 경력기술서 MD 파일 (50+ 개인)
- ✅ 회사내부자료 초기 업로드 (조직도, 회사소개서, 인증서)

---

### Week 2: 정부지침 & 발주처 정보 수집

**목표**: 섹션 4 (정부지침), 섹션 7 (발주처 정보) 준비

**Task**:
1. **T2-1** (Day 6-7): 정부지침 문서 수집 & 정리
   - 인건비 단가 (최근 3년)
   - 예산편성지침
   - 출장비 규정
   - 제출서류 서식 (5-10가지)
   - 저장: `vault/정부지침/`

2. **T2-2** (Day 7-8): 발주처 DB 구축 (신규 테이블)
   - 테이블: `clients_db` (client_id, name, contact, relationship, success_count, failure_count, last_transaction_date)
   - 데이터: 나라장터에서 TENOPA 입찰 이력 기반 (200+ 기관)
   - 수동 보정: 주요 발주처 담당자 정보 추가

3. **T2-3** (Day 8-9): 발주처 정보 MD 파일 생성
   - 각 발주처별: `{client_name}-info.md`
   - 저장: `vault/발주처정보/`

4. **T2-4** (Day 9-10): 경쟁사 정보 분석
   - 나라장터 자료 기반 유사과제 수행기관 분석
   - 저장: `vault/경쟁사정보/similar-projects-analysis.md`

**산출물**:
- ✅ 정부지침 문서 (10+ 파일)
- ✅ `clients_db` 테이블 (200+ 레코드)
- ✅ 경쟁사 정보 분석 문서

---

### Week 3: 종료프로젝트 & AI Chat 정확성 검증

**목표**: 섹션 1 (종료프로젝트) 마스터파일 생성, AI Chat 정확성 테스트

**Task**:
1. **T3-1** (Day 11-12): 종료프로젝트 마스터파일 자동 생성
   - proposals 테이블 (status = "completed" or "closed") 50+ 레코드
   - 마스터파일 MD 생성 스크립트 작성
   - 저장: `vault/종료프로젝트/{proposal_id}/`

2. **T3-2** (Day 12-13): 성공사례 정리 (win_result = "won")
   - 발표자료, Q&A 아카이브
   - 성공사례 요약 MD 파일
   - 저장: `vault/성공사례/`

3. **T3-3** (Day 13-14): 리서치 자료 통합 & TTL 설정
   - 기존 리서치 자료 수집 (분야별)
   - 각 자료에 source_proposal_id, ttl_expires_at 메타데이터 추가
   - 저장: `vault/리서치자료/`

4. **T3-4** (Day 14-15): **AI Chat 정확성 검증**
   
   **테스트 케이스**:
   ```
   Test 1: 프로젝트 검색 (정확성)
   Q: "최근 5년간 AI 프로젝트 리스트"
   검증: proposals 테이블 정확 쿼리 결과 vs AI Chat 응답 일치율 100%
   
   Test 2: 다중 섹션 검색
   Q1: "IoT 관련 과제가 있어?"
   Q2: "인건비 단가는?"
   검증: 컨텍스트 유지 + 정부지침 섹션 정확 데이터
   
   Test 3: 할루시네이션 방지
   Q: "존재하지 않는 프로젝트에 대해 알려줄래?"
   검증: AI Chat이 "정보가 없습니다" 응답 (거짓 정보 생성 X)
   
   Test 4: 인건비 정확도
   Q: "2024년 연구원 인건비?"
   검증: 정부 공시 기준과 100% 일치
   ```

   **검증 기준**:
   - 정확성: 90%+ (데이터 기반)
   - 할루시네이션: 0%
   - 응답시간: < 3초
   - 문맥 유지: 동일 대화에서 섹션 전환 가능

5. **T3-5** (Day 15): Vault Phase 0 완료 검증 & 문서화
   - 각 섹션 데이터 로드 확인
   - 검색 인덱싱 생성
   - 사용자 가이드 작성

**산출물**:
- ✅ 종료프로젝트 마스터파일 (50+ 파일)
- ✅ 성공사례 정리 (10+ 사례)
- ✅ 리서치 자료 통합 (100+ 문서)
- ✅ AI Chat 정확성 검증 리포트

---

## 4. 데이터 마이그레이션 스크립트 (필요)

### 4.1 Supabase 신규 테이블

```sql
-- completed_projects 테이블
CREATE TABLE completed_projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR NOT NULL,
  client_name VARCHAR,
  contract_amount NUMERIC,
  start_date DATE,
  end_date DATE,
  team_id UUID REFERENCES teams(id),
  status VARCHAR,  -- completed, executing, pending
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- clients_db 테이블
CREATE TABLE clients_db (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR NOT NULL UNIQUE,
  client_code VARCHAR,
  parent_organization VARCHAR,
  contact_person VARCHAR,
  phone VARCHAR,
  email VARCHAR,
  relationship VARCHAR,  -- new, existing
  success_count INT DEFAULT 0,
  failure_count INT DEFAULT 0,
  last_transaction_date DATE,
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- vault_metadata 테이블 (모든 Vault 자료)
CREATE TABLE vault_metadata (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  section VARCHAR NOT NULL,  -- 8개 섹션명
  title VARCHAR NOT NULL,
  description TEXT,
  tags VARCHAR[],
  source_proposal_id UUID REFERENCES proposals(id),
  source_completed_project_id UUID REFERENCES completed_projects(id),
  owner_id UUID REFERENCES users(id),
  team_id UUID REFERENCES teams(id),
  file_path VARCHAR,
  file_format VARCHAR,
  is_searchable BOOLEAN DEFAULT true,
  retention_policy VARCHAR,  -- permanent, ttl
  ttl_expires_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  INDEX (section, created_at)
);

-- research_materials 테이블 (리서치 자료 TTL 관리)
CREATE TABLE research_materials (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title VARCHAR NOT NULL,
  content_path VARCHAR,
  proposal_id UUID REFERENCES proposals(id),
  created_at TIMESTAMP DEFAULT NOW(),
  ttl_expires_at TIMESTAMP,
  auto_delete BOOLEAN DEFAULT true
);
```

### 4.2 자동 삭제 트리거 (리서치 자료)

```sql
-- 3개월마다 만료된 리서치 자료 자동 삭제
CREATE OR REPLACE FUNCTION delete_expired_research()
RETURNS void AS $$
BEGIN
  DELETE FROM research_materials
  WHERE auto_delete = true 
  AND ttl_expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- 매월 1일 실행 (또는 Cron Job)
```

---

## 5. 검증 기준

### 5.1 데이터 품질

| 섹션 | 검증 항목 | 기준 |
|------|----------|------|
| 종료프로젝트 | 마스터파일 생성율 | 90%+ |
| 회사내부자료 | 경력기술서 완성도 | 모든 활동 인력 기록 |
| 실적증명서 | 파일 보존율 | 최근 3년 100% |
| 정부지침 | 최신 기준 반영 | 2024년 기준 적용 |
| 경쟁사 정보 | 데이터 정확도 | 나라장터 기반 검증 |
| 성공사례 | 문서화 완성도 | 10+ 사례 |
| 발주처 정보 | DB 커버율 | 200+ 기관 |
| 리서치 자료 | 구분 정확도 | won/lost 구분 100% |

### 5.2 AI Chat 정확성

| 테스트 | 기준 | 검증방법 |
|-------|------|---------|
| 프로젝트 검색 | 100% 정확 | DB 쿼리 결과 vs AI 응답 비교 |
| 다중섹션 검색 | 맥락 유지 | 동일 대화에서 섹션 전환 테스트 |
| 할루시네이션 방지 | 0% | 거짓 정보 생성 시도 테스트 |
| 응답시간 | < 3초 | 평균 응답시간 측정 |
| 인건비 정확도 | 100% 일치 | 정부 공시 기준과 비교 |

---

## 6. 위험요소 & 대응방안

| 위험 | 영향 | 대응방안 |
|-----|------|--------|
| **인트라넷 데이터 불완전** | 섹션 2, 3 지연 | 수동 보정 + 분기별 업데이트 주기 수립 |
| **정부지침 최신화 누락** | 섹션 4 신뢰도 저하 | 월간 정부 공시 모니터링 |
| **AI Chat 할루시네이션** | 잘못된 정보 제공 | SQL 직접 쿼리 + 벡터 검색 조합 |
| **리서치 자료 TTL 관리 실패** | 만료 자료 보존 | Cron Job 자동화 + 수동 검증 주간 |
| **발주처 정보 정확도** | 영업 기회 상실 | 나라장터 기반 자동 동기화 |

---

## 7. Phase 1 연계 (이후)

Phase 0 완료 후:
- **Phase 1**: Vault UI 구현 (메뉴, 검색, 업로드)
- **Phase 2**: AI Chat 심화 (다국어 지원, 고급 분석)
- **Phase 3**: 자동화 확대 (정기 업데이트, 스케줄링)

---

## 8. 승인 & 사인오프

| 역할 | 승인 | 날짜 |
|-----|------|------|
| PM (제품) | ☐ | ____ |
| 데이터 담당 | ☐ | ____ |
| IT (인프라) | ☐ | ____ |
| CTO (기술) | ☐ | ____ |

