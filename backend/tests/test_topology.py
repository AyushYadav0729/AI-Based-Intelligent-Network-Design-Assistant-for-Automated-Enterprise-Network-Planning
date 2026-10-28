"""
test_topology.py — Unit tests for topology threshold boundary checks.
Spec Section 15:
- threshold boundaries (100, 101, 800, 801 users; 2/3/4/5 floors)
"""
import pytest
from app.engine.topology import select_topology


@pytest.mark.parametrize(
    "users, floors, access_sw, expected_topology",
    [
        # Star boundaries: <= 100 users and <= 2 floors
        (50, 1, 2, "star"),
        (100, 2, 3, "star"),
        # User threshold exceeded -> collapsed_core
        (101, 2, 4, "collapsed_core"),
        # Floor threshold exceeded -> collapsed_core
        (90, 3, 3, "collapsed_core"),
        # Collapsed core limits: <= 800 users, <= 4 floors, <= 24 access switches
        (400, 3, 10, "collapsed_core"),
        (800, 4, 20, "collapsed_core"),
        # Users > 800 -> three_tier
        (801, 3, 20, "three_tier"),
        # Floors > 4 -> three_tier
        (300, 5, 8, "three_tier"),
        # Access switches > 24 -> three_tier
        (600, 4, 25, "three_tier"),
    ],
)
def test_topology_threshold_boundaries(users: int, floors: int, access_sw: int, expected_topology: str):
    selection = select_topology(total_planned_users=users, floors=floors, access_switch_count=access_sw)
    assert selection.topology == expected_topology
    assert selection.decision.stage == "topology"
    assert "total_planned_users" in selection.decision.params

