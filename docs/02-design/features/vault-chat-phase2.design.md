# Vault Chat Phase 2 — Technical Design Document

**Version**: 2.0  
**Date**: 2026-04-20  
**Status**: DRAFT  
**Reviewed by**: (pending)  

---

## 1. Architecture Overview

### 1.1 System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User Interfaces                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │  Web UI      │    │ Teams Adaptive   │ │ Teams Digest (push)  │  │
│  │ (existing)   │    │ Bot (mention)    │ │ (scheduled)          │  │
│  └──────────────┘    └──────────────┘    └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Vault API Layer (FastAPI)                          │
│  ┌──────────────────────┐  ┌──────────────────────────────────────┐ │
│  │ Chat Endpoints       │  │ Teams Bot Endpoints                  │ │
│  │ ├─ POST /chat        │  │ ├─ POST /teams/bot/query            │ │
│  │ │  (context inject)  │  │ │  (adaptive)                        │ │
│  │ ├─ GET /conv/{id}    │  │ ├─ PUT /teams/bot/config/{team_id}  │ │
│  │ │  /context          │  │ │  (settings)                        │ │
│  │ │  (latest N turns)  │  │ ├─ POST /teams/bot/digest           │ │
│  │ └─ POST /conv/{id}   │  │ │  (manual trigger)                  │ │
│  │    /search-history   │  │ └─ GET /teams/bot/messages          │ │
│  │    (hybrid search)   │  │    (audit)                           │ │
│  └──────────────────────┘  └──────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Service Layer                                     │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐   │
│  │ VaultContext     │  │ VaultPermission  │  │ VaultMultiLang  │   │
│  │ Manager          │  │ Filter           │  │ Handler         │   │
│  │ ├─extract()      │  │ ├─filter()       │  │ ├─detect_lang() │   │
│  │ ├─build_string() │  │ ├─validate()     │  │ ├─translate()   │   │
│  │ └─inject()       │  │ └─log_denied()   │  │ └─embed()       │   │
│  └──────────────────┘  └──────────────────┘  └─────────────────┘   │
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐   │
│  │ TeamsBotService  │  │ VaultSearch      │  │ VaultEmbedding  │   │
│  │ ├─send_msg()     │  │ (hybrid SQL+Vec) │  │ Service (exist) │   │
│  │ ├─schedule_      │  │ └─search()       │  │                 │   │
│  │ │ digest()       │  │                  │  │                 │   │
│  │ └─match_rfp()    │  │                  │  │                 │   │
│  └──────────────────┘  └──────────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  External Services                                    │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────────┐   │
│  │ Claude API     │  │ OpenAI Embed   │  │ Microsoft Teams     │   │
│  │ (response)     │  │ (3-large)      │  │ Webhook             │   │
│  └────────────────┘  └────────────────┘  └─────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  Data Layer (PostgreSQL)                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐   │
│  │ vault_messages   │  │ vault_documents  │  │ teams_bot_      │   │
│  │ ├─context_embed  │  │ ├─min_required   │  │ config          │   │
│  │ ├─is_question    │  │ │  _role         │  │ ├─webhook_url   │   │
│  │ └─indexes(5)     │  │ ├─language       │  │ ├─bot_modes     │   │
│  │                  │  │ └─translated_from│  │ └─digest_time    │   │
│  └──────────────────┘  └──────────────────┘  └─────────────────┘   │
│                                                                       │
│  ┌──────────────────┐  ┌──────────────────┐                         │
│  │ vault_audit_logs │  │ teams_bot_       │                         │
│  │ ├─action_denied  │  │ messages         │                         │
│  │ └─denied_reason  │  │ ├─message_id     │                         │
│  │                  │  │ └─created_at     │                         │
│  └──────────────────┘  └──────────────────┘                         │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Data Flow

#### Flow 1: Context-Aware Chat (대화 문맥 유지)
```
사용자 질문
  ↓
1️⃣ 언어 감지 (VaultMultiLangHandler.detect_lang)
  ↓
2️⃣ 최근 대화 로드 (VaultContextManager.extract_context)
   - DB에서 마지막 6-8 회전 조회
   - 각 메시지 벡터 임베딩 재계산 (선택)
  ↓
3️⃣ 하이브리드 검색 (VaultSearch.search)
   - SQL 키워드 검색 + 벡터 유사도 검색
   - 대화 이력과 현재 질문 함께 고려
  ↓
4️⃣ 컨텍스트 주입 (Claude API)
   "[이전 대화]"
   사용자: Q1
   어시스턴트: A1
   ...
   사용자: 현재 질문
   → 응답 생성
  ↓
5️⃣ 역할 검증 (VaultPermissionFilter.filter)
   - 응답에 포함된 소스 문서 검증
   - 권한 없는 정보 제거
  ↓
6️⃣ 응답 저장 & 반환
   - vault_messages에 새 메시지 저장
   - context_embedding 계산 저장
```

