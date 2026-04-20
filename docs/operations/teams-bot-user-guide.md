# Teams Bot User Guide — Vault Chat Phase 2

**Version**: 1.0  
**Date**: 2026-04-20  
**Status**: Operational  

---

## 1. Overview

The Vault Teams Bot integrates three intelligent modes to enhance team collaboration:

| Mode | Use Case | Trigger | Format |
|------|----------|---------|--------|
| **Adaptive** | Real-time Q&A | @Vault mention | Inline Teams response |
| **Digest** | Daily KB summary | Scheduled (9:00 UTC) | Teams channel message |
| **Matching** | RFP recommendations | New RFP detection | Team channel message |

---

## 2. Adaptive Mode (Real-time Q&A)

### What is Adaptive Mode?

When you mention **@Vault** in Teams, the bot instantly searches your organization's knowledge base and responds with:
- Direct answers from past projects, processes, and documents
- Confidence levels and sources
- Context from conversation history (last 8 turns)

### How to Use

**Basic Query:**
```
@Vault What was our last major win in the financial sector?
```

**Expected Response (in Teams):**
```
💡 Vault AI Response

Based on your knowledge base, your most recent financial sector win was:
"Bank Digital Transformation" — ₩2.5B, Q4 2025

Sources:
📄 Completed Projects (2 documents)
```

**Multi-turn Conversation:**
```
@Vault Tell me about the team that won that project
```
→ Bot remembers previous context and answers accordingly

### Advanced Features

#### Context Awareness
- Last 8 conversation turns are automatically included
- Bot considers project type, timeline, team composition
- Detects when you're asking for clarifications

#### Language Support
- English, Korean, Chinese, Japanese auto-detected
- Bot responds in your detected language
- Can override: `@Vault [EN]` or `@Vault [KO]` prefix

#### Source Verification
- Each response shows referenced documents
- Confidence score indicates reliability
- Denied: "Some information is restricted to Lead+ roles"

### Examples

**Win Rate Query:**
```
@Vault What's our win rate this quarter?
→ Response: "Your win rate is 35% (7 wins from 20 bids)"
```

**Technical Questions:**
```
@Vault How did we approach the database migration in Project X?
→ Response: "Detailed technical approach from archived Project X..."
```

**Market Intelligence:**
```
@Vault Who are our top 3 competitors in AI solutions?
→ Response: "Based on recent bids: Company A, Company B, Company C with 45% combined market share"
```

---

## 3. Digest Mode (Daily Summary)

### What is Digest Mode?

Every day at **9:00 UTC** (configurable), the bot automatically posts a curated summary to your team channel containing:
- New RFP announcements matching your keywords
- Competitor bid activity
- Technology trends in your domain

### Configuration

**Step 1: Access Settings**
```
Teams → Vault Bot Configuration → Edit Digest Keywords
```

**Step 2: Add Keywords**

| Format | Example | Searches For |
|--------|---------|--------------|
| `G2B:KEYWORD` | `G2B:환경부` | Government bids from 나라장터 |
| `competitor:NAME` | `competitor:ACME` | Bid activity from ACME Corp |
| `tech:DOMAIN` | `tech:AI` | AI/ML technology trends |

**Example Configuration:**
```yaml
Digest Keywords:
  - G2B:환경부
  - G2B:금융
  - competitor:ACME
  - competitor:SKC
  - tech:AI
  - tech:Cloud
```

**Step 3: Set Time (Optional)**
```
Digest Time: 09:00 (default)
Digest Enabled: ✅ (toggle)
```

### Daily Digest Example

**Posted at 9:00 UTC:**
```
📊 오늘의 Vault 다이제스트 (2026-04-20)

### 🏛️ G2B 신규공고 (환경부)
- 전국 수자원 관리 AI 시스템 구축 (점수: 78%)
- 스마트팩토리 탄소관리 솔루션 (점수: 85%)
- 환경 모니터링 IoT 네트워크 (점수: 71%)

### 🎯 경쟁사 입찰 (ACME Corp)
- ACME, "인프라 IT 현대화" 프로젝트 낙찰 가능 (가능성: 88%)
- ACME, "클라우드 전환" 입찰 (규모: ₩500M 예상)

### 🔬 기술 트렌드 (AI)
- 최신 AI 문서: "Generative AI in Enterprise" (2026-04-20)
- 산업 리포트: "AI 거버넌스 프레임워크" (2026-04-15)
```

