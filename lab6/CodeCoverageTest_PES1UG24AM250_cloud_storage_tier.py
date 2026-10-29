"""Code coverage test suite for the Cloud Storage Tier module.

This file targets *line coverage*: every executable statement in
``cloud_storage_tier.py`` should be exercised at least once so the
``coverage report -m`` output reaches 90% (or more) line coverage.

Run:
    coverage run -m pytest CodeCoverageTest_PES1UG24AM250_cloud_storage_tier.py
    coverage report -m
"""

import pytest

from cloud_storage_tier import process_storage_tenants, monitor_replication_latency


# ---------------------------------------------------------------------------
# process_storage_tenants — input validation
# ---------------------------------------------------------------------------

def test_raises_value_error_when_tenants_not_a_list():
    with pytest.raises(ValueError):
        process_storage_tenants("not-a-list", 10.0)


def test_raises_value_error_when_fee_is_negative():
    with pytest.raises(ValueError):
        process_storage_tenants([], -1.0)


# ---------------------------------------------------------------------------
# process_storage_tenants — tenant / tier handling
# ---------------------------------------------------------------------------

def test_single_active_hot_tenant():
    tenants = [
        {
            "account_active": True,
            "tier": "hot",
            "has_backup_vault": False,
            "buckets": [{"size_gb": 100, "corrupted": False, "egress_gb": 50}],
        }
    ]
    result = process_storage_tenants(tenants, 10.0)
    assert result["total_billed"] == 2.5
    assert result["status"] == "BILLED"


def test_cool_tier_rate():
    tenants = [
        {
            "account_active": True,
            "tier": "cool",
            "has_backup_vault": False,
            "buckets": [{"size_gb": 100, "corrupted": False, "egress_gb": 0}],
        }
    ]
    result = process_storage_tenants(tenants, 10.0)
    assert result["total_billed"] == 1.5
    assert result["status"] == "BILLED"


def test_archive_tier_rate():
    tenants = [
        {
            "account_active": True,
            "tier": "archive",
            "has_backup_vault": False,
            "buckets": [{"size_gb": 100, "corrupted": False, "egress_gb": 0}],
        }
    ]
    result = process_storage_tenants(tenants, 10.0)
    assert result["total_billed"] == 0.5
    assert result["status"] == "BILLED"


def test_default_tier_is_hot_when_tier_missing():
    tenants = [
        {
            "account_active": True,
            "has_backup_vault": False,
            "buckets": [{"size_gb": 100, "corrupted": False, "egress_gb": 0}],
        }
    ]
    result = process_storage_tenants(tenants, 10.0)
    assert result["total_billed"] == 2.5


def test_unknown_tier_is_flagged_and_skipped():
    tenants = [
        {
            "account_active": True,
            "tier": "mystery",
            "has_backup_vault": False,
            "buckets": [{"size_gb": 100, "corrupted": False, "egress_gb": 0}],
        }
    ]
    result = process_storage_tenants(tenants, 10.0)
    assert result["total_billed"] == 0.0
    assert result["status"] == "ZERO_USAGE"


def test_inactive_tenant_is_skipped():
    tenants = [
        {
            "account_active": False,
            "tier": "hot",
            "has_backup_vault": False,
            "buckets": [{"size_gb": 100, "corrupted": False, "egress_gb": 0}],
        }
    ]
    result = process_storage_tenants(tenants, 10.0)
    assert result["total_billed"] == 0.0
    assert result["status"] == "ZERO_USAGE"


# ---------------------------------------------------------------------------
# process_storage_tenants — bucket edge cases
# ---------------------------------------------------------------------------

def test_large_bucket_gets_ten_percent_discount():
    tenants = [
        {
            "account_active": True,
            "tier": "hot",
            "has_backup_vault": False,
            "buckets": [{"size_gb": 600, "corrupted": False, "egress_gb": 0}],
        }
    ]
    result = process_storage_tenants(tenants, 10.0)
    assert result["total_billed"] == 13.5


def test_egress_above_100_adds_surcharge():
    tenants = [
        {
            "account_active": True,
            "tier": "hot",
            "has_backup_vault": False,
            "buckets": [{"size_gb": 100, "corrupted": False, "egress_gb": 200}],
        }
    ]
    result = process_storage_tenants(tenants, 10.0)
    assert result["total_billed"] == 10.5


def test_backup_vault_adds_support_fee():
    tenants = [
        {
            "account_active": True,
            "tier": "hot",
            "has_backup_vault": True,
            "buckets": [{"size_gb": 100, "corrupted": False, "egress_gb": 0}],
        }
    ]
    result = process_storage_tenants(tenants, 10.0)
    assert result["total_billed"] == 12.5


def test_zero_size_bucket_is_flagged():
    tenants = [
        {
            "account_active": True,
            "tier": "hot",
            "has_backup_vault": False,
            "buckets": [{"size_gb": 0, "corrupted": False, "egress_gb": 0}],
        }
    ]
    result = process_storage_tenants(tenants, 10.0)
    assert result["status"] == "ZERO_USAGE"


def test_corrupted_archive_bucket_zeroes_charge():
    tenants = [
        {
            "account_active": True,
            "tier": "archive",
            "has_backup_vault": False,
            "buckets": [{"size_gb": 100, "corrupted": True, "egress_gb": 0}],
        }
    ]
    result = process_storage_tenants(tenants, 10.0)
    assert result["total_billed"] == 0.0
    assert result["status"] == "ZERO_USAGE"


def test_corrupted_non_archive_bucket_adds_nothing():
    tenants = [
        {
            "account_active": True,
            "tier": "hot",
            "has_backup_vault": False,
            "buckets": [{"size_gb": 100, "corrupted": True, "egress_gb": 0}],
        }
    ]
    result = process_storage_tenants(tenants, 10.0)
    assert result["total_billed"] == 0.0
    assert result["status"] == "ZERO_USAGE"


def test_audit_flagged_when_more_than_four_flags():
    tenants = [
        {
            "account_active": True,
            "tier": "hot",
            "has_backup_vault": False,
            "buckets": [
                {"size_gb": 0, "corrupted": False, "egress_gb": 0} for _ in range(5)
            ],
        }
    ]
    result = process_storage_tenants(tenants, 10.0)
    assert result["status"] == "AUDIT_FLAGGED"


def test_multiple_tenants_are_summed():
    tenants = [
        {
            "account_active": True,
            "tier": "hot",
            "has_backup_vault": False,
            "buckets": [{"size_gb": 100, "corrupted": False, "egress_gb": 0}],
        },
        {
            "account_active": True,
            "tier": "cool",
            "has_backup_vault": False,
            "buckets": [{"size_gb": 100, "corrupted": False, "egress_gb": 0}],
        },
    ]
    result = process_storage_tenants(tenants, 10.0)
    assert result["total_billed"] == 4.0
    assert result["status"] == "BILLED"


# ---------------------------------------------------------------------------
# monitor_replication_latency
# ---------------------------------------------------------------------------

def test_monitor_no_data_when_empty():
    assert monitor_replication_latency([]) == "NO_DATA"


def test_monitor_synced_when_all_latency_low():
    assert monitor_replication_latency([[50, 60, 70]]) == "SYNCED"


def test_monitor_lag_alert_on_consecutive_spikes():
    assert monitor_replication_latency([[100, 250, 300]]) == "SYNC_LAG_ALERT"


def test_monitor_synced_when_spikes_are_not_consecutive():
    assert monitor_replication_latency([[250, 100, 250, 100]]) == "SYNCED"


def test_monitor_synced_for_empty_node_logs():
    assert monitor_replication_latency([[]]) == "SYNCED"
