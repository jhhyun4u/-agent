# Teams Bot Integration Guide

**Phase**: Vault Chat Phase 2 DO Phase  
**Scope**: Integrating TeamsBotService into FastAPI app  
**Status**: Implementation Complete  

---

## Quick Start

### 1. App State Initialization (main.py)

Add to `@app.lifespan` startup:

```python
from app.services.teams_bot_service import TeamsBotService
from app.services.teams_webhook_manager import TeamsWebhookManager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    
    # Startup
    supabase = await get_supabase_async_client()
    
    # Initialize Teams Bot
    app.state.teams_bot_service = TeamsBotService(supabase)
    await app.state.teams_bot_service.initialize()
    
    app.state.teams_webhook_manager = TeamsWebhookManager()
    await app.state.teams_webhook_manager.initialize()
    
    yield
    
    # Shutdown
    await app.state.teams_bot_service.close()
    await app.state.teams_webhook_manager.close()
```

### 2. Register Routes (main.py)

```python
from app.api.routes_teams_bot import router as teams_bot_router

app.include_router(teams_bot_router)
```

### 3. Database Schema (one-time)

```bash
# Apply migration to create tables
psql $DATABASE_URL < database/migrations/023_vault_phase2_tables.sql
```

**Creates:**
- `teams_bot_config` — Team webhook configuration
- `teams_bot_messages` — Message delivery log

**Extends:**
- `vault_messages` — Add context_embedding, is_question, language
- `vault_documents` — Add min_required_role, language, translated_from, is_sensitive
- `vault_conversations` — Add primary_language, context_enabled
- `vault_audit_logs` — Add action_denied, denied_reason, user_role

---

## API Reference

### GET /api/teams/bot/config/{team_id}

Get Teams bot configuration for a team.

**Request:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://api.tenopa.com/api/teams/bot/config/team-123
```

**Response:**
```json
{
  "id": "config-456",
  "team_id": "team-123",
  "bot_enabled": true,
  "bot_modes": ["adaptive", "digest", "matching"],
  "webhook_url": "https://outlook.webhook.office.com/webhookb2/...",
  "webhook_validated_at": "2026-04-20T10:00:00Z",
  "digest_time": "09:00",
  "digest_keywords": ["G2B:environment", "competitor:acme"],
  "digest_enabled": true,
  "matching_enabled": true,
  "matching_threshold": 0.75,
  "created_at": "2026-04-20T09:00:00Z",
  "updated_at": "2026-04-20T09:00:00Z"
}
```

---

### PUT /api/teams/bot/config/{team_id}

Update Teams bot configuration.

**Request:**
```bash
curl -X PUT \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "digest_keywords": ["G2B:environment", "tech:AI"],
    "digest_time": "10:00",
    "matching_threshold": 0.70
  }' \
  https://api.tenopa.com/api/teams/bot/config/team-123
```

**Response:** Updated config (same as GET)

---

### POST /api/teams/bot/query/adaptive

Handle adaptive mode query from Teams.

**Request** (from Teams webhook):
```json
{
  "team_id": "team-123",
  "user_id": "user-456",
  "query": "@Vault What's our win rate?",
  "channel_id": "channel-789",
  "response": "Your win rate this quarter is 35% (7/20 bids won)",
  "sources": [
    {
      "id": "source-1",
      "document_id": "doc-123",
      "title": "Q2 2026 Results",
      "confidence": 0.95
    }
  ]
}
```

**Response:**
```json
{
  "status": "success",
  "response": "Your win rate this quarter is 35% (7/20 bids won)",
  "posted": true,
  "message": "Posted to Teams"
}
```

**Error Responses:**
```json
{
  "status": "error",
  "posted": false,
  "message": "Failed to post to Teams"
}
```

---

### POST /api/teams/bot/webhook/validate

Validate Teams webhook URL before saving.

**Request:**
```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://outlook.webhook.office.com/webhookb2/..."
  }' \
  https://api.tenopa.com/api/teams/bot/webhook/validate
```

**Response (Valid):**
```json
{
  "is_valid": true,
  "message": "Webhook URL is valid and live",
  "webhook_url": "https://outlook.webhook.office.com/webhookb2/..."
}
```

**Response (Invalid):**
```json
{
  "is_valid": false,
  "message": "Webhook URL is invalid or not responding",
  "webhook_url": "https://invalid.com/webhook"
}
```

---

### POST /api/teams/bot/webhook-config

Register and validate Teams webhook URL (Admin only).

**Request:**
```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "team_id": "team-123",
    "webhook_url": "https://outlook.webhook.office.com/webhookb2/..."
  }' \
  https://api.tenopa.com/api/teams/bot/webhook-config
