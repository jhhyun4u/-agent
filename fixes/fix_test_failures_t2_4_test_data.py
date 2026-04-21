"""
Fix T2.4: Test Data Seeding (1 failing test)

Issue: Test database fixtures not initializing required data (org, team, user)

Root cause: conftest.py fixtures don't create database records before tests run
"""

# FILE: tests/conftest.py
# CURRENT: Missing database seeding

# AFTER: Add session-scoped fixture for database initialization

conftest_fix = '''
import pytest
from datetime import datetime
from app.utils.supabase_client import get_async_client
from app.models.auth_schemas import CurrentUser

@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """Seed test database with required data (org, team, users)."""
    client = await get_async_client()

    # Test org
    test_org = {
        "id": "test-org-001",
        "name": "Test Organization",
        "created_at": datetime.utcnow().isoformat(),
    }
    await client.table("organizations").upsert(test_org).execute()

    # Test division
    test_division = {
        "id": "test-div-001",
        "org_id": "test-org-001",
        "name": "Test Division",
        "created_at": datetime.utcnow().isoformat(),
    }
    await client.table("divisions").upsert(test_division).execute()

    # Test team
    test_team = {
        "id": "test-team-001",
        "org_id": "test-org-001",
        "division_id": "test-div-001",
        "name": "Test Team",
        "created_at": datetime.utcnow().isoformat(),
    }
    await client.table("teams").upsert(test_team).execute()

    # Test users with different roles
    test_users = [
        {
            "id": "test-user-admin",
            "email": "admin@test.co.kr",
            "name": "Admin User",
            "role": "admin",
            "org_id": "test-org-001",
            "team_id": "test-team-001",
            "division_id": "test-div-001",
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
        },
        {
            "id": "test-user-lead",
            "email": "lead@test.co.kr",
            "name": "Team Lead",
            "role": "lead",
            "org_id": "test-org-001",
            "team_id": "test-team-001",
            "division_id": "test-div-001",
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
        },
        {
            "id": "test-user-member",
            "email": "member@test.co.kr",
            "name": "Team Member",
            "role": "member",
            "org_id": "test-org-001",
            "team_id": "test-team-001",
            "division_id": "test-div-001",
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
        },
    ]

    for user in test_users:
        await client.table("users").upsert(user).execute()

    yield

    # Cleanup after all tests
    await client.table("users").delete().eq("org_id", "test-org-001").execute()
    await client.table("teams").delete().eq("org_id", "test-org-001").execute()
    await client.table("divisions").delete().eq("org_id", "test-org-001").execute()
    await client.table("organizations").delete().eq("id", "test-org-001").execute()


@pytest.fixture
async def test_org_id():
    """Test organization ID."""
    return "test-org-001"


@pytest.fixture
async def test_team_id():
    """Test team ID."""
    return "test-team-001"


@pytest.fixture
async def test_user_admin() -> CurrentUser:
    """Admin user fixture."""
    return CurrentUser(
        id="test-user-admin",
        email="admin@test.co.kr",
        name="Admin User",
        role="admin",
        org_id="test-org-001",
        team_id="test-team-001",
        division_id="test-div-001",
        status="active",
    )


@pytest.fixture
async def test_user_lead() -> CurrentUser:
    """Team lead user fixture."""
    return CurrentUser(
        id="test-user-lead",
        email="lead@test.co.kr",
        name="Team Lead",
        role="lead",
        org_id="test-org-001",
        team_id="test-team-001",
        division_id="test-div-001",
        status="active",
    )
'''

print("""
Steps to fix test data seeding (T2.4):

1. Open tests/conftest.py
2. Add setup_test_database() fixture (copy from fix above)
3. Mark as scope="session", autouse=True
4. Creates: org, division, team, 3 users (admin, lead, member)
5. Runs BEFORE any tests, cleans up AFTER all tests
6. Add helper fixtures: test_org_id, test_team_id, test_user_admin, test_user_lead
7. Run full test suite: pytest tests/ -v
8. All tests should now find required database data
9. Previously failing test should pass
""")
