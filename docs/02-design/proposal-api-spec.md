# Phase 4: 제안 프로젝트 상태 시스템 - API 설계 및 스펙

## 📌 API 개요

### 기본 정보
- **Base URL**: `https://api.tenopa.co.kr/api/v1`
- **인증**: Bearer Token (JWT)
- **응답 형식**: JSON
- **타임존**: UTC (ISO 8601)

### API 성숙도 레벨 (Richardson Maturity Model)
- **Level 3**: HATEOAS (하이퍼링크) 미포함, 상태 전환 전용 엔드포인트 사용

---

## 📋 엔드포인트 설계

### 1️⃣ 제안 프로젝트 CRUD

#### 1-1. 제안 생성
```
POST /proposals

Request:
{
  "projectName": "K공사 터널 운영 용역",
  "clientName": "K공사",
  "description": "터널 운영 용역 제안",
  "teamId": "uuid-team-001",
  "bidPrice": 2300000000,
  "plannedBudget": 2500000000,
  "deadlineDate": "2026-03-25"
}

Response: 201 Created
{
  "data": {
    "proposalId": "uuid-prop-001",
    "projectCode": "PROP-2026-001",
    "projectName": "K공사 터널 운영 용역",
    "clientName": "K공사",
    "teamId": "uuid-team-001",
    "bidPrice": 2300000000,
    "deadlineDate": "2026-03-25",
    "status": "waiting",
    "progressPercentage": 0,
    "phase": 0,
    "projectManagerId": null,
    "projectLeaderId": null,
    "createdAt": "2026-03-20T10:00:00Z",
    "createdBy": "uuid-user-001"
  },
  "meta": {
    "timestamp": "2026-03-20T10:00:00Z"
  }
}

Error: 400 Bad Request
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "요청 데이터 검증 실패",
    "details": [
      { "field": "projectName", "message": "필수 입력 항목입니다" },
      { "field": "deadlineDate", "message": "미래 날짜여야 합니다" }
    ]
  }
}
```

#### 1-2. 제안 조회 (단건)
```
GET /proposals/{proposalId}

Response: 200 OK
{
  "data": {
    "proposalId": "uuid-prop-001",
    "projectCode": "PROP-2026-001",
    "projectName": "K공사 터널 운영 용역",
    "clientName": "K공사",
    "teamId": "uuid-team-001",
    "teamName": "수주전략팀",
    "bidPrice": 2300000000,
    "plannedBudget": 2500000000,
    "deadlineDate": "2026-03-25",
    "daysRemaining": 5,
    "status": "waiting",
    "statusLabel": "대기",
    "progressPercentage": 0,
    "phase": 0,
    "projectManagerId": null,
    "projectManagerName": null,
    "projectLeaderId": null,
    "projectLeaderName": null,
    "proposalDocumentUrl": null,
    "presentationMaterialUrl": null,
    "complianceMatrixUrl": null,
    "evaluationResult": null,
    "evaluationScore": null,
    "isAwarded": false,
    "createdAt": "2026-03-20T10:00:00Z",
    "startedAt": null,
    "completedAt": null,
    "submittedAt": null,
    "closedAt": null,
    "archivedAt": null,
    "isArchived": false
  },
  "meta": {
    "timestamp": "2026-03-20T10:15:00Z"
  }
}

Error: 404 Not Found
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "해당 제안을 찾을 수 없습니다",
    "details": [
      { "field": "proposalId", "message": "존재하지 않는 ID입니다" }
    ]
  }
}
```

#### 1-3. 제안 목록 조회
```
GET /proposals?status=waiting&teamId=uuid-team-001&sort=-deadline_date&page=1&limit=20

Query Parameters:
- status: waiting|in_progress|completed|submitted|presentation|closed (선택)
- teamId: uuid (선택)
- search: 프로젝트명/발주기관 검색 (선택)
- sort: deadline_date|-deadline_date|created_at|-created_at (기본: -created_at)
- page: 1~ (기본: 1)
- limit: 10~100 (기본: 20)
- excludeArchived: true|false (기본: true)

Response: 200 OK
{
  "data": [
    {
      "proposalId": "uuid-prop-001",
      "projectCode": "PROP-2026-001",
      "projectName": "K공사 터널 운영 용역",
      "clientName": "K공사",
      "teamName": "수주전략팀",
      "bidPrice": 2300000000,
      "deadlineDate": "2026-03-25",
      "daysRemaining": 5,
      "status": "waiting",
      "statusLabel": "대기",
      "progressPercentage": 0,
      "phase": 0,
      "projectManagerName": null,
      "projectLeaderName": null,
      "createdAt": "2026-03-20T10:00:00Z"
    },
    {
      "proposalId": "uuid-prop-002",
      "projectCode": "PROP-2026-002",
      "projectName": "서울시 교통 시뮬레이션",
      "clientName": "서울시청",
      "teamName": "인프라본부",
      "bidPrice": 1700000000,
      "deadlineDate": "2026-03-26",
      "daysRemaining": 6,
      "status": "in_progress",
      "statusLabel": "진행 중",
      "progressPercentage": 55,
      "phase": 3,
      "projectManagerName": "이순신",
      "projectLeaderName": "김영희",
      "createdAt": "2026-03-15T09:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 42,
    "totalPages": 3,
    "hasNextPage": true,
    "hasPreviousPage": false
  },
  "meta": {
    "timestamp": "2026-03-20T10:20:00Z"
  }
}
```

