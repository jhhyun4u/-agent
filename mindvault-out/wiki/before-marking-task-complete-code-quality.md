# Before Marking Task Complete & Code Quality
Cohesion: 0.22 | Nodes: 9

## Key Nodes
- **Before Marking Task Complete** (C:\project\tenopa proposer\.serena\memories\task_completion_checklist.md) -- 8 connections
  - -> contains -> [[code-quality]]
  - -> contains -> [[testing-80-minimum-coverage]]
  - -> contains -> [[performance]]
  - -> contains -> [[documentation]]
  - -> contains -> [[git-workflow]]
  - -> contains -> [[security]]
  - -> contains -> [[pre-merge-verification]]
  - <- contains <- [[task-completion-checklist]]
- **Code Quality** (C:\project\tenopa proposer\.serena\memories\task_completion_checklist.md) -- 1 connections
  - <- contains <- [[before-marking-task-complete]]
- **Documentation** (C:\project\tenopa proposer\.serena\memories\task_completion_checklist.md) -- 1 connections
  - <- contains <- [[before-marking-task-complete]]
- **Git Workflow** (C:\project\tenopa proposer\.serena\memories\task_completion_checklist.md) -- 1 connections
  - <- contains <- [[before-marking-task-complete]]
- **Performance** (C:\project\tenopa proposer\.serena\memories\task_completion_checklist.md) -- 1 connections
  - <- contains <- [[before-marking-task-complete]]
- **Pre-Merge Verification** (C:\project\tenopa proposer\.serena\memories\task_completion_checklist.md) -- 1 connections
  - <- contains <- [[before-marking-task-complete]]
- **Security** (C:\project\tenopa proposer\.serena\memories\task_completion_checklist.md) -- 1 connections
  - <- contains <- [[before-marking-task-complete]]
- **Task Completion Checklist** (C:\project\tenopa proposer\.serena\memories\task_completion_checklist.md) -- 1 connections
  - -> contains -> [[before-marking-task-complete]]
- **Testing (80% minimum coverage)** (C:\project\tenopa proposer\.serena\memories\task_completion_checklist.md) -- 1 connections
  - <- contains <- [[before-marking-task-complete]]

## Internal Relationships
- Before Marking Task Complete -> contains -> Code Quality [EXTRACTED]
- Before Marking Task Complete -> contains -> Testing (80% minimum coverage) [EXTRACTED]
- Before Marking Task Complete -> contains -> Performance [EXTRACTED]
- Before Marking Task Complete -> contains -> Documentation [EXTRACTED]
- Before Marking Task Complete -> contains -> Git Workflow [EXTRACTED]
- Before Marking Task Complete -> contains -> Security [EXTRACTED]
- Before Marking Task Complete -> contains -> Pre-Merge Verification [EXTRACTED]
- Task Completion Checklist -> contains -> Before Marking Task Complete [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Before Marking Task Complete, Code Quality, Documentation를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 task_completion_checklist.md이다.

### Key Facts
- Code Quality - [ ] Code is readable and well-named (snake_case functions, PascalCase classes) - [ ] Functions are focused (<50 lines preferred) - [ ] Files are cohesive (<800 lines preferred) - [ ] No deep nesting (>4 levels) - [ ] No hardcoded secrets or credentials - [ ] No console.log or debug…
- Testing (80% minimum coverage) - [ ] Unit tests written for new functions - [ ] Integration tests for API endpoints - [ ] Tests pass locally: `pytest tests/ -v` - [ ] Coverage verified: `pytest tests/ --cov=app` - [ ] Async tests use `@pytest.mark.asyncio` - [ ] Load tests verify performance…
- Git Workflow - [ ] Changes staged: `git add .` - [ ] Commit with meaningful message: `git commit -m "feat: description"` - [ ] Push to branch: `git push -u origin feature-branch` - [ ] PR created with: - Full commit history analyzed - Comprehensive summary - Test plan with TODOs - Performance…
- Security - [ ] No hardcoded API keys or secrets - [ ] All user inputs validated - [ ] SQL injection prevention (parameterized queries) - [ ] CORS and CSRF configured - [ ] Error messages don't leak sensitive info
- Testing (80% minimum coverage) - [ ] Unit tests written for new functions - [ ] Integration tests for API endpoints - [ ] Tests pass locally: `pytest tests/ -v` - [ ] Coverage verified: `pytest tests/ --cov=app` - [ ] Async tests use `@pytest.mark.asyncio` - [ ] Load tests verify performance…
