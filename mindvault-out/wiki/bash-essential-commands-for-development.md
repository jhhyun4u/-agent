# bash & Essential Commands for Development
Cohesion: 0.43 | Nodes: 8

## Key Nodes
- **bash** (C:\project\tenopa proposer\.serena\memories\suggested_commands.md) -- 6 connections
  - <- has_code_example <- [[project-setup]]
  - <- has_code_example <- [[testing-commands]]
  - <- has_code_example <- [[database-and-migrations]]
  - <- has_code_example <- [[monitoring-and-logs]]
  - <- has_code_example <- [[verification-commands]]
  - <- has_code_example <- [[code-quality]]
- **Essential Commands for Development** (C:\project\tenopa proposer\.serena\memories\suggested_commands.md) -- 6 connections
  - -> contains -> [[project-setup]]
  - -> contains -> [[testing-commands]]
  - -> contains -> [[database-and-migrations]]
  - -> contains -> [[monitoring-and-logs]]
  - -> contains -> [[verification-commands]]
  - -> contains -> [[code-quality]]
- **Code Quality** (C:\project\tenopa proposer\.serena\memories\suggested_commands.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[essential-commands-for-development]]
- **Database and Migrations** (C:\project\tenopa proposer\.serena\memories\suggested_commands.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[essential-commands-for-development]]
- **Monitoring and Logs** (C:\project\tenopa proposer\.serena\memories\suggested_commands.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[essential-commands-for-development]]
- **Project Setup** (C:\project\tenopa proposer\.serena\memories\suggested_commands.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[essential-commands-for-development]]
- **Testing Commands** (C:\project\tenopa proposer\.serena\memories\suggested_commands.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[essential-commands-for-development]]
- **Verification Commands** (C:\project\tenopa proposer\.serena\memories\suggested_commands.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[essential-commands-for-development]]

## Internal Relationships
- Code Quality -> has_code_example -> bash [EXTRACTED]
- Database and Migrations -> has_code_example -> bash [EXTRACTED]
- Essential Commands for Development -> contains -> Project Setup [EXTRACTED]
- Essential Commands for Development -> contains -> Testing Commands [EXTRACTED]
- Essential Commands for Development -> contains -> Database and Migrations [EXTRACTED]
- Essential Commands for Development -> contains -> Monitoring and Logs [EXTRACTED]
- Essential Commands for Development -> contains -> Verification Commands [EXTRACTED]
- Essential Commands for Development -> contains -> Code Quality [EXTRACTED]
- Monitoring and Logs -> has_code_example -> bash [EXTRACTED]
- Project Setup -> has_code_example -> bash [EXTRACTED]
- Testing Commands -> has_code_example -> bash [EXTRACTED]
- Verification Commands -> has_code_example -> bash [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 bash, Essential Commands for Development, Code Quality를 중심으로 has_code_example 관계로 연결되어 있다. 주요 소스 파일은 suggested_commands.md이다.

### Key Facts
- Project Setup ```bash Navigate to project cd c:\project\tenopa proposer\-agent-master
- Project Setup ```bash Navigate to project cd c:\project\tenopa proposer\-agent-master
- Linting ruff check app/ tests/
- Check current schema psql -d tenopa_db -c "\dt"     # PostgreSQL/Supabase ```
- Check frontend logs tail -f frontend.log