#### 1-4. 제안 수정
```
PUT /proposals/{proposalId}

Request:
{
  "projectName": "K공사 터널 운영 용역 (수정)",
  "bidPrice": 2400000000,
  "plannedBudget": 2600000000
}

Response: 200 OK
{
  "data": {
    "proposalId": "uuid-prop-001",
    "projectName": "K공사 터널 운영 용역 (수정)",
    "bidPrice": 2400000000,
    "plannedBudget": 2600000000,
    ...
  },
  "meta": {
    "timestamp": "2026-03-20T10:25:00Z"
  }
}

Error: 409 Conflict
{
  "error": {
    "code": "INVALID_STATE_TRANSITION",
    "message": "현재 상태에서 수정할 수 없습니다",
    "details": [
      { "field": "status", "message": "제출됨(SUBMITTED) 이상 상태에서는 수정 불가" }
    ]
  }
}
```

#### 1-5. 제안 삭제
```
DELETE /proposals/{proposalId}

Response: 204 No Content
(응답 본문 없음)

Error: 409 Conflict
{
  "error": {
    "code": "INVALID_STATE_TRANSITION",
    "message": "현재 상태에서 삭제할 수 없습니다",
    "details": [
      { "field": "status", "message": "대기(WAITING) 상태에서만 삭제 가능" }
    ]
  }
}
```

---

### 2️⃣ PM/PL 할당

#### 2-1. PM 할당
```
POST /proposals/{proposalId}/assign-pm

Request:
{
  "projectManagerId": "uuid-user-002"
}

Response: 200 OK
{
  "data": {
    "proposalId": "uuid-prop-001",
    "projectManagerId": "uuid-user-002",
    "projectManagerName": "박준호",
    "assignedAt": "2026-03-20T10:30:00Z"
  },
  "meta": {
    "timestamp": "2026-03-20T10:30:00Z"
  }
}

Error: 404 Not Found
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "해당 사용자를 찾을 수 없습니다"
  }
}
```

#### 2-2. PL 할당
```
POST /proposals/{proposalId}/assign-pl

Request:
{
  "projectLeaderId": "uuid-user-003"
}

Response: 200 OK
{
  "data": {
    "proposalId": "uuid-prop-001",
    "projectLeaderId": "uuid-user-003",
    "projectLeaderName": "최민지",
    "assignedAt": "2026-03-20T10:32:00Z"
  },
  "meta": {
    "timestamp": "2026-03-20T10:32:00Z"
  }
}
```

#### 2-3. 자동 상태 전환 검사
**로직**: PM + PL 모두 할당 후 자동으로 응답에 포함
```
Response: 200 OK
{
  "data": {
    "proposalId": "uuid-prop-001",
    "projectLeaderId": "uuid-user-003",
    "projectLeaderName": "최민지",
    "assignedAt": "2026-03-20T10:32:00Z",
    "statusTransitionInfo": {
      "triggered": true,
      "previousStatus": "waiting",
      "newStatus": "ready_to_start",
      "message": "PM과 PL이 모두 할당되었습니다. 이제 착수 버튼을 눌러 진행을 시작할 수 있습니다."
    }
  }
}
```

---

### 3️⃣ 상태 전환

