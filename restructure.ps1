#!/usr/bin/env pwsh
# 프로젝트 디렉토리 구조 정리 스크립트
# 모든 파일을 -agent-master에서 루트로 이동

$ErrorActionPreference = "Stop"
$sourceDir = "C:\project\tenopa proposer\-agent-master"
$rootDir = "C:\project\tenopa proposer"
$logFile = "$rootDir\restructure.log"

function Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage
    Add-Content -Path $logFile -Value $logMessage
}

function SafeMove {
    param([string]$Source, [string]$Dest)
    try {
        if (Test-Path $Source) {
            $sourceName = Split-Path $Source -Leaf
            Log "이동 중: $sourceName"
            Move-Item -Path $Source -Destination $Dest -Force
            Log "  ✓ 완료: $sourceName"
            return $true
        }
    } catch {
        Log "  ✗ 오류: $($_.Exception.Message)"
        return $false
    }
    return $true
}

function SafeDelete {
    param([string]$Path)
    try {
        if (Test-Path $Path) {
            $itemName = Split-Path $Path -Leaf
            Log "삭제 중: $itemName"
            Remove-Item -Path $Path -Recurse -Force
            Log "  ✓ 완료: $itemName"
            return $true
        }
    } catch {
        Log "  ✗ 오류: $($_.Exception.Message)"
        return $false
    }
    return $true
}

# ===== 시작 =====
Log "================================"
Log "프로젝트 구조 정리 시작"
Log "================================"
Log "소스: $sourceDir"
Log "대상: $rootDir"

# Phase 1: 캐시 폴더 삭제
Log ""
Log "=== Phase 1: 캐시 폴더 정리 ==="
@('.mypy_cache', '.pytest_cache', '.ruff_cache', 'test-results') | ForEach-Object {
    SafeDelete "$sourceDir\$_"
}

# 이상한 폴더들 삭제
SafeDelete "$sourceDir\-p"

# Phase 2: 핵심 폴더 이동
Log ""
Log "=== Phase 2: 핵심 폴더 이동 ==="
@('app', 'frontend', 'tests', 'database', 'docs', 'scripts', 'monitoring', 'supabase', 'data') | ForEach-Object {
    SafeMove "$sourceDir\$_" "$rootDir\$_"
}

# 숨김 폴더들
@('.github', '.bkit', '.serena') | ForEach-Object {
    SafeMove "$sourceDir\$_" "$rootDir\$_"
}

# Phase 3: 핵심 파일 이동
Log ""
Log "=== Phase 3: 핵심 파일 이동 ==="
@('pyproject.toml', 'uv.lock', 'Dockerfile', 'docker-compose.yml', 'docker-compose.monitoring.yml', 'docker-compose.logging.yml', '.gitignore', 'CLAUDE.md', '.env', '.env.example', '.env.production.example', '.dockerignore', '.pdca-status.json', '.bkit-memory.json') | ForEach-Object {
    SafeMove "$sourceDir\$_" "$rootDir\$_"
}

# Phase 4: .git 폴더 이동 (최중요!)
Log ""
Log "=== Phase 4: Git 저장소 이동 ==="
SafeMove "$sourceDir\.git" "$rootDir\.git"

# Phase 5: 임시 출력 폴더 정리
Log ""
Log "=== Phase 5: 임시 폴더 정리 ==="
SafeDelete "$rootDir\mindvault-out"
SafeDelete "$rootDir\output"
SafeDelete "$rootDir\tmp_screenshots"

# Phase 6: .gitignore 업데이트
Log ""
Log "=== Phase 6: .gitignore 업데이트 ==="
$gitignorePath = "$rootDir\.gitignore"
$tempRules = @"

# 임시 출력 폴더
/mindvault-out/
/output/
/tmp_screenshots/

# 개발 환경
.venv/
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.next/
node_modules/
*.tar
*.log
"@

try {
    if (Test-Path $gitignorePath) {
        $content = Get-Content $gitignorePath -Raw
        if (-not $content.Contains("mindvault-out")) {
            Add-Content -Path $gitignorePath -Value $tempRules
            Log ".gitignore 업데이트 완료"
        } else {
            Log ".gitignore 이미 최신 (변경 불필요)"
        }
    } else {
        Set-Content -Path $gitignorePath -Value $tempRules
        Log ".gitignore 새로 생성"
    }
} catch {
    Log ".gitignore 업데이트 오류: $($_.Exception.Message)"
}

# Phase 7: -agent-master 폴더 정리
Log ""
Log "=== Phase 7: -agent-master 폴더 정리 ==="
try {
    if (Test-Path $sourceDir) {
        $itemCount = @(Get-ChildItem -Path $sourceDir -Recurse).Count
        if ($itemCount -eq 0) {
            Log "-agent-master 폴더 비어있음 - 삭제 중..."
            Remove-Item -Path $sourceDir -Force
            Log "✓ -agent-master 폴더 삭제 완료"
        } else {
            Log "⚠️ -agent-master 폴더에 아직 $itemCount개 항목 있음 (수동 정리 필요)"
            Get-ChildItem -Path $sourceDir | ForEach-Object {
                Log "  - $($_.Name)"
            }
        }
    }
} catch {
    Log "⚠️ -agent-master 폴더 정리 오류: $($_.Exception.Message)"
}

# 최종 검증
Log ""
Log "=== 최종 검증 ==="
$rootItems = @(Get-ChildItem -Path $rootDir -Directory | Where-Object {$_.Name -in @('app', 'frontend', 'tests', 'database', '.github')})
$fileItems = @(Get-ChildItem -Path $rootDir -File | Where-Object {$_.Name -in @('pyproject.toml', 'Dockerfile', 'docker-compose.yml')})

if ($rootItems.Count -ge 5 -and $fileItems.Count -ge 3) {
    Log "✓ 주요 폴더/파일 이동 확인됨"
    Log ""
    Log "================================"
    Log "✓ 구조 정리 완료!"
    Log "================================"
    Log "다음 단계:"
    Log "1. Git 상태 확인: git status"
    Log "2. Python 의존성 설치: uv sync"
    Log "3. Docker 빌드 테스트: docker build ."
    Log "4. 임포트 오류 확인: Python 스크립트 실행"
} else {
    Log "✗ 오류: 주요 항목이 이동되지 않았습니다"
    Log "  폴더: $($rootItems.Count)/5 "
    Log "  파일: $($fileItems.Count)/3"
}

Log ""
Log "로그 파일: $logFile"