#### Flow 2: Permission-Based Filtering (역할 기반 필터링)
```
AI 응답 생성 (Claude)
  ↓
소스 인용 추출 (VaultCitationService)
  ↓
각 소스 검증:
  FOR EACH source_document:
    user_role >= document.min_required_role?
      YES → 응답 유지
      NO  → 응답에서 제거 + vault_audit_logs에 denied 기록
  ↓
필터링된 응답 반환
  IF 모든 소스가 제거됨:
    → "죄송하지만, 이 정보는 ${required_role} 이상만 접근 가능합니다"
  IF 부분 제거:
    → "[* 일부 정보는 접근 권한으로 인해 제외되었습니다]"
  ↓
응답 저장
```

#### Flow 3: Teams Adaptive Bot (멘션 기반 실시간 봇)
```
Teams 채널 멘션: @Vault [질문]
  ↓
Teams Webhook → FastAPI /teams/bot/query
  ↓
사용자 검증 (Teams user_id → app users)
  ↓
Vault Chat 실행 (위의 Flow 1 동일)
  ↓
응답을 Teams 메시지로 포스트
  - Main message: 답변 + 소스 (compact)
  - Thread: 상세 설명 + 메타데이터
  ↓
teams_bot_messages 테이블에 기록
```

#### Flow 4: Teams Daily Digest (정기 다이제스트)
```
매일 오전 9시 (APScheduler trigger)
  ↓
각 팀의 teams_bot_config 조회
  ↓
FOR EACH team with digest_keywords:
    모니터링 키워드 검색:
      - G2B 신규공고 (매일 새로운 공고)
      - 경쟁사 입찰 정보 (경쟁사 이름 검색)
      - 기술 동향 (기술 문서 최신 업데이트)
    ↓
    결과를 마크다운으로 요약:
      ## 오늘의 Vault 다이제스트 (2026-04-20)
      ### G2B 공고 (3건)
      - [적격성 85%] 환경부 스마트팩토리...
      ### 경쟁사 입찰
      - OOO사, BBB 프로젝트 낙찰 예상
      ### 기술 동향
      - AI 기반 탄소관리 솔루션 최신 정보
    ↓
    Teams Webhook으로 발송
    ↓
    teams_bot_messages 기록
```

#### Flow 5: RFP Auto-Recommendation (자동 추천)
```
새로운 RFP 수집 (G2B 또는 수동)
  ↓
RFP 내용 벡터 임베딩
  ↓
Vault의 완료된 프로젝트 검색
  - 벡터 유사도 > 0.75
  - 유사 프로젝트 상위 3개 추천
  ↓
각 프로젝트의 담당 팀 식별
  ↓
Teams에 자동 메시지 발송:
  "새 RFP: [공고명]
   유사 경험:
   1. [Project A] - 팀B (낙찰 가능성 85%)
   2. [Project B] - 팀C (75%)
   3. [Project C] - 팀D (70%)
   조기 대응을 권장합니다"
  ↓
teams_bot_messages 기록
```

---

## 2. Database Schema Design

### 2.1 New Tables

#### 2.1.1 teams_bot_config
```sql
CREATE TABLE teams_bot_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) NOT NULL UNIQUE,
    
    -- 봇 활성화 및 모드
    bot_enabled BOOLEAN DEFAULT true,
    bot_modes TEXT[] DEFAULT ARRAY['adaptive', 'digest']
    CHECK (bot_modes <@ ARRAY['adaptive', 'digest', 'matching']),
    
    -- Webhook 및 인증
    webhook_url TEXT NOT NULL,
    webhook_validated_at TIMESTAMPTZ,
    
    -- 다이제스트 설정
    digest_time TIME DEFAULT '09:00',        -- 발송 시간 (UTC)
    digest_keywords TEXT[] DEFAULT '{}',     -- 모니터링 키워드
    digest_enabled BOOLEAN DEFAULT true,
    
    -- 추천 (RFP 매칭) 설정
    matching_enabled BOOLEAN DEFAULT true,
    matching_threshold FLOAT DEFAULT 0.75,
    
    -- 메타데이터
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_teams_bot_config_team_id 
  ON teams_bot_config(team_id);
CREATE INDEX idx_teams_bot_config_digest_enabled 
  ON teams_bot_config(digest_enabled);
```

#### 2.1.2 teams_bot_messages
```sql
CREATE TABLE teams_bot_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) NOT NULL,
    
    -- 연결 정보
    conversation_id UUID REFERENCES vault_conversations(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- 메시지 내용
    query TEXT NOT NULL,
    response TEXT NOT NULL,
    mode TEXT CHECK (mode IN ('adaptive', 'digest', 'matching')),
    
    -- Teams 메시지 ID (추적용)
    teams_message_id TEXT,
    teams_thread_id TEXT,
    
    -- 상태
    delivery_status TEXT DEFAULT 'pending'
    CHECK (delivery_status IN ('pending', 'sent', 'failed', 'archived')),
    delivery_error TEXT,
    
    -- 메타데이터
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_teams_bot_messages_team_id 
  ON teams_bot_messages(team_id, created_at DESC);
CREATE INDEX idx_teams_bot_messages_status 
  ON teams_bot_messages(delivery_status);
CREATE INDEX idx_teams_bot_messages_teams_message_id 
  ON teams_bot_messages(teams_message_id) WHERE teams_message_id IS NOT NULL;
```

### 2.2 Modified Tables

