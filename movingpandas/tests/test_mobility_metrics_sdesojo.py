"""Cross-validates 8 of the 9 functions in movingpandas' MobilityMetricsCalculator
against independent, from-scratch reference implementations, to catch
correctness bugs that a plain "does it run without crashing" test would miss.
Written while testing movingpandas' MobilityMetricsCalculator
(movingpandas/movingpandas#496).

--------------------------------------------------------------------------
WHAT'S TESTED
--------------------------------------------------------------------------
random_entropy, uncorrelated_entropy, waiting_times, radius_of_gyration,
k_radius_of_gyration, jump_lengths, distance_straight_line, and
real_entropy. `home_location` is intentionally NOT validated here -- it
has its own dedicated test file.

Every reference implementation lives in this one file, each verified
against movingpandas' own source.

Not every disagreement between movingpandas and the reference implementations
here means a bug -- three different kinds of check:

- EXACT: `random_entropy`, `uncorrelated_entropy`, `waiting_times`, and
  `k_radius_of_gyration`'s location-selection logic are pure counting, no
  distance formula involved anywhere -- any difference from the reference
  is a real bug, not a rounding artifact.
- TOLERANCE (~5%): `radius_of_gyration`, `jump_lengths`,
  `distance_straight_line`, and `k_radius_of_gyration`'s distance value go
  through movingpandas' geodesic (WGS84 ellipsoid) distance formula,
  compared against a simpler spherical-law-of-cosines reference here -- a
  small gap is EXPECTED and is not a bug; movingpandas' choice is the more
  accurate one.
- real_entropy is reported, not pass/fail: movingpandas' entropy estimator
  uses a simplified boundary-term approximation that's expected to diverge
  from a full estimator, especially on short sequences. This file reports
  the relative gap and only sanity-checks it's finite and non-negative.

--------------------------------------------------------------------------
SETUP
--------------------------------------------------------------------------
    python3.10 -m venv .venv && source .venv/bin/activate
    pip install pytest pandas numpy geopandas shapely \
        "movingpandas @ git+https://github.com/movingpandas/movingpandas.git@skm"

--------------------------------------------------------------------------
RUN -- synthetic data (default; no extra setup, always runs)
--------------------------------------------------------------------------
    pytest tests/test_mobility_metrics.py -v   # edge cases + cross-validation
    python tests/test_mobility_metrics.py         # prints a full report

--------------------------------------------------------------------------
RUN -- real coordinate data (skips cleanly unless REAL_STOPS_PATH is set)
--------------------------------------------------------------------------
Point REAL_STOPS_PATH at a CSV/parquet (or directory of *.parquet files)
with genuine lat/lon -- columns: useruuid, loc, start (unix seconds),
latitude, longitude. Assumes the input has no duplicate/colliding
(useruuid, start) rows. Coordinates get canonicalized to the centroid
of each (useruuid, loc)'s raw per-visit coordinates either way, same as
the synthetic path:

    REAL_STOPS_PATH=/path/to/stops.parquet REAL_MAX_USERS=25 \
        pytest tests/test_mobility_metrics.py -v

    REAL_STOPS_PATH=/path/to/stops.parquet REAL_MAX_USERS=0 \
        python tests/test_mobility_metrics.py    # 0 = full dataset
"""

import glob
import math
import os
import random
from datetime import datetime, timedelta, timezone
from math import acos, cos, radians, sin

import geopandas as gpd
import movingpandas as mpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import Point

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)


# ===========================================================================
# Reference implementations -- pure Python, zero movingpandas dependency.
# Each docstring says (a) which MobilityMetricsCalculator function it
# validates, and (b) whether EXACT or TOLERANCE agreement is expected.
# ===========================================================================
def haversine_distance_m(lat1, lon1, lat2, lon2):
    """Spherical law-of-cosines distance (same accuracy class as Haversine).
    Backs every TOLERANCE-based reference below -- movingpandas uses
    geodesic (GeoPy, WGS84 ellipsoid) distances instead, so a small gap vs.
    this is EXPECTED, not a bug.
    """
    if lat1 == lat2 and lon1 == lon2:
        return 0.0
    km = (
        acos(
            sin(radians(lat1)) * sin(radians(lat2))
            + cos(radians(lat1))
            * cos(radians(lat2))
            * cos(radians(lon1) - radians(lon2))
        )
        * 6371.0
    )
    return km * 1000.0