#### 3-1. 착수 (WAITING → IN_PROGRESS)
```
POST /proposals/{proposalId}/start

Request:
{
  "startedBy": "uuid-user-002"  // PM ID
}

Response: 200 OK
{
  "data": {
    "proposalId": "uuid-prop-001",
    "previousStatus": "waiting",
    "newStatus": "in_progress",
    "startedAt": "2026-03-20T10:45:00Z",
    "progressPercentage": 20,
    "phase": 1,
    "message": "제안 프로젝트가 시작되었습니다"
  },
  "meta": {
    "timestamp": "2026-03-20T10:45:00Z"
  }
}

Error: 409 Conflict
{
  "error": {
    "code": "INVALID_STATE_TRANSITION",
    "message": "현재 상태에서 착수할 수 없습니다",
    "details": [
      { "field": "status", "message": "대기(WAITING) 상태에서만 착수 가능" },
      { "field": "projectManagerId", "message": "PM이 할당되어 있지 않습니다" },
      { "field": "projectLeaderId", "message": "PL이 할당되어 있지 않습니다" }
    ]
  }
}
```

#### 3-2. 완료 (IN_PROGRESS → COMPLETED)
```
POST /proposals/{proposalId}/complete

Request:
{
  "completedBy": "uuid-user-002"  // PM ID
}

Response: 200 OK
{
  "data": {
    "proposalId": "uuid-prop-001",
    "previousStatus": "in_progress",
    "newStatus": "completed",
    "completedAt": "2026-03-24T18:00:00Z",
    "progressPercentage": 100,
    "phase": 5,
    "message": "제안서 작성이 완료되었습니다. 이제 검토 후 제출할 수 있습니다"
  },
  "meta": {
    "timestamp": "2026-03-24T18:00:00Z"
  }
}

Validation:
- 모든 필수 섹션이 완료되어야 함
- 자가진단 점수가 70점 이상이어야 함 (옵션)
```

#### 3-3. 제출 (COMPLETED → SUBMITTED)
```
POST /proposals/{proposalId}/submit

Request:
{
  "submittedBy": "uuid-user-002",  // PM ID
  "proposalDocumentUrl": "s3://bucket/proposals/uuid-prop-001/proposal.docx"
}

Response: 200 OK
{
  "data": {
    "proposalId": "uuid-prop-001",
    "previousStatus": "completed",
    "newStatus": "submitted",
    "submittedAt": "2026-03-25T10:00:00Z",
    "proposalDocumentUrl": "s3://bucket/proposals/uuid-prop-001/proposal.docx",
    "message": "제안서가 성공적으로 제출되었습니다"
  },
  "meta": {
    "timestamp": "2026-03-25T10:00:00Z"
  }
}
```

#### 3-4. 발표 준비 (SUBMITTED → PRESENTATION)
```
POST /proposals/{proposalId}/prepare-presentation

Request:
{
  "approvedBy": "uuid-user-002",  // PM ID
  "presentationDate": "2026-03-28"
}

Response: 200 OK
{
  "data": {
    "proposalId": "uuid-prop-001",
    "previousStatus": "submitted",
    "newStatus": "presentation",
    "presentationDate": "2026-03-28",
    "progressPercentage": 80,
    "message": "평가대상 확정! 발표 준비를 시작합니다"
  },
  "meta": {
    "timestamp": "2026-03-26T14:00:00Z"
  }
}
```

#### 3-5. 종료 (PRESENTATION → CLOSED)
```
POST /proposals/{proposalId}/close

Request:
{
  "closedBy": "uuid-user-002",
  "evaluationResult": "awarded",  // awarded|rejected|disqualified
  "evaluationScore": 85,
  "notes": "발표 평가 완료"
}

Response: 200 OK
{
  "data": {
    "proposalId": "uuid-prop-001",
    "previousStatus": "presentation",
    "newStatus": "closed",
    "closedAt": "2026-03-28T16:00:00Z",
    "evaluationResult": "awarded",
    "evaluationScore": 85,
    "isAwarded": true,
    "message": "🏆 축하합니다! 제안이 수주되었습니다"
  },
  "meta": {
    "timestamp": "2026-03-28T16:00:00Z"
  }
}
```

---

### 4️⃣ 진행률 관리

