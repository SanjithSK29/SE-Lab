"""Cloud Storage Tier processor — hardened against malformed input.

This module contains three functions that parse and compute values used by a
cloud storage service:

* ``parse_storage_quota``  - parse a storage quota string into Gigabytes
* ``compute_compression_ratio`` - compute raw/compressed byte ratio
* ``lookup_bandwidth_tier_rate`` - look up the egress rate for a storage tier

The original (buggy) implementations crashed on a wide range of unexpected
inputs (``None``, empty strings, missing units, non-numeric values, division
by zero, unknown tier prefixes, ...).  After fuzz testing with Hypothesis, the
functions were hardened defensively so that they **never raise an unhandled
exception**.  Any input that cannot be interpreted is rejected gracefully and
returns ``None`` instead of crashing.
"""

import re

# '<digits><2-letter unit>' (case-insensitive), e.g. '500MB', '20GB', '2TB'.
_QUOTA_PATTERN = re.compile(r"^(\d+)(MB|GB|TB)$")

# bytes:unit multiplier that converts a value into Gigabytes (GB).
_QUOTA_MULTIPLIERS = {
    "MB": 0.001,
    "GB": 1.0,
    "TB": 1000.0,
}

# First three letters of a tier name -> egress rate per GB (USD).
_TIER_RATES = {
    "HOT": 0.08,
    "COL": 0.05,
    "ARC": 0.02,
}


def parse_storage_quota(quota_str):
    """
    Parses a storage quota string with a unit suffix into Gigabytes (GB).

    Expected format: ``'<digits><2-letter unit>'`` (e.g. ``'500MB'``,
    ``'20GB'``, ``'2TB'``).  The unit suffix is case-insensitive.

    Returns a formatted string such as ``"Quota: 0.50 GB"`` for valid input,
    or ``None`` when the input is missing, malformed, or uses an unsupported
    unit.
    """
    if not isinstance(quota_str, str):
        return None

    cleaned = quota_str.strip().upper()
    match = _QUOTA_PATTERN.match(cleaned)
    if match is None:
        return None

    value = int(match.group(1))
    unit = match.group(2)
    gb_total = value * _QUOTA_MULTIPLIERS[unit]
    return f"Quota: {gb_total:.2f} GB"


def compute_compression_ratio(size_metric_str):
    """
    Computes the compression ratio: ``raw_bytes / compressed_bytes``.

    Expected format: ``'raw_bytes:compressed_bytes'`` (e.g. ``'1024:256'``).

    Returns the ratio rounded to two decimal places for valid input, or
    ``None`` when the input is missing, malformed, non-numeric, or the
    compressed byte count is zero (which would otherwise cause a division by
    zero).
    """
    if not isinstance(size_metric_str, str):
        return None

    if ":" not in size_metric_str:
        return None

    raw_str, comp_str = size_metric_str.split(":", 1)

    try:
        raw_bytes = float(raw_str)
        comp_bytes = float(comp_str)
    except ValueError:
        return None

    if comp_bytes == 0:
        return None

    ratio = raw_bytes / comp_bytes
    return round(ratio, 2)


def lookup_bandwidth_tier_rate(tier_descriptor):
    """
    Looks up the rate per GB for egress traffic using the first three letters
    of the tier name (e.g. ``'HOT_TIER'``, ``'COLD'``, ``'ARCHIVE'``).

    Returns the matching rate (a float) for a recognised tier prefix, or
    ``None`` when the input is missing, too short, or does not start with a
    known tier prefix.
    """
    if not isinstance(tier_descriptor, str):
        return None

    prefix = tier_descriptor.strip().upper()[:3]
    return _TIER_RATES.get(prefix)


def main():
    print("==== Running parse_storage_quota ====")
    q_input = input("Enter quota (e.g. 500MB, 10GB, 2TB): ")
    print(parse_storage_quota(q_input))

    print("\n==== Running compute_compression_ratio ====")
    c_input = input("Enter raw:compressed bytes (e.g. 1024:256): ")
    print("Compression Ratio:", compute_compression_ratio(c_input))

    print("\n==== Running lookup_bandwidth_tier_rate ====")
    t_input = input("Enter tier descriptor (e.g. HOT_TIER, COLD, ARCHIVE): ")
    print("Rate per GB: $", lookup_bandwidth_tier_rate(t_input))


if __name__ == "__main__":
    main()