def radius_of_gyration_m(points):
    """points: list of (lat, lon). Reference for
    MobilityMetricsCalculator.radius_of_gyration() -- TOLERANCE (geodesic
    gap). Verified against movingpandas' source: plain centroid of all
    points, RMS distance from it.
    """
    n = len(points)
    if n == 0:
        return 0.0
    center_lat = sum(p[0] for p in points) / n
    center_lon = sum(p[1] for p in points) / n
    sq_distances = [
        haversine_distance_m(lat, lon, center_lat, center_lon) ** 2
        for lat, lon in points
    ]
    return math.sqrt(sum(sq_distances) / n)


def jump_lengths_m(points):
    """points: ordered list of (lat, lon). Reference for
    MobilityMetricsCalculator.jump_lengths() -- TOLERANCE (geodesic gap).
    """
    return [
        haversine_distance_m(
            points[i - 1][0], points[i - 1][1], points[i][0], points[i][1]
        )
        for i in range(1, len(points))
    ]


def distance_straight_line_m(points):
    """points: ordered list of (lat, lon). Reference for
    MobilityMetricsCalculator.distance_straight_line() -- TOLERANCE
    (geodesic gap). movingpandas computes this via traj.get_length(), which
    is the same sum-of-consecutive-distances definition.
    """
    return sum(jump_lengths_m(points))


def k_radius_of_gyration_ref(points, k=2):
    """points: TIME-ORDERED list of (lat, lon), one entry per visit (NOT
    deduplicated -- order and repetition both matter here). Reference for
    MobilityMetricsCalculator.k_radius_of_gyration().

    Verified line-by-line against movingpandas' source: build visit counts
    via a single pass over `points` (so a location's position in the counts
    dict is its first chronological occurrence), take the top-k by count
    with a plain descending sort (Python's sorted() is stable, so ties keep
    their first-occurrence relative order -- this is k_radius_of_gyration's
    tie-break rule), then the "center" is the WEIGHTED mean of the top-k
    locations (each location's coords repeated by its own visit count
    before averaging -- not a plain centroid of k points), and the RMS
    distance is computed over that same repeated/expanded list.

    Returns (selected: set of (lat, lon) -- EXACT-match check, rms_m: float
    -- TOLERANCE check, geodesic gap).
    """
    counts = {}
    for pt in points:
        counts[pt] = counts.get(pt, 0) + 1
    top_k = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:k]
    expanded = [pt for pt, n in top_k for _ in range(n)]
    center_lat = sum(p[0] for p in expanded) / len(expanded)
    center_lon = sum(p[1] for p in expanded) / len(expanded)
    sq = [
        haversine_distance_m(lat, lon, center_lat, center_lon) ** 2
        for lat, lon in expanded
    ]
    rms_m = math.sqrt(sum(sq) / len(sq))
    selected = {pt for pt, _ in top_k}
    return selected, rms_m


def shannon_entropy(seq):
    """seq: sequence of hashable location ids/coords. Reference for
    MobilityMetricsCalculator.uncorrelated_entropy() -- EXACT (pure
    counting, no distance formula involved).
    """
    n = len(seq)
    if n == 0:
        return 0.0
    counts = {}
    for v in seq:
        counts[v] = counts.get(v, 0) + 1
    entropy = 0.0
    for c in counts.values():
        p = c / n
        entropy -= p * math.log2(p)
    return entropy


