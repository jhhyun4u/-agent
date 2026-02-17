"""
MCP 서버 메모리 모드 테스트
"""
import asyncio
from services.mcp_server import MCPServer


async def test_memory_mode():
    """메모리 모드로 MCP 서버 테스트"""

    print("\n" + "="*70)
    print("MCP Server Test - Memory Mode Only")
    print("="*70)

    # Supabase 비활성화하고 생성
    mcp = MCPServer(use_supabase=False)

    # 1. Proposal DB Test
    print("\n[1] ProposalDB Test")
    proposals = await mcp.search_similar_proposals("클라우드")
    print(f"    Found: {len(proposals)} proposals")
    for p in proposals:
        print(f"    - {p['title']} ({p['client']})")

    # 2. Personnel DB Test
    print("\n[2] PersonnelDB Test")
    team = await mcp.get_team_for_project(["AWS", "Python"], 3)
    print(f"    Team size: {len(team)}")
    for member in team:
        print(f"    - {member['name']} ({member['grade']}, {member['role']})")

    # 3. RAG Server Test
    print("\n[3] RAGServer Test")
    refs = await mcp.search_references("클라우드 보안")
    print(f"    Found: {len(refs)} references")
    for ref in refs:
        print(f"    - {ref['title']}")

    print("\n" + "="*70)
    print("Memory Mode Test Complete!")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(test_memory_mode())