#### 2.2.1 vault_messages (확장)
```sql
ALTER TABLE vault_messages ADD COLUMN
  context_embedding VECTOR(1536);  -- 컨텍스트용 임베딩 (선택)

ALTER TABLE vault_messages ADD COLUMN
  is_question BOOLEAN DEFAULT true;  -- true=user question, false=assistant response

ALTER TABLE vault_messages ADD COLUMN
  language TEXT DEFAULT 'ko'
  CHECK (language IN ('ko', 'en', 'zh', 'ja'));

-- Index 추가
CREATE INDEX idx_vault_messages_context
  ON vault_messages(conversation_id, created_at DESC, is_question);

CREATE INDEX idx_vault_messages_language
  ON vault_messages(language) WHERE language != 'ko';
```

#### 2.2.2 vault_documents (확장)
```sql
ALTER TABLE vault_documents ADD COLUMN
  min_required_role TEXT DEFAULT 'member'
  CHECK (min_required_role IN ('member', 'lead', 'director', 'executive', 'admin'));

ALTER TABLE vault_documents ADD COLUMN
  language TEXT DEFAULT 'ko'
  CHECK (language IN ('ko', 'en', 'zh', 'ja'));

ALTER TABLE vault_documents ADD COLUMN
  translated_from UUID REFERENCES vault_documents(id) ON DELETE SET NULL;

ALTER TABLE vault_documents ADD COLUMN
  is_sensitive BOOLEAN DEFAULT false;  -- 데이터 분류용

-- Index 추가
CREATE INDEX idx_vault_documents_min_required_role
  ON vault_documents(min_required_role);

CREATE INDEX idx_vault_documents_language
  ON vault_documents(language) WHERE language != 'ko';

CREATE INDEX idx_vault_documents_translated_from
  ON vault_documents(translated_from) WHERE translated_from IS NOT NULL;
```

#### 2.2.3 vault_conversations (확장)
```sql
ALTER TABLE vault_conversations ADD COLUMN
  primary_language TEXT DEFAULT 'ko'
  CHECK (primary_language IN ('ko', 'en', 'zh', 'ja'));

ALTER TABLE vault_conversations ADD COLUMN
  context_enabled BOOLEAN DEFAULT true;  -- 컨텍스트 주입 활성화 여부
```

#### 2.2.4 vault_audit_logs (확장)
```sql
ALTER TABLE vault_audit_logs ADD COLUMN
  action_denied BOOLEAN DEFAULT false;  -- 거부된 접근

ALTER TABLE vault_audit_logs ADD COLUMN
  denied_reason TEXT;  -- "insufficient_role" | "sensitive_document" | etc

ALTER TABLE vault_audit_logs ADD COLUMN
  user_role TEXT;  -- 접근 시도자 역할 (추적용)

-- Index 추가
CREATE INDEX idx_vault_audit_logs_action_denied
  ON vault_audit_logs(action_denied) WHERE action_denied = true;
```

### 2.3 Database Migrations

**File**: `database/migrations/023_vault_phase2_tables.sql`
```sql
-- Create new tables (teams_bot_config, teams_bot_messages)
-- Alter existing tables (vault_messages, vault_documents, vault_conversations, vault_audit_logs)
-- Create indexes
-- Create RLS policies for teams_bot_* tables
```

**Deployment Order**:
1. 새 테이블 생성 (teams_bot_config, teams_bot_messages)
2. 기존 테이블 확장 (필드 추가)
3. Index 생성
4. RLS 정책 적용
5. Data migration (선택): 기존 문서에 min_required_role = 'member' 설정

---

## 3. Service Layer Design

### 3.1 VaultContextManager (확장)

**File**: `app/services/vault_context_manager.py`

```python
class VaultContextManager:
    """관리: 대화 이력 추출 및 컨텍스트 주입"""
    
    CONTEXT_WINDOW = 8  # 최근 8 회전 (Phase 1: 6)
    EMBEDDING_DIM = 1536  # OpenAI 임베딩 차원
    
    @staticmethod
    async def extract_context_with_embeddings(
        supabase_client,
        conversation_id: str,
        limit: int = CONTEXT_WINDOW
    ) -> List[ChatMessage]:
        """
        대화 이력 조회 + 벡터 임베딩 포함
        
        Returns:
            마지막 N개 메시지 (user + assistant, 가장 최신부터)
        """
        # 1. DB에서 마지막 N개 메시지 조회
        messages = await supabase_client.table("vault_messages") \
            .select("*") \
            .eq("conversation_id", conversation_id) \
            .order("created_at", desc=False) \
            .limit(limit * 2) \
            .execute()
        
        # 2. 최신 순서로 반환 (오래된 것부터)
        return messages.data[-limit:] if messages.data else []
    
    @staticmethod
    def build_context_string(messages: List[ChatMessage]) -> str:
        """
        메시지를 프롬프트용 문자열로 변환
        
        Format:
        [이전 대화 맥락]
        사용자: Q1
        어시스턴트: A1
        ...
        """
        if not messages:
            return ""
        
        context_lines = ["[이전 대화 맥락]"]
        for msg in messages:
            role_label = "사용자:" if msg.role == "user" else "어시스턴트:"
            # 긴 메시지는 요약 (max 500 chars)
            content = msg.content[:500] + "..." if len(msg.content) > 500 else msg.content
            context_lines.append(f"{role_label} {content}")
        
        return "\n".join(context_lines)
    
    @staticmethod
    def should_inject_context(conversation_id: str, message_count: int) -> bool:
        """
        컨텍스트 주입 판단
        
        - 동일 대화 & 메시지 2개 이상 → 주입
        - 새 대화 → 주입 안함
        """
        return message_count >= 2
    
    @staticmethod
    async def store_context_embedding(
        supabase_client,
        message_id: str,
        embedding: List[float]
    ) -> None:
        """
        메시지의 컨텍스트 임베딩 저장 (선택)
        """
        await supabase_client.table("vault_messages") \
            .update({"context_embedding": embedding}) \
            .eq("id", message_id) \
            .execute()
```