#### 4-1. 진행률 조회
```
GET /proposals/{proposalId}/progress

Response: 200 OK
{
  "data": {
    "proposalId": "uuid-prop-001",
    "progressPercentage": 55,
    "phase": 3,
    "phaseLabel": "Phase 3: 팀 구성 및 일정 계획",
    "sections": [
      {
        "sectionId": "uuid-sec-001",
        "sectionName": "기술방안",
        "sectionType": "technical_approach",
        "status": "approved",
        "completionPercentage": 100,
        "assignedTo": "uuid-user-004",
        "completedAt": "2026-03-22T15:00:00Z"
      },
      {
        "sectionId": "uuid-sec-002",
        "sectionName": "조직 및 관리",
        "sectionType": "organization",
        "status": "in_draft",
        "completionPercentage": 60,
        "assignedTo": "uuid-user-005",
        "completedAt": null
      }
    ],
    "totalSections": 5,
    "completedSections": 2,
    "estimatedCompletion": "2026-03-24",
    "timeline": {
      "startedAt": "2026-03-20T10:45:00Z",
      "daysSpent": 4,
      "estimatedDaysRemaining": 4,
      "deadlineDate": "2026-03-25"
    }
  },
  "meta": {
    "timestamp": "2026-03-24T12:00:00Z"
  }
}
```

#### 4-2. 진행률 자동 계산
```
API 응답에 자동 포함되는 필드:

progressPercentage = (completedSections / totalSections) * 100

Phase Mapping:
- PHASE 1 (20%): RFP 분석 완료
- PHASE 2 (40%): 전략 수립 완료
- PHASE 3 (60%): 팀 구성 완료
- PHASE 4 (80%): 본문 작성 완료
- PHASE 5 (100%): 최종 검토 완료
```

---

### 5️⃣ 평가 결과 관리

#### 5-1. 평가 결과 등록
```
POST /proposals/{proposalId}/evaluation

Request:
{
  "evaluationType": "documentary_review",  // documentary_review|presentation|interview
  "evaluationDate": "2026-03-28",
  "evaluationScore": 85,
  "evaluationResult": "awarded",  // pending|qualified|shortlisted|awarded|rejected
  "rejectionReason": null,
  "notes": "우수한 기술 제안. 가격 경쟁력 보완 필요",
  "recordedBy": "uuid-user-manager"
}

Response: 201 Created
{
  "data": {
    "evaluationId": "uuid-eval-001",
    "proposalId": "uuid-prop-001",
    "evaluationType": "documentary_review",
    "evaluationDate": "2026-03-28",
    "evaluationScore": 85,
    "evaluationResult": "awarded",
    "recordedAt": "2026-03-28T17:30:00Z",
    "recordedBy": "uuid-user-manager"
  },
  "meta": {
    "timestamp": "2026-03-28T17:30:00Z"
  }
}
```

#### 5-2. 평가 이력 조회
```
GET /proposals/{proposalId}/evaluations

Response: 200 OK
{
  "data": [
    {
      "evaluationId": "uuid-eval-001",
      "evaluationType": "documentary_review",
      "evaluationDate": "2026-03-26",
      "evaluationScore": 75,
      "evaluationResult": "qualified",
      "recordedAt": "2026-03-26T18:00:00Z"
    },
    {
      "evaluationId": "uuid-eval-002",
      "evaluationType": "presentation",
      "evaluationDate": "2026-03-28",
      "evaluationScore": 85,
      "evaluationResult": "awarded",
      "recordedAt": "2026-03-28T17:30:00Z"
    }
  ],
  "meta": {
    "timestamp": "2026-03-28T18:00:00Z"
  }
}
```

---

### 6️⃣ 생애주기 이벤트 조회

#### 6-1. 타임라인 조회
```
GET /proposals/{proposalId}/timeline

Response: 200 OK
{
  "data": [
    {
      "eventId": "uuid-evt-001",
      "eventType": "created",
      "eventDescription": "제안 프로젝트 생성",
      "previousStatus": null,
      "newStatus": "waiting",
      "triggeredBy": "uuid-user-001",
      "triggeredAt": "2026-03-20T10:00:00Z"
    },
    {
      "eventId": "uuid-evt-002",
      "eventType": "assigned",
      "eventDescription": "PM 할당: 박준호",
      "previousStatus": "waiting",
      "newStatus": "waiting",
      "triggeredBy": "uuid-user-001",
      "triggeredAt": "2026-03-20T10:15:00Z"
    },
    {
      "eventId": "uuid-evt-003",
      "eventType": "assigned",
      "eventDescription": "PL 할당: 최민지",
      "previousStatus": "waiting",
      "newStatus": "waiting",
      "triggeredBy": "uuid-user-001",
      "triggeredAt": "2026-03-20T10:20:00Z"
    },
    {
      "eventId": "uuid-evt-004",
      "eventType": "started",
      "eventDescription": "제안 프로젝트 착수",
      "previousStatus": "waiting",
      "newStatus": "in_progress",
      "triggeredBy": "uuid-user-002",
      "triggeredAt": "2026-03-20T10:45:00Z"
    },
    {
      "eventId": "uuid-evt-005",
      "eventType": "phase_completed",
      "eventDescription": "Phase 3 완료",
      "previousStatus": "in_progress",
      "newStatus": "in_progress",
      "triggeredBy": "system",
      "triggeredAt": "2026-03-24T10:00:00Z",
      "metadata": {
        "phase": 3
      }
    },
    {
      "eventId": "uuid-evt-006",
      "eventType": "submitted",
      "eventDescription": "제안서 제출",
      "previousStatus": "completed",
      "newStatus": "submitted",
      "triggeredBy": "uuid-user-002",
      "triggeredAt": "2026-03-25T10:00:00Z"
    }
  ],
  "meta": {
    "timestamp": "2026-03-28T18:15:00Z"
  }
}
```

