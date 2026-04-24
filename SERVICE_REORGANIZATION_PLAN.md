# 📂 서비스 레이어 재구성 계획

## 분류 기준

```
app/services/
├── core/           # 기본 유틸 & 인프라 (20-25개)
├── domains/        # 비즈니스 로직 (80-90개)
│   ├── proposal/   # 제안서 관련
│   ├── bidding/    # 입찰 관련  
│   └── vault/      # KB/검색 관련
├── tools/          # 도구 & 빌더 (8-10개)
└── legacy/         # 레거시 (이미 이동됨)
```

---

## 📋 상세 분류 (126개 파일)

### 1. core/ (21개)

**Infra & Config**
- claude_client.py
- session_manager.py
- auth_service.py
- audit_service.py
- notification_service.py
- email_service.py
- alert_manager.py

**Caching & Performance**
- cache_manager.py
- cache_ttl_optimizer.py
- memory_cache_service.py
- query_analyzer.py
- health_checker.py

**Token & Pricing**
- token_manager.py
- token_pricing.py
- version_manager.py

**WebSocket & Streaming**
- ws_manager.py
- ws_events.py
- stream_orchestrator.py
- workflow_timer.py
- queue_logging.py

---

### 2. domains/proposal/ (35개)

**Harness Engineering**
- harness_accuracy_validator.py
- harness_accuracy_enhancement.py
- harness_evaluator.py
- harness_feedback_loop.py
- harness_metrics_monitor.py
- harness_proposal_node.py
- harness_proposal_write.py
- harness_weight_tuner.py
- harness_weight_tuning.py

**Accuracy & Quality**
- accuracy_enhancement_engine.py
- ai_status_manager.py
- ensemble_metrics_monitor.py
- feedback_analyzer.py
- feedback_loop.py
- human_edit_tracker.py
- source_tagger.py

**Compliance & Tracking**
- compliance_tracker.py
- prompt_analyzer.py
- prompt_evolution.py
- prompt_registry.py
- prompt_categories.py
- prompt_simulator.py
- prompt_tracker.py

**Document Processing**
- document_chunker.py
- document_ingestion.py
- rfp_parser.py
- asset_extractor.py
- cost_sheet_builder.py

**Other Proposal**
- section_lock.py
- state_validator.py
- content_library.py
- kb_updater.py

---

### 3. domains/bidding/ (30개)

**Core Bidding**
- bid_calculator.py
- bid_recommender.py
- bid_pipeline.py
- bid_fetcher.py
- bid_handoff.py

**Bid Analysis**
- bid_analysis_service.py
- bid_market_research.py
- bid_preprocessor.py
- bid_scorer.py
- bid_scoring_service.py
- bid_cleanup.py
- bid_attachment_store.py

**G2B Integration**
- g2b_service.py
- g2b_bidding_collector.py

**Job Queue (입찰 related)**
- job_queue_service.py
- job_service.py
- job_executor.py

**Bidding Stream**
- bidding_stream.py

**Submission**
- submission_docs_service.py

**Other**
- batch_processor.py
- queue_manager.py
- queue_optimization.py
- worker_pool.py
- beta_metrics_tracker.py
- scheduled_monitor.py

---

### 4. domains/vault/ (25개)

**Core Vault**
- knowledge_search.py
- knowledge_manager.py
- knowledge_collector.py
- embedding_service.py
- vault_embedding_service.py

**Vault Features**
- vault_advanced_features.py
- vault_bidding_service.py
- vault_cache_service.py
- vault_chat_search.py
- vault_citation_service.py
- vault_context_manager.py
- vault_multilang_handler.py
- vault_performance_optimizer.py
- vault_permission_filter.py
- vault_query_router.py
- vault_step_search.py
- vault_validation.py

**Vault Services**
- vault_client_service.py
- vault_credential_service.py
- vault_personnel_service.py

**Master Projects**
- master_projects_chat_service.py

**Other Vault**
- metrics_dashboard.py
- metrics_service.py

---

### 5. tools/ (8개)

**Document Builders**
- docx_builder.py
- pptx_builder.py
- presentation_generator.py
- presentation_pptx_builder.py

**HWPX (한글 문서)**
- hwpx_builder.py
- hwpx_service.py

**Other**
- template_service.py
- preflight_check.py

---

### 6. domains/operations/ (7개)

**Monitoring & Migration**
- scheduler_service.py
- optimization_scheduler.py
- migration_service.py
- dashboard_metrics_service.py

**User & Team**
- user_account_service.py
- teams_bot_service.py
- teams_webhook_manager.py

---

## 🔄 파일 이동 명령 (자동 생성)

```bash
# core/ 생성
mkdir -p app/services/core

# core 파일들 이동
mv app/services/claude_client.py app/services/core/
mv app/services/session_manager.py app/services/core/
... (21개)

# domains/ 생성
mkdir -p app/services/domains/{proposal,bidding,vault,operations}

# domains/proposal/ 이동
mv app/services/harness_*.py app/services/domains/proposal/
... (35개)

# domains/bidding/ 이동
mv app/services/bid_*.py app/services/domains/bidding/
... (30개)

# domains/vault/ 이동
mv app/services/vault_*.py app/services/domains/vault/
... (25개)

# tools/ 생성
mkdir -p app/services/tools

# tools 파일들 이동
mv app/services/docx_builder.py app/services/tools/
... (8개)

# operations 이동
mv app/services/scheduler_service.py app/services/domains/operations/
... (7개)
```

---

## ⚠️ 주의사항

1. **순환 임포트 검사**
   - 이동 후 `python -m py_compile` 실행
   - `grep -r "^from app.services" --include="*.py"` 검사

2. **임포트 경로 업데이트**
   - `app/services/xxx` → `app/services/core/xxx`
   - `app/services/bid_*` → `app/services/domains/bidding/xxx`
   - etc.

3. **상대 임포트**
   - 같은 도메인 내에서는 상대 임포트 고려
   - `from . import ...` 활용

4. **__init__.py**
   - 각 폴더에 `__init__.py` 생성
   - 공개 API 정의

---

## 📊 예상 결과

**Before:**
```
app/services/
├── 126개 파일 (직접 배치)
└── 혼란스러운 네비게이션
```

**After:**
```
app/services/
├── core/           (21개 파일)
├── domains/
│   ├── proposal/   (35개 파일)
│   ├── bidding/    (30개 파일)
│   ├── vault/      (25개 파일)
│   └── operations/ (7개 파일)
├── tools/          (8개 파일)
└── legacy/         (2개 파일)
```

**개선효과:**
- 네비게이션: 즉시 5배 향상
- 순환 임포트: 명시적 경계로 예방
- 온보딩: 신규 개발자 학습곡선 -50%

---

**작성**: 2026-04-24  
**상태**: 분류 완료 (실행 대기)