### 3.2 VaultPermissionFilter (신규)

**File**: `app/services/vault_permission_filter.py`

```python
class VaultPermissionFilter:
    """관리: 역할 기반 응답 필터링"""
    
    ROLE_HIERARCHY = {
        "member": 0,
        "lead": 1,
        "director": 2,
        "executive": 3,
        "admin": 4
    }
    
    @staticmethod
    async def filter_response(
        user_role: str,
        response_text: str,
        sources: List[DocumentSource],
        supabase_client,
        user_id: str
    ) -> Tuple[str, List[DocumentSource], List[str]]:
        """
        응답 텍스트와 소스를 사용자 역할로 필터링
        
        Args:
            user_role: 사용자 역할
            response_text: AI 생성 응답
            sources: 인용된 문서 목록
            
        Returns:
            (필터링된_응답, 필터링된_소스, 제외된_이유들)
        """
        user_role_level = VaultPermissionFilter.ROLE_HIERARCHY.get(user_role, 0)
        filtered_sources = []
        excluded_reasons = []
        
        # 1. 각 소스 검증
        for source in sources:
            # DB에서 문서의 min_required_role 조회
            doc = await supabase_client.table("vault_documents") \
                .select("min_required_role") \
                .eq("id", source.document_id) \
                .single() \
                .execute()
            
            required_level = VaultPermissionFilter.ROLE_HIERARCHY.get(
                doc.data["min_required_role"], 0
            )
            
            if user_role_level >= required_level:
                # 접근 가능
                filtered_sources.append(source)
            else:
                # 접근 불가 → 감시 로깅
                excluded_reasons.append(
                    f"{source.title} (요구 역할: {doc.data['min_required_role']})"
                )
                await VaultPermissionFilter._log_denied_access(
                    supabase_client,
                    user_id,
                    source.document_id,
                    user_role,
                    doc.data["min_required_role"]
                )
        
        # 2. 응답 재구성 (권한 없는 내용 제거)
        # 단순 규칙: "[출처 X]" 패턴 제거
        filtered_response = response_text
        for reason in excluded_reasons:
            # 응답 내 해당 소스 참조 제거
            pass  # Citation service와 협력 필요
        
        # 3. 필터링 결과 알림
        if not filtered_sources:
            # 모든 소스가 제외됨
            filtered_response = f"죄송하지만, 이 정보는 {doc.data['min_required_role']} 이상만 접근 가능합니다."
        elif excluded_reasons:
            # 일부 소스만 제외
            excluded_str = ", ".join(excluded_reasons)
            filtered_response += f"\n\n[참고] 다음 정보는 권한으로 인해 제외되었습니다: {excluded_str}"
        
        return filtered_response, filtered_sources, excluded_reasons
    
    @staticmethod
    async def _log_denied_access(
        supabase_client,
        user_id: str,
        document_id: str,
        user_role: str,
        required_role: str
    ) -> None:
        """거부된 접근 기록"""
        await supabase_client.table("vault_audit_logs").insert({
            "user_id": user_id,
            "action": "search",
            "action_denied": True,
            "denied_reason": f"insufficient_role (user:{user_role}, required:{required_role})",
            "user_role": user_role,
            "created_at": datetime.utcnow().isoformat()
        }).execute()
```

### 3.3 VaultMultiLangHandler (신규)

**File**: `app/services/vault_multilang_handler.py`