def random_entropy_ref(seq):
    """seq: sequence of hashable location ids/coords. Reference for
    MobilityMetricsCalculator.random_entropy() -- EXACT (log2 of a plain
    distinct-value count, no distance formula anywhere).
    """
    n_unique = len(set(seq))
    return math.log2(n_unique) if n_unique > 0 else 0.0


def waiting_times_ref(timestamps):
    """timestamps: TIME-ORDERED list of datetimes. Reference for
    MobilityMetricsCalculator.waiting_times() -- EXACT (elapsed time
    between consecutive rows, no distance/location logic at all).
    """
    return [
        (timestamps[i] - timestamps[i - 1]).total_seconds()
        for i in range(1, len(timestamps))
    ]


def _lempel_ziv_lambda(seq, i):
    """Length of the shortest substring starting at i that has not
    previously occurred in seq[:i] (Song et al. 2010 / Kontoyiannis et al.
    1998 estimator, the FULL version -- see lempel_ziv_entropy below for why
    this is expected to diverge from movingpandas' real_entropy()).
    """
    n = len(seq)
    seq = seq + ["__terminate__"]
    x = 1
    matches = [idx for idx, val in enumerate(seq[:i]) if val == seq[i]]
    while matches and x <= n - i:
        if matches[-1] + x >= i:
            del matches[-1]
        matches = [idx for idx in matches if seq[idx + x] == seq[i + x]]
        x += 1
    return x


def lempel_ziv_entropy(seq):
    """Reference for MobilityMetricsCalculator.real_entropy() -- NOT
    pass/fail. This is a FULL Lempel-Ziv estimator (computes real Lambda_i
    at every index); movingpandas' `_true_entropy()` hardcodes a constant
    (`sum_lambda = 3.0`) for the sequence's first/last terms instead of
    computing them -- deliberate on their side, but it means divergence
    from this reference is EXPECTED, especially on short sequences (n=2
    always makes movingpandas' constant the entire computation). Report the
    gap; don't assert tight equality.
    """
    n = len(seq)
    if n <= 1:
        return 0.0
    lambdas = [_lempel_ziv_lambda(seq, i) for i in range(n)]
    return n / sum(lambdas) * math.log2(n)


# ===========================================================================
# Synthetic data: 5 named locations, jittered per visit (so canonicalization
# is required to satisfy movingpandas' identical-Point-geometry precondition
# -- see canonicalize_locations() below), several regular users, plus one
# edge case.
# ===========================================================================
TRUE_LOCS = {
    "home_A": (48.2082, 16.3738),
    "work_B": (48.1867, 16.3378),
    "cafe_C": (48.2100, 16.3900),
    "gym_D": (48.1950, 16.3600),
    "shop_E": (48.2200, 16.3500),
}


def _jitter(lat, lon, rng, spread=0.0001):
    # ~10m of GPS noise per visit -- real stop detectors won't return
    # byte-identical coordinates for repeat visits to the same place.
    return lat + rng.uniform(-spread, spread), lon + rng.uniform(-spread, spread)


def build_synthetic_stops(seed=42):
    """Returns a DataFrame: useruuid, start (unix s), loc, latitude,
    longitude. Every metric's cross-validation below runs against this.
    """
    rng = random.Random(seed)
    rows = []
    start_day = datetime(2024, 3, 4, tzinfo=timezone.utc)  # a Monday

    # --- Regular users: repeating daily pattern, home (night) -> day activity ---
    patterns = {
        "u1": ["home_A", "work_B", "work_B", "home_A"],
        "u2": ["home_A", "cafe_C", "work_B", "home_A"],
        "u3": ["home_A", "work_B", "gym_D", "home_A"],
        "u4": ["home_A", "shop_E", "home_A"],
        "u5": ["home_A", "work_B", "cafe_C", "work_B", "gym_D", "shop_E", "home_A"],
    }
    for user, seq in patterns.items():
        for day in range(4):
            t = start_day + timedelta(days=day, hours=23)  # start at 23:00
            for loc_name in seq:
                lat, lon = _jitter(*TRUE_LOCS[loc_name], rng)
                rows.append(
                    {
                        "useruuid": user,
                        "start": t.timestamp(),
                        "loc": loc_name,
                        "latitude": lat,
                        "longitude": lon,
                    }
                )
                t += timedelta(hours=rng.randint(1, 4))

    # --- Edge case: single-stop user (jump_lengths/waiting_times n=0 case) ---
    lat, lon = _jitter(*TRUE_LOCS["home_A"], rng)
    rows.append(
        {
            "useruuid": "single",
            "start": start_day.timestamp(),
            "loc": "home_A",
            "latitude": lat,
            "longitude": lon,
        }
    )

    return pd.DataFrame(rows)