### Common Keywords

**Government (나라장터):**
- `G2B:환경부`, `G2B:행정안전부`, `G2B:과학기술정보통신부`
- `G2B:국방`, `G2B:교육`, `G2B:스마트시티`

**Competitors:**
- `competitor:삼성`, `competitor:LG`, `competitor:현대`
- `competitor:SKC`, `competitor:SK텔레콤`

**Technologies:**
- `tech:AI`, `tech:Cloud`, `tech:Blockchain`
- `tech:IoT`, `tech:5G`, `tech:Quantum`

---

## 4. Matching Mode (RFP Auto-Recommendation)

### What is Matching Mode?

When new RFP announcements are detected, the bot automatically:
1. Analyzes the RFP content
2. Finds 3-5 similar past projects
3. Posts recommendations to relevant team channels

### How It Works

**Flow:**
```
1. New RFP detected
   ↓
2. Bot embeds RFP content (vector search)
   ↓
3. Searches vault for similar completed projects
   ↓
4. Calculates relevance score (threshold: 0.75)
   ↓
5. Groups by responsible team
   ↓
6. Posts recommendation to team channel
```

### Recommendation Message

**Example:**

```
🎯 신규 RFP 자동 매칭

RFP: "국방부 통합 지휘통제 시스템"

유사 경험:
1. "육군 C4I 시스템" — Team C (낙찰 가능성 89%)
2. "국방 사이버 보안 센터" — Team C (85%)
3. "해군 함정 운영 체계" — Team D (78%)

조기 대응을 권장합니다.
```

### Configuration

| Setting | Default | Range | Purpose |
|---------|---------|-------|---------|
| **Matching Enabled** | ✅ | On/Off | Enable/disable mode |
| **Similarity Threshold** | 0.75 | 0.5-1.0 | How similar a project must be (higher = stricter) |

**Adjust Sensitivity:**
- **0.75** (default): Shows only highly relevant projects
- **0.65**: Shows moderately relevant projects
- **0.55**: Shows all potentially related projects

---

## 5. Integration Setup

### Prerequisite

Teams channel webhook URL must be registered and validated.

### Step 1: Get Teams Webhook URL

**From Teams:**
```
1. Go to team channel settings
2. Click "Connectors"
3. Search for "Incoming Webhook"
4. Configure → Copy URL
```

**Example URL:**
```
https://outlook.webhook.office.com/webhookb2/abc123...@example.com/IncomingWebhook/def456...
```

### Step 2: Register Webhook in Vault

**Via API (Admin Only):**
```bash
curl -X POST https://api.tenopa.com/api/teams/bot/webhook-config \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "team_id": "your-team-uuid",
    "webhook_url": "https://outlook.webhook.office.com/webhookb2/..."
  }'
```

**Via UI:**
```
Vault → Team Settings → Teams Bot → Register Webhook URL
→ Paste URL → Validate → Save
```

### Step 3: Enable Modes

```
Vault → Team Settings → Teams Bot

☑ Adaptive Mode
☑ Digest Mode (Daily 9:00 UTC)
☑ Matching Mode
```

### Step 4: Configure Keywords (Digest Mode)

```
Digest Keywords:
+ Add G2B:환경부
+ Add competitor:ACME
+ Add tech:AI
```

---

## 6. Troubleshooting

### "Webhook URL is invalid"

**Cause:** URL format error or webhook is dead

**Solution:**
1. Copy webhook URL again from Teams
2. Verify URL starts with `https://outlook.webhook.office.com`
3. Check webhook is still active (Teams → Connector Settings)

### "No response from @Vault"

**Possible causes:**
- Bot is disabled (check settings)
- Adaptive mode is off
- Network timeout (try again)

**Solution:**
1. Check bot is enabled: `Vault → Settings → Bot Enabled = ✅`
2. Check adaptive mode: `Bot Modes → Adaptive = ✅`
3. Verify team has valid webhook
4. Contact support if issue persists

