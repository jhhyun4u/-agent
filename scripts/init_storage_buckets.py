#!/usr/bin/env python3
"""Supabase Storage 버킷 초기화 스크립트

필요한 버킷 생성:
1. documents — RFP분석, 공고문, 과업지시서 저장
2. proposals — 제안서 산출물 저장 (DOCX, HWPX, PPTX 등)
"""

import asyncio
import sys
import httpx
from dotenv import load_dotenv

load_dotenv()

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


async def init_buckets():
    """필요한 스토리지 버킷 생성 (REST API 직접 호출)"""
    from app.config import settings

    buckets_to_create = ["documents", "proposals"]

    print("[INFO] Supabase Storage 버킷 초기화 중...\n")

    # Supabase REST API 엔드포인트
    storage_url = f"{settings.supabase_url}/storage/v1/bucket"
    headers = {
        "apiKey": settings.supabase_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key or settings.supabase_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        for bucket_name in buckets_to_create:
            print(f"[INFO] 버킷 확인: {bucket_name}")

            try:
                # 버킷 생성 시도 (REST API)
                # POST /storage/v1/bucket
                payload = {
                    "name": bucket_name,
                    "public": False,  # 비공개 버킷 (인증 필요)
                }

                response = await client.post(
                    storage_url,
                    json=payload,
                    headers=headers,
                )

                # 201 Created = 새로 생성, 200 OK = 이미 존재
                if response.status_code == 201:
                    print(f"  ✓ 생성 완료: {bucket_name}")
                elif response.status_code == 200:
                    # 버킷이 이미 존재
                    print(f"  ✓ 이미 존재: {bucket_name}")
                elif response.status_code == 400:
                    # 이미 존재하는지 확인
                    error_data = response.json()
                    if "already exists" in str(error_data).lower():
                        print(f"  ✓ 이미 존재: {bucket_name}")
                    else:
                        print(f"  ✗ 오류: {response.text}")
                        return False
                else:
                    print(f"  ✗ HTTP {response.status_code}: {response.text}")
                    return False

            except Exception as e:
                print(f"  ✗ 예외: {type(e).__name__}: {e}")
                return False

    print("\n[SUCCESS] 스토리지 버킷 초기화 완료!")
    return True


if __name__ == "__main__":
    result = asyncio.run(init_buckets())
    sys.exit(0 if result else 1)