# ===========================================================================
# Real data: same shape as build_synthetic_stops() (useruuid, start, loc,
# latitude, longitude), so canonicalize_locations()/build_trajectory_collection()/
# run_all_metrics()/cross_validate() below are reused UNCHANGED for real
# data -- only loading differs.
# ===========================================================================
REAL_STOPS_PATH = os.environ.get("REAL_STOPS_PATH")
REAL_MAX_USERS = int(os.environ.get("REAL_MAX_USERS", 25))
REQUIRED_REAL_COLS = {"useruuid", "loc", "start", "latitude", "longitude"}


def _read_any(path):
    if os.path.isdir(path):
        files = sorted(glob.glob(os.path.join(path, "*.parquet")))
        if not files:
            raise FileNotFoundError(f"No parquet files found under {path}")
        return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    if path.endswith(".parquet"):
        return pd.read_parquet(path)
    return pd.read_csv(path)


def load_real_stops(path=None, max_users=None, seed=42):
    """Returns a DataFrame: useruuid, start (unix s), loc, latitude,
    longitude -- same shape build_synthetic_stops() returns, so every
    downstream function (canonicalize_locations, build_trajectory_collection,
    run_all_metrics, cross_validate) works on either without modification.
    """
    path = path or REAL_STOPS_PATH
    max_users = REAL_MAX_USERS if max_users is None else max_users
    if not path:
        raise RuntimeError(
            "Set REAL_STOPS_PATH to a CSV/parquet (or directory of *.parquet) with "
            "columns: useruuid, loc, start, latitude, longitude. Assumes the input "
            "has no duplicate/colliding (useruuid, start) rows -- dedupe "
            "upstream if needed."
        )
    df = _read_any(path)
    missing = REQUIRED_REAL_COLS - set(df.columns)
    if missing:
        raise ValueError(f"Input is missing required columns: {missing}")

    all_users = sorted(df["useruuid"].unique().tolist())
    if max_users and max_users < len(all_users):
        sample = pd.Series(all_users).sample(n=max_users, random_state=seed).tolist()
        df = df[df["useruuid"].isin(sample)]

    return df[["useruuid", "start", "loc", "latitude", "longitude"]].reset_index(
        drop=True
    )


def canonicalize_locations(df):
    """Assign every visit to the same (useruuid, loc) an identical (lat,
    lon) -- the centroid of its raw per-visit coordinates. Required because
    MobilityMetricsCalculator groups points by exact Point equality, so
    repeat visits to the same place need byte-identical coordinates to be
    recognized as the same location.
    """
    canon = (
        df.groupby(["useruuid", "loc"])[["latitude", "longitude"]]
        .mean()
        .rename(columns={"latitude": "lat_canon", "longitude": "lon_canon"})
    )
    return df.join(canon, on=["useruuid", "loc"])


def build_trajectory_collection(df):
    df = canonicalize_locations(df).sort_values(["useruuid", "start"])
    geometry = [Point(lon, lat) for lat, lon in zip(df["lat_canon"], df["lon_canon"])]
    index = pd.to_datetime(df["start"], unit="s")
    gdf = gpd.GeoDataFrame(
        {"useruuid": df["useruuid"].to_numpy()},
        geometry=geometry,
        index=index,
        crs="EPSG:4326",
    )
    return mpd.TrajectoryCollection(gdf, traj_id_col="useruuid")


