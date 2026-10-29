# Lab 6 — Code and Branch Coverage Analysis

> Cloud Storage Tier — `L6_L7_12`

## Objective

Measure and improve **line coverage** and **branch coverage** of the
`cloud_storage_tier` module using the `coverage` tool, and write test cases
that reach **≥ 90%** coverage on both metrics.

## Module under test

`cloud_storage_tier.py` provides two functions:

| Function | Description |
|----------|-------------|
| `process_storage_tenants(tenants, fixed_support_fee)` | Computes tenant storage and network egress costs across `hot`, `cool`, and `archive` tiers. |
| `monitor_replication_latency(cluster_matrix)` | Monitors distributed cluster nodes for replication latency spikes. |

## Files

| File | Description |
|------|-------------|
| `cloud_storage_tier.py` | The module under test |
| `test_cloud_storage.py` | Starter test file (provided) |
| `CodeCoverageTest_PES1UG24AM250_cloud_storage_tier.py` | Test cases targeting **line coverage** (≥ 90%) |
| `BranchCoverageTest_PES1UG24AM250_cloud_storage_tier.py` | Test cases targeting **branch coverage** (≥ 90%) |
| `code_coverage_report.png` | Terminal screenshot of the code coverage run & report |
| `branch_coverage_report.png` | Terminal screenshot of the branch coverage run & report |

## Setup

```bash
pip install coverage pytest
```

## Running the tests

### 1. Code (line) coverage

```bash
coverage run -m pytest CodeCoverageTest_PES1UG24AM250_cloud_storage_tier.py
coverage report -m
```

### 2. Branch coverage

```bash
coverage run --branch -m pytest BranchCoverageTest_PES1UG24AM250_cloud_storage_tier.py
coverage report -m
```

## Results

| Metric | Coverage |
|--------|----------|
| Line coverage | **100%** |
| Branch coverage | **100%** |
