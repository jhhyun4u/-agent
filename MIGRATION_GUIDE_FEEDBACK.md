# Feedback Submissions 마이그레이션 가이드

## 📋 개요
STEP 4A Gap 3 (주간 피드백 분석) 기능을 위한 DB 마이그레이션

**파일**: `database/migrations/005_feedback_submissions.sql`

---

## 🚀 적용 방법

### 방법 1: Supabase 웹 콘솔 (권장)

1. [Supabase 대시보드](https://app.supabase.com) 접속
2. 프로젝트 선택
3. **SQL Editor** 탭 클릭
4. 새 쿼리 작성 (New Query)
5. `database/migrations/005_feedback_submissions.sql` 파일 내용 복사
6. 붙여넣기 후 **Run** 클릭

### 방법 2: CLI

```bash
# psql을 통한 직접 적용 (Supabase 연결 정보 필요)
psql \
  -h db.[PROJECT_ID].supabase.co \
  -U postgres \
  -d postgres \
  -f database/migrations/005_feedback_submissions.sql
```

연결 정보는 Supabase → Settings → Database 에서 확인

### 방법 3: Python 스크립트

```bash
uv run python scripts/migration_runner.py --migration 005_feedback_submissions
```

---

## ✅ 마이그레이션 확인

마이그레이션 적용 후 다음 명령으로 확인:

```bash
# Supabase SQL Editor에서 실행
SELECT * FROM feedback_submissions LIMIT 1;
```

성공: 0행 반환 (빈 테이블이 생성됨)  
실패: 테이블 없음 에러

---

## 📝 생성되는 객체

### 테이블
- `feedback_submissions` - 피드백 제출 기록

### 인덱스
- `idx_feedback_proposal` - proposal_id로 빠른 조회
- `idx_feedback_created_at` - 최신 피드백 먼저 조회
- `idx_feedback_section` - 섹션별 조회

### RLS (Row Level Security)
- 해당 제안서 조직 멤버만 조회 가능
- 인증된 사용자만 추가 가능
- 작성자만 수정/삭제 가능

### 트리거
- `update_feedback_submissions_updated_at` - updated_at 자동 갱신

---

## 🎯 테스트

마이그레이션 후 샘플 데이터 생성:

```bash
uv run python scripts/seed_feedback_data.py
```

출력:
```
✅ 피드백 테이블 확인 완료
✅ 피드백 데이터 생성 완료: 7개

📊 분석 결과:
  - 총 피드백: 7개
  - 전체 승인률: 57.1%
  - 주의 필요 섹션: technical_approach, cost_proposal
  - 우수 섹션: executive_summary, benefits
  - 권장사항: Minor adjustments recommended

✅ 완료!
```

---

## 🔄 API 테스트

마이그레이션 + 샘플 데이터 후 API 호출:

```bash
# 개발 서버 시작
uv run uvicorn app.main:app --reload

# 다른 터미널에서 API 테스트
curl -X POST http://localhost:8000/api/feedback/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"proposal_id": null, "days": 7}'
```

응답 예시:
```json
{
  "period": "weekly",
  "analysis_date": "2026-04-18T10:30:00",
  "total_feedback": 7,
  "section_stats": [
    {
      "section_type": "executive_summary",
      "total_feedback": 2,
      "approved": 2,
      "approval_rate": 1.0,
      "avg_hallucination": 4.65
    }
  ],
  "weight_recommendations": [...],
  "summary": {
    "overall_approval_rate": 0.571,
    "sections_needing_attention": ["technical_approach"],
    "sections_performing_well": ["executive_summary", "benefits"],
    "recommendations_count": 2,
    "next_action": "Minor adjustments recommended"
  }
}
```

---

## 🆘 문제 해결

### "permission denied" 에러
- Supabase 권한 확인
- Service Role Key 사용 확인

### "relation does not exist" 에러
- 마이그레이션이 완료되지 않음
- SQL Editor에서 마이그레이션 파일 다시 실행

### RLS 정책 오류
- organization_members 테이블 확인
- Azure AD 통합 완료 확인

---

## 📅 배포 일정

- **Staging**: 2026-04-20 배포 전 마이그레이션 적용
- **Production**: 2026-04-25 배포 전 마이그레이션 적용

---

## 📚 관련 파일

- 스키마: `database/migrations/005_feedback_submissions.sql`
- 라우터: `app/api/routes_feedback.py`
- 서비스: `app/services/feedback_analyzer.py`
- 시드: `scripts/seed_feedback_data.py`
- 테스트: `tests/test_feedback_analyzer.py`, `tests/test_routes_feedback.py`