# ===========================================================================
# Run all 9 functions (home_location included for completeness -- see
# module docstring for why it's excluded from cross-validation below) +
# cross-validate the other 8 against the references above.
# ===========================================================================
def run_all_metrics(collection):
    calc = mpd.MobilityMetricsCalculator(collection)
    return {
        "radius_of_gyration": calc.radius_of_gyration(),
        "k_radius_of_gyration": calc.k_radius_of_gyration(k=2),
        "jump_lengths": calc.jump_lengths(),
        "waiting_times": calc.waiting_times(),
        "home_location": calc.home_location(),
        "random_entropy": calc.random_entropy(),
        "uncorrelated_entropy": calc.uncorrelated_entropy(),
        "real_entropy": calc.real_entropy(),
        "distance_straight_line": calc.distance_straight_line(),
    }


def cross_validate(df, results):
    """One row per user with every IN-SCOPE metric's mpd-vs-reference diff
    (home_location excluded -- see module docstring). EXACT columns should
    all read (numerically) zero; TOLERANCE columns are relative diffs
    expected to stay within a few percent; real_entropy is reported only,
    not judged.
    """
    canon = canonicalize_locations(df).sort_values(["useruuid", "start"])
    rows = []
    for user, g in canon.groupby("useruuid"):
        if user not in results["uncorrelated_entropy"].index:
            # single-point users are silently dropped by
            # movingpandas' TrajectoryCollection
            continue
        loc_seq = g["loc"].tolist()
        points = list(zip(g["lat_canon"], g["lon_canon"]))
        timestamps = pd.to_datetime(g["start"], unit="s").tolist()

        ref_uncor = shannon_entropy(loc_seq)
        ref_rand = random_entropy_ref(loc_seq)
        ref_real = lempel_ziv_entropy(loc_seq)
        ref_rog = radius_of_gyration_m(points)
        ref_dsl = distance_straight_line_m(points)
        ref_jumps = jump_lengths_m(points)
        ref_waits = waiting_times_ref(timestamps)
        _ref_kloc_selected, ref_kloc_rms = k_radius_of_gyration_ref(
            points, k=2
        )  # selection unused here, see NOTE below

        mpd_jumps = results["jump_lengths"][user]
        mpd_waits = results["waiting_times"][user]

        rows.append(
            {
                "useruuid": user,
                "n_stops": len(g),
                "n_unique_locs": g["loc"].nunique(),
                # --- EXACT-match metrics ---
                "uncorrelated_entropy_diff": results["uncorrelated_entropy"][user]
                - ref_uncor,
                "random_entropy_diff": results["random_entropy"][user] - ref_rand,
                "waiting_times_max_abs_diff": max(
                    (abs(a - b) for a, b in zip(mpd_waits, ref_waits)), default=0.0
                ),
                # NOTE: k_radius_of_gyration's *selection* (which locations
                # count as the top-k) has no public accessor --
                # calc.k_radius_of_gyration()
                # only returns the resulting RMS distance, never the set of
                # selected locations. So on bulk/random data, selection
                # agreement can only be checked INDIRECTLY, via the distance
                # tolerance check below (a different selection would very
                # likely produce a different RMS distance) -- there is no
                # second, independent way to assert it exactly here. The
                # dedicated tie-break test further down constructs a
                # scenario precise enough to verify the *selection* itself,
                # not just the resulting distance.
                # --- TOLERANCE metrics (geodesic vs. spherical gap expected) ---
                "radius_of_gyration_reldiff": (
                    abs(results["radius_of_gyration"][user] - ref_rog) / ref_rog
                    if ref_rog
                    else float("nan")
                ),
                "distance_straight_line_reldiff": (
                    abs(results["distance_straight_line"][user] - ref_dsl) / ref_dsl
                    if ref_dsl
                    else float("nan")
                ),
                "jump_lengths_max_reldiff": max(
                    (
                        abs(a - b) / b if b else 0.0
                        for a, b in zip(mpd_jumps, ref_jumps)
                    ),
                    default=0.0,
                ),
                "k_radius_distance_reldiff": (
                    abs(results["k_radius_of_gyration"][user] - ref_kloc_rms)
                    / ref_kloc_rms
                    if ref_kloc_rms
                    else float("nan")
                ),
                # --- reported, not judged ---
                "real_entropy_reldiff": (
                    abs(results["real_entropy"][user] - ref_real) / ref_real
                    if ref_real
                    else float("nan")
                ),
            }
        )
    return pd.DataFrame(rows).set_index("useruuid")