```python
from langdetect import detect, LangDetectException

class VaultMultiLangHandler:
    """관리: 다국어 감지 및 처리"""
    
    SUPPORTED_LANGUAGES = {
        "ko": "한국어",
        "en": "English",
        "zh": "中文",
        "ja": "日本語"
    }
    
    @staticmethod
    def detect_language(text: str) -> str:
        """
        텍스트 언어 자동 감지
        
        Returns:
            언어 코드 (ko, en, zh, ja) or 'ko' (기본값)
        """
        try:
            lang = detect(text)
            # ISO 639-1 코드 정규화
            if lang.startswith("zh"):
                return "zh"  # zh-cn, zh-tw → zh
            elif lang.startswith("ja"):
                return "ja"
            elif lang.startswith("en"):
                return "en"
            elif lang.startswith("ko"):
                return "ko"
            else:
                return "ko"  # 기본값
        except LangDetectException:
            return "ko"
    
    @staticmethod
    async def get_user_language_preference(
        supabase_client,
        user_id: str
    ) -> str:
        """
        사용자 언어 선호도 조회
        
        Returns:
            언어 코드 or None (기본값 사용)
        """
        user = await supabase_client.table("users") \
            .select("preferred_language") \
            .eq("id", user_id) \
            .single() \
            .execute()
        
        return user.data.get("preferred_language") if user.data else None
    
    @staticmethod
    async def save_language_preference(
        supabase_client,
        user_id: str,
        language: str
    ) -> None:
        """사용자 언어 선호도 저장"""
        await supabase_client.table("users") \
            .update({"preferred_language": language}) \
            .eq("id", user_id) \
            .execute()
    
    @staticmethod
    def get_language_label(lang_code: str) -> str:
        """언어 코드 → 라벨 변환"""
        return VaultMultiLangHandler.SUPPORTED_LANGUAGES.get(
            lang_code, "Unknown"
        )
    
    @staticmethod
    async def search_multilang(
        supabase_client,
        query: str,
        language: str = None,
        limit: int = 10
    ) -> List[DocumentSource]:
        """
        다국어 기반 검색
        
        - 감지 언어로 먼저 검색
        - 없으면 영어로 재검색 (국제 자료)
        """
        if language is None:
            language = VaultMultiLangHandler.detect_language(query)
        
        # 1. 감지 언어로 검색
        results = await supabase_client.table("vault_documents") \
            .select("*") \
            .eq("language", language) \
            .ilike("title", f"%{query}%") \
            .limit(limit) \
            .execute()
        
        # 2. 결과 부족시 영어 재검색
        if len(results.data) < limit // 2 and language != "en":
            en_results = await supabase_client.table("vault_documents") \
                .select("*") \
                .eq("language", "en") \
                .ilike("title", f"%{query}%") \
                .limit(limit - len(results.data)) \
                .execute()
            results.data.extend(en_results.data)
        
        return results.data
```

### 3.4 TeamsBotService (신규)

**File**: `app/services/teams_bot_service.py`