### "Digest not sent"

**Cause:** Digest generation failed or no results for keywords

**Solution:**
1. Check digest is enabled: `Digest Enabled = ✅`
2. Verify digest keywords return results
3. Check digest time is correct (default 9:00 UTC)
4. Manual trigger: `POST /api/teams/bot/digest` (admin only)

### "Some information excluded"

**Cause:** Response contains restricted documents

**Solution:**
- This is by design (role-based access control)
- Ask team lead/director for document access
- Request escalation if needed

### Missing Sources

**Cause:** Document sources not found in vault

**Solution:**
1. Ensure documents are indexed (uploaded to vault)
2. Check document language matches query
3. Update document metadata (title, tags)

---

## 7. Best Practices

### For Managers

1. **Monitor Digest Keywords Weekly**
   - Remove keywords that don't generate results
   - Add keywords for new growth areas
   - Review recommendation accuracy

2. **Set Digest Time by Timezone**
   - 9:00 UTC = 17:00 KST (Korea)
   - 9:00 UTC = 01:00 PST (US West)
   - Adjust for team convenience

3. **Enable Matching for RFP Teams**
   - Critical for bid decisions
   - Reduces time to identify relevant experience
   - Improves win rate (estimated 5-10% lift)

### For Users

1. **Ask Specific Questions**
   - Good: "What was the team structure for Project X?"
   - Bad: "Tell me about Project X" (too vague)

2. **Use Context in Multi-turn**
   - Vault remembers last 8 turns
   - Build on previous answers
   - Ask follow-ups for clarity

3. **Verify Sources**
   - Check confidence level (aim for 80%+)
   - Review cited documents
   - Confirm facts before relying on response

4. **Multi-language Queries**
   - English, Korean, Chinese, Japanese supported
   - Auto-detected (usually accurate)
   - Specify language if detection fails: `@Vault [EN] ...`

---

## 8. Administration

### Metrics Dashboard

**Access:** `Vault → Admin → Teams Bot Metrics`

Monitor:
- Messages sent (adaptive, digest, matching)
- Delivery success rate (target: 98%+)
- Average response time (target: <2s)
- Webhook health (target: 100%)

### Health Checks

**Webhook Status:**
```
Teams Bot → Configuration → Webhook Health
Status: 🟢 Healthy (last checked 2 mins ago)
```

**Revalidate Webhook (Manual):**
```
POST /api/teams/bot/webhook/validate
Response: {"is_valid": true, "message": "Webhook is live"}
```

### Audit Log

**View all Teams bot activity:**
```
Admin → Audit Logs → Filter: "Teams Bot"
- Message sent to team X (2026-04-20 09:00 UTC)
- Webhook validation passed (2026-04-20 08:59 UTC)
- RFP recommendation sent (5 teams) (2026-04-20 07:30 UTC)
```

---

## 9. FAQ

**Q: Can I mention @Vault in DMs?**  
A: Not yet. Currently supported in team channels only.

**Q: What if Vault responds with outdated information?**  
A: Update the source document in Vault. Responses are rebuilt from live KB.

**Q: Can I customize the digest time per team?**  
A: Yes. Each team has independent `digest_time` (default 9:00 UTC).

**Q: How far back does context go?**  
A: Last 8 conversation turns in same thread. Starts fresh in new thread.

**Q: What's the response time for adaptive queries?**  
A: Typical <2 seconds. Can reach 4-6s with large context windows.

**Q: Are responses logged for compliance?**  
A: Yes. All Teams bot messages logged to `teams_bot_messages` table with audit trail.

---

## 10. Support

**Documentation:** [Vault Chat Technical Design](./vault-chat-phase2.design.md)

**API Reference:** [OpenAPI Docs](https://api.tenopa.com/docs#/teams-bot)

**Report Issues:** [Teams Bot Issues](https://github.com/tenopa/proposer/issues?label=teams-bot)

**Contact:** `vault-support@tenopa.co.kr`

---

**Last Updated**: 2026-04-20  
**Next Review**: 2026-05-04