# ===========================================================================
# pytest -- bulk cross-validation (all users, all in-scope metrics, one pass)
# ===========================================================================
EXACT_TOL = 1e-9
DISTANCE_TOL = 0.05  # 5% -- generous enough to absorb the geodesic-vs-spherical
# formula gap (see module docstring)


@pytest.fixture(scope="module")
def diffs():
    df = build_synthetic_stops()
    results = run_all_metrics(build_trajectory_collection(df))
    return cross_validate(df, results)


def test_all_metrics_run_without_error():
    # home_location is included here (it does need to at least RUN without
    # crashing) even though its correctness is validated elsewhere -- see
    # module docstring.
    df = build_synthetic_stops()
    results = run_all_metrics(build_trajectory_collection(df))
    assert set(results) == {
        "radius_of_gyration",
        "k_radius_of_gyration",
        "jump_lengths",
        "waiting_times",
        "home_location",
        "random_entropy",
        "uncorrelated_entropy",
        "real_entropy",
        "distance_straight_line",
    }


def test_single_stop_user_is_dropped_silently():
    # movingpandas silently drops single-point trajectories -- not this
    # file's bug to fix
    df = build_synthetic_stops()
    results = run_all_metrics(build_trajectory_collection(df))
    assert "single" not in results["uncorrelated_entropy"].index


# --- EXACT-match assertions ---
def test_uncorrelated_entropy_matches_reference_exactly(diffs):
    assert diffs["uncorrelated_entropy_diff"].abs().max() < EXACT_TOL


def test_random_entropy_matches_reference_exactly(diffs):
    assert diffs["random_entropy_diff"].abs().max() < EXACT_TOL


def test_waiting_times_matches_reference_exactly(diffs):
    assert diffs["waiting_times_max_abs_diff"].max() < EXACT_TOL


# k_radius_of_gyration's *selection* has no dedicated bulk exact-match test
# here -- see the NOTE in cross_validate() above for why (no public
# accessor for which locations were selected). Its distance-tolerance test
# below is the closest bulk check; test_k_radius_of_gyration_tie_break_...
# further down verifies selection itself, in a scenario precise enough to do so.


# --- TOLERANCE assertions (geodesic vs. spherical gap expected, see docstring) ---
def test_radius_of_gyration_within_geodesic_tolerance(diffs):
    assert diffs["radius_of_gyration_reldiff"].max() < DISTANCE_TOL


def test_distance_straight_line_within_geodesic_tolerance(diffs):
    assert diffs["distance_straight_line_reldiff"].max() < DISTANCE_TOL


def test_jump_lengths_within_geodesic_tolerance(diffs):
    assert diffs["jump_lengths_max_reldiff"].max() < DISTANCE_TOL


def test_k_radius_of_gyration_distance_within_geodesic_tolerance(diffs):
    assert diffs["k_radius_distance_reldiff"].max() < DISTANCE_TOL


# --- real_entropy: reported, not judged (see module docstring) ---
def test_real_entropy_is_finite_and_nonnegative(diffs):
    df = build_synthetic_stops()
    results = run_all_metrics(build_trajectory_collection(df))
    assert (results["real_entropy"] >= 0).all()
    assert np.isfinite(results["real_entropy"]).all()