```python
import aiohttp
import json
from datetime import datetime, time
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class TeamsBotService:
    """관리: Teams 봇 통합 (3가지 모드)"""
    
    def __init__(self, supabase_client, scheduler: AsyncIOScheduler):
        self.supabase = supabase_client
        self.scheduler = scheduler
        self.http_session = None
    
    async def initialize(self):
        """초기화: HTTP 세션 생성, 정기 작업 스케줄"""
        self.http_session = aiohttp.ClientSession()
        
        # 정기 다이제스트 스케줄링
        self.scheduler.add_job(
            self._run_daily_digests,
            "cron",
            hour="*",  # 매시 정각
            minute="0",
            timezone="UTC"
        )
    
    # Mode 1: Adaptive Bot
    async def send_response_to_teams(
        self,
        team_id: str,
        query: str,
        response: str,
        sources: List[DocumentSource]
    ) -> bool:
        """
        Vault 응답을 Teams에 메시지로 발송
        
        Returns:
            성공 여부
        """
        # 1. 팀의 webhook_url 조회
        config = await self.supabase.table("teams_bot_config") \
            .select("webhook_url") \
            .eq("team_id", team_id) \
            .single() \
            .execute()
        
        webhook_url = config.data["webhook_url"]
        
        # 2. Teams 메시지 형식으로 구성
        message = self._build_teams_message(query, response, sources)
        
        # 3. Webhook으로 발송
        try:
            async with self.http_session.post(
                webhook_url,
                json=message,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"Teams API error: {resp.status}")
                
                # 4. 발송 기록
                teams_message_id = await resp.text()
                await self.supabase.table("teams_bot_messages").insert({
                    "team_id": team_id,
                    "query": query,
                    "response": response,
                    "mode": "adaptive",
                    "delivery_status": "sent",
                    "teams_message_id": teams_message_id
                }).execute()
                
                return True
        except Exception as e:
            # 실패 기록
            await self.supabase.table("teams_bot_messages").insert({
                "team_id": team_id,
                "query": query,
                "response": response,
                "mode": "adaptive",
                "delivery_status": "failed",
                "delivery_error": str(e)
            }).execute()
            return False
    
    @staticmethod
    def _build_teams_message(
        query: str,
        response: str,
        sources: List[DocumentSource]
    ) -> dict:
        """Teams Adaptive Card 형식 메시지 생성"""
        return {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": "Vault AI Response",
            "themeColor": "0078D4",
            "sections": [
                {
                    "activityTitle": "Vault AI Response",
                    "text": response,
                    "facts": [
                        {
                            "name": "Query",
                            "value": query[:100]
                        },
                        {
                            "name": "Sources",
                            "value": f"{len(sources)} document(s)"
                        }
                    ]
                }
            ]
        }
    
    # Mode 2: Daily Digest
    async def _run_daily_digests(self):
        """정기 다이제스트 실행 (매시 정각)"""
        # 1. 다이제스트 활성화된 팀 조회
        configs = await self.supabase.table("teams_bot_config") \
            .select("*") \
            .eq("digest_enabled", True) \
            .execute()
        
        for config in configs.data:
            await self._generate_and_send_digest(config)
    
    async def _generate_and_send_digest(self, config: dict):
        """
        팀별 다이제스트 생성 및 발송
        
        키워드:
        - "G2B:환경부" → 환경부 공고 검색
        - "competitor:OOO사" → 경쟁사 입찰 정보
        - "tech:AI" → 기술 트렌드
        """
        digest_sections = []
        
        for keyword in config.get("digest_keywords", []):
            if keyword.startswith("G2B:"):
                # G2B 공고 검색
                topic = keyword.split(":", 1)[1]
                results = await self._search_g2b_keyword(topic)
                if results:
                    digest_sections.append({
                        "title": f"G2B 신규공고 ({topic})",
                        "results": results
                    })
            
            elif keyword.startswith("competitor:"):
                # 경쟁사 입찰 정보
                competitor = keyword.split(":", 1)[1]
                results = await self._search_competitor_bids(competitor)
                if results:
                    digest_sections.append({
                        "title": f"경쟁사 입찰 ({competitor})",
                        "results": results
                    })
            
            elif keyword.startswith("tech:"):
                # 기술 트렌드
                tech = keyword.split(":", 1)[1]
                results = await self._search_tech_trends(tech)
                if results:
                    digest_sections.append({
                        "title": f"기술 트렌드 ({tech})",
                        "results": results
                    })
        
        # 다이제스트 메시지 구성 및 발송
        digest_text = self._build_digest_text(digest_sections)
        
        try:
            async with self.http_session.post(
                config["webhook_url"],
                json={
                    "@type": "MessageCard",
                    "summary": "Vault Daily Digest",
                    "sections": [{
                        "activityTitle": "📊 오늘의 Vault 다이제스트",
                        "text": digest_text,
                        "activitySubtitle": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }]
                }
            ) as resp:
                if resp.status == 200:
                    await self.supabase.table("teams_bot_messages").insert({
                        "team_id": config["team_id"],
                        "query": f"Daily digest: {', '.join(config['digest_keywords'])}",
                        "response": digest_text,
                        "mode": "digest",
                        "delivery_status": "sent"
                    }).execute()
        except Exception as e:
            logger.error(f"Digest send failed for team {config['team_id']}: {e}")
    
    async def _search_g2b_keyword(self, keyword: str) -> List[dict]:
        """G2B 공고 검색"""
        # Vault 또는 G2B 서비스 연동
        pass
    
    async def _search_competitor_bids(self, competitor: str) -> List[dict]:
        """경쟁사 입찰 정보 검색"""
        pass
    
    async def _search_tech_trends(self, tech: str) -> List[dict]:
        """기술 트렌드 검색"""
        pass
    
    @staticmethod
    def _build_digest_text(sections: List[dict]) -> str:
        """다이제스트 마크다운 생성"""
        lines = []
        for section in sections:
            lines.append(f"### {section['title']}")
            for result in section['results'][:5]:  # 상위 5개
                lines.append(f"- {result['title']} (적격성: {result.get('score', 'N/A')}%)")
        return "\n".join(lines)
    
    # Mode 3: Project Matching
    async def recommend_similar_projects(
        self,
        rfp_id: str,
        rfp_content: str
    ):
        """
        RFP 기반 유사 프로젝트 자동 추천
        """
        # 1. RFP 벡터 임베딩 생성
        embedding = await self._embed_text(rfp_content)
        
        # 2. Vault의 완료 프로젝트 검색 (유사도 > 0.75)
        similar_projects = await self._vector_search_projects(embedding)
        
        # 3. 팀별 추천 메시지 생성
        for project in similar_projects:
            team_id = project["team_id"]
            
            # 팀의 webhook_url 조회
            config = await self.supabase.table("teams_bot_config") \
                .select("webhook_url") \
                .eq("team_id", team_id) \
                .single() \
                .execute()
            
            # 추천 메시지 발송
            message = {
                "@type": "MessageCard",
                "summary": "RFP Auto-Recommendation",
                "sections": [{
                    "activityTitle": "🎯 신규 RFP 자동 매칭",
                    "text": f"RFP: {rfp_content[:200]}...\n\n유사 경험: {project['title']} (낙찰 가능성 {project['matching_score']}%)"
                }]
            }
            
            async with self.http_session.post(config["webhook_url"], json=message):
                pass
    
    async def _embed_text(self, text: str) -> List[float]:
        """텍스트 벡터 임베딩"""
        # OpenAI API 호출
        pass
    
    async def _vector_search_projects(self, embedding: List[float]) -> List[dict]:
        """벡터 임베딩 기반 프로젝트 검색"""
        pass
    
    async def close(self):
        """정리: HTTP 세션 종료"""
        if self.http_session:
            await self.http_session.close()
```

---

## 4. API Endpoints

### 4.1 Chat with Context (기존 확장)

**Endpoint**: `POST /api/vault/chat`  
**Change**: 컨텍스트 자동 주입 + 언어 감지

**Request**:
```json
{
  "message": "이전 답변을 기반으로 더 자세히 설명해주세요",
  "conversation_id": "uuid-...",
  "scope": ["completed_projects"],
  "context_enabled": true,  // NEW
  "language": "auto"  // NEW: auto | ko | en | zh | ja
}
```

**Response**:
```json
{
  "response": "컨텍스트를 고려한 응답...",
  "confidence": 0.92,
  "sources": [...],
  "language_detected": "ko",  // NEW
  "context_used": true,  // NEW
  "message_id": "uuid-..."
}
```

### 4.2 Conversation Context History (신규)

**Endpoint**: `GET /api/vault/conversations/{conversation_id}/context`  
**Auth**: User (자신의 대화만)

