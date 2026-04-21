"""
Fix T2.2: Budget Filtering Logic (1 failing test)

Test: test_bid_with_budget_below_threshold
File: tests/integration/test_bid_to_proposal_workflow.py

Issue: Budget threshold filter is inverted or test expectation is wrong
"""

# TEST CODE (tests/integration/test_bid_to_proposal_workflow.py):
"""
async def test_bid_with_budget_below_threshold(staging_api_client):
    '''Test that bids with budget below $300K are excluded'''

    # Create bid with budget=$250K (below threshold)
    response = await staging_api_client.post(
        "/api/bids/search",
        json={"budget_min": 300000, "budget_max": 999999}
    )

    # Expect this bid NOT to be in results
    assert response.status_code == 200
    assert len(response.json()["results"]) == 0  # Should be excluded
"""

# ANALYSIS:
# The test expects bids with budget < $300K to be EXCLUDED from results
# when querying with budget_min=$300K.
#
# Either:
# A) The service logic is filtering correctly, but test data setup is wrong
# B) The service logic is wrong, filtering returns the opposite

# CHECK POINT:
# 1. Verify test setup creates a $250K bid
# 2. Verify query sends budget_min=$300K
# 3. Check service: app/services/bid_market_research.py

# FIX OPTIONS:

# OPTION 1: Service bug (most likely)
# File: app/services/bid_market_research.py
# BEFORE:
"""
async def search_bids(self, filters):
    query = self.db.table("bids").select("*")
    if filters.get("budget_min"):
        query = query.gte("budget", filters["budget_min"])  # >= instead of >
    if filters.get("budget_max"):
        query = query.lte("budget", filters["budget_max"])  # <= instead of <
"""

# AFTER (fix inverted logic):
"""
async def search_bids(self, filters):
    query = self.db.table("bids").select("*")
    if filters.get("budget_min"):
        query = query.gte("budget", filters["budget_min"])  # CORRECT: >= $300K
    if filters.get("budget_max"):
        query = query.lte("budget", filters["budget_max"])  # CORRECT: <= max
    # A bid of $250K should NOT match budget_min=$300K ✓
"""

# OPTION 2: Test data bug
# File: tests/conftest.py or test file setup
# BEFORE:
"""
@pytest.fixture
async def test_bid_low_budget():
    return {"budget": 250000}  # $250K
"""

# AFTER:
"""
@pytest.fixture
async def test_bid_low_budget():
    # Ensure test data is seeded BEFORE test runs
    await create_test_bid(budget=250000, status="posted")
    return await fetch_test_bid_by_budget(250000)
"""

# IMPLEMENTATION STEPS:
print("""
Steps to fix budget filtering (T2.2):

1. Read test carefully: tests/integration/test_bid_to_proposal_workflow.py
   - Line: async def test_bid_with_budget_below_threshold
   - Check what budget is being created
   - Check what filter query is being sent

2. Check service: app/services/bid_market_research.py
   - Method: search_bids() or similar
   - Verify gte/lte operators are correct
   - Test: Budget 250K + query min=300K should return 0 results ✓

3. If service is correct, check test data:
   - Verify fixture creates bid with correct budget
   - Ensure bid is persisted to DB before test runs

4. Run test: pytest tests/integration/test_bid_to_proposal_workflow.py::test_bid_with_budget_below_threshold -v
5. Should pass with green checkmark
""")