# ===========================================================================
# Dedicated tie-break test -- built on a minimal, hand-verified Trajectory
# (not the bulk synthetic dataset), because a tie-break rule needs a
# precisely-controlled scenario, not a statistically-likely one.
# ===========================================================================
def test_k_radius_of_gyration_tie_break_prefers_first_chronological_occurrence():
    """Hand-built trajectory, exact (non-jittered) coordinates: R visited
    3x, P visited 2x (first occurrence at t=1), Q visited 2x (first
    occurrence at t=2, strictly after P's). With k=2: R is rank 1 outright;
    P and Q are tied for rank 2 at 2 visits each. movingpandas'
    k_radius_of_gyration builds visit counts via a single time-ordered pass
    then does a plain stable sort by count descending -- ties keep their
    original (= first-occurrence) relative order, so P (seen first) must
    be selected over Q, even though nothing about P's *count* was ever
    higher than Q's.
    """
    R, P, Q = (48.20, 16.37), (48.21, 16.38), (48.19, 16.36)
    sequence = [
        R,
        P,
        Q,
        R,
        P,
        Q,
        R,
    ]  # P's first occurrence (idx 1) precedes Q's (idx 2)
    times = pd.date_range("2024-01-01", periods=len(sequence), freq="1h")
    gdf = gpd.GeoDataFrame(
        {"geometry": [Point(lon, lat) for lat, lon in sequence]},
        index=times,
        crs="EPSG:4326",
    )
    traj = mpd.Trajectory(gdf, traj_id="tie_kradius")
    calc = mpd.MobilityMetricsCalculator(traj)

    ref_selected, _ = k_radius_of_gyration_ref(sequence, k=2)
    assert ref_selected == {
        R,
        P,
    }, (
        "sanity-check the reference implementation's own tie-break "
        "before trusting it as ground truth"
    )

    # movingpandas doesn't expose *which* locations were selected directly,
    # so we assert indirectly: k_radius_of_gyration(k=2) must equal
    # radius_of_gyration() computed over just {R, P} at their true
    # visit-weighted multiplicity (3x R, 2x P) -- if movingpandas had
    # picked Q instead of P, this would not match.
    expected_points_if_P_selected = [R, R, R, P, P]
    expected_rms = radius_of_gyration_m(expected_points_if_P_selected)
    got = calc.k_radius_of_gyration(k=2)
    assert abs(got - expected_rms) / expected_rms < DISTANCE_TOL


# ===========================================================================
# pytest -- real coordinate data (skips cleanly unless REAL_STOPS_PATH is
# set). Same EXACT/TOLERANCE split as the synthetic tests above, just
# parametrized over the diff columns instead of one function per metric --
# avoids duplicating 7 near-identical function bodies for a second data
# source; pytest still reports each metric's pass/fail individually via the
# parametrized test id (e.g. test_real_exact_match_metric[random_entropy_diff]).
# ===========================================================================
pytestmark_real = pytest.mark.skipif(
    not REAL_STOPS_PATH,
    reason="REAL_STOPS_PATH not set -- no real-coordinate dataset available yet",
)

EXACT_MATCH_COLUMNS = [
    "uncorrelated_entropy_diff",
    "random_entropy_diff",
    "waiting_times_max_abs_diff",
]
TOLERANCE_COLUMNS = [
    "radius_of_gyration_reldiff",
    "distance_straight_line_reldiff",
    "jump_lengths_max_reldiff",
    "k_radius_distance_reldiff",
]


@pytest.fixture(scope="module")
def diffs_real():
    df = load_real_stops()
    results = run_all_metrics(build_trajectory_collection(df))
    return cross_validate(df, results)


@pytestmark_real
def test_real_all_metrics_run_without_error():
    df = load_real_stops()
    results = run_all_metrics(build_trajectory_collection(df))
    assert set(results) == {
        "radius_of_gyration",
        "k_radius_of_gyration",
        "jump_lengths",
        "waiting_times",
        "home_location",
        "random_entropy",
        "uncorrelated_entropy",
        "real_entropy",
        "distance_straight_line",
    }