**Query Params**:
- `limit`: 최근 N 회전 (default: 6, max: 20)
- `include_embeddings`: 벡터 임베딩 포함 (default: false)

**Response**:
```json
{
  "conversation_id": "uuid-...",
  "messages": [
    {
      "id": "uuid-...",
      "role": "user",
      "content": "Q1",
      "created_at": "2026-04-20T10:00:00Z",
      "language": "ko",
      "context_embedding": [0.123, -0.456, ...]  // if requested
    },
    {
      "id": "uuid-...",
      "role": "assistant",
      "content": "A1",
      "created_at": "2026-04-20T10:01:00Z",
      "sources": [...]
    }
  ]
}
```

### 4.3 Teams Bot Configuration (신규)

**Endpoint**: `GET /api/teams/bot/config/{team_id}`  
**Auth**: Team member (팀 관리자)

**Response**:
```json
{
  "id": "uuid-...",
  "team_id": "uuid-...",
  "bot_enabled": true,
  "bot_modes": ["adaptive", "digest"],
  "webhook_url": "https://...",
  "digest_time": "09:00",
  "digest_keywords": ["G2B:환경부", "competitor:OOO사"],
  "matching_enabled": true,
  "matching_threshold": 0.75
}
```

**Endpoint**: `PUT /api/teams/bot/config/{team_id}` (수정)

**Request**:
```json
{
  "bot_enabled": true,
  "digest_keywords": ["G2B:환경부", "tech:AI"],
  "digest_time": "09:00"
}
```

### 4.4 Teams Bot Query (신규 - 적응형 봇)

**Endpoint**: `POST /api/teams/bot/query`  
**Auth**: Teams (Webhook validation)

**Request** (Teams Webhook):
```json
{
  "message": "@Vault 당사의 낙찰 현황은?",
  "team_id": "uuid-...",
  "user_id": "uuid-...",
  "channel_id": "..."
}
```

**Response**:
```json
{
  "status": "success",
  "teams_message_id": "...",
  "response": "답변...",
  "posted": true
}
```

---

## 5. Testing Strategy

### 5.1 Unit Tests (15개)

| 테스트 | 검증 항목 |
|--------|---------|
| `test_context_extraction` | 마지막 N 회전 조회 정확도 |
| `test_context_building` | 프롬프트 포맷팅 |
| `test_permission_filter_member` | member 역할 필터링 |
| `test_permission_filter_denied` | 권한 없는 문서 제거 |
| `test_language_detection_ko` | 한국어 감지 |
| `test_language_detection_en` | 영어 감지 |
| `test_language_detection_zh` | 중문 감지 |
| `test_language_detection_ja` | 일본어 감지 |
| `test_teams_message_format` | Teams Adaptive Card 포맷 |
| `test_digest_text_generation` | 다이제스트 마크다운 생성 |
| `test_audit_logging_denied` | 거부된 접근 로깅 |
| `test_role_hierarchy` | 역할 계층 검증 |
| `test_multilang_search` | 다국어 검색 |
| `test_teams_webhook_send` | Teams Webhook 발송 |
| `test_rfp_matching` | RFP 매칭 로직 |

### 5.2 Integration Tests (20개)

| 테스트 | 검증 항목 |
|--------|---------|
| `test_chat_with_context` | 컨텍스트 주입된 채팅 |
| `test_context_persistence` | 컨텍스트 DB 저장 |
| `test_permission_filter_in_chat` | 채팅 중 필터링 |
| `test_multilang_chat` | 다국어 채팅 |
| `test_teams_adaptive_bot_flow` | 적응형 봇 전체 흐름 |
| `test_teams_digest_generation` | 다이제스트 생성 |
| `test_teams_message_delivery` | Teams 메시지 발송 |
| `test_permission_denied_logging` | 감시 로그 기록 |
| `test_language_preference_save` | 언어 선호도 저장/조회 |
| `test_context_window_limit` | 컨텍스트 윈도우 제한 (8턴) |
| `test_concurrent_conversations` | 동시 대화 처리 |
| `test_teams_config_update` | Teams 봇 설정 수정 |
| `test_digest_keyword_search` | 다이제스트 키워드 검색 |
| `test_rfp_auto_recommendation` | RFP 자동 추천 |
| `test_teams_webhook_validation` | Teams Webhook 검증 |
| `test_api_rate_limiting` | API 레이트 제한 |
| `test_error_handling_teams_api` | Teams API 오류 처리 |
| `test_multilang_document_translation` | 다국어 문서 인덱싱 |
| `test_permission_escalation` | 권한 에스컬레이션 방지 |
| `test_audit_trail_complete` | 감시 추적 완전성 |

### 5.3 E2E Tests (15개)

