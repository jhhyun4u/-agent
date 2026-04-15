# Knowledge Base v2.0 — Phase 0 Validation & Cold Start Planning

**Date:** 2026-04-14  
**Status:** Ready for User Confirmation  

---

## 1. Design Validation Checklist

Review the 7-category KB design to confirm alignment with business needs:

### Category 1: 인력 자산 (People Asset Database)
- [ ] HR has current employee database with CVs, certs, experience
- [ ] Can map employee expertise to RFP requirements
- [ ] Quarterly update cycle is feasible

### Category 2: 수행실적 자산 (Project Portfolio)
- [ ] 30+ past projects (3-5 years) available for import
- [ ] Project records include: client, contract value, duration, team, outcomes
- [ ] Can categorize by client, field, price range

### Category 3: 제안서 & 콘텐츠 라이브러리 (Proposal Templates)
- [ ] 5-10 well-written past proposals can serve as templates
- [ ] Can extract by field type (medical, defense, IT, etc.)
- [ ] PPT templates and storyboards available

### Category 4: Q&A 아카이브 (Q&A Archive)
- [ ] Willing to record Q&A after each bid presentation
- [ ] Can classify by: technical, pricing, schedule, org/team, client-specific
- [ ] Success/failure tracking per Q&A useful

### Category 5: 회사소개 & 브랜딩 (Company Profile)
- [ ] Current company profile document exists
- [ ] Org chart and personnel info current
- [ ] Certifications and awards list maintained

### Category 6: 가이드라인 & 정책 (Guidelines)
- [ ] Internal proposal writing guide exists
- [ ] References to: 예타지침, 예산편성지침, 성과관리지침
- [ ] Public procurement regulations (나라장터, 조달청) checklist needed

### Category 7: 성과분석 대시보드 (Performance Analytics)
- [ ] Bid results (win/loss) are being tracked
- [ ] Evaluation scores available for analysis
- [ ] Can track: team performance, client preferences, positioning results

---

## 2. Phase 0 Scope: Cold Start Data Collection

### 2.1 Data Inventory & Collection Timeline

| Category | Data Type | Volume | Source | Owner | Timeline |
|----------|-----------|--------|--------|-------|----------|
| 1 | 경력기술서 | 50-70 people | HR system | HR | Week 1 |
| 2 | 수행실적 | 30-50 projects | Project files | PM | Week 1-2 |
| 3 | 제안서 샘플 | 5-10 docs | Archive | Proposals lead | Week 1-2 |
| 4 | Q&A | 20-30 items | Team notes | Proposal team | Week 2-3 |
| 5 | 회사정보 | 1-2 docs | Marketing | Marketing | Week 1 |
| 6 | 가이드라인 | 6-8 docs | Various | Compliance/PM | Week 2 |
| 7 | 입찰결과 | 50-100 records | Project DB | Finance/PM | Week 1 |

**Total: 3 weeks (overlapped)**

### 2.2 Detailed Phase 0 Tasks

#### Week 1: Foundation Data (People, Projects, Company)

**Task 1.1: HR Data Export**
- [ ] Request employee database export (name, title, education, certs, skills)
- [ ] Format: CSV or Excel with columns: 이름 | 직급 | 전공 | 자격증 | 경력연수 | 주요경력
- [ ] Data quality check: no duplicates, names standardized
- [ ] Estimated volume: 50-70 people

**Task 1.2: Project Portfolio Extract**
- [ ] Compile 30-50 past projects from project management system
- [ ] Format: 프로젝트명 | 발주처 | 계약금액 | 기간 | 담당팀 | 주요성과 | 수행일자
- [ ] Filter: Projects completed in last 3-5 years
- [ ] Categorize by: field (IT, medical, defense, etc.), client type, price range
- [ ] Estimated volume: 30-50 rows

**Task 1.3: Company Profile**
- [ ] Extract current company profile document from Marketing
- [ ] Get latest org chart
- [ ] List certifications, awards, media coverage (if any)
- [ ] Estimated volume: 1-2 documents

**Task 1.4: Bid Results Historical Data**
- [ ] Pull bid results from Finance/Project database
- [ ] Format: 날짜 | 입찰공고 | RFP명 | 계약금액 | 낙찰여부 | 기술점수 | 가격점수
- [ ] Include: 50-100 past bids (3-5 years)
- [ ] Estimated volume: 50-100 rows

---

#### Week 2: Content & Knowledge (Templates, Guidelines)

**Task 2.1: Proposal Template Selection**
- [ ] Audit past proposals from archive
- [ ] Identify 5-10 **best examples** (high evaluation score, clear structure)
- [ ] Score each by: clarity, completeness, visual design, evaluation results
- [ ] Extract 2-3 as "model templates" for each field type
- [ ] Organize: 제목 | 유형 | 난이도 | 페이지수 | 평가점수 | 템플릿/예시구분

