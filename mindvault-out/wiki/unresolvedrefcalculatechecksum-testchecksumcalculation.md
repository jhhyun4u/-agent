# __unresolved__::ref::_calculate_checksum & TestChecksumCalculation
Cohesion: 0.60 | Nodes: 5

## Key Nodes
- **__unresolved__::ref::_calculate_checksum** () -- 4 connections
  - <- calls <- [[executenodeandcreateversion]]
  - <- calls <- [[testchecksumconsistency]]
  - <- calls <- [[testchecksumdiffersonchange]]
  - <- calls <- [[testchecksumorderinsensitive]]
- **TestChecksumCalculation** (C:\project\tenopa proposer\-agent-master\tests\test_artifact_versioning.py) -- 4 connections
  - -> contains -> [[testchecksumconsistency]]
  - -> contains -> [[testchecksumdiffersonchange]]
  - -> contains -> [[testchecksumorderinsensitive]]
  - <- contains <- [[testartifactversioning]]
- **test_checksum_consistency** (C:\project\tenopa proposer\-agent-master\tests\test_artifact_versioning.py) -- 2 connections
  - -> calls -> [[unresolvedrefcalculatechecksum]]
  - <- contains <- [[testchecksumcalculation]]
- **test_checksum_differs_on_change** (C:\project\tenopa proposer\-agent-master\tests\test_artifact_versioning.py) -- 2 connections
  - -> calls -> [[unresolvedrefcalculatechecksum]]
  - <- contains <- [[testchecksumcalculation]]
- **test_checksum_order_insensitive** (C:\project\tenopa proposer\-agent-master\tests\test_artifact_versioning.py) -- 2 connections
  - -> calls -> [[unresolvedrefcalculatechecksum]]
  - <- contains <- [[testchecksumcalculation]]

## Internal Relationships
- TestChecksumCalculation -> contains -> test_checksum_consistency [EXTRACTED]
- TestChecksumCalculation -> contains -> test_checksum_differs_on_change [EXTRACTED]
- TestChecksumCalculation -> contains -> test_checksum_order_insensitive [EXTRACTED]
- test_checksum_consistency -> calls -> __unresolved__::ref::_calculate_checksum [EXTRACTED]
- test_checksum_differs_on_change -> calls -> __unresolved__::ref::_calculate_checksum [EXTRACTED]
- test_checksum_order_insensitive -> calls -> __unresolved__::ref::_calculate_checksum [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 __unresolved__::ref::_calculate_checksum, TestChecksumCalculation, test_checksum_consistency를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 test_artifact_versioning.py이다.

### Key Facts
- class TestChecksumCalculation: """Test checksum-based duplicate detection."""
- def test_checksum_consistency(self): """Checksum should be consistent for same data.""" data = {"title": "Test", "content": "Content"} checksum1 = _calculate_checksum(data) checksum2 = _calculate_checksum(data)
- def test_checksum_differs_on_change(self): """Checksum should differ when data changes.""" data1 = {"title": "Test1"} data2 = {"title": "Test2"}
- def test_checksum_order_insensitive(self): """Checksum should be same regardless of dict key order.""" data1 = {"a": 1, "b": 2, "c": 3} data2 = {"c": 3, "a": 1, "b": 2}
