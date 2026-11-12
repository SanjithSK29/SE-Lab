# Lab 7 — Fuzz Testing with Hypothesis

> Cloud Storage Tier — `L6_L7_12`

## Objective

Explore fuzz testing as a security and quality-assurance technique by
identifying and fixing input-validation bugs in the `processor.py` script using
the [Hypothesis](https://hypothesis.readthedocs.io/) property-based fuzzing
library.

## Module under test

`processor.py` provides three functions:

| Function | Description |
|----------|-------------|
| `parse_storage_quota(quota_str)` | Parses a storage quota string (`500MB`, `20GB`, `2TB`) into Gigabytes. |
| `compute_compression_ratio(size_metric_str)` | Computes `raw_bytes / compressed_bytes` from a `raw:compressed` string. |
| `lookup_bandwidth_tier_rate(tier_descriptor)` | Looks up the egress rate per GB from the first 3 letters of a tier name. |

## Setup

```bash
pip install hypothesis pytest
```

## Running the tests

```bash
pytest test_processor.py
# or
python -m pytest test_processor.py
```

Run the module interactively with:

```bash
python processor.py
```

## Files

| File | Description |
|------|-------------|
| `processor.py` | The hardened (fixed) module under test |
| `test_processor.py` | Property-based fuzz tests written with Hypothesis |
| `screenshots/` | Terminal screenshots for each lab step |
| `Lab_7_FuzzTesting_PES1UG24AM250.pdf` | Final report with screenshots and analysis |
| `L6_L7_12_cloud_storage_tier/` | Reference starter code (provided) |

## Bugs found by fuzzing

| Function | Bug(s) uncovered |
|----------|------------------|
| `parse_storage_quota` | `AttributeError` on `None`; `ValueError` on empty / non-numeric value; `KeyError` on unsupported unit. |
| `compute_compression_ratio` | `AttributeError` on `None`; `ValueError` when `:` missing or values non-numeric; `ZeroDivisionError` when compressed bytes = 0. |
| `lookup_bandwidth_tier_rate` | `AttributeError` on `None`; `KeyError` on empty / unknown tier prefix. |

## Fix approach (defensive programming)

Every function now validates its input and returns `None` instead of raising an
unhandled exception:

* **regex validation** of the quota format (`^\d+(MB|GB|TB)$`) plus `None`/type
  guards.
* **guards** against a missing `:`, non-numeric values, and a zero denominator
  in the compression ratio.
* a **`.get()` lookup** that tolerates unknown tier prefixes, plus `None`/type
  guards.

## Results

After hardening, all three Hypothesis fuzz tests pass:

```
3 passed in 0.17s
```