---

### 7️⃣ 아카이브 관리

#### 7-1. 아카이브 목록 조회
```
GET /proposals?isArchived=true&page=1&limit=20

Response: 200 OK
{
  "data": [
    {
      "proposalId": "uuid-prop-100",
      "projectCode": "PROP-2025-100",
      "projectName": "과거 프로젝트 A",
      "clientName": "클라이언트 A",
      "status": "archived",
      "archivedAt": "2026-03-20T00:00:00Z",
      "isAwarded": true
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 5,
    "totalPages": 1
  }
}
```

#### 7-2. 자동 아카이브 (스케줄러)
```
**매일 자정에 실행되는 자동 처리**

Schedule: CRON 0 0 * * * (매일 자정)

Logic:
SELECT * FROM proposals
WHERE status = 'closed'
AND closed_at < NOW() - INTERVAL '30 days'
→ UPDATE status = 'archived'
→ UPDATE archived_at = NOW()
→ CREATE timeline event

Example:
- 2026-02-15: 종료됨 (CLOSED)
- 2026-03-17: 30일 경과 → 자동 아카이브
```

---

## 🔐 인증 및 권한

### 인증 헤더
```
Authorization: Bearer {jwt_token}
```

### JWT Token 구조
```json
{
  "sub": "uuid-user-002",
  "email": "user@tenopa.co.kr",
  "name": "박준호",
  "role": "pm",
  "teamId": "uuid-team-001",
  "iat": 1648000000,
  "exp": 1648086400
}
```

### 권한 검증

| 엔드포인트 | PM | PL | 팀장 | 경영진 |
|-----------|:--:|:--:|:----:|:-----:|
| GET /proposals | ✅ | ✅ | ✅ | ✅ |
| POST /proposals | ✅ | ✗ | ✅ | ✅ |
| PUT /proposals/{id} | ✅ | ✗ | ✅ | ✅ |
| DELETE /proposals/{id} | ✅ | ✗ | ✅ | ✅ |
| POST /assign-pm | ✅ | ✗ | ✅ | ✅ |
| POST /start | ✅ | ✅ | ✗ | ✅ |
| POST /submit | ✅ | ✗ | ✅ | ✅ |
| POST /close | ✅ | ✗ | ✅ | ✅ |

---

## 📊 에러 코드 정의

### HTTP 상태 코드

| 상태 | 코드 | 상황 |
|------|------|------|
| 200 | OK | 요청 성공 |
| 201 | Created | 리소스 생성 성공 |
| 204 | No Content | 요청 성공 (응답 본문 없음) |
| 400 | Bad Request | 요청 데이터 검증 실패 |
| 401 | Unauthorized | 인증 필요 |
| 403 | Forbidden | 권한 없음 |
| 404 | Not Found | 리소스 미존재 |
| 409 | Conflict | 상태 전환 불가 또는 충돌 |
| 500 | Internal Server Error | 서버 오류 |

