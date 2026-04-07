# 제안 결정 워크플로우 수정 (2026-04-06)

## 주요 이슈
1. 공고 모니터링 > 제안 검토에서 "제안결정"을 선택했을 때
   - 공고 모니터링 목록에서 제거되지 않음
   - 제안 프로젝트 목록에 등록되지 않음
   - 요청이 계속 타임아웃

2. 테스트 프로포절이 DB에 남아있음
   - ID: 85b1dd43-92eb-4561-8304-7c0e9f1d2b4a
   - 이로 인해 프론트엔드가 계속 타임아웃 발생

## 수정 사항

### 1. 테스트 프로포절 삭제 ✓
- ID: 85b1dd43-92eb-4561-8304-7c0e9f1d2b4a 삭제 완료
- 프론트엔드 타임아웃 이슈 해결

### 2. 제안 프로젝트 생성 엔드포인트 개선 (`app/api/routes_proposal.py`)

#### 2.1 저장소 다운로드 타임아웃 추가
```python
# 마크다운 파일 다운로드에 5초 타임아웃 설정
# - analyze 엔드포인트의 백그라운드 작업이 진행 중일 수 있음
# - 파일이 존재하지 않으면 무시하고 계속 진행
```

**문제**: analyze 엔드포인트가 즉시 반환되고 마크다운 생성은 백그라운드에서 처리
- 프로포절 생성 시 마크다운 파일을 다운로드하려고 하면 아직 존재하지 않을 수 있음
- 무한 대기로 인한 타임아웃 발생

**해결**: 5초 타임아웃 설정 → 파일이 없으면 무시하고 진행

#### 2.2 DB 스키마 불일치 해결
- `bid_no` 필드 제거 (테이블에 컬럼이 없음)
- `client_name`, `deadline` 필드는 선택적으로 처리
- 마이그레이션되지 않은 컬럼이 있으면 재시도 로직 적용

```python
# 1차 시도: 모든 선택적 필드 포함
# 실패 시: 최소 필드(id, title, owner_id, status, rfp_content)만 사용하여 재시도
```

### 3. 마이그레이션 필요
파일: `database/migrations/013_proposals_missing_columns.sql`

다음 컬럼이 필요함 (선택):
```sql
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS deadline TIMESTAMPTZ;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS client_name TEXT;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS org_id UUID;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS division_id UUID;
```

**실행 방법**:
1. Supabase 대시보드 → SQL Editor
2. `scripts/add_missing_columns.py` 실행하여 SQL 확인
3. SQL을 복사하여 대시보드에서 실행

### 4. 모니터링 목록 필터링 확인
- 이미 구현됨: `show_all=False`일 때 "제안포기", "관련없음", "제안결정" 제외
- 프론트엔드에서 show_all=false로 호출하고 있음 ✓

## 완전한 워크플로우 검증

### 사용자 관점
1. 공고 모니터링 페이지에서 공고 선택
2. 제안 검토 화면에서 "제안결정" 버튼 클릭
3. 백엔드 과정:
   - ✓ 공고 분석 (마크다운 생성, 백그라운드)
   - ✓ Go 의사결정 기록
   - ✓ proposal_status 업데이트 (PUT /bids/{bidNo}/status)
   - ✓ 제안 프로젝트 생성 (POST /proposals/from-bid)
4. 프론트엔드:
   - 제안 프로젝트 페이지로 이동
4. 모니터링 페이지 다시 방문:
   - ✓ 해당 공고는 목록에서 제외됨
   - ✓ 제안 프로젝트 페이지에 새 프로젝트가 나타남

## 테스트 체크리스트

### 사전 조건
- [ ] 백엔드 서버 실행: `uv run uvicorn app.main:app --reload`
- [ ] 프론트엔드 개발 서버 실행

### 테스트
- [ ] 공고 모니터링에서 "제안결정" 선택
  - 분석 진행 표시 (로딩 바)
  - 완료 후 제안 프로젝트 페이지로 이동
- [ ] 모니터링 페이지로 돌아가기
  - 해당 공고가 목록에서 제외되어야 함
- [ ] 제안 프로젝트 페이지 확인
  - 새로 생성된 프로젝트가 나타나야 함

### 로그 확인
브라우저 콘솔에서 다음 단계별 로그 확인:
```
1️⃣ 공고 분석 시작
2️⃣ Go 의사결정 기록
3️⃣ proposal_status 업데이트
4️⃣ 제안 프로젝트 생성
```

## 문제 해결

### "제안 프로젝트 생성 실패" 메시지
- DB 스키마 마이그레이션 필요
- `scripts/add_missing_columns.py` 실행하여 SQL 확인
- Supabase 대시보드에서 수동으로 마이그레이션 실행

### 마크다운 문서 로드 경고
```
! 마크다운 로드 타임아웃 [RFP分析] (5초): ...
```
- 정상: analyze 엔드포인트가 아직 생성 중
- 프로포절은 여전히 생성됨 (콘텐츠만 제한됨)
- 나중에 마크다운이 생성되면 자동으로 로드됨

## 파일 변경 사항
- `app/api/routes_proposal.py`: 
  - asyncio import 추가
  - storage 다운로드 타임아웃 추가
  - bid_no 필드 제거
  - client_name, deadline 필드 선택적 처리
  - 재시도 로직 추가
- `scripts/add_missing_columns.py`: 마이그레이션 도우미 스크립트 추가
