# Vault Chat Phase 2 — Test Execution Guide

Quick reference for running E2E and performance tests.

---

## Prerequisites

```bash
# Ensure dependencies installed
uv sync

# Verify pytest is available
pytest --version
```

---

## Running All Tests

### All Tests (14 E2E + 10 Performance = 24 total)
```bash
pytest tests/e2e/test_vault_chat_e2e.py tests/performance/test_vault_performance.py -v
```

**Expected Output**:
```
========================= 24 passed in 45.2s ==========================
- 14 E2E tests: PASSED
- 10 Performance tests: PASSED
```

---

## Running E2E Tests Only

### All E2E Tests (14 tests)
```bash
pytest tests/e2e/test_vault_chat_e2e.py -v
```

### Specific E2E Test Class
```bash
# Adaptive Mode tests only
pytest tests/e2e/test_vault_chat_e2e.py::TestAdaptiveModeE2E -v

# Digest Mode tests only
pytest tests/e2e/test_vault_chat_e2e.py::TestDigestModeE2E -v

# Matching Mode tests only
pytest tests/e2e/test_vault_chat_e2e.py::TestMatchingModeE2E -v

# Infrastructure tests only
pytest tests/e2e/test_vault_chat_e2e.py::TestInfrastructureE2E -v

# Performance tests only
pytest tests/e2e/test_vault_chat_e2e.py::TestPerformanceE2E -v

# Security tests only
pytest tests/e2e/test_vault_chat_e2e.py::TestSecurityE2E -v
```

### Single E2E Test
```bash
pytest tests/e2e/test_vault_chat_e2e.py::TestAdaptiveModeE2E::test_adaptive_mode_simple_query -v
```

---

## Running Performance Benchmarks

### All Benchmarks (10 tests)
```bash
pytest tests/performance/test_vault_performance.py -v
```

### Specific Benchmark Class
```bash
# Adaptive response time
pytest tests/performance/test_vault_performance.py::TestAdaptiveResponseTime -v

# Context loading speed
pytest tests/performance/test_vault_performance.py::TestContextLoadingSpeed -v

# Permission filtering
pytest tests/performance/test_vault_performance.py::TestPermissionFilteringSpeed -v

# Embedding batch speed
pytest tests/performance/test_vault_performance.py::TestEmbeddingBatchSpeed -v

# Digest generation
pytest tests/performance/test_vault_performance.py::TestDigestGenerationSpeed -v

# Bottleneck analysis
pytest tests/performance/test_vault_performance.py::TestBottleneckAnalysis -v
```

### Single Benchmark
```bash
pytest tests/performance/test_vault_performance.py::TestAdaptiveResponseTime::test_adaptive_response_time_p95 -v
```

---

## Performance Markers

### Run Only Performance Tests
```bash
pytest -m performance tests/performance/test_vault_performance.py -v
```

---

## Test Output Options

### Verbose Output
```bash
pytest tests/e2e/test_vault_chat_e2e.py -v
```

### Very Verbose (includes docstrings)
```bash
pytest tests/e2e/test_vault_chat_e2e.py -vv
```

### Show Print Statements
```bash
pytest tests/e2e/test_vault_chat_e2e.py -v -s
```

### Short Summary
```bash
pytest tests/e2e/test_vault_chat_e2e.py -q
```

### Quiet Mode (only failures)
```bash
pytest tests/e2e/test_vault_chat_e2e.py --tb=short
```

---

## Coverage Analysis

### Generate Coverage Report
```bash
pytest tests/e2e/test_vault_chat_e2e.py tests/performance/test_vault_performance.py --cov=app/services --cov-report=term-missing
```

### HTML Coverage Report
```bash
pytest tests/e2e/test_vault_chat_e2e.py tests/performance/test_vault_performance.py --cov=app/services --cov-report=html
# Open htmlcov/index.html in browser
```

---

## Debugging Tests

### Run with Python Debugger
```bash
pytest tests/e2e/test_vault_chat_e2e.py::TestAdaptiveModeE2E::test_adaptive_mode_simple_query -v --pdb
```

