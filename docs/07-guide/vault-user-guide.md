# Vault User Guide
**Document Status:** Draft v1.0  
**Last Updated:** 2026-04-14  
**Target Audience:** TENOPA Team (Consultants, Researchers, PMs)  
**Target Phase:** Phase 1 (2026-05-01 launch)

---

## Table of Contents
1. [5-Minute Quick Start](#5-minute-quick-start)
2. [What is Vault?](#what-is-vault)
3. [Section-Specific Guides](#section-specific-guides)
4. [Using AI Chat](#using-ai-chat)
5. [Advanced Features](#advanced-features)
6. [FAQ & Troubleshooting](#faq--troubleshooting)
7. [Best Practices](#best-practices)

---

## 5-Minute Quick Start

### Step 1: Access Vault
1. Login to TENOPA proposer
2. Click **VAULT** in left sidebar
3. You'll see 8 sections to explore

### Step 2: Search for Information
**Example Scenario:** You're proposing an AI solution and need to reference similar past projects.

1. Click **Success Cases** section
2. Type in AI Chat: `"우리가 수행한 AI 프로젝트 성공 사례"`
3. Read responses with references to past wins
4. Click linked projects to see full details

### Step 3: Download What You Need
1. Find the information you need
2. Click **Download** button (or **Export** for multiple items)
3. Opens as PDF or Word for proposal writing

**That's it!** You can now research, write, and propose faster.

---

## What is Vault?

### The Problem We're Solving

Before VAULT:
- 📁 **Scattered Information** — Files in Email, SharePoint, Server, Drive, Slack
- ❌ **Time Wasted** — 30 minutes searching for "that one proposal from 2024"
- 🤷 **Forgotten Knowledge** — "Did we do an AI project? I can't remember..."
- 📝 **Manual Writing** — Copy-pasting from 5 different documents

### What VAULT Offers

✅ **One Place to Find Everything**
- 8 organized sections (completed projects, clients, guidelines, success cases, etc.)
- Full-text search + AI Chat
- Real-time auto-updates from proposals system

✅ **Smart AI Chat Assistant**
- Ask questions naturally in Korean
- Answers backed by actual TENOPA data (no hallucinations)
- Confidence ratings so you know when to double-check

✅ **Automatic Updates**
- When you close a proposal as "won," it automatically becomes a success case
- New clients are automatically added to Clients DB
- Government guidelines refresh monthly

✅ **Better Proposals**
- Reference real past project numbers (budget, duration, team size)
- Include proven success stories
- Respond to competitor threats with concrete data
- Generate personnel CVs instantly

### How It Works (Simple Version)

```
You: "우리 AI 팀의 최근 5년 프로젝트는?"
     ↓
VAULT AI Chat (Claude Sonnet):
     ├→ Searches SQL database for actual project records
     ├→ Searches vector embeddings for context matches
     └→ Synthesizes into readable answer with sources
     ↓
You: "이 프로젝트의 팀원은?" → Assistant provides data with names
You: "낙찰율은?" → Assistant provides actual success statistics
You: Download → Create proposal with real data
```

---

## Section-Specific Guides

### 1. Completed Projects
**What's in it:** All closed proposals (won/lost) from 2019-present  
**Who updates it:** Automatic (when proposal closes)  
**Use case:** Reference past project numbers, budgets, teams, timelines

#### How to Use: "Our Budget Baseline"

**Scenario:** You're writing a proposal for an AI project and need to estimate budget.

1. **Open Completed Projects** section
2. **Search:** `"AI 프로젝트 예산" or click filter: Category = "AI"`
3. **AI Chat question:** `"최근 AI 프로젝트 3개 예산과 기간은?"`

**Expected Response:**
```
최근 AI 프로젝트 3개:
1. AI 챗봇 구축 (2025) — 예산: 250만원, 기간: 3개월, 팀: 3명
2. 문서 자동화 (2024) — 예산: 180만원, 기간: 2개월, 팀: 2명  
3. 데이터 분석 (2024) — 예산: 320만원, 기간: 4개월, 팀: 4명

평균 예산: 250만원, 평균 기간: 3개월
```

4. **Use this data in proposal:** "유사 과제 예산: 250만원, 기간: 3개월"

#### How to Use: "Did We Do This Before?"

**Scenario:** Client asks, "Have you ever done a project like X?"

1. **Search:** `"[Client Name]"` or `"[Technology Type]"`
2. **Grid View:** See all past projects with that client/tech
3. **Click project:** See full proposal, team, timeline, results
4. **Tell client:** "Yes, we did similar work in [Project Name] (2024)"

#### How to Export

1. Select projects you want
2. Click **Export to PDF/Word**
3. Includes: Project name, budget, team, timeline, results
4. Use in "유사 과제 실적" (Similar Project Track Record) section of proposal

---

### 2. Company Internal
**What's in it:** Company overview, org structure, team bios, financial summaries  
**Who updates it:** HR, Finance, Admin team  
**Update frequency:** Weekly  
**Use case:** Standardize company description in proposals

#### How to Use: "Company Description Template"

**Scenario:** Writing proposal company description and need current company info.

1. **Open Company Internal** section
2. **Download:** "회사소개서" (Company Profile) or "조직도" (Org Chart)
3. **Copy relevant parts into proposal**
4. **AI Chat question:** `"우리 회사는 어떤 회사야?"`

**Expected Response:**
```
TENOPA는 2015년 설립된 경영기획 및 디지털혁신 컨설팅 회사입니다.
- 직원: 40명
- 주요 사업: 정부 공고 제안, 디지털 전환, AI 도입
- 강점: 낙찰률 67%, 평균 프로젝트 기간 3개월
```

**Note:** This section is read-only for consultants (only admins can update)

---

### 3. Credentials (인증 자료)
**What's in it:** Company certifications (ISO, security, quality), licenses, awards  
**Who updates it:** Compliance, Admin team  
**Update frequency:** Quarterly (when new certs obtained)  
**Use case:** Reference in proposals for credibility

#### How to Use: "Do We Have the Right Certification?"

**Scenario:** Client asks "Do you have ISO 27001?" in RFP.

1. **Open Credentials** section
2. **Search:** `"ISO 27001"` or `"정보보호"`
3. **View:** Certification name, issue date, expiration date
4. **Proposal:** Include "ISO 27001 certified (expires 2026-12-31)"

#### How to Export

1. Select needed credentials
2. Click **Export**
3. Get scans/copies suitable for proposal
4. Attach to proposal as supporting document

---

### 4. Government Guidelines (공고 정보)
**What's in it:** Government salary standards, public project rates, bidding rules  
**Who updates it:** Research team  
**Update frequency:** Monthly (on 1st)  
**Use case:** Ensure proposals comply with government standards

#### How to Use: "What's the Government Daily Rate?"

**Scenario:** Writing proposal for government project, need to calculate labor cost.

1. **Open Government Guidelines** section
2. **AI Chat question:** `"2026년 정부 급여 기준은?"`

**Expected Response:**
```
2026년 정부 급여 기준 (공고 기준):

연구진:
- 수석 연구원: 일급 180,000원
- 선임 연구원: 일급 150,000원
- 연구원: 일급 120,000원
- 보조 연구원: 일급 80,000원

특수직:
- PM: 일급 200,000원
- 품질보증: 일급 140,000원

기준 적용일: 2026-01-01
```

3. **Use in proposal:** Calculate team labor = (5명 × 120,000원/일) × 60일 = 36,000,000원

#### How to Use: "Government Bidding Rules"

1. **Search:** `"낙찰률" or "입찰 규칙"`
2. **Read:** Government project markup limits, winning bid ranges
3. **Proposal:** Ensure your bid falls within acceptable range

---

### 5. Competitors
**What's in it:** Competitive landscape, other firms' projects, market trends  
**Who updates it:** Marketing/Research team  
**Update frequency:** Monthly  
**Use case:** Differentiate TENOPA value in proposals

#### How to Use: "What Are Competitors Doing?"

**Scenario:** Writing proposal for AI consulting and want to mention TENOPA's unique value.

1. **Open Competitors** section
2. **Search:** `"AI 컨설팅"` or `"디지털혁신"`
3. **AI Chat question:** `"경쟁사는 어떤 AI 프로젝트를 했어?"`

**Expected Response:**
```
주요 경쟁사 AI 프로젝트:

1. Firm A: AI 챗봇 구축 (비용: 500만원, 3개월)
   → TENOPA 대비 2배 비용, 비슷한 기간

2. Firm B: 문서 자동화 (비용: 200만원, 2개월)
   → TENOPA과 유사 수준

3. Firm C: 데이터 분석 (비용: 700만원, 4개월)
   → 고가 프리미엄 서비스

TENOPA의 강점:
- 경쟁사 대비 20-40% 저렴
- 빠른 완료 기간 (평균 3개월)
- 높은 낙찰률 (67%)
```

4. **Proposal differentiation:** "TENOPA는 경쟁사 대비 비용 효율적이며 빠른 완료 기간을 제공합니다"

---

### 6. Success Cases (성공 사례)
**What's in it:** Past project outcomes, lessons learned, client testimonials  
**Who updates it:** Automatic (when projects close as "won")  
**Use case:** Demonstrate proven capability in proposals

#### How to Use: "Similar Success Stories"

**Scenario:** Writing proposal for client similar to past successful project.

1. **Open Success Cases** section
2. **Search:** `"[Client Type]"` e.g., `"대형 제조사"` or `"[Technology]"` e.g., `"AI"`
3. **View:** Project outcome, budget, team, client quote/feedback
4. **Copy into proposal:** "우리는 2024년 유사 프로젝트에서 성공한 경험이 있습니다."

#### How to Use: "Showcase Expertise"

**Example Query:** `"우리가 수행한 AI 프로젝트 중 가장 성공적인 것은?"`

**Expected Response:**
```
가장 성공적인 AI 프로젝트:

프로젝트명: "O사 업무자동화 AI 시스템 구축"
- 클라이언트: O사 (대형 제조사)
- 기간: 4개월 (2024-01 ~ 2024-04)
- 팀: 5명 (PM 1, 개발자 3, QA 1)
- 예산: 450만원
- 결과: ✅ 승리, 클라이언트 만족도 95/100

주요 성과:
- 업무 자동화로 월 50시간 절감
- 오류율 80% 감소
- 클라이언트 재계약 의향 90%

배운 점:
- AI 학습 데이터 전처리가 가장 중요
- 사용자 교육 필수 (완료율 +40%)
- 단계적 배포로 리스크 감소
```

5. **Include in proposal:** "2024년 유사 프로젝트 성공 경험, 클라이언트 만족도 95점 달성"

---

### 7. Clients DB
**What's in it:** All client contacts, past projects, relationship history  
**Who updates it:** Automatic (from proposals system)  
**Use case:** Reference client history when writing new proposals

#### How to Use: "Client Contact & History"

**Scenario:** Getting a new RFP from previous client. Need their contact info and project history.

1. **Open Clients DB** section
2. **Search:** `"[Client Name]"`
3. **View:** Company info, contacts, past projects, success rate with this client
4. **Email/Call:** Use contact info to clarify RFP requirements

#### How to Use: "Reference Check"

**Query:** `"[Client Name] 과의 과거 프로젝트는?"`

**Expected Response:**
```
Client Name (ABC 주식회사) 과의 프로젝트 이력:

1. "시스템 구축" (2023-06) — 예산: 280만원, 결과: ✅ 승리
2. "데이터 분석" (2024-02) — 예산: 150만원, 결과: ✅ 승리
3. "AI 도입" (2024-11) — 예산: 320만원, 결과: ✅ 승리

클라이언트와의 관계:
- 총 3개 프로젝트, 3승 (승률 100%)
- 평균 재계약 기간: 6개월
- 평균 만족도: 92/100
- 다음 문의 예상: 2026년 상반기
```

---

### 8. Research Materials (리서치 자료)
**What's in it:** Ad-hoc research uploads (market reports, case studies, articles)  
**Who uploads it:** Any team member  
**Auto-delete:** After 3 months  
**Use case:** Temporary reference for current proposals

#### How to Use: "Use Current Research"

**Scenario:** Just downloaded latest market report. Need to include insights in proposal.

1. **Open Research Materials** section
2. **Upload:** Click upload, drag-drop PDF/document
3. **Tag:** `"AI 시장", "2026년 전망"` (optional)
4. **Share:** Link accessible to all team for 3 months
5. **Auto-delete:** After 3 months, document is removed (set retention policy)

#### How to Use: "Search by Tag"

1. **Filter by tag:** `"AI시장"`, `"정부 정책"`, etc.
2. **AI Chat question:** `"2026년 AI 시장 동향은?"`
3. **Read:** Summary + citation to research document
4. **Note:** Research material automatically deleted in 3 months

---

## Using AI Chat

### What AI Chat Can Do

✅ **Answer questions about TENOPA's data:**
- "우리가 한 AI 프로젝트는?" (AI projects)
- "낙찰율이 몇 %야?" (Win rate)
- "정부 급여 기준은?" (Government salary rates)
- "이 클라이언트와의 과거는?" (Client history)

✅ **Synthesize across sections:**
- "2024년 AI 프로젝트 중 가장 성공적인 것은?" (Cross-section synthesis)
- "우리 AI팀이 가능한 최대 예산은?" (Aggregate data)

✅ **Provide confidence ratings:**
- 90% confidence: "Definitely true, from our actual data"
- 75% confidence: "Likely true, but manually verify"
- <70% confidence: "Not enough info in Vault, consult expert"

❌ **What AI Chat CANNOT do (will refuse):**
- Make up projects we didn't do
- Guess at numbers without data
- Create content not based on actual TENOPA data
- Answer questions outside Vault (general knowledge)

### How to Ask Good Questions

**Good Questions:**

❓ `"2024년 AI 프로젝트는?"` (specific year + tech)  
→ Structured, answerable, confident response

❓ `"우리의 평균 프로젝트 기간은?"` (aggregate metric)  
→ Can calculate from data

❓ `"SKC 프로젝트의 팀원은 누구?"` (specific project)  
→ Exact match in system

---

**Vague Questions (avoid):**

❓ `"프로젝트 정보 줘"` (too broad)  
→ "더 구체적으로 어떤 프로젝트?"

❓ `"우리가 뭘 잘 해?"` (too subjective)  
→ "성공한 프로젝트 3개를 보여드릴게" (reframes to data)

❓ `"경쟁사보다 우리가 나아?"` (opinion)  
→ "경쟁사 AI 예산은 X, 우리는 Y" (fact-based comparison)

---

### Reading Confidence Ratings

Each AI response includes a confidence score. Here's what they mean:

| Confidence | Meaning | Action |
|------------|---------|--------|
| **90-100%** | Sourced directly from TENOPA database | Use as-is in proposal |
| **75-89%** | Based on partial data or synthesis | Mention in proposal with "약 X" |
| **60-74%** | Multiple sources or interpretation | Verify before using |
| **<60%** | Low confidence, insufficient data | Marked as "신뢰도 낮음" — ask expert |

**Example Response:**

```
질문: "우리 AI팀의 최근 5년 프로젝트 3개는?"

응답:
1. AI 챗봇 (2025) | 신뢰도 95% ← 데이터베이스에 정확한 기록
2. 문서 분석 (2024) | 신뢰도 92%
3. 데이터 학습 (2024) | 신뢰도 88%

평균 예산: 250만원 | 신뢰도 90%
평균 기간: 3개월 | 신뢰도 93%

🔒 출처: proposals 테이블 (자동 검증됨)
```

**How to use this:**
- 95% confidence → Cite directly: "우리는 AI 챗봇 프로젝트를 2025년에 완료했습니다"
- 90% confidence → Use with qualifier: "평균적으로 약 250만원대의 예산이 필요합니다"

---

### Common AI Chat Scenarios

#### Scenario 1: Writing Company Overview

**You:** `"우리 회사 소개 한 문단으로 정리해줄래?"`

**AI Chat returns:**
```
TENOPA는 2015년 설립된 경영기획 및 AI 혁신 컨설팅 회사로, 정부 공고 대응, 디지털 전환, AI 도입 분야의 전문성을 갖추고 있습니다. 지난 10년간 40명 규모의 팀으로 67% 낙찰률을 기록하며, 평균 3개월 내 프로젝트를 완료한 실적이 있습니다.

📌 신뢰도: 95% (회사 정보 데이터베이스 기반)
```

✅ **Copy directly into proposal.** 신뢰도 95%이므로 검증 필요 없음.

---

#### Scenario 2: Estimating Project Budget

**You:** `"AI 시스템 구축 예산은 보통 얼마나 해?"`

**AI Chat returns:**
```
TENOPA의 AI 시스템 구축 프로젝트 예산 분포:

낮음 (2-3개월): 150~250만원
중간 (3-4개월): 250~400만원  
높음 (4개월+): 400만원 이상

평균: 280만원, 기간: 3개월

최근 3개 사례:
1. 챗봇 구축 - 250만원
2. 문서 자동화 - 180만원
3. 데이터 분석 - 320만원

📌 신뢰도: 92% (과거 10개 유사 프로젝트 분석)
```

✅ **Use with confidence:** "유사 과제 실적에 따르면 약 250~350만원 범위 예상"

---

#### Scenario 3: Client Reference Check

**You:** `"ABC 회사와 과거 작업한 프로젝트 있어?"`

**AI Chat returns:**
```
ABC 회사와의 프로젝트 이력:

1️⃣ "시스템 구축" (2023-06)
   - 예산: 280만원
   - 팀: PM 1명, 개발자 2명
   - 결과: ✅ 성공 (만족도 92/100)

2️⃣ "데이터 분석" (2024-02)  
   - 예산: 150만원
   - 기간: 2개월
   - 결과: ✅ 성공 (재계약 승인)

3️⃣ "AI 도입" (2024-11)
   - 예산: 320만원
   - 기간: 4개월
   - 결과: ✅ 성공 (향후 협업 의향)

관계 평가:
- 총 3개 프로젝트 3승 (100% 성공률)
- 평균 만족도: 95/100
- 재계약률: 100%

📌 신뢰도: 99% (데이터베이스 정확 일치)
```

✅ **Use for confidence:** "ABC사와는 과거 3개 프로젝트를 성공적으로 수행한 실적이 있습니다"

---

#### Scenario 4: Competitive Differentiation

**You:** `"경쟁사 대비 우리의 장점은?"`

**AI Chat returns:**
```
TENOPA vs 경쟁사 AI 프로젝트 비교:

📊 예산 효율성:
- Firm A 평균: 450만원
- Firm B 평균: 380만원
- TENOPA 평균: 280만원 ← 30% 저렴

⏱️ 완료 기간:
- 경쟁사 평균: 3.8개월
- TENOPA 평균: 2.9개월 ← 30% 빠름

🎯 성공률:
- Firm A: 78%
- Firm B: 82%
- TENOPA: 89% ← 업계 최고

💡 강점 요약:
TENOPA는 경쟁사 대비 20-30% 저렴하면서도 높은 성공률로 신뢰성을 입증합니다.

📌 신뢰도: 87% (경쟁사 데이터 부분 추정)
```

✅ **Use with qualifier:** "시장 조사에 따르면, TENOPA는 가격 대비 최고의 가치를 제공합니다"

---

## Advanced Features

### Feature 1: Batch Export (다중 문서 다운로드)

**Scenario:** Writing a proposal and need 5 past projects + client history + company info.

1. **Select Multiple Items:**
   - Click projects: ☑️ Project A, ☑️ Project B, ☑️ Project C
   - Click clients: ☑️ Client Overview
   - Click company: ☑️ Company Profile

2. **Export All at Once:**
   - Click **Export Selected (5 items)**
   - Choose format: **PDF Bundle** or **Word Documents** (separate files)

3. **Output:**
   - PDF: One bundled document with TOC, bookmarks
   - Word: 5 separate .docx files, zipped

4. **Use:** Copy sections directly into proposal.docx

---

### Feature 2: Smart Resume Generation

**Scenario:** Need to add a team member's CV to proposal but their CV is outdated.

1. **Open Credentials** or **Company Internal**
2. **Find team member:** Click "박OO (Senior Researcher)"
3. **Generate Resume:**
   ```
   프로젝트 이력을 바탕으로 이력서 자동 생성
   ├─ AI 프로젝트 3개 (2022-2025)
   ├─ 데이터 분석 프로젝트 2개
   ├─ 팀 규모: 평균 4명 (리더 경험)
   └─ 총 경력: 8년 (2017-2025)
   ```

4. **Review & Customize:**
   - Auto-generated CV appears
   - Edit: Add skills, remove outdated projects
   - Format: Professional PDF

5. **Download:** Use in proposal immediately

---

### Feature 3: Related Documents Sidebar

When viewing any document in Vault, right sidebar shows:

**"관련 자료" (Related Documents):**
- 같은 클라이언트의 다른 프로젝트
- 같은 기술의 다른 사례
- 같은 팀이 수행한 다른 프로젝트

**Example:** Viewing "AI 챗봇" project → Sidebar shows 3 other chatbot projects

Click to jump to related project instantly.

---

## FAQ & Troubleshooting

### Q: "AI Chat이 틀린 답을 줬어요"

**A:** 이것이 바로 신뢰도 점수가 있는 이유입니다.

- 신뢰도 <80%? → "신뢰도 낮음" 표시되어 있어야 합니다. PM이나 담당자에게 확인하세요.
- 신뢰도 >90%? → 데이터베이스 오류일 가능성. DevOps에 보고해주세요.
- 반복되는 오류? → 문서 업로드 담당자에게 알려주세요 (데이터 품질 이슈).

---

### Q: "내가 업로드한 문서가 검색되지 않아요"

**A:** 업로드 후 24시간 기다려주세요.

- 문서 텍스트 추출 (PDF → 텍스트): 5분
- AI 임베딩 생성 (OpenAI API): 10분
- 검색 인덱싱: 1시간
- 총 처리 시간: 1-2시간 (보통 1시간 이내)

늦으면 DevOps에 "doc ID: XXXX 검색 안 됨" 으로 보고.

---

### Q: "Research Materials가 갑자기 사라졌어요"

**A:** 맞습니다! Research Materials는 3개월 후 자동 삭제됩니다.

- 업로드: 2026-01-14
- 만료: 2026-04-14 (3개월 후)
- 중요한 자료? → 다른 섹션으로 옮기거나 로컬에 저장하세요.

---

### Q: "이 섹션 정보가 틀렸어요"

**A:** 어느 섹션인지에 따라 보고 대상이 달라집니다:

| 섹션 | 오류 보고 대상 | 응답 시간 |
|------|--------------|---------|
| Completed Projects | Project Manager | 24시간 |
| Company Internal | HR / Admin | 3일 |
| Government Guidelines | Research Team | 3일 |
| Success Cases | PM (자동 동기화) | 24시간 |
| Credentials | Compliance | 5일 |
| Clients DB | Account Manager | 24시간 |
| Competitors | Marketing | 5일 |
| Research Materials | Uploader | 1시간 |

---

### Q: "AI Chat 응답 신뢰도가 계속 낮아요"

**A:** 두 가지 원인:

1. **데이터 부족:** 질문이 너무 구체적이거나, Vault에 그 정보가 없을 수 있습니다.
   - 더 넓은 질문으로 다시 시도: `"AI 프로젝트"` 대신 `"최근 프로젝트"`
   - 다른 섹션도 확인: Completed Projects에 없으면 Success Cases 검색

2. **신뢰도 계산 방식:** 신뢰도는 데이터 일관성을 기반으로 합니다.
   - 여러 소스가 다르면? → 신뢰도 낮음 ("이 데이터 검증 필요")
   - 데이터 출처 확인? → AI가 "여기서 찾음" 링크 제공

**해결책:** PM이나 담당자에게 "X에 대한 확실한 정보 있나요?" 물어보세요.

---

### Q: "Export가 느려요 / 실패해요"

**A:** 한 번에 너무 많은 문서를 Export하려고 할 수 있습니다.

- 한 번에 최대: 20개 문서
- 20개 이상 필요? → 2회에 걸쳐 Export
- 파일이 크면? → Word 형식 대신 PDF 선택 (용량 작음)

계속 실패? → DevOps에 보고 (export queue full).

---

### Q: "팀에서 내가 Upload한 문서를 못 봐요"

**A:** 두 가지 가능성:

1. **권한 문제:**
   - Vault Admin만 업로드 가능
   - 당신이 Vault Admin 아니면? → Admin에게 요청

2. **RLS (Row-Level Security):**
   - 팀 문서는 팀원만 볼 수 있음
   - 다른 팀에서 업로드? → Admin에게 "크로스팀 접근" 요청

---

## Best Practices

### When Writing Proposals

✅ **DO:**
1. **Search first, write second**
   - 10분 Vault 검색 > 30분 수동 찾기
   
2. **Use Confidence Ratings**
   - 90%+ 신뢰도 = 직접 인용 가능
   - <80% 신뢰도 = "약 X" 로 표현하거나 확인 필수

3. **Reference Real Data**
   - "평균 250만원" (실제 과거 데이터)
   - vs "약 250-300만원" (추정치)

4. **Leverage Success Cases**
   - "유사 프로젝트 성공 실적 있습니다"
   - "과거 3년간 같은 분야 100% 성공률"

5. **Export Everything Needed at Once**
   - 프로젝트 3개 + 클라이언트 + 회사 정보 → Batch Export
   - 타이핑 시간 대폭 절감

---

### When Sharing with Clients

✅ **Recommendations:**
1. **Export as PDF** (formatting preserved, professional look)
2. **Add Vault attribution** 
   - "TENOPA 내부 데이터베이스 기반"
   - Clients는 data integrity에 신뢰감 가짐

3. **Use specific numbers**
   - "약 250만원" ✗
   - "과거 유사 프로젝트 실적 280만원" ✓

4. **Include confidence where relevant**
   - 높은 신뢰도는 안 써도 되지만
   - 추정치/합성 답변은 표시: "시장 분석 기반"

---

### When Updating Vault

✅ **Who should update what:**

| Role | Responsibility |
|------|-----------------|
| **모든 팀원** | New project links, corrections (오류 발견 시 PM에 보고) |
| **PM** | Project outcomes, team assignments, budget finalizations |
| **HR** | Company bios, org changes, team member updates |
| **Finance** | Budget actuals, final project costs |
| **Compliance** | New certifications, license renewals |
| **Research** | Government guideline updates (monthly) |
| **Marketing** | Competitor updates, success case narratives |
| **모든 팀원** | Research material uploads (temporary) |

---

### Document Retention Tips

📌 **Keep in Vault (permanent):**
- Completed projects with actual results
- Credentials & certifications
- Client contact information
- Government salary guidelines (current year)

📌 **Archive locally (RFP-specific):**
- RFP response drafts
- Internal notes, edits
- Version history

📌 **Auto-delete (3mo):**
- Research material you uploaded
- Temporary market reports
- Draft analysis

---

## Getting Help

### Support Channels

| Question Type | Contact | Response Time |
|---------------|---------|----------------|
| **Vault not working** | DevOps | 1 hour |
| **Data question** | Relevant section owner | 4 hours |
| **How do I...?** | Team lead or Slack #vault | 1 hour |
| **Bug report** | DevOps Slack #bugs | 2 hours |
| **Feature request** | PM | Within sprint |

### Quick Reference

- **Vault URL:** tenopa-proposer.vercel.app/vault
- **Support Slack:** #vault-support
- **Feedback Form:** vault feedback form (TBD)

---

## Feedback & Continuous Improvement

We're constantly improving Vault based on your feedback!

📝 **Found a bug?** → Report in Slack #vault-bugs  
💡 **Feature idea?** → Post in Slack #vault-ideas  
❓ **Have a question?** → Ask in Slack #vault-support  

Your feedback directly shapes Vault development!

---

**Last Updated:** 2026-04-14  
**Version:** 1.0 (Phase 1 Launch)  
**Next Update:** 2026-06-30 (Post Phase 1 Review)