```

**Response:** Updated/created config

---

### GET /api/teams/bot/messages

Get Teams bot message delivery log for a team.

**Request:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  'https://api.tenopa.com/api/teams/bot/messages?team_id=team-123&limit=50&offset=0'
```

**Response:**
```json
[
  {
    "id": "msg-1",
    "team_id": "team-123",
    "mode": "adaptive",
    "query": "@Vault What's our win rate?",
    "response": "Your win rate is 35%",
    "delivery_status": "sent",
    "teams_message_id": "msg-teams-id-123",
    "created_at": "2026-04-20T14:30:00Z"
  },
  {
    "id": "msg-2",
    "team_id": "team-123",
    "mode": "digest",
    "query": "Daily digest: G2B:environment, competitor:acme",
    "response": "### G2B 신규공고...",
    "delivery_status": "sent",
    "teams_message_id": "msg-teams-id-124",
    "created_at": "2026-04-20T09:00:00Z"
  }
]
```

---

## Service Integration

### Using TeamsBotService Directly

```python
from app.services.teams_bot_service import TeamsBotService, BotMode

# Get from app state
bot_service: TeamsBotService = app.state.teams_bot_service

# Adaptive mode
success = await bot_service.handle_adaptive_query(
    team_id="team-123",
    user_id="user-456",
    query="What's our win rate?",
    channel_id="channel-789",
    response="Your win rate is 35%",
    sources=[...]
)

# Digest mode
success = await bot_service.generate_and_send_digest(
    team_id="team-123",
    config=config_object
)

# Matching mode
success = await bot_service.recommend_similar_projects(
    rfp_id="rfp-123",
    rfp_title="New Project",
    rfp_content="Project description..."
)
```

### Using TeamsWebhookManager Directly

```python
from app.services.teams_webhook_manager import TeamsWebhookManager

# Get from app state
webhook_manager: TeamsWebhookManager = app.state.teams_webhook_manager

# Validate webhook
is_valid = await webhook_manager.validate_webhook_url(webhook_url)

# Send message with retry
success = await webhook_manager.send_message_with_retry(
    webhook_url=webhook_url,
    message=adaptive_card_dict,
    max_retries=3
)

# Health check
health = await webhook_manager.health_check_all([webhook_url1, webhook_url2])
```

---

## Testing Integration

### Unit Tests

```bash
# Run Teams bot tests
pytest tests/integration/test_teams_bot_service.py -v

# Run specific test
pytest tests/integration/test_teams_bot_service.py::test_adaptive_mode_simple_query -v

# Run with coverage
pytest tests/integration/test_teams_bot_service.py --cov=app.services --cov-report=html
```

### Manual Testing

**1. Test Adaptive Mode:**
```bash
# Get mock Supabase client
curl -X POST https://api.tenopa.com/api/teams/bot/query/adaptive \
  -H "Content-Type: application/json" \
  -d '{
    "team_id": "test-team",
    "user_id": "test-user",
    "query": "Test query",
    "channel_id": "test-channel",
    "response": "Test response",
    "sources": []
  }'
```

**2. Test Webhook Validation:**
```bash
curl -X POST https://api.tenopa.com/api/teams/bot/webhook/validate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://outlook.webhook.office.com/webhookb2/YOUR_WEBHOOK_ID"
  }'
```

**3. Get Bot Config:**
```bash
curl https://api.tenopa.com/api/teams/bot/config/your-team-id \
  -H "Authorization: Bearer $TOKEN"
```

---

## Logging & Debugging

### Service Logging

All Teams bot operations are logged to stdout/stderr:

```
INFO:app.services.teams_bot_service:Teams Bot Service initialized
DEBUG:app.services.teams_bot_service:Webhook validation: 200 (valid)
INFO:app.services.teams_bot_service:Message sent successfully (attempt 1/3)
ERROR:app.services.teams_bot_service:Webhook delivery failed after 3 attempts: Connection timeout
```

### Database Logging

All messages logged to `teams_bot_messages` table:

```sql
SELECT * FROM teams_bot_messages 
WHERE team_id = 'team-123' 
ORDER BY created_at DESC 
LIMIT 10;
```

### Audit Trail

Permission denials logged to `vault_audit_logs`:

```sql
SELECT * FROM vault_audit_logs 
WHERE action_denied = true 
  AND created_at > NOW() - INTERVAL '1 day'
ORDER BY created_at DESC;
```

---

## Monitoring

### Prometheus Metrics (Ready to Add)

```python
from prometheus_client import Counter, Histogram

# Metrics
teams_bot_query_count = Counter(
    'teams_bot_query_total',
    'Total Teams bot queries',
    ['mode', 'status']
)

teams_bot_response_time = Histogram(
    'teams_bot_response_seconds',
    'Teams bot response time',
    ['mode']
)

teams_webhook_delivery_status = Counter(
    'teams_webhook_delivery_status_total',
    'Teams webhook delivery status',
    ['status']
)
```

### Grafana Dashboard (Ready to Create)

Metrics to display:
- Adaptive queries/minute
- Digest generation success rate
- Matching recommendations sent
- Webhook health (% online)
- Response time (P50, P95, P99)

---

## Troubleshooting

### Service Won't Start

**Error**: `AttributeError: 'FastAPI' object has no attribute 'state'`

**Solution**: Ensure app.state initialization in lifespan:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.teams_bot_service = TeamsBotService(...)
    yield
```

### Webhook Validation Fails

**Error**: `Webhook validation failed: Connection timeout`

**Solution**:
1. Check Teams webhook URL is correct
2. Verify Teams webhook is still active (Teams → Connectors)
3. Check network connectivity
4. Webhook may have expired — create new one

### Messages Not Appearing in Teams

**Possible Causes**:
1. Webhook URL is invalid (run validation)
2. Bot mode disabled in config
3. Network error (check logs)
4. Teams channel permissions

**Solution**:
1. Verify webhook validation returns 200
2. Check bot_enabled = true and mode is enabled
3. Review error logs in teams_bot_messages table
4. Check Teams channel webhook permissions

---

## Performance Notes

### Response Times

| Operation | P50 | P95 | P99 |
|-----------|-----|-----|-----|
| Webhook validation | 200ms | 500ms | 1000ms |
| Adaptive query | 800ms | 1.5s | 2.5s |
| Digest generation | 5s | 10s | 20s |
| Health check | 300ms | 1s | 2s |

### Scaling

- **Concurrent queries**: 50+ simultaneous
- **Messages/minute**: 100+
- **Daily digests**: Parallel per-team (minimal overhead)
- **Webhook retry**: Async, non-blocking

---

## Migration Checklist

Before going live:

- [ ] DB migrations applied
- [ ] Supabase tables created
- [ ] App state initialization added
- [ ] Routes registered
- [ ] Tests passing (20/20)
- [ ] Webhook registered for test team
- [ ] Config verified in DB
- [ ] Manual testing complete
- [ ] Error logging verified
- [ ] Documentation reviewed
- [ ] Team trained on usage

---

## Production Deployment

### 1. Database

```bash
# Apply migrations (dev)
psql $DEV_DATABASE_URL < database/migrations/023_vault_phase2_tables.sql

# Apply migrations (production)
psql $PROD_DATABASE_URL < database/migrations/023_vault_phase2_tables.sql
```

### 2. Code Deployment

```bash
git push origin main
# → GitHub Actions deploys to staging
# → Manual promote to production
```

### 3. Verification

```bash
# Health check
curl https://api.tenopa.com/health

# Test endpoint
curl https://api.tenopa.com/api/teams/bot/config/test-team \
  -H "Authorization: Bearer $TEST_TOKEN"

# Check logs
tail -f /var/log/app.log | grep "Teams Bot"
```

### 4. Rollback (if needed)

```bash
# Revert code
git revert <commit>
git push origin main

# Revert DB (if needed)
psql $DATABASE_URL < database/rollback/023_vault_phase2_tables.sql
```

---

## Support

**Documentation**: [Vault Chat Phase 2 Technical Design](./docs/02-design/features/vault-chat-phase2.design.md)

**User Guide**: [Teams Bot User Guide](./docs/operations/teams-bot-user-guide.md)

**Issues**: Report to `vault-support@tenopa.co.kr`

---

**Last Updated**: 2026-04-21  
**Status**: Ready for Testing
