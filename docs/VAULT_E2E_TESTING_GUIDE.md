# Vault AI Chat - E2E Testing Guide

## Overview

Complete end-to-end testing suite for Vault AI Chat system covering:
- **Backend Integration Tests** - API endpoints and business logic
- **Frontend E2E Tests** - User workflows with Playwright
- **Performance Tests** - Response time and stability
- **Error Scenarios** - Graceful degradation and error handling

## Test Structure

```
tests/
├── integration/
│   ├── test_vault_chat_complete_e2e.py      # Backend E2E tests
│   ├── test_vault_semantic_search_e2e.py    # Vector search E2E
│   ├── test_vault_vector_search.py          # Vector search units
│   └── test_vault_integration.py            # Conversation CRUD
│
frontend/
└── e2e/
    ├── vault-chat-complete.spec.ts          # Frontend E2E tests
    └── ...
```

## Test Coverage

### Backend E2E Tests (test_vault_chat_complete_e2e.py)

#### ChatComplete FlowTests (20 tests)

**Core Chat Flow (7 tests)**:
1. `test_complete_chat_flow_with_sources` - Full pipeline from message to response
2. `test_vector_search_sources_included_in_response` - Sources in response
3. `test_llm_response_includes_sources_context` - LLM gets source context
4. `test_validation_gate_checks_response_quality` - 3-point validation gate
5. `test_conversation_message_history` - Loads conversation context
6. `test_different_vault_sections_routed_correctly` - Intent routing
7. `test_conversation_creation` - New conversation creation

**Rate Limiting & Security (3 tests)**:
8. `test_rate_limiting_enforced` - 30 requests/min limit
9. `test_conversation_ownership_verified` - RLS security check
10. `test_unauthorized_conversation_access` - User isolation

**Database Operations (3 tests)**:
11. `test_message_saves_with_confidence_score` - Confidence persistence
12. `test_conversation_last_activity_timestamp` - Activity tracking
13. `test_delete_conversation_cascades_messages` - Cascade deletes

**Conversation Management (4 tests)**:
14. `test_list_conversations_pagination` - Pagination support
15. `test_conversation_title_auto_generation` - Title generation
16. `test_conversation_message_history` - Multi-turn context
17. `test_conversation_last_activity_timestamp` - Activity tracking

**Error Handling (3 tests)**:
18. `test_vector_search_failure_graceful_fallback` - Graceful degradation
19. `test_database_error_returns_500` - Error code handling
20. `test_invalid_conversation_id_returns_404` - 404 handling

#### Performance Tests (2 tests)
21. `test_response_time_under_2_seconds` - Latency requirement
22. `test_handles_large_conversation_history` - Large dataset handling

#### Concurrency Tests (1 test)
23. `test_concurrent_chat_requests` - Concurrent users

### Frontend E2E Tests (vault-chat-complete.spec.ts)

#### User Workflows (7 tests)

**Complete Chat Flow (1 test)**:
1. `Complete chat flow: Create conversation -> Send message -> Get response`
   - New conversation creation
   - Message sending
   - AI response generation
   - Source display
   - Confidence scoring

**Message Persistence (1 test)**:
2. `Message history persistence: Conversation retains messages`
   - Multi-turn conversations
   - Page refresh persistence
   - Message order preservation

**Search Integration (1 test)**:
3. `Vector search results integration: Sources displayed correctly`
   - Source list display
   - Relevance indicators
   - Source metadata

**Conversation Management (1 test)**:
4. `Conversation management: Create, list, and delete conversations`
   - Multiple conversations
   - Conversation switching
   - Conversation deletion

**Search Filters (1 test)**:
5. `Search with filters: Section selection and filtering`
   - Section dropdown
   - Query filtering
   - Section-specific results

**Rate Limiting (1 test)**:
6. `Rate limiting: User is notified when limit is exceeded`
   - Limit detection
   - User notification
   - Button disabling

**Error Handling (1 test)**:
7. `Error handling: Graceful error display`
   - Error messages
   - Chat usability post-error
   - Recovery

#### Responsive Design (1 test)
8. `Responsive design: Chat works on mobile view`
   - Mobile viewport (375x812)
   - Sidebar behavior
   - Touch interaction

#### Accessibility (1 test)
9. `Accessibility: Keyboard navigation works`
   - Tab navigation
   - Enter to submit
   - Focus management

#### Performance Tests (2 tests)
10. `Response time under 2 seconds` - Latency measurement
11. `No layout shift during message loading` - Visual stability

## Running the Tests

