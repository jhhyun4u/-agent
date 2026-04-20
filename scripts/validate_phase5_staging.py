#!/usr/bin/env python3
"""Phase 5 Staging Deployment Validation Script"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def validate_files():
    """Check all required files exist"""
    files = [
        "database/migrations/006_scheduler_integration.sql",
        "app/services/scheduler_service.py",
        "app/services/batch_processor.py",
        "app/api/routes_migration.py",
        "tests/test_scheduler_integration.py",
    ]

    results = []
    for f in files:
        exists = os.path.exists(f)
        status = "PASS" if exists else "FAIL"
        print(f"[{status}] File exists: {f}")
        results.append(exists)

    return all(results)


def validate_sql_migration():
    """Check SQL migration has required tables"""
    with open("database/migrations/006_scheduler_integration.sql", encoding="utf-8") as f:
        sql = f.read()

    required = ["migration_schedules", "migration_batches", "migration_logs"]
    results = []
    for table in required:
        found = table in sql
        status = "PASS" if found else "FAIL"
        print(f"[{status}] Table {table} defined in migration")
        results.append(found)

    # Check for indices
    indices_count = sql.count("CREATE INDEX")
    status = "PASS" if indices_count >= 8 else "FAIL"
    print(f"[{status}] {indices_count} indices created (expected 8+)")
    results.append(indices_count >= 8)

    return all(results)


def validate_app_integration():
    """Check app.main.py has scheduler integration"""
    with open("app/main.py", encoding="utf-8") as f:
        content = f.read()

    checks = {
        "migration_scheduler_router registered": "migration_scheduler_router" in content,
        "SchedulerService imported": "SchedulerService" in content,
        "Scheduler initialization": "scheduler_service.initialize" in content,
    }

    results = []
    for check, found in checks.items():
        status = "PASS" if found else "FAIL"
        print(f"[{status}] {check}")
        results.append(found)

    return all(results)


def validate_routes_definition():
    """Check routes are properly defined"""
    with open("app/api/routes_migration.py", encoding="utf-8") as f:
        content = f.read()

    endpoints = [
        "/schedules",
        "/trigger/",
        "/batches",
    ]

    results = []
    for endpoint in endpoints:
        found = endpoint in content
        status = "PASS" if found else "FAIL"
        print(f"[{status}] Endpoint {endpoint} defined")
        results.append(found)

    return all(results)


def main():
    print("\n" + "=" * 60)
    print("Phase 5 Scheduler Integration - Staging Validation")
    print("=" * 60 + "\n")

    print("Step 1: File Existence Check")
    check1 = validate_files()
    print()

    print("Step 2: Database Migration Validation")
    check2 = validate_sql_migration()
    print()

    print("Step 3: App Integration Check")
    check3 = validate_app_integration()
    print()

    print("Step 4: API Routes Definition Check")
    check4 = validate_routes_definition()
    print()

    # Summary
    all_passed = check1 and check2 and check3 and check4

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    if all_passed:
        print("[PASS] All validation checks passed")
        print("\nReady for staging deployment!")
        print("Next: Execute database migration on staging database")
        return 0
    else:
        print("[FAIL] Some validation checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
