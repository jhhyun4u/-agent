# MockResponse & __init__
Cohesion: 1.00 | Nodes: 2

## Key Nodes
- **MockResponse** (C:\project\tenopa proposer\-agent-master\tests\integration\conftest.py) -- 2 connections
  - -> contains -> [[init]]
  - <- contains <- [[conftest]]
- **__init__** (C:\project\tenopa proposer\-agent-master\tests\integration\conftest.py) -- 1 connections
  - <- contains <- [[mockresponse]]

## Internal Relationships
- MockResponse -> contains -> __init__ [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 MockResponse, __init__를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 conftest.py이다.

### Key Facts
- class MockResponse: """Mock response object with .data attribute""" def __init__(self, data): self.data = data
- class MockResponse: """Mock response object with .data attribute""" def __init__(self, data): self.data = data
