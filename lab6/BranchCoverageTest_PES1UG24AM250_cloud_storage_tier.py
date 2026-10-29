"""Branch coverage test suite for the Cloud Storage Tier module.

This file targets *branch coverage*: every decision point (``if`` / ``elif`` /
``else`` and short-circuit ``or``) must be evaluated as both ``True`` and
``False``. Boundary values are used so each branch is explicitly exercised and
the ``coverage run --branch`` report reaches 90% (or more) branch coverage.

Run:
    coverage run --branch -m pytest BranchCoverageTest_PES1UG24AM250_cloud_storage_tier.py
    coverage report -m
"""

import pytest

from cloud_storage_tier import process_storage_tenants, monitor_replication_latency


# ---------------------------------------------------------------------------
# Input-validation decision: `not isinstance(...) or fixed_support_fee < 0`
# ---------------------------------------------------------------------------

def test_or_left_true_raises():
    """`not isinstance(tenants, list)` is True -> raise (short-circuit)."""
    with pytest.raises(ValueError):
        process_storage_tenants(42, 10.0)


def test_or_left_false_right_true_raises():
    """`isinstance(...)` True, `fixed_support_fee < 0` True -> raise."""
    with pytest.raises(ValueError):
        process_storage_tenants([], -1.0)


def test_or_left_false_right_false_accepts():
    """Both operands False -> valid, falls through to billing logic."""
    result = process_storage_tenants([], 0.0)
    assert result == {"total_billed": 0.0, "status": "ZERO_USAGE"}


# ---------------------------------------------------------------------------
# `account_active` decision
# ---------------------------------------------------------------------------

def test_inactive_tenant_continue_branch():
    tenants = [{"account_active": False, "tier": "hot", "has_backup_vault": False,
                "buckets": [{"size_gb": 100, "corrupted": False, "egress_gb": 0}]}]
    assert process_storage_tenants(tenants, 10.0)["status"] == "ZERO_USAGE"


def test_active_tenant_not_continue_branch():
    tenants = [{"account_active": True, "tier": "hot", "has_backup_vault": False,
                "buckets": [{"size_gb": 100, "corrupted": False, "egress_gb": 0}]}]
    assert process_storage_tenants(tenants, 10.0)["status"] == "BILLED"


# ---------------------------------------------------------------------------
# Tier decision chain: hot / cool / archive / unknown
# ---------------------------------------------------------------------------

def _tenant(tier, size_gb, corrupted=False, egress_gb=0, vault=False):
    return {
        "account_active": True,
        "tier": tier,
        "has_backup_vault": vault,
        "buckets": [{"size_gb": size_gb, "corrupted": corrupted,
                     "egress_gb": egress_gb}],
    }


def test_tier_hot_branch():
    assert process_storage_tenants([_tenant("hot", 100)], 10.0)["total_billed"] == 2.5


def test_tier_cool_branch():
    assert process_storage_tenants([_tenant("cool", 100)], 10.0)["total_billed"] == 1.5


def test_tier_archive_branch():
    assert process_storage_tenants([_tenant("archive", 100)], 10.0)["total_billed"] == 0.5


def test_tier_unknown_else_branch():
    assert process_storage_tenants([_tenant("frozen", 100)], 10.0)["status"] == "ZERO_USAGE"


# ---------------------------------------------------------------------------
# `size_gb <= 0` decision
# ---------------------------------------------------------------------------

def test_size_zero_flagged():
    assert process_storage_tenants([_tenant("hot", 0)], 10.0)["status"] == "ZERO_USAGE"


def test_size_negative_flagged():
    assert process_storage_tenants([_tenant("hot", -5)], 10.0)["status"] == "ZERO_USAGE"


# ---------------------------------------------------------------------------
# `is_corrupted` decision and nested `tier == "archive"`
# ---------------------------------------------------------------------------

def test_corrupted_archive_zeroes_and_breaks():
    assert process_storage_tenants([_tenant("archive", 100, corrupted=True)], 10.0)["total_billed"] == 0.0


