# 인트라넷 스토리지 구조 재설계

> **상태:** 설계 제안  
> **작성일:** 2026-04-11  
> **이유:** 조직 변경 시 경로 재편성 불필요 → 프로젝트 ID 중심 구조로

---

## 문제점

### 현재 구조 (조직 기반)
```
Supabase Storage (bucket: tenopa-org-files)
  └── {org_id}/
      └── {document_id}/
          └── {filename}
```

**문제:**
- 조직명 변경 → 폴더명 변경 필요 ❌
- 조직 통합/분사 → 복잡한 경로 재구성 ❌
- 조직 삭제 → 데이터 손실 위험 ❌
- 프로젝트 이동 시 경로 갱신 필요 ❌

---

## 해결안: 프로젝트 ID 중심 구조

### ✅ 새로운 구조 (프로젝트 기반)

```
Supabase Storage (bucket: intranet-projects)
  └── projects/
      └── {project_id}/                           # 불변 식별자
          ├── metadata/
          │   ├── project-info.json                # 현재 프로젝트 정보
          │   ├── org-snapshot.json                # 저장 시점 조직정보
          │   └── manifest.json                    # 파일 인벤토리
          │
          └── documents/
              ├── proposal/                         # doc_type별 폴더
              │   ├── proposal.pdf
              │   ├── proposal.docx
              │   ├── proposal.hwpx
              │   └── proposal-summary.txt         # extracted_text 미리보기
              │
              ├── supporting-documents/
              │   ├── org-chart.pdf
              │   ├── capability-statement.pdf
              │   └── references.pdf
              │
              ├── presentation/
              │   └── presentation.pptx
              │
              └── other/
                  └── attachment.zip
```

### 📊 경로 매핑

| 항목 | 현재 | 신규 |
|------|------|------|
| **경로 구조** | `org_id/document_id/filename` | `projects/project_id/doc_type/filename` |
| **프로젝트 이동 시** | 경로 수정 필요 ❌ | 변경 없음 ✅ |
| **조직 변경 시** | 경로 수정 필요 ❌ | 변경 없음 ✅ |
| **직관성** | 낮음 | 높음 ✅ |
| **확장성** | 제한적 | 우수 ✅ |

---

## DB 스키마 변경

### intranet_documents 테이블 (변경)

```sql
CREATE TABLE intranet_documents (
    id                UUID PRIMARY KEY,
    project_id        UUID NOT NULL,         -- ← 강화: 항상 필수
    org_id            UUID NOT NULL,         -- ← 유지: RLS 용도
    
    -- 파일 메타
    file_slot         TEXT NOT NULL,
    doc_type          TEXT NOT NULL,         -- proposal, report, presentation, etc.
    doc_subtype       TEXT,
    
    -- 파일
    filename          TEXT NOT NULL,
    file_type         TEXT NOT NULL,         -- pdf, docx, hwpx, etc.
    file_size         BIGINT,
    storage_path      TEXT NOT NULL,         -- 변경: projects/{id}/doc_type/filename
    
    -- 처리
    processing_status TEXT DEFAULT 'pending',
    extracted_text    TEXT,
    total_chars       INTEGER,
    chunk_count       INTEGER,
    
    created_at        TIMESTAMPTZ,
    updated_at        TIMESTAMPTZ,
    
    UNIQUE(project_id, file_slot)
);
```

### intranet_projects 테이블 (변경 없음)

스키마는 이미 프로젝트 ID 중심이므로 그대로 유지:
```sql
CREATE TABLE intranet_projects (
    id              UUID PRIMARY KEY,        -- ← 중심축
    org_id          UUID NOT NULL,           -- ← RLS용 (참조용)
    project_name    TEXT NOT NULL,
    client_name     TEXT,
    budget_krw      BIGINT,
    keywords        TEXT[],
    status          TEXT,
    -- ...
);
```

---

## API 엔드포인트 설계

### 프로젝트 검색 & 문서 조회
```typescript
// 프로젝트 목록 + 문서 요약
GET /api/intranet/projects?keyword=AI&budget_min=500000000

Response:
[
  {
    id: "2c59535a-1a27-47e3-8ff8-550f76a819af",
    project_name: "AI 기반 제안서 자동 작성 플랫폼",
    client_name: "국방부",
    budget_krw: 500000000,
    keywords: ["AI", "NLP"],
    documents: [
      {
        id: "doc-123",
        doc_type: "proposal",
        filename: "proposal.pdf",
        extracted_text: "본 제안서는 국방부의 AI 기반...",
        storage_path: "projects/2c59535a-1a27-47e3-8ff8-550f76a819af/proposal/proposal.pdf"
      }
    ]
  }
]
```

