# Plan: hwp-output

## 개요

제안서 자동 생성 시스템에 HWP/HWPX 출력 기능을 추가한다.
현재 DOCX + PPTX만 지원하는데, 국내 공공기관·정부 입찰 제출 시 HWP 형식이 사실상 표준이므로 필수 기능이다.

---

## 배경 및 필요성

- 나라장터(G2B) 제출 서류는 대부분 HWP 형식 요구
- 기존 `python-hwpx` 기반 구현은 전면 재작성 결정 (삭제됨)
- DOCX 빌더(`app/services/docx_builder.py`)는 sections dict → 문서 변환 방식으로 단순 구조

---

## 기능 요구사항

| ID | 요구사항 | 우선순위 |
|----|----------|----------|
| FR-01 | 제안서 내용(sections)을 HWP/HWPX 형식으로 출력 | P0 |
| FR-02 | 기존 DOCX와 동일한 섹션 구성 (제목, 본문 단락) | P0 |
| FR-03 | Supabase Storage 업로드 (기존 DOCX/PPTX 업로드 파이프라인과 동일) | P0 |
| FR-04 | 다운로드 API 엔드포인트 연동 (`/proposals/{id}/download/hwpx`) | P0 |
| FR-05 | 제안서 결과 페이지에 HWPX 다운로드 버튼 추가 | P1 |

---

## 기술 접근 방식 (검토 필요)

### 옵션 A — HWPX XML 직접 생성 (권장 후보)
- HWPX는 ZIP 압축 + XML 구조 (OOXML과 유사)
- 외부 라이브러리 없이 `zipfile` + `xml.etree` 로 직접 작성 가능
- 포맷 완전 제어 가능, 의존성 최소화
- 단점: HWPX 스펙 문서 분석 필요, 초기 구현 공수 높음

### 옵션 B — LibreOffice 변환
- DOCX 생성 후 `libreoffice --headless --convert-to hwp` 명령어로 변환
- 신뢰도 높음, 추가 구현 거의 없음
- 단점: 서버에 LibreOffice 설치 필요 (~300MB), Docker 이미지 용량 증가

### 옵션 C — python-hwpx 재도입 (개선 버전)
- 이전 구현의 문제점을 파악 후 올바르게 재사용
- 단점: 이전 실패 이유가 라이브러리 자체 문제일 경우 동일 문제 재발

---

## 구현 범위

### In Scope
- HWP/HWPX 빌더 서비스 (`app/services/hwpx_builder.py`)
- 제안서 생성 파이프라인에 HWPX 빌드 단계 추가
- Supabase Storage 업로드 + 다운로드 URL
- 프론트엔드 다운로드 버튼

### Out of Scope
- HWP 바이너리(.hwp) 형식 지원 (HWPX XML만 대상)
- 복잡한 표/이미지/차트 레이아웃 (텍스트 + 제목 구조만)
- HWP 템플릿 기반 스타일링 (2차 작업)

---

## 의존 관계

- `app/services/docx_builder.py` — 동일한 sections dict 입력 인터페이스 참고
- `app/api/routes.py` — 다운로드 엔드포인트 추가
- `app/services/phase_executor.py` — 빌드 파이프라인에 HWPX 단계 추가
- `frontend/app/proposals/[id]/page.tsx` — 다운로드 버튼 추가

---

## 성공 기준

- 제안서 생성 완료 후 HWPX 파일이 Supabase Storage에 정상 업로드됨
- 한글(Hangul) 프로그램에서 파일이 정상 열림 (텍스트 깨짐 없음)
- 다운로드 버튼 클릭 시 HWPX 파일 다운로드 성공

---

## 열린 질문

1. **기술 접근 방식**: 옵션 A/B/C 중 어느 것으로 진행할지 결정 필요
2. **파일 형식**: `.hwpx`(XML) vs `.hwp`(바이너리) — HWPX로 진행 가정
3. **이전 실패 원인**: python-hwpx에서 어떤 문제가 있었는지 파악하면 옵션 C 재검토 가능