### Backend E2E Tests

```bash
# Run all backend E2E tests
pytest tests/integration/test_vault_chat_complete_e2e.py -v

# Run specific test class
pytest tests/integration/test_vault_chat_complete_e2e.py::TestVaultChatCompleteFlow -v

# Run specific test
pytest tests/integration/test_vault_chat_complete_e2e.py::TestVaultChatCompleteFlow::test_complete_chat_flow_with_sources -v

# Run with coverage
pytest tests/integration/test_vault_chat_complete_e2e.py --cov=app.api.routes_vault_chat --cov-report=html

# Run tests matching pattern
pytest tests/integration/test_vault_chat_complete_e2e.py -k "rate_limit" -v

# Run tests with output
pytest tests/integration/test_vault_chat_complete_e2e.py -v -s
```

### Frontend E2E Tests

```bash
# Install Playwright dependencies
npm install -D @playwright/test

# Run all frontend tests
npx playwright test frontend/e2e/vault-chat-complete.spec.ts

# Run specific test
npx playwright test frontend/e2e/vault-chat-complete.spec.ts -g "Complete chat flow"

# Run with headed browser (see browser)
npx playwright test frontend/e2e/vault-chat-complete.spec.ts --headed

# Run on specific browser
npx playwright test frontend/e2e/vault-chat-complete.spec.ts --project=chromium

# Debug mode
npx playwright test frontend/e2e/vault-chat-complete.spec.ts --debug

# Generate report
npx playwright test frontend/e2e/vault-chat-complete.spec.ts --reporter=html
```

### Combined Test Run

```bash
# Run both backend and frontend tests
./scripts/run-all-tests.sh

# Or manually:
pytest tests/integration/test_vault_chat_complete_e2e.py -v && \
npx playwright test frontend/e2e/vault-chat-complete.spec.ts
```

## Test Scenarios

### Scenario 1: New User Chat Experience

**Flow**:
1. User creates new conversation
2. Sends question about past projects
3. System searches vector database
4. Returns relevant past projects as sources
5. AI generates response based on sources
6. User sees response with confidence score and sources

**Tests Covering**:
- `test_complete_chat_flow_with_sources`
- `test_vector_search_results_integration`
- `Complete chat flow: Create conversation -> Send message`

**Expected Behavior**:
- ✅ Response generated within 2 seconds
- ✅ Sources displayed with relevance scores
- ✅ Confidence score between 0.5-1.0
- ✅ Message saved to database

### Scenario 2: Multi-Turn Conversation

**Flow**:
1. User sends first question
2. AI responds with context
3. User sends follow-up question
4. AI uses conversation history as context
5. Response reflects previous context

**Tests Covering**:
- `test_conversation_message_history`
- `Message history persistence`

**Expected Behavior**:
- ✅ All messages persisted
- ✅ Conversation context loaded
- ✅ Follow-up answers reference previous context
- ✅ Messages survive page refresh

### Scenario 3: Rate Limit Handling

**Flow**:
1. User makes 30 requests within 60 seconds (allowed)
2. 31st request within window is rejected
3. User sees rate limit message
4. Submit button is disabled
5. After 60 seconds, limit resets

**Tests Covering**:
- `test_rate_limiting_enforced`
- `Rate limiting: User is notified`

**Expected Behavior**:
- ✅ First 30 requests succeed
- ✅ 31st request returns 429 error
- ✅ User notification displayed
- ✅ Button disabled until reset

### Scenario 4: Error Recovery

**Flow**:
1. Vector search fails (service unavailable)
2. System falls back to SQL-only search
3. Response generated with lower confidence
4. User informed about limited sources
5. Chat remains usable

**Tests Covering**:
- `test_vector_search_failure_graceful_fallback`
- `Error handling: Graceful error display`

**Expected Behavior**:
- ✅ Graceful degradation
- ✅ Chat not blocked
- ✅ User informed
- ✅ Response still generated

### Scenario 5: Conversation Management

**Flow**:
1. User creates conversation A
2. Sends messages to conversation A
3. Creates conversation B (new, empty)
4. Switches to conversation A (messages restored)
5. Deletes conversation B
6. Conversation B removed from list

**Tests Covering**:
- `test_conversation_management`
- `Conversation management` E2E test

**Expected Behavior**:
- ✅ Multiple conversations independent
- ✅ Switching preserves message history
- ✅ Deletion removes from list
- ✅ No message cross-contamination

## Test Data

### Mock Data Fixtures

