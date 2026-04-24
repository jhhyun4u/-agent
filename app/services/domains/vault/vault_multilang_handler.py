"""
Vault Multi-Language Handler - Language detection and multi-language support
Phase 2: Language detection, preference storage, multi-language search
Design Ref: §3.3
"""

import logging
from typing import List, Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class SupportedLanguage(str, Enum):
    """Supported languages"""
    KOREAN = "ko"
    ENGLISH = "en"
    CHINESE = "zh"
    JAPANESE = "ja"


class VaultMultiLangHandler:
    """Handle language detection, preference management, and multi-language queries

    Supports:
    - 4 languages: Korean (ko), English (en), Chinese (zh), Japanese (ja)
    - Automatic language detection from user input
    - User language preference storage
    - Fallback search strategies (detect → pref → english)
    """

    SUPPORTED_LANGUAGES = {
        "ko": "한국어",
        "en": "English",
        "zh": "中文",
        "ja": "日本語"
    }

    LANGUAGE_LABELS = {
        "ko": "한국어",
        "en": "영어",
        "zh": "중국어",
        "ja": "일본어"
    }

    @staticmethod
    def detect_language(text: str) -> str:
        """
        Detect language of text using heuristic rules.

        For production, integrate with langdetect or google-cloud-translate.

        Args:
            text: Text to detect language from

        Returns:
            Language code (ko, en, zh, ja) or 'ko' (default)
        """
        if not text or len(text) < 2:
            return "ko"

        try:
            # Heuristic detection by character ranges
            # Korean: U+AC00-U+D7A3 (Hangul)
            # Chinese: U+4E00-U+9FFF (CJK)
            # Japanese: U+3040-U+309F (Hiragana), U+30A0-U+30FF (Katakana)

            korean_count = 0
            chinese_count = 0
            japanese_count = 0
            english_count = 0

            for char in text:
                code = ord(char)

                # Korean Hangul
                if 0xAC00 <= code <= 0xD7A3:
                    korean_count += 1
                # Chinese CJK
                elif 0x4E00 <= code <= 0x9FFF:
                    chinese_count += 1
                # Japanese Hiragana or Katakana
                elif (0x3040 <= code <= 0x309F) or (0x30A0 <= code <= 0x30FF):
                    japanese_count += 1
                # ASCII letters
                elif (0x41 <= code <= 0x5A) or (0x61 <= code <= 0x7A):
                    english_count += 1

            # Determine dominant language
            counts = {
                "ko": korean_count,
                "zh": chinese_count,
                "ja": japanese_count,
                "en": english_count
            }

            dominant = max(counts, key=counts.get)

            # Only return detected language if it has clear presence
            if counts[dominant] > len(text) * 0.2:  # 20% threshold
                logger.debug(f"Detected language: {dominant} (counts={counts})")
                return dominant

            # Default to Korean if no clear detection
            return "ko"

        except Exception as e:
            logger.warning(f"Language detection error: {e}, defaulting to 'ko'")
            return "ko"

    @staticmethod
    async def get_user_language_preference(
        supabase_client: Any,
        user_id: str
    ) -> Optional[str]:
        """
        Retrieve user's language preference from database.

        Args:
            supabase_client: Supabase async client
            user_id: User ID

        Returns:
            Language code (ko, en, zh, ja) or None if not set
        """
        try:
            user = await supabase_client.table("users") \
                .select("preferred_language") \
                .eq("id", user_id) \
                .single() \
                .execute()

            if user.data:
                pref = user.data.get("preferred_language")
                if pref and pref in VaultMultiLangHandler.SUPPORTED_LANGUAGES:
                    logger.debug(f"User {user_id} language preference: {pref}")
                    return pref

            return None

        except Exception as e:
            logger.warning(f"Failed to get language preference for {user_id}: {e}")
            return None

    @staticmethod
    async def save_language_preference(
        supabase_client: Any,
        user_id: str,
        language: str
    ) -> bool:
        """
        Save user's language preference.

        Args:
            supabase_client: Supabase async client
            user_id: User ID
            language: Language code to save

        Returns:
            True if successful
        """
        if language not in VaultMultiLangHandler.SUPPORTED_LANGUAGES:
            logger.warning(f"Invalid language code: {language}")
            return False

        try:
            await supabase_client.table("users") \
                .update({"preferred_language": language}) \
                .eq("id", user_id) \
                .execute()

            logger.info(f"Saved language preference for user {user_id}: {language}")
            return True

        except Exception as e:
            logger.error(f"Failed to save language preference: {e}")
            return False

    @staticmethod
    def get_language_label(lang_code: str) -> str:
        """
        Convert language code to human-readable label.

        Args:
            lang_code: Language code (ko, en, zh, ja)

        Returns:
            Human-readable label (e.g., "한국어") or "Unknown"
        """
        return VaultMultiLangHandler.LANGUAGE_LABELS.get(lang_code, "Unknown")

    @staticmethod
    async def determine_query_language(
        text: str,
        supabase_client: Any,
        user_id: Optional[str] = None,
        explicit_language: Optional[str] = None
    ) -> str:
        """
        Determine language for query using priority: explicit > detect > user pref > default.

        Design Ref: §3.3 — Language determination strategy

        Args:
            text: Query text
            supabase_client: Supabase async client
            user_id: Current user ID (for preference lookup)
            explicit_language: Explicitly specified language (overrides everything)

        Returns:
            Language code to use for query
        """
        # Priority 1: Explicit language specification
        if explicit_language and explicit_language in VaultMultiLangHandler.SUPPORTED_LANGUAGES:
            logger.debug(f"Using explicit language: {explicit_language}")
            return explicit_language

        # Priority 2: Detect from text
        detected = VaultMultiLangHandler.detect_language(text)
        if detected != "ko":  # If something other than default was detected
            logger.debug(f"Using detected language: {detected}")
            return detected

        # Priority 3: User preference
        if user_id:
            pref = await VaultMultiLangHandler.get_user_language_preference(
                supabase_client, user_id
            )
            if pref:
                logger.debug(f"Using user preference: {pref}")
                return pref

        # Priority 4: Default
        logger.debug("Using default language: ko")
        return "ko"

    @staticmethod
    async def search_multilang(
        supabase_client: Any,
        query: str,
        language: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Perform multi-language search with fallback strategy.

        Design Ref: §3.3 — Multi-language search

        Strategy:
        1. Search in detected/specified language
        2. If fewer than limit/2 results, search in English
        3. Deduplicate results

        Args:
            supabase_client: Supabase async client
            query: Search query
            language: Explicit language code (optional)
            limit: Maximum results to return

        Returns:
            List of matching documents
        """
        if language is None:
            language = VaultMultiLangHandler.detect_language(query)

        results = []

        try:
            # Primary search in detected/specified language
            logger.debug(f"Searching in {language} for: {query}")

            primary = await supabase_client.table("vault_documents") \
                .select("id, title, language, section, metadata") \
                .eq("language", language) \
                .ilike("title", f"%{query}%") \
                .limit(limit) \
                .execute()

            if primary.data:
                results.extend(primary.data)
                logger.debug(f"Primary search returned {len(primary.data)} results")

            # Fallback to English if results are sparse
            if len(results) < limit // 2 and language != "en":
                logger.debug(f"Fallback to English search (got {len(results)} results)")

                english = await supabase_client.table("vault_documents") \
                    .select("id, title, language, section, metadata") \
                    .eq("language", "en") \
                    .ilike("title", f"%{query}%") \
                    .limit(limit - len(results)) \
                    .execute()

                if english.data:
                    results.extend(english.data)
                    logger.debug(f"Fallback search returned {len(english.data)} results")

            # Deduplicate by ID
            seen_ids = set()
            unique_results = []
            for doc in results:
                if doc["id"] not in seen_ids:
                    unique_results.append(doc)
                    seen_ids.add(doc["id"])

            logger.info(f"Multi-language search: {query} → {len(unique_results)} results")
            return unique_results

        except Exception as e:
            logger.error(f"Multi-language search error: {e}")
            return []

    @staticmethod
    def get_supported_languages_info() -> Dict[str, str]:
        """
        Get information about all supported languages.

        Returns:
            Dict of language_code -> display_name
        """
        return VaultMultiLangHandler.SUPPORTED_LANGUAGES.copy()

    @staticmethod
    def validate_language_code(lang_code: str) -> bool:
        """
        Validate language code.

        Args:
            lang_code: Language code to validate

        Returns:
            True if valid
        """
        return lang_code in VaultMultiLangHandler.SUPPORTED_LANGUAGES

    @staticmethod
    async def auto_translate_query(
        text: str,
        target_language: str,
        translator_client: Optional[Any] = None
    ) -> Optional[str]:
        """
        Auto-translate query to target language (stub for future integration).

        Currently returns None (translation disabled).
        In production, integrate with Google Translate or Azure Translator.

        Args:
            text: Text to translate
            target_language: Target language code
            translator_client: Translation service client (optional)

        Returns:
            Translated text or None if translation not available
        """
        # TODO: Integrate with translation API
        logger.debug(f"Translation requested but not implemented: {text} → {target_language}")
        return None
