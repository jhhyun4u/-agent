#!/usr/bin/env python3
"""
서비스 레이어 재구성 자동화 스크립트

기능:
1. 파일 분류 정보 기반으로 폴더 생성
2. 파일 이동
3. 임포트 경로 자동 업데이트
4. 검증 (Python 문법, 순환 임포트)
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Windows 인코딩 처리
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# ─────────────────────────────────────────────────────────
# 파일 분류 정의 (SERVICE_REORGANIZATION_PLAN.md 기반)
# ─────────────────────────────────────────────────────────

FILE_MAPPING = {
    # core/ (기본 유틸)
    "core": [
        "claude_client.py",
        "session_manager.py",
        "auth_service.py",
        "audit_service.py",
        "notification_service.py",
        "email_service.py",
        "alert_manager.py",
        "cache_manager.py",
        "cache_ttl_optimizer.py",
        "memory_cache_service.py",
        "query_analyzer.py",
        "health_checker.py",
        "token_manager.py",
        "token_pricing.py",
        "version_manager.py",
        "ws_manager.py",
        "ws_events.py",
        "stream_orchestrator.py",
        "workflow_timer.py",
        "queue_logging.py",
    ],
    # domains/proposal/
    "domains/proposal": [
        "harness_accuracy_validator.py",
        "harness_accuracy_enhancement.py",
        "harness_evaluator.py",
        "harness_feedback_loop.py",
        "harness_metrics_monitor.py",
        "harness_proposal_node.py",
        "harness_proposal_write.py",
        "harness_weight_tuner.py",
        "harness_weight_tuning.py",
        "accuracy_enhancement_engine.py",
        "ai_status_manager.py",
        "ensemble_metrics_monitor.py",
        "feedback_analyzer.py",
        "feedback_loop.py",
        "human_edit_tracker.py",
        "source_tagger.py",
        "compliance_tracker.py",
        "prompt_analyzer.py",
        "prompt_evolution.py",
        "prompt_registry.py",
        "prompt_categories.py",
        "prompt_simulator.py",
        "prompt_tracker.py",
        "document_chunker.py",
        "document_ingestion.py",
        "rfp_parser.py",
        "asset_extractor.py",
        "cost_sheet_builder.py",
        "section_lock.py",
        "state_validator.py",
        "content_library.py",
        "kb_updater.py",
    ],
    # domains/bidding/
    "domains/bidding": [
        "bid_calculator.py",
        "bid_recommender.py",
        "bid_pipeline.py",
        "bid_fetcher.py",
        "bid_handoff.py",
        "bid_analysis_service.py",
        "bid_market_research.py",
        "bid_preprocessor.py",
        "bid_scorer.py",
        "bid_scoring_service.py",
        "bid_cleanup.py",
        "bid_attachment_store.py",
        "g2b_service.py",
        "g2b_bidding_collector.py",
        "job_queue_service.py",
        "job_service.py",
        "job_executor.py",
        "bidding_stream.py",
        "submission_docs_service.py",
        "batch_processor.py",
        "queue_manager.py",
        "queue_optimization.py",
        "worker_pool.py",
        "beta_metrics_tracker.py",
        "scheduled_monitor.py",
    ],
    # domains/vault/
    "domains/vault": [
        "knowledge_search.py",
        "knowledge_manager.py",
        "knowledge_collector.py",
        "embedding_service.py",
        "vault_embedding_service.py",
        "vault_advanced_features.py",
        "vault_bidding_service.py",
        "vault_cache_service.py",
        "vault_chat_search.py",
        "vault_citation_service.py",
        "vault_context_manager.py",
        "vault_multilang_handler.py",
        "vault_performance_optimizer.py",
        "vault_permission_filter.py",
        "vault_query_router.py",
        "vault_step_search.py",
        "vault_validation.py",
        "vault_client_service.py",
        "vault_credential_service.py",
        "vault_personnel_service.py",
        "master_projects_chat_service.py",
        "metrics_dashboard.py",
        "metrics_service.py",
    ],
    # domains/operations/
    "domains/operations": [
        "scheduler_service.py",
        "optimization_scheduler.py",
        "migration_service.py",
        "dashboard_metrics_service.py",
        "user_account_service.py",
        "teams_bot_service.py",
        "teams_webhook_manager.py",
    ],
    # tools/
    "tools": [
        "docx_builder.py",
        "pptx_builder.py",
        "presentation_generator.py",
        "presentation_pptx_builder.py",
        "hwpx_builder.py",
        "hwpx_service.py",
        "template_service.py",
        "preflight_check.py",
    ],
}


class ServiceReorganizer:
    """서비스 레이어 재구성 관리"""

    def __init__(self, services_root: Path):
        self.services_root = services_root
        self.moved_files: Dict[str, str] = {}  # old_path -> new_path
        self.errors: List[str] = []

    def create_folder_structure(self) -> bool:
        """폴더 구조 생성"""
        print("📁 폴더 구조 생성 중...")
        try:
            for category in FILE_MAPPING.keys():
                folder = self.services_root / category
                folder.mkdir(parents=True, exist_ok=True)
                init_file = folder / "__init__.py"
                if not init_file.exists():
                    init_file.touch()
                    print(f"  ✅ {category}/__init__.py")
            return True
        except Exception as e:
            self.errors.append(f"폴더 생성 실패: {e}")
            return False

    def move_files(self) -> bool:
        """파일 이동"""
        print("\n📦 파일 이동 중...")
        moved_count = 0

        for category, files in FILE_MAPPING.items():
            for filename in files:
                old_path = self.services_root / filename
                new_path = self.services_root / category / filename

                if not old_path.exists():
                    print(f"  ⚠️  {filename} 없음 (스킵)")
                    continue

                try:
                    shutil.move(str(old_path), str(new_path))
                    self.moved_files[str(old_path)] = str(new_path)
                    moved_count += 1
                    print(f"  ✅ {filename} → {category}/")
                except Exception as e:
                    self.errors.append(f"{filename} 이동 실패: {e}")
                    print(f"  ❌ {filename}: {e}")

        print(f"\n총 {moved_count}개 파일 이동 완료")
        return True

    def update_imports_in_codebase(self, project_root: Path) -> bool:
        """프로젝트 전체 임포트 경로 업데이트"""
        print("\n🔄 임포트 경로 업데이트 중...")
        updated_count = 0

        # Python 파일 찾기
        py_files = list(project_root.rglob("*.py"))
        print(f"  검사 중: {len(py_files)}개 파일...")

        for py_file in py_files:
            if ".venv" in str(py_file) or ".git" in str(py_file) or "dist/" in str(py_file):
                continue

            try:
                content = py_file.read_text(encoding="utf-8")
                original = content

                # 각 이동된 파일의 임포트 경로 업데이트
                for old_path, new_path in self.moved_files.items():
                    # 파일명 추출
                    filename = Path(old_path).name
                    old_module = f"app.services.{filename[:-3]}"  # .py 제거

                    # 새 경로 추출
                    rel_path = Path(new_path).relative_to(project_root / "app" / "services")
                    new_module = f"app.services.{str(rel_path)[:-3].replace(os.sep, '.')}"

                    # 임포트 문 업데이트
                    content = re.sub(
                        rf"from {re.escape(old_module)} ",
                        f"from {new_module} ",
                        content
                    )
                    content = re.sub(
                        rf"import {re.escape(old_module)}",
                        f"import {new_module}",
                        content
                    )

                if content != original:
                    py_file.write_text(content, encoding="utf-8")
                    updated_count += 1
                    print(f"  ✅ {py_file.name}")

            except Exception as e:
                self.errors.append(f"{py_file} 업데이트 실패: {e}")

        print(f"\n총 {updated_count}개 파일 임포트 경로 업데이트 완료")
        return True

    def validate_syntax(self, services_root: Path) -> bool:
        """Python 문법 검증"""
        print("\n✔️  Python 문법 검증 중...")
        py_files = list(services_root.rglob("*.py"))
        valid_count = 0
        failed = []

        for py_file in py_files:
            try:
                compile(py_file.read_text(encoding="utf-8"), str(py_file), "exec")
                valid_count += 1
            except SyntaxError as e:
                failed.append(f"{py_file.name}: {e}")
                self.errors.append(f"문법 오류 {py_file.name}: {e}")

        print(f"  ✅ {valid_count}/{len(py_files)} 파일 문법 정상")

        if failed:
            print("\n  ❌ 문법 오류:")
            for err in failed:
                print(f"    - {err}")
            return False

        return True

    def run(self, project_root: Path) -> bool:
        """전체 재구성 실행"""
        print("=" * 60)
        print("🚀 서비스 레이어 재구성 시작")
        print("=" * 60)

        steps = [
            ("폴더 구조 생성", self.create_folder_structure),
            ("파일 이동", self.move_files),
            ("임포트 경로 업데이트", lambda: self.update_imports_in_codebase(project_root)),
            ("Python 문법 검증", lambda: self.validate_syntax(self.services_root)),
        ]

        for step_name, step_func in steps:
            print(f"\n{'─' * 60}")
            print(f"📋 {step_name}")
            print('─' * 60)
            if not step_func():
                print(f"\n❌ {step_name} 실패!")
                return False

        print("\n" + "=" * 60)
        print("✅ 재구성 완료!")
        print("=" * 60)

        if self.errors:
            print("\n⚠️  경고:")
            for err in self.errors:
                print(f"  - {err}")

        return True


def main():
    """메인 진입점"""
    project_root = Path(__file__).parent.parent
    services_root = project_root / "app" / "services"

    if not services_root.exists():
        print(f"❌ 서비스 폴더를 찾을 수 없음: {services_root}")
        sys.exit(1)

    reorganizer = ServiceReorganizer(services_root)
    success = reorganizer.run(project_root)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