def test_corrupted_non_archive_adds_zero():
    assert process_storage_tenants([_tenant("hot", 100, corrupted=True)], 10.0)["total_billed"] == 0.0


def test_not_corrupted_branch():
    assert process_storage_tenants([_tenant("hot", 100)], 10.0)["total_billed"] == 2.5


# ---------------------------------------------------------------------------
# `size_gb > 500` decision (with boundary values)
# ---------------------------------------------------------------------------

def test_size_below_500_no_discount():
    assert process_storage_tenants([_tenant("hot", 499)], 10.0)["total_billed"] == 12.48


def test_size_exactly_500_no_discount():
    assert process_storage_tenants([_tenant("hot", 500)], 10.0)["total_billed"] == 12.5


def test_size_above_500_discount():
    assert process_storage_tenants([_tenant("hot", 501)], 10.0)["total_billed"] == 11.27


# ---------------------------------------------------------------------------
# `egress_gb > 100` decision (with boundary values)
# ---------------------------------------------------------------------------

def test_egress_exactly_100_no_surcharge():
    assert process_storage_tenants([_tenant("hot", 100, egress_gb=100)], 10.0)["total_billed"] == 2.5


def test_egress_above_100_surcharge():
    assert process_storage_tenants([_tenant("hot", 100, egress_gb=101)], 10.0)["total_billed"] == 2.58


# ---------------------------------------------------------------------------
# `has_backup_vault` decision
# ---------------------------------------------------------------------------

def test_backup_vault_true_adds_fee():
    assert process_storage_tenants([_tenant("hot", 100, vault=True)], 10.0)["total_billed"] == 12.5


def test_backup_vault_false_no_fee():
    assert process_storage_tenants([_tenant("hot", 100, vault=False)], 10.0)["total_billed"] == 2.5


# ---------------------------------------------------------------------------
# Final status decisions: `flagged_buckets > 4` and `total_billed == 0.0`
# ---------------------------------------------------------------------------

def test_flagged_buckets_over_four():
    tenants = [{"account_active": True, "tier": "hot", "has_backup_vault": False,
                "buckets": [{"size_gb": 0, "corrupted": False, "egress_gb": 0}
                            for _ in range(5)]}]
    assert process_storage_tenants(tenants, 10.0)["status"] == "AUDIT_FLAGGED"


def test_flagged_buckets_under_four():
    tenants = [{"account_active": True, "tier": "hot", "has_backup_vault": False,
                "buckets": [{"size_gb": 0, "corrupted": False, "egress_gb": 0}
                            for _ in range(4)]}]
    assert process_storage_tenants(tenants, 10.0)["status"] == "ZERO_USAGE"


def test_total_billed_non_zero_billed():
    assert process_storage_tenants([_tenant("hot", 100)], 10.0)["status"] == "BILLED"


# ---------------------------------------------------------------------------
# monitor_replication_latency — all branches
# ---------------------------------------------------------------------------

def test_monitor_empty_cluster_no_data():
    assert monitor_replication_latency([]) == "NO_DATA"


def test_monitor_single_node_all_low_synced():
    assert monitor_replication_latency([[10, 20, 30]]) == "SYNCED"


def test_monitor_boundary_200_resets_streak():
    assert monitor_replication_latency([[250, 200, 250, 200]]) == "SYNCED"


def test_monitor_boundary_201_counts_as_spike():
    assert monitor_replication_latency([[201, 201]]) == "SYNC_LAG_ALERT"


def test_monitor_streak_below_two_no_alert():
    assert monitor_replication_latency([[300, 100]]) == "SYNCED"


def test_monitor_streak_two_or_more_alert():
    assert monitor_replication_latency([[100, 300, 300]]) == "SYNC_LAG_ALERT"


def test_monitor_alert_in_later_node():
    assert monitor_replication_latency([[50, 50], [10, 250, 300]]) == "SYNC_LAG_ALERT"