**Task 2.2: Guideline Documents Compilation**
- [ ] Collect existing internal proposal writing guidelines
- [ ] Download reference materials:
  - 예비타당성조사지침 (PIMAC)
  - 예산편성지침 (MOE)
  - 성과관리지침 (MOE)
- [ ] Compile 나라장터 / 조달청 submission rules
- [ ] Create Shipley Color Team Review framework (if not exists)
- [ ] Organize: 항목 | 내용 | 출처 | 적용범위

**Task 2.3: Q&A Archive Initial Population**
- [ ] Request Q&A notes from proposal team for recent bids
- [ ] Collect from: 최근 3-5년 발표/평가 기록
- [ ] Categorize: 기술 | 가격 | 일정 | 조직/인력 | 발주처별
- [ ] Record: 분류 | 발주처 | 프로젝트명 | 질문 | 우리의답변 | 낙찰여부
- [ ] Estimated volume: 20-30 Q&A pairs

---

#### Week 3: Data Validation & Import Preparation

**Task 3.1: Data Quality Audit**
- [ ] Validate all data for: completeness, accuracy, consistency
- [ ] Check for duplicates, missing fields
- [ ] Standardize formats (dates, names, categories)
- [ ] Owner sign-off on each category

**Task 3.2: Import Planning**
- [ ] Define data schema for each KB category
- [ ] Decide: DB tables vs. vector store vs. document storage
- [ ] Plan metadata tagging (field type, difficulty, currency date)
- [ ] Create import scripts or manual upload workflow

**Task 3.3: Baseline Metrics Setup**
- [ ] Set up time tracking for proposal writing (before KB)
- [ ] Create survey template for "information search time" baseline
- [ ] Record current proposal turnaround: RFP → submission (days)
- [ ] Baseline quality score (from recent eval feedback)

---

## 3. Success Criteria Validation

**Before proceeding to Phase 1, confirm these baselines:**

| Metric | Baseline | Goal | Measurement |
|--------|----------|------|-------------|
| SC-1 제안 작성 시간 | ? days | 30% ↓ | Project timeline tracking |
| SC-2 정보 검색 시간 | ? hrs | 60% ↓ | Team survey (info search hrs/proposal) |
| SC-3 제안 품질 점수 | ? points | +3pts | Self-diagnosis score + eval feedback |
| SC-4 낙찰률 | ? % | +5%p | Bid results count |
| SC-5 정보 최신성 | ? | 100% Q4 | Update audit trail |
| SC-6 채택률 | ? % | 60%+ | Usage survey (60% of proposal team using KB regularly) |

---

## 4. Governance & Ownership Assignment

| Category | Owner | Update Cycle | Trigger | Responsibility |
|----------|-------|--------------|---------|-----------------|
| 1 인력DB | HR | Quarterly | 신입/퇴직/스킬 변경 | HR + self-report |
| 2 수행실적 | PM | Post-project + Q | 프로젝트 종료 시 | PM Team |
| 3 제안서 | Proposals lead | Post-bid | 수주/낙선 후 | Senior proposal writer |
| 4 Q&A | Proposals team | Post-presentation | 평가 완료 후 | Presentation team |
| 5 회사정보 | Marketing | Monthly | 정책/인증 변경 | Marketing + HR |
| 6 가이드라인 | Compliance | Semi-annual + event | 정책 개정 | Compliance officer |
| 7 성과분석 | Finance/PM | Post-result | 낙찰 결과 확정 | Finance/PM |

---

## 5. Implementation Roadmap (Phases 1-4)

### Phase 1: System Build (2-3 weeks)
- DB schema setup (Supabase tables for 7 categories)
- Vector embeddings for semantic search
- Basic UI for KB search and recommendations

### Phase 2: Recommendation Engine (2 weeks)
- RFP → Category matching (AI-driven)
- Context-based recommendations during proposal writing
- Integration with proposal editor

### Phase 3: Adoption & Training (1-2 weeks)
- User training for proposal team
- UAT (User Acceptance Testing)
- Target: 50% adoption in first month

### Phase 4: Optimization & Learning (ongoing)
- Monitor usage metrics
- Gather feedback
- Iterate on recommendations
- Target: 70%+ adoption by month 3

**Total Timeline: 2-3 months to full deployment**

---

## 6. User Approval Required

Please confirm:

- [ ] All 7 categories align with your needs
- [ ] Cold start data can be collected in 3 weeks
- [ ] Ownership assignments are realistic
- [ ] Phase 0 scope is complete
- [ ] Ready to proceed with Phase 1 system design?

**Next Step:** Once approved, we move to Phase 1 (System Build) — database schema, data import, and basic search UI.