### 문서 다운로드
```typescript
// 직접 다운로드
GET /api/intranet/projects/{projectId}/documents/{documentId}/download
→ Supabase Storage signed URL 반환

// 또는 스트리밍
GET /api/intranet/documents/{documentId}/stream
→ 파일 직접 스트리밍
```

### 추출된 텍스트 조회
```typescript
// 미리보기 (자동으로 extracted_text 반환)
GET /api/intranet/projects/{projectId}/documents/{documentId}/preview

Response:
{
  filename: "proposal.pdf",
  doc_type: "proposal",
  extracted_text: "...",
  total_chars: 15234,
  chunk_count: 12
}
```

---

## 마이그레이션 전략

### Phase 1: 신규 구조로 저장 (즉시)
```python
# 새 파일은 new_storage_path로 저장
storage_path = f"projects/{project_id}/documents/{doc_type}/{filename}"
```

### Phase 2: 기존 파일 이관 (선택)
```python
# 기존 org_id 기반 파일을 프로젝트 중심으로 재정렬
# 파일 이동 스크립트 실행
# intranet_documents.storage_path 갱신
```

### Phase 3: API 업데이트 (즉시)
```typescript
// 다운로드 경로 → 신규 storage_path 기반
// 검색 API 유지 (org_id는 내부 RLS 용도)
```

---

## 구현 체크리스트

- [ ] **DB 마이그레이션**
  - [ ] `intranet_documents.storage_path` 주석 업데이트
  - [ ] 신규 저장 프로세스 정의

- [ ] **파일 업로드 로직 수정**
  - [ ] `scripts/pilot_migration_demo.py` → 신규 경로 형식 적용
  - [ ] `app/services/document_service.py` → `projects/{id}/doc_type/` 경로 사용
  - [ ] Supabase Storage bucket 구조 작성 (선택)

- [ ] **API 엔드포인트 수정**
  - [ ] `GET /api/intranet/projects/{projectId}/documents` → 신규 경로 반환
  - [ ] `GET /api/intranet/documents/{documentId}/download` → 신규 경로로 signed URL 생성
  - [ ] 프로젝트별 폴더 자동 생성 로직

- [ ] **기존 파일 이관 (선택)**
  - [ ] 스크립트: `scripts/migrate_storage_structure.py`
  - [ ] 테스트: 소수 파일로 먼저 테스트
  - [ ] 백업: 이동 전 기존 구조 스냅샷

- [ ] **문서화**
  - [ ] Storage 경로 가이드 작성
  - [ ] API 문서 업데이트
  - [ ] 운영 가이드 (폴더 생성, 파일 정리)

---

## 장점 정리

| 항목 | 효과 |
|------|------|
| **안정성** | 조직 변경 무영향 🔒 |
| **이동성** | 프로젝트 간 이동 용이 🚀 |
| **직관성** | 저장 경로로 계층 파악 가능 📍 |
| **확장성** | 메타데이터/청크 저장 용이 📦 |
| **RLS** | org_id는 여전히 보안 필터 역할 🔐 |

---

## 예시: 조직 변경 시나리오

### 현재 구조 (문제)
```
Before: AI팀
  b92b8f14-f0d2-4d9e-a6c8-a5b0ec1dd114/
    └── {document_id}/proposal.pdf

After: AI팀 → 기술혁신부로 통합
  ??? 경로 수정 필요 (복잡함) ❌
```

### 신규 구조 (해결)
```
Before: AI팀 (org_id: b92b8f14-...)
  projects/
    └── 2c59535a-1a27-47e3-8ff8-550f76a819af/
        └── proposal/proposal.pdf

After: AI팀 → 기술혁신부로 통합 (org_id: c3d5e2f4-...)
  projects/
    └── 2c59535a-1a27-47e3-8ff8-550f76a819af/  ← 변화 없음! ✅
        └── proposal/proposal.pdf
        
→ intranet_projects.org_id만 업데이트, 파일 이동 불필요 ✅
```

---

## 다음 단계

1. **설계 검토** → 사용자 승인
2. **로컬 테스트** → 신규 경로로 파일 저장 및 다운로드 테스트
3. **API 구현** → 프로젝트별 문서 조회/다운로드 엔드포인트
4. **파일럿 마이그레이션** → 신규 경로로 10개 프로젝트 재저장
5. **운영 가이드** → 팀 공유