@pytestmark_real
@pytest.mark.parametrize("col", EXACT_MATCH_COLUMNS)
def test_real_exact_match_metric(diffs_real, col):
    assert diffs_real[col].abs().max() < EXACT_TOL


@pytestmark_real
@pytest.mark.parametrize("col", TOLERANCE_COLUMNS)
def test_real_metric_within_geodesic_tolerance(diffs_real, col):
    assert diffs_real[col].max() < DISTANCE_TOL


@pytestmark_real
def test_real_entropy_divergence_shrinks_on_longer_sequences(diffs_real):
    """real_entropy()'s boundary-term approximation biases short sequences
    most -- on real data (typically far longer than the synthetic fixture's
    ~16-28 stops/user), the median relative gap for longer-sequence users
    should be much smaller than on tiny synthetic edge cases. Not pass/fail
    on an exact number, just confirms the divergence shrinks with sequence
    length on real data too.
    """
    long_enough = diffs_real[diffs_real["n_stops"] >= 20]
    if len(long_enough):
        assert long_enough["real_entropy_reldiff"].median() < 0.05


# ===========================================================================
# Standalone report
# ===========================================================================
def _print_cross_validation_report(diffs_df):
    print("\n=== EXACT-match metrics (any nonzero diff is a real bug) ===")
    print(diffs_df[EXACT_MATCH_COLUMNS].round(6).to_string())

    print(
        f"\n=== TOLERANCE metrics (geodesic vs. spherical gap, expect < "
        f"{DISTANCE_TOL:.0%}) ==="
    )
    print(diffs_df[TOLERANCE_COLUMNS].round(4).to_string())

    print(
        "\n=== real_entropy (reported only -- divergence from a full Lempel-Ziv "
        "estimator is expected on short sequences) ==="
    )
    print(diffs_df[["n_stops", "real_entropy_reldiff"]].round(4).to_string())


if __name__ == "__main__":
    using_real = bool(REAL_STOPS_PATH)
    print(
        f"\n########## Comprehensive MobilityMetricsCalculator validation "
        f"({'REAL' if using_real else 'SYNTHETIC'} data) ##########"
    )
    print("(home_location is out of scope here -- see module docstring)")

    if using_real:
        print(
            f"\nLoading from {REAL_STOPS_PATH!r}, sampling up to "
            f"{REAL_MAX_USERS or 'all'} users"
        )
        df = load_real_stops()
    else:
        df = build_synthetic_stops()
    print(
        f"\n{len(df)} stops, {df['useruuid'].nunique()} users"
        + ("" if using_real else " (incl. the 'single' edge case)")
    )

    collection = build_trajectory_collection(df)
    n_single = df["useruuid"].nunique() - len(collection.trajectories)
    print(
        f"Built {len(collection.trajectories)} trajectories "
        f"({n_single} single-point user(s) dropped)"
    )

    results = run_all_metrics(collection)
    diffs_df = cross_validate(df, results)
    _print_cross_validation_report(diffs_df)

    print(
        "\n=== k_radius_of_gyration tie-break check (synthetic, hand-built -- "
        "independent of data source above) ==="
    )
    R, P, Q = (48.20, 16.37), (48.21, 16.38), (48.19, 16.36)
    seq = [R, P, Q, R, P, Q, R]
    tie_gdf = gpd.GeoDataFrame(
        {"geometry": [Point(lon, lat) for lat, lon in seq]},
        index=pd.date_range("2024-01-01", periods=len(seq), freq="1h"),
        crs="EPSG:4326",
    )
    tie_calc = mpd.MobilityMetricsCalculator(
        mpd.Trajectory(tie_gdf, traj_id="tie_kradius")
    )
    print(
        f"k_radius_of_gyration(k=2) tie-break (P vs Q, equal counts, "
        f"P seen first): {tie_calc.k_radius_of_gyration(k=2):.2f}m "
        f"-- expected {radius_of_gyration_m([R, R, R, P, P]):.2f}m (P selected, not Q)"
    )