### Show Local Variables on Failure
```bash
pytest tests/e2e/test_vault_chat_e2e.py -v --tb=long
```

### Stop on First Failure
```bash
pytest tests/e2e/test_vault_chat_e2e.py -v -x
```

### Stop After N Failures
```bash
pytest tests/e2e/test_vault_chat_e2e.py -v --maxfail=2
```

---

## Performance Benchmark Results

### Save Results to CSV
Benchmarks automatically save to:
```
tests/performance/benchmark_results/
  ├── adaptive_response_time_20260428_143022.csv
  ├── context_loading_speed_20260428_143045.csv
  ├── permission_filtering_speed_20260428_143108.csv
  ├── embedding_batch_speed_20260428_143141.csv
  └── digest_generation_speed_20260428_143203.csv
```

### Analyze Benchmark Results
```bash
# View CSV in terminal
cat tests/performance/benchmark_results/adaptive_response_time_*.csv

# Import to Excel for analysis
# Or use Python:
import pandas as pd
df = pd.read_csv('tests/performance/benchmark_results/adaptive_response_time_*.csv')
print(df.describe())
```

---

## Test Patterns

### Test Naming Convention
All tests follow pattern:
- `test_<feature>_<scenario>` — Descriptive and self-documenting

### Fixture Pattern
```python
@pytest.fixture
def sample_config():
    """Reusable test data"""
    return TeamsBotConfig(...)

async def test_something(sample_config):
    """Uses fixture automatically"""
    pass
```

### Async Test Pattern
```python
@pytest.mark.asyncio
async def test_async_operation():
    """Mark as async to use await"""
    result = await service.some_async_method()
    assert result is not None
```

---

## Common Issues & Solutions

### Issue: Tests not collecting
**Solution**: Ensure imports are correct
```python
# Check imports in test file
from app.services.teams_bot_service import TeamsBotService
```

### Issue: Async test not running
**Solution**: Add @pytest.mark.asyncio
```python
@pytest.mark.asyncio
async def test_something():
    pass
```

### Issue: Mock not working
**Solution**: Use AsyncMock for async functions
```python
from unittest.mock import AsyncMock
mock_service = AsyncMock()
result = await mock_service.method()
```

### Issue: Performance tests too slow
**Solution**: Reduce iterations in benchmark
```python
# In test file, modify:
num_iterations = 5  # Reduce from 20
```

---

## Continuous Integration

### Run Tests in CI/CD Pipeline
```bash
# .github/workflows/test.yml example
- name: Run E2E Tests
  run: pytest tests/e2e/ -v --cov --cov-report=xml

- name: Run Performance Tests
  run: pytest tests/performance/ -v -m performance
```

---

## Performance Targets Checklist

When reviewing test results, verify:

```
E2E Tests:
  ✅ All 14 tests pass
  ✅ Test duration < 2s each
  ✅ No timeouts or hangs

Performance Benchmarks:
  ✅ Adaptive P95: < 2000ms
  ✅ Context load P95: < 500ms
  ✅ Permission filter P95: < 100ms
  ✅ Embedding P95: < 1000ms
  ✅ Digest generation: < 5000ms
  ✅ Cache hit rate: > 60%

Code Quality:
  ✅ All tests have docstrings
  ✅ All functions type-hinted
  ✅ No print() statements (use logging)
  ✅ No hardcoded values
```

---

## Next Steps

After running tests:

1. **Review Results**: Check all metrics meet targets
2. **Analyze Bottlenecks**: Use optimizer's analyze_bottleneck()
3. **Check Coverage**: Verify 85%+ code coverage
4. **Export Data**: Save CSV benchmark results
5. **Document Findings**: Update performance baseline

---

## Contact & Support

- 📧 **Issues**: Report to vault-support@tenopa.co.kr
- 📖 **Docs**: See VAULT_PHASE2_CHECK_PHASE_REPORT.md
- 🔗 **Code**: tests/e2e/ and tests/performance/

---

**Last Updated**: 2026-04-28  
**Test Suite Version**: Phase 2 CHECK  
**Status**: Ready for Production
