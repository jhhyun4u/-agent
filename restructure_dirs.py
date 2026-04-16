#!/usr/bin/env python3
import os
import shutil
from pathlib import Path

root_dir = Path("c:\\project\\tenopa proposer")
source_dir = root_dir / "-agent-master"

print("="*50)
print("Directory Restructuring Script")
print("="*50)

# Phase 1: Delete cache folders
print("\nPhase 1: Deleting cache folders...")
cache_dirs = ['.mypy_cache', '.pytest_cache', '.ruff_cache', 'test-results', '-p']
for cache_dir in cache_dirs:
    path = source_dir / cache_dir
    if path.exists():
        try:
            shutil.rmtree(path)
            print(f"  [OK] Deleted: {cache_dir}")
        except Exception as e:
            print(f"  [ERR] Error deleting {cache_dir}: {e}")

# Phase 2: Move core directories
print("\nPhase 2: Moving core directories...")
core_dirs = ['app', 'frontend', 'tests', 'database', 'docs', 'scripts', 'monitoring', 'supabase', 'data']
for dir_name in core_dirs:
    src = source_dir / dir_name
    dst = root_dir / dir_name
    if src.exists() and not dst.exists():
        try:
            shutil.move(str(src), str(dst))
            print(f"  [OK] Moved: {dir_name}")
        except Exception as e:
            print(f"  [ERR] Error moving {dir_name}: {e}")

# Phase 3: Move hidden directories
print("\nPhase 3: Moving hidden directories...")
hidden_dirs = ['.github', '.bkit', '.serena', '.claude']
for dir_name in hidden_dirs:
    src = source_dir / dir_name
    dst = root_dir / dir_name
    if src.exists() and not dst.exists():
        try:
            shutil.move(str(src), str(dst))
            print(f"  [OK] Moved: {dir_name}")
        except Exception as e:
            print(f"  [ERR] Error moving {dir_name}: {e}")

# Phase 4: Move core files
print("\nPhase 4: Moving core files...")
core_files = [
    'pyproject.toml', 'uv.lock', 'Dockerfile',
    'docker-compose.yml', 'docker-compose.monitoring.yml', 'docker-compose.logging.yml',
    '.gitignore', 'CLAUDE.md', '.env', '.env.example', '.env.production.example',
    '.dockerignore', '.pdca-status.json', '.bkit-memory.json', 'README.md', 'vercel.json', 'mypy.ini'
]
for file_name in core_files:
    src = source_dir / file_name
    dst = root_dir / file_name
    if src.exists() and not dst.exists():
        try:
            shutil.move(str(src), str(dst))
            print(f"  [OK] Moved: {file_name}")
        except Exception as e:
            print(f"  [ERR] Error moving {file_name}: {e}")

# Phase 5: Move .git
print("\nPhase 5: Moving .git repository...")
src = source_dir / '.git'
dst = root_dir / '.git'
if src.exists() and not dst.exists():
    try:
        shutil.move(str(src), str(dst))
        print(f"  [OK] Moved: .git")
    except Exception as e:
        print(f"  [ERR] Error moving .git: {e}")

# Phase 6: Delete temp folders at root
print("\nPhase 6: Cleaning up temp folders...")
temp_dirs = ['mindvault-out', 'output', 'tmp_screenshots']
for temp_dir in temp_dirs:
    path = root_dir / temp_dir
    if path.exists():
        try:
            shutil.rmtree(path)
            print(f"  [OK] Deleted: {temp_dir}")
        except Exception as e:
            print(f"  [ERR] Error deleting {temp_dir}: {e}")

# Phase 7: Check if -agent-master is empty and delete it
print("\nPhase 7: Cleaning up -agent-master...")
try:
    if source_dir.exists():
        remaining_items = list(source_dir.iterdir())
        if len(remaining_items) == 0:
            shutil.rmtree(source_dir)
            print("  [OK] Deleted: -agent-master folder")
        else:
            print(f"  ⚠ Warning: -agent-master still has {len(remaining_items)} items")
            for item in remaining_items[:10]:
                print(f"    - {item.name}")
            if len(remaining_items) > 10:
                print(f"    ... and {len(remaining_items)-10} more")
except Exception as e:
    print(f"  [ERR] Error: {e}")

# Phase 8: Verification
print("\nPhase 8: Verification...")
major_dirs = ['app', 'frontend', 'tests', 'database', '.github']
present = sum(1 for dir_name in major_dirs if (root_dir / dir_name).exists())
print(f"  Major directories present: {present}/5")

if present >= 4:
    print("\n" + "="*50)
    print("[OK] Restructuring completed successfully!")
    print("="*50)
    print("\nNext steps:")
    print("1. Check git status: git status")
    print("2. Install Python deps: uv sync")
    print("3. Test Docker build: docker build .")
    print("4. Check imports: python -c 'from app.main import app'")
else:
    print("\n" + "="*50)
    print("[ERR] Some directories may not have moved correctly")
    print("="*50)