```python
# Completed project
{
    "id": "proj-1",
    "title": "Mobile App Development - TechCorp",
    "content": "Built iOS and Android apps...",
    "metadata": {
        "client": "TechCorp",
        "budget": 45000,
        "duration": "6 months"
    }
}

# Government guideline
{
    "id": "guide-1",
    "title": "정부 급여 기준 2024",
    "content": "정부 공사에 투입되는 기술인의 일급 기준...",
    "metadata": {
        "category": "salary",
        "effective_date": "2024-01-01"
    }
}
```

## Assertions & Validation

### Response Quality Checks

```python
# Confidence score range
assert 0 <= confidence_score <= 1.0

# Response has content
assert len(response_text) > 10

# Sources included
assert len(sources) >= 0  # Can be 0 in graceful degradation

# Message persistence
assert saved_message["id"] is not None
```

### Performance Assertions

```python
# Response time
assert response_time_ms < 2000

# Concurrent requests
assert len(concurrent_results) == num_requests

# Large dataset handling
assert len(large_history) == expected_count
```

### Security Assertions

```python
# User isolation
assert conv_owner == user_id

# Unauthorized access blocked
assert error_code == 403

# Message ownership
assert message["user_id"] == current_user.id
```

## Continuous Integration

### GitHub Actions Workflow

```yaml
name: Vault E2E Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pytest tests/integration/test_vault_chat_complete_e2e.py -v --cov

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npx playwright install
      - run: npx playwright test frontend/e2e/vault-chat-complete.spec.ts
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
```

## Test Results Interpretation

### Pass Criteria

✅ **All tests pass** when:
- Backend tests: 100% pass rate
- Frontend tests: 100% pass rate
- Performance: Response time < 2000ms
- Coverage: > 80% code coverage

⚠️ **Warning** when:
- Response time 1500-2000ms
- Coverage 70-80%
- Flaky tests (intermittent failures)

❌ **Failure** when:
- Any test fails consistently
- Response time > 2000ms
- Coverage < 70%
- Security tests fail

## Debugging Failed Tests

### Backend Debugging

```bash
# Run with verbose output
pytest tests/integration/test_vault_chat_complete_e2e.py -vv -s

# Run with pdb on failure
pytest tests/integration/test_vault_chat_complete_e2e.py --pdb

# Run single test with logging
pytest tests/integration/test_vault_chat_complete_e2e.py::TestVaultChatCompleteFlow::test_complete_chat_flow_with_sources -vv --log-cli-level=DEBUG
```

### Frontend Debugging

```bash
# Run in headed mode (see browser)
npx playwright test frontend/e2e/vault-chat-complete.spec.ts --headed

# Debug mode with step-through
npx playwright test frontend/e2e/vault-chat-complete.spec.ts --debug

# Trace viewer
npx playwright show-trace trace.zip

# Screenshot on failure
npx playwright test frontend/e2e/vault-chat-complete.spec.ts --screenshot=only-on-failure
```

## Known Issues & Limitations

### Environment-Specific

1. **API Timeout**: Frontend tests may timeout if API slow
   - Solution: Increase timeout in `await page.waitForSelector(selector, { timeout: 15000 })`

2. **Mock Data**: Tests use mocked Supabase responses
   - Use real database in staging for integration tests
   - Run against real API before production

3. **Playwright Browser**: Requires Chrome/Chromium
   - Install: `npx playwright install chromium`

### Test Flakiness

1. **Race Conditions**: Vector search may be slower
   - Solution: Increase wait timeouts
   - Use `expect` with polling instead of `waitForSelector`

2. **Rate Limiter**: Tests may interfere if run in parallel
   - Solution: Run tests serially with `--workers=1`
   - Use separate rate limiter instances per test

## Next Steps

1. **Setup CI/CD**: Add tests to GitHub Actions
2. **Performance Monitoring**: Track response times over time
3. **Flaky Test Analysis**: Identify and fix intermittent failures
4. **Coverage Reports**: Generate and review coverage
5. **Load Testing**: Test with > 100 concurrent users
6. **User Acceptance Testing**: Get user feedback on flows

## References

- [Backend E2E Tests](../tests/integration/test_vault_chat_complete_e2e.py)
- [Frontend E2E Tests](../frontend/e2e/vault-chat-complete.spec.ts)
- [Vector Search Tests](../tests/integration/test_vault_semantic_search_e2e.py)
- [Vault Chat Routes](../app/api/routes_vault_chat.py)
- [Playwright Documentation](https://playwright.dev)
- [Pytest Documentation](https://docs.pytest.org)