### 비즈니스 에러 코드

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "사용자 친화적 메시지",
    "details": [
      { "field": "fieldName", "message": "필드별 상세 메시지" }
    ]
  }
}
```

**주요 에러 코드**:

| 코드 | HTTP | 설명 |
|------|------|------|
| VALIDATION_ERROR | 400 | 입력 데이터 검증 실패 |
| RESOURCE_NOT_FOUND | 404 | 리소스 미존재 |
| INVALID_STATE_TRANSITION | 409 | 상태 전환 불가능 |
| INSUFFICIENT_PERMISSIONS | 403 | 권한 부족 |
| AUTHENTICATION_REQUIRED | 401 | 인증 필요 |
| DUPLICATE_RESOURCE | 409 | 중복된 리소스 |
| DEADLINE_PASSED | 409 | 마감일 경과 |

---

## 📝 응답 포맷 규칙

### 성공 응답

```json
{
  "data": {
    // 실제 데이터
  },
  "meta": {
    "timestamp": "2026-03-20T10:00:00Z",
    "version": "v1"
  }
}
```

### 목록 응답 (Pagination)

```json
{
  "data": [
    // 배열 데이터
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "totalPages": 5,
    "hasNextPage": true,
    "hasPreviousPage": false
  },
  "meta": {
    "timestamp": "2026-03-20T10:00:00Z"
  }
}
```

### 에러 응답

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "사용자 친화적 메시지",
    "details": [
      { "field": "fieldName", "message": "상세 메시지" }
    ]
  }
}
```

---

## 🧪 Zero Script QA 계획

### 테스트 케이스

| 항목 | 테스트 | 검증 기준 |
|------|--------|---------|
| **제안 생성** | POST /proposals | Status 201, projectCode 생성 확인 |
| **PM/PL 할당** | POST /assign-pm, /assign-pl | 두 번 할당 후 statusTransitionInfo 확인 |
| **상태 전환** | POST /start, /complete, /submit | 이전/새 상태 일치, timestamp 기록 |
| **진행률** | GET /progress | progressPercentage 0~100, phase 0~5 |
| **타임라인** | GET /timeline | 모든 상태 전환 이벤트 기록 |
| **아카이브** | 30일 자동 처리 | status='archived', is_archived=true |
| **에러 처리** | 잘못된 상태 전환 시도 | HTTP 409, 에러 코드 일치 |

### 로깅 체크리스트

```
✅ [API] POST /proposals
✅ [INPUT] { projectName: "...", clientName: "...", ... }
✅ [VALIDATION] 필드 검증 통과
✅ [DB] INSERT proposals 성공
✅ [EVENT] ProposalCreated 이벤트 발행
✅ [OUTPUT] { proposalId: "uuid", status: "waiting" }
✅ [RESULT] 201 Created

✅ [API] POST /proposals/{id}/assign-pm
✅ [INPUT] { projectManagerId: "uuid-user-002" }
✅ [VALIDATION] PM 존재 확인
✅ [DB] UPDATE proposals SET project_manager_id
✅ [LOGIC] PM + PL 확인 → 둘 다 할당되면 statusTransitionInfo 포함
✅ [OUTPUT] { statusTransitionInfo: { triggered: true, ... } }
✅ [RESULT] 200 OK

✅ [API] POST /proposals/{id}/start
✅ [VALIDATION] status=waiting 확인
✅ [VALIDATION] PM, PL 할당 확인
✅ [DB] UPDATE proposals SET status='in_progress', started_at=NOW()
✅ [EVENT] ProposalStarted 이벤트
✅ [TIMELINE] 생애주기 이벤트 INSERT
✅ [OUTPUT] { newStatus: "in_progress", startedAt: "...", progressPercentage: 20 }
✅ [RESULT] 200 OK
```

---

## 📌 구현 순서

1. **기본 CRUD** (1주)
   - POST /proposals (생성)
   - GET /proposals (목록)
   - GET /proposals/{id} (조회)
   - PUT /proposals/{id} (수정)
   - DELETE /proposals/{id} (삭제)

2. **할당 및 상태 전환** (1주)
   - POST /assign-pm, /assign-pl
   - POST /start, /complete, /submit
   - 상태 전환 로직 및 검증

3. **진행률 및 평가** (1주)
   - GET /progress (진행률 조회)
   - POST /evaluation (평가 등록)
   - GET /evaluations (평가 이력)

4. **생애주기 및 아카이브** (3일)
   - GET /timeline (생애주기 조회)
   - 자동 아카이브 스케줄러
   - Zero Script QA

---

## ✅ API 설계 체크리스트

- [x] RESTful 원칙 준수 (명사 기반 URL, 적절한 HTTP 메서드)
- [x] 일관된 응답 포맷 (data, meta, pagination)
- [x] 포괄적 에러 처리 (HTTP 상태 + 에러 코드)
- [x] 인증/권한 정의 (JWT, 역할별 접근 제어)
- [x] 상태 전환 규칙 명확 (유효한 경로만 허용)
- [x] 자동화 로직 정의 (PM+PL 할당 시 자동 상태 변경)
- [x] 생애주기 추적 (Timeline 이벤트)
- [x] Zero Script QA 계획 수립