| 테스트 | 검증 항목 |
|--------|---------|
| `test_e2e_multi_turn_context` | 다중 회전 맥락 유지 |
| `test_e2e_permission_enforcement` | 역할 기반 접근 제어 |
| `test_e2e_multilang_workflow` | 다국어 전체 워크플로우 |
| `test_e2e_teams_bot_interaction` | Teams 봇 상호작용 |
| `test_e2e_teams_digest_delivery` | Teams 다이제스트 배포 |
| `test_e2e_rfp_matching_pipeline` | RFP 매칭 파이프라인 |
| `test_e2e_context_performance` | 컨텍스트 성능 (< 2s) |
| `test_e2e_permission_logging` | 감시 로그 추적 |
| `test_e2e_teams_config_flow` | Teams 봇 설정 전체 흐름 |
| `test_e2e_multilang_and_permission` | 다국어 + 권한 조합 |
| `test_e2e_concurrent_users` | 동시 50명 사용자 |
| `test_e2e_storage_lifecycle` | 저장소 수명주기 |
| `test_e2e_teams_reliability` | Teams 안정성 (98%+) |
| `test_e2e_error_recovery` | 오류 복구 메커니즘 |
| `test_e2e_audit_compliance` | 감사 규정 준수 |

---

## 6. Performance & Scalability

### 6.1 Response Time Targets

| 시나리오 | P50 | P95 | P99 |
|---------|-----|-----|-----|
| 일반 채팅 (컨텍스트 없음) | 800ms | 1.5s | 2.5s |
| 컨텍스트 주입 (8턴) | 1.2s | 2.5s | 4s |
| 다국어 (임베딩 재계산) | 1.5s | 3s | 5s |
| Teams 적응형 봇 | 2s | 4s | 6s |
| Teams 다이제스트 | 5s | 10s | 20s |

### 6.2 Scalability

| 메트릭 | 목표 | 달성 방법 |
|--------|------|---------|
| **동시 사용자** | 50+ | 연결 풀링, 비동기 처리 |
| **메시지/분** | 100 | 메시지 큐 (RabbitMQ 선택) |
| **저장소 증가** | 500GB/월 | 자동 아카이빙 (90일 정책) |
| **메모리** | < 2GB | 컨텍스트 윈도우 제한 (8턴) |

---

## 7. Security & Compliance

### 7.1 Access Control

| 계층 | 구현 |
|------|------|
| **DB** | RLS (Row-Level Security) |
| **API** | 역할 검증 (FastAPI Depends) |
| **응답** | VaultPermissionFilter (내용 필터링) |
| **감시** | vault_audit_logs (모든 접근 기록) |

### 7.2 Data Classification

```
Public (member 접근):
  - 낙찰 사례, 정부 공고

Internal (lead 접근):
  - 팀별 실적, 팀원 정보

Confidential (director 접근):
  - 수주전략, 경쟁사 분석

Restricted (executive 접근):
  - 매출, 수익성, 급여

Admin Only:
  - 시스템 설정, 전체 감시 로그
```

### 7.3 Audit Trail

```sql
SELECT * FROM vault_audit_logs
WHERE action_denied = true
ORDER BY created_at DESC;
-- 거부된 모든 접근 추적 가능
```

---

## 8. Migration & Deployment

### 8.1 Migration Steps

1. **Week 1 (04/20-22)**:
   - 스키마 마이그레이션 (023 파일)
   - 신규 테이블 생성
   - 기존 테이블 확장

2. **Week 1 (04/23-24)**:
   - Data backfill: 기존 vault_documents에 `min_required_role = 'member'` 설정
   - Data backfill: 기존 vault_messages에 `language = 'ko'` 설정

3. **Week 2 (04/27-04/28)**:
   - 서비스 배포 (Context, Permission, MultiLang)
   - Teams Bot 테스트 (sandbox)

4. **Week 2 (05/01-05/02)**:
   - 통합 테스트 및 성능 검증
   - 스테이징 배포

5. **Week 2 (05/03-05/04)**:
   - 24시간 모니터링
   - 프로덕션 배포 준비

### 8.2 Rollback Plan

- **데이터베이스**: 트랜잭션 롤백 (마이그레이션 이전 스냅샷)
- **API**: 이전 버전 배포 (feature flag로 gradual rollback)
- **Teams**: Webhook URL 변경 또는 봇 비활성화

---

## 9. Monitoring & Observability

### 9.1 Metrics

```python
# Prometheus metrics
vault_chat_response_time_seconds.histogram()
vault_context_window_size.histogram()
vault_permission_denied_total.counter()
vault_multilang_query_total.counter(labels=['language'])
teams_bot_message_delivery_status.counter(labels=['status'])
teams_digest_generation_time.histogram()
```

### 9.2 Alerts

| 알림 | 조건 | 액션 |
|------|------|------|
| **응답시간 증가** | P95 > 4s (5분 평균) | 개발팀 호출 |
| **Permission 오류** | denied_access > 10/분 | 보안팀 검토 |
| **Teams 배송 실패** | delivery_status = 'failed' > 5% | API 재시도 |
| **저장소 폭증** | daily_growth > 600GB | 아카이빙 정책 검토 |

---

## 10. Documentation

### 10.1 User Guide
- Teams 봇 사용법 (3가지 모드)
- 다국어 쿼리 예시
- 권한 기반 접근 (역할별 설명)

### 10.2 API Documentation
- OpenAPI/Swagger 자동 생성
- cURL 예시 (각 엔드포인트)

### 10.3 Operations Guide
- 배포 체크리스트
- 모니터링 대시보드 해석
- 트러블슈팅

---

**Document Version**: 2.0  
**Last Updated**: 2026-04-20  
**Next Review**: 2026-04-27 (DO Phase 점검)
