"""Compares movingpandas' `MobilityMetricsCalculator.home_location()`
against HoWDe's `HoWDe_labelling()` on the same stop-sequence data.

- `home_location()` (movingpandas): most-visited location during a fixed
  22:00-07:00 nighttime window, no data-quality filter, sets one single
  home for a user's entire history.
- `HoWDe_labelling()` (HoWDe, https://github.com/LLucchini/HoWDe): a
  sliding-window heuristic with explicit data-quality gates (`C_days_H`,
  `f_hours_H`) that can re-evaluate over time and can legitimately return
  no home when data is too sparse or ambiguous.

Two independent sections, each usable on its own:
1. Synthetic scenarios ("regular", "gappy", "ambiguous_nights") -- always
   run, no extra setup.
2. An optional, user-supplied dataset with ground truth at USER-WEEK
   granularity -- reports accuracy scored per user-week (movingpandas'
   single whole-history guess is broadcast across every week it has data
   for, since it doesn't re-evaluate over time).

Self-contained: only third-party packages (movingpandas, pandas, geopandas,
shapely, geopy, pytest, and optionally pyspark + HoWDe) are imported --
nothing from elsewhere in this repository, so this file can be copied and
run on its own.

--------------------------------------------------------------------------
SETUP
--------------------------------------------------------------------------
    pip install movingpandas pandas geopandas shapely geopy pytest
    pip install pyspark HoWDe   # optional, needed for section 2; needs a working Java

--------------------------------------------------------------------------
RUN -- synthetic scenarios (always available)
--------------------------------------------------------------------------
    pytest test_home_detection.py -v -s
    python test_home_detection.py                  # prints a full report

--------------------------------------------------------------------------
RUN -- against week-level ground truth (per-user-week accuracy)
--------------------------------------------------------------------------
Point WEEKLY_STOPS_PATH at a stops directory (useruuid, loc, start, end) and
WEEKLY_TRUELABELS_PATH at a directory with columns useruuid, s_yy, s_woy,
loc, true_location_type:
    WEEKLY_STOPS_PATH=/path/to/stops WEEKLY_TRUELABELS_PATH=/path/to/truelabels_uwy \\
        pytest test_home_detection.py -v -s -k weekly
    WEEKLY_STOPS_PATH=... WEEKLY_TRUELABELS_PATH=... python test_home_detection.py
"""

import glob
import math
import os
import random

import geopandas as gpd
import movingpandas as mpd
import pandas as pd
import pytest
from geopy.distance import distance as geopy_distance
from shapely.geometry import Point

try:
    from pyspark.sql import SparkSession
    from pyspark.sql import functions as F

    from howde import HoWDe_labelling

    HAVE_HOWDE = True
except ImportError:
    HAVE_HOWDE = False

# No default for the real-data path -- it's opt-in via env var and
# skips/errors cleanly when unset, so this file works out of the box on
# synthetic data alone.
WEEKLY_STOPS_PATH = os.environ.get("WEEKLY_STOPS_PATH")
WEEKLY_TRUELABELS_PATH = os.environ.get("WEEKLY_TRUELABELS_PATH")
WEEKLY_MAX_USERS = int(os.environ.get("WEEKLY_MAX_USERS", 0))  # 0 = all users

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)


# ===========================================================================
# Shared utilities (inlined so this file has no dependency on anything else
# in this repository)
# ===========================================================================
def dedupe_stops(
    df, user_col="useruuid", time_col="start", duration_col=None, verbose=True
):
    """Remove (user_col, time_col) collisions from a stops DataFrame.

    Real stop-sequence exports can contain exact duplicate rows, and
    occasionally two genuinely different rows that share a (user,
    timestamp) pair -- neither should reach movingpandas/HoWDe silently.
    Two passes:
      1. Exact full-row duplicates are dropped outright.
      2. Remaining (user_col, time_col) collisions are resolved by keeping
         the longest-duration row (using `duration_col`/`end`), logged with
         counts; falls back to first-row-wins if no duration signal.
    """
    n0 = len(df)
    df = df.drop_duplicates()
    n1 = len(df)
    exact_dupes_dropped = n0 - n1
    if verbose and exact_dupes_dropped:
        print(
            f"[dedupe_stops] dropped {exact_dupes_dropped} exact full-row duplicates "
            f"({exact_dupes_dropped / n0:.1%} of {n0} input rows)"
        )

    collision_mask = df.duplicated(subset=[user_col, time_col], keep=False)
    if collision_mask.sum() == 0:
        return df

    collisions = df[collision_mask]
    n_groups = collisions.groupby([user_col, time_col]).ngroups

    if duration_col is None and "end" in df.columns:
        duration_col = "end"
    if duration_col is not None and duration_col in df.columns:
        df = df.assign(_dur=(df[duration_col] - df[time_col]))
        df = df.sort_values("_dur", ascending=False)
        rule = (
            f"kept longest-duration row per group (using {duration_col} - {time_col})"
        )
    else:
        rule = (
            "kept first row per group (no duration column available to break ties on)"
        )

    deduped = df[~df.duplicated(subset=[user_col, time_col], keep="first")]
    if "_dur" in deduped.columns:
        deduped = deduped.drop(columns="_dur")

    n_dropped = len(df) - len(deduped)
    if verbose:
        print(
            f"[dedupe_stops] found {n_groups} residual ({user_col}, {time_col}) collision "
            f"groups ({collision_mask.sum()} rows involved, not exact duplicates) -- {rule}. "
            f"Dropped {n_dropped} rows."
        )
    return deduped.sort_values([user_col, time_col]).reset_index(drop=True)


# EPR/Levy-flight fabricated coordinates: HoWDe-shaped stop data has only
# categorical location ids, no lat/lon, but home_location() needs geometry.
# Parameters from Gonzalez, Hidalgo & Barabasi (2008) "Understanding
# individual human mobility patterns", Nature 453, 779-782; placement
# scheme from Song, Koren, Wang & Barabasi (2010) "Modelling the scaling
# properties of human mobility", Nature Physics 6, 818-823 -- the same EPR
# model already cited in movingpandas' own waiting_times()/
# k_radius_of_gyration() docstrings. This does not make the resulting
# distances real, only statistically representative of real human mobility
# distance distributions -- good enough for exercising both detectors on
# realistic-scale data, not for reading any single distance as a real
# measurement.
_JUMP_BETA = 1.75
_JUMP_R0_KM = 1.5
_JUMP_KAPPA_KM = 400.0


def _sample_jump_length_km(
    rng, beta=_JUMP_BETA, r0_km=_JUMP_R0_KM, kappa_km=_JUMP_KAPPA_KM, max_tries=1000
):
    for _ in range(max_tries):
        u = rng.random()
        dr = r0_km * ((1 - u) ** (-1 / (beta - 1)) - 1)
        if rng.random() <= math.exp(-dr / kappa_km):
            return dr
    return kappa_km


def assign_epr_coordinates(df, origin=(48.2082, 16.3738), seed=42):
    """Assign a (lat, lon) to every (useruuid, loc) pair in df via an
    EPR-style exploration walk, processed in time order per user. Returns
    df with two new columns, lat_synth / lon_synth.
    """
    rng = random.Random(seed)
    df_sorted = df.sort_values(["useruuid", "start"])

    assigned = {}
    current_pos = {}
    lat_out, lon_out = [], []
    for row in df_sorted.itertuples(index=False):
        key = (row.useruuid, row.loc)
        if key in assigned:
            lat, lon = assigned[key]
        elif row.useruuid not in current_pos:
            lat, lon = origin  # first stop ever seen for this user -> shared anchor
            assigned[key] = (lat, lon)
        else:
            dr_km = _sample_jump_length_km(rng)
            bearing_deg = rng.uniform(0, 360)
            dest = geopy_distance(kilometers=dr_km).destination(
                current_pos[row.useruuid], bearing=bearing_deg
            )
            lat, lon = dest.latitude, dest.longitude
            assigned[key] = (lat, lon)

        current_pos[row.useruuid] = (lat, lon)
        lat_out.append(lat)
        lon_out.append(lon)

    df_sorted = df_sorted.copy()
    df_sorted["lat_synth"] = lat_out
    df_sorted["lon_synth"] = lon_out
    return df_sorted


# ===========================================================================
# Spark session (module-scoped fixture for pytest; a plain function for
# __main__, same helper either way)
# ===========================================================================
def _make_spark():
    spark = (
        SparkSession.builder.master("local[*]")
        .appName("test_home_detection")
        .getOrCreate()
    )
    spark.conf.set("spark.sql.shuffle.partitions", "4")
    return spark


@pytest.fixture(scope="module")
def spark():
    if not HAVE_HOWDE:
        pytest.skip("pip install pyspark HoWDe")
    s = _make_spark()
    yield s
    s.stop()


# ===========================================================================
# Synthetic scenarios
# ===========================================================================
ORIGIN_DAY = pd.Timestamp("2024-01-01")  # a Monday
N_DAYS = 35  # > HoWDe's default range_window_home=28


def _overnight_stop(uid, loc, day_idx, country="US"):
    """One continuous stay from day 22:00 to (day+1) 07:00 -- HoWDe splits
    multi-day stops into daily segments itself; for movingpandas we only
    ever emit ONE Point per stop row (at its start time), so a single
    overnight stay contributes exactly one nighttime-window count, not one
    per raw ping.
    """
    start = ORIGIN_DAY + pd.Timedelta(days=day_idx, hours=22)
    end = ORIGIN_DAY + pd.Timedelta(days=day_idx + 1, hours=7)
    return (uid, loc, int(start.timestamp()), int(end.timestamp()), country)


def _daytime_stop(uid, loc, day_idx, start_hour, end_hour, country="US"):
    start = ORIGIN_DAY + pd.Timedelta(days=day_idx, hours=start_hour)
    end = ORIGIN_DAY + pd.Timedelta(days=day_idx, hours=end_hour)
    return (uid, loc, int(start.timestamp()), int(end.timestamp()), country)


def build_synthetic_stops(scenario, uid="synthetic_user", seed=0):
    """Returns (stops_df, true_home_loc_or_None).

    `true_home_loc_or_None` is None for "ambiguous_nights", where there is
    deliberately no single correct answer -- that scenario is descriptive
    (report what each detector picks), not a pass/fail check.
    """
    rows = []

    if scenario == "regular":
        for d in range(N_DAYS):
            rows.append(_overnight_stop(uid, "home", d))
            if (ORIGIN_DAY + pd.Timedelta(days=d)).dayofweek < 5:  # weekday
                rows.append(_daytime_stop(uid, "work", d, 9, 17))
            if d % 6 == 0:
                rows.append(_daytime_stop(uid, "cafe", d, 12, 13))
        true_home = "home"

    elif scenario == "gappy":
        import random

        rng = random.Random(seed)
        for d in range(N_DAYS):
            if rng.random() < 0.30:  # only ~30% of nights have data
                rows.append(_overnight_stop(uid, "home", d))
            if (
                ORIGIN_DAY + pd.Timedelta(days=d)
            ).dayofweek < 5 and rng.random() < 0.30:
                rows.append(_daytime_stop(uid, "work", d, 9, 17))
        true_home = "home"

    elif scenario == "ambiguous_nights":
        import random

        rng = random.Random(seed)
        for d in range(N_DAYS):
            loc = "home_a" if rng.random() < 0.5 else "home_b"
            rows.append(_overnight_stop(uid, loc, d))
            if (ORIGIN_DAY + pd.Timedelta(days=d)).dayofweek < 5:
                rows.append(_daytime_stop(uid, "work", d, 9, 17))
        true_home = None

    else:
        raise ValueError(f"unknown scenario {scenario!r}")

    df = pd.DataFrame(rows, columns=["useruuid", "loc", "start", "end", "country"])
    return df.sort_values(["useruuid", "start"]).reset_index(drop=True), true_home


# ===========================================================================
# Coordinate fabrication + reverse lookup
# ===========================================================================
def build_coord_lookup(stops_df, seed=42):
    """(useruuid, loc) -> (lat, lon), plus the reverse mapping, via the
    EPR/Levy-flight fabrication above -- home_location() needs geometry;
    HoWDe-shaped stop data has none.
    """
    coords_df = assign_epr_coordinates(stops_df, seed=seed)
    per_loc = coords_df[["useruuid", "loc", "lat_synth", "lon_synth"]].drop_duplicates(
        subset=["useruuid", "loc"]
    )
    forward = {
        (row.useruuid, row.loc): (row.lat_synth, row.lon_synth)
        for row in per_loc.itertuples(index=False)
    }
    reverse = {
        (row.useruuid, row.lat_synth, row.lon_synth): row.loc
        for row in per_loc.itertuples(index=False)
    }
    return forward, reverse


# ===========================================================================
# Adapter 1: movingpandas home_location()
# ===========================================================================
def run_movingpandas_home_detection(stops_df, forward_lookup, reverse_lookup):
    """One movingpandas Trajectory per user (one Point per STOP, not per raw
    ping, indexed by stop start time). Returns dict[useruuid -> loc or None].
    """
    results = {}
    for uid, g in stops_df.groupby("useruuid"):
        g = g.sort_values("start")
        if len(g) < 2:
            results[uid] = None
            continue
        geometry = [
            Point(forward_lookup[(uid, loc)][1], forward_lookup[(uid, loc)][0])
            for loc in g["loc"]
        ]
        gdf = gpd.GeoDataFrame(
            geometry=geometry,
            index=pd.to_datetime(g["start"], unit="s"),
            crs="EPSG:4326",
        )
        traj = mpd.Trajectory(gdf, traj_id=uid)
        home_pt = mpd.MobilityMetricsCalculator(traj).home_location()
        results[uid] = reverse_lookup.get((uid, home_pt.y, home_pt.x))
    return results


# ===========================================================================
# Adapter 2: HoWDe HoWDe_labelling()
# ===========================================================================
def run_howde_home_detection(spark, stops_df, **config_overrides):
    """Runs HoWDe with its own defaults (unless overridden) and reduces its
    day-level `detect_H_loc` output to one label per user: the modal
    non-null value across all days in the output. HoWDe's natural output is
    per-day (a user's detected home can in principle drift over time); this
    reduction is a deliberate simplification for a single-home comparison,
    not something HoWDe itself does.

    Returns dict[useruuid -> loc or None] plus the raw per-day pandas
    DataFrame (useruuid, date, detect_H_loc), for inspecting non-detection
    rates without re-running Spark.
    """
    cols = ["useruuid", "loc", "start", "end"]
    if "country" in stops_df.columns:
        cols.append("country")
    sdf = spark.createDataFrame(stops_df[cols])

    out = HoWDe_labelling(sdf, verbose=False, **config_overrides)
    daily = out.select("useruuid", "date", "detect_H_loc").dropDuplicates().toPandas()

    results = {}
    for uid, g in daily.groupby("useruuid"):
        non_null = g["detect_H_loc"].dropna()
        results[uid] = non_null.mode().iloc[0] if len(non_null) else None
    return results, daily


# ===========================================================================
# Weekly ground truth: user-week-level labels (useruuid, s_yy, s_woy, loc,
# true_location_type), for datasets where ground truth is annotated per
# week rather than once per user -- optional, off-repo data, never bundled
# with this file.
# ===========================================================================
def load_weekly_stops_and_labels(max_users=WEEKLY_MAX_USERS, seed=42):
    """Returns (stops_df, truelabels_wy_df).

    stops_df: useruuid, loc, start, end -- same shape everything else in
    this file expects.
    truelabels_wy_df: useruuid, s_yy, s_woy, loc, true_location_type --
    week-level ground truth, used as-is (no reduction to a single per-user
    label, unlike the ground-truth section above).
    """
    if not WEEKLY_STOPS_PATH or not WEEKLY_TRUELABELS_PATH:
        raise RuntimeError(
            "Set WEEKLY_STOPS_PATH to a directory of parquet files with columns "
            "useruuid, loc, start, end, and WEEKLY_TRUELABELS_PATH to a directory "
            "with columns useruuid, s_yy, s_woy, loc, true_location_type."
        )
    stop_files = sorted(glob.glob(os.path.join(WEEKLY_STOPS_PATH, "*.parquet")))
    label_files = sorted(glob.glob(os.path.join(WEEKLY_TRUELABELS_PATH, "*.parquet")))
    if not stop_files:
        raise FileNotFoundError(
            f"No parquet files found in WEEKLY_STOPS_PATH={WEEKLY_STOPS_PATH}"
        )
    if not label_files:
        raise FileNotFoundError(
            f"No parquet files found in WEEKLY_TRUELABELS_PATH={WEEKLY_TRUELABELS_PATH}"
        )

    stops = pd.concat([pd.read_parquet(f) for f in stop_files], ignore_index=True)
    # `loc` may be numeric in some exports; HoWDe internally casts it to a
    # string, so its output always comes back as strings -- cast here too,
    # up front, so every downstream merge on `loc` compares like types.
    stops["loc"] = stops["loc"].astype(str)
    stops = dedupe_stops(stops)
    labels = pd.concat([pd.read_parquet(f) for f in label_files], ignore_index=True)
    labels["loc"] = labels["loc"].astype(str)

    all_users = sorted(stops["useruuid"].unique().tolist())
    sample_users = (
        all_users
        if not max_users or max_users >= len(all_users)
        else pd.Series(all_users).sample(n=max_users, random_state=seed).tolist()
    )
    stops = stops[stops["useruuid"].isin(sample_users)].reset_index(drop=True)
    labels = labels[labels["useruuid"].isin(sample_users)].reset_index(drop=True)
    return stops[["useruuid", "loc", "start", "end"]], labels


def _week_year_columns(unix_start_series):
    """s_yy = calendar year, s_woy = ISO week number, computed independently
    from `start` (unix seconds), mirroring Spark's `F.year()` +
    `F.weekofyear()` -- these two don't always agree at year boundaries
    (e.g. Dec 30 2024 is ISO week 1 of 2025 but still gets s_yy=2024), kept
    as-is rather than "fixed" so this matches how the ground-truth labels
    were themselves built.
    """
    dt = pd.to_datetime(unix_start_series, unit="s")
    return dt.dt.year, dt.dt.isocalendar().week.astype(int)


def run_howde_weekly_labels(spark, stops_df, **config_overrides):
    """Week-level output: useruuid, s_yy, s_woy, loc, location_type,
    detect_H_loc -- HoWDe's day-level stop output, with s_yy/s_woy derived
    from each stop's start time and duplicate (useruuid, s_yy, s_woy, loc,
    location_type, detect_H_loc) combinations collapsed.
    """
    cols = ["useruuid", "loc", "start", "end"]
    if "country" in stops_df.columns:
        cols.append("country")
    sdf = spark.createDataFrame(stops_df[cols])

    out = HoWDe_labelling(sdf, verbose=False, **config_overrides)
    wy = (
        out.withColumn(
            "s_woy", F.weekofyear(F.from_unixtime("start").cast("timestamp"))
        )
        .withColumn("s_yy", F.year(F.from_unixtime("start").cast("timestamp")))
        .select("useruuid", "s_yy", "s_woy", "loc", "location_type", "detect_H_loc")
        .dropDuplicates()
    )
    return wy.toPandas()


def movingpandas_weekly_labels(stops_df, mpd_homes, target="H"):
    """Week-level output for movingpandas: since home_location() only ever
    produces ONE home for a user's entire history (no per-week
    re-evaluation), that single pick is broadcast across every week the
    user has stop data in -- "if you commit to this one answer, how often
    is it right that week", not a claim that movingpandas does weekly
    detection.
    """
    df = stops_df.copy()
    df["s_yy"], df["s_woy"] = _week_year_columns(df["start"])
    df["detect_H_loc"] = df["useruuid"].map(mpd_homes)
    df["location_type"] = [
        target if loc == home else "O"
        for loc, home in zip(df["loc"], df["detect_H_loc"])
    ]
    return df[
        ["useruuid", "s_yy", "s_woy", "loc", "location_type", "detect_H_loc"]
    ].drop_duplicates()


def evaluate_weekly_home_accuracy(detectlocs_wy, truelabels_wy, target="H"):
    """Accuracy scored per user-week rather than per user: a true-target-
    labeled user-week where that location wasn't actually visited that week
    (so it never appears in `detectlocs_wy`) drops out of the comparison
    entirely -- it can't be scored either way without a detection to
    compare against.

    detectlocs_wy: useruuid, s_yy, s_woy, loc, location_type, detect_H_loc
    truelabels_wy: useruuid, s_yy, s_woy, loc, true_location_type

    Returns dict(count, detected, acc, none) -- `acc`/`none` as percentages.
    """
    detect_col = f"detect_{target}_loc"
    key = ["useruuid", "s_woy", "s_yy"]

    # Step 1: did this user-week detect ANY target location at all (any day)?
    has_detected = (
        detectlocs_wy.groupby(key)[detect_col]
        .apply(lambda s: bool(s.notna().any()))
        .rename(f"hasdetected_{target}_uw")
        .reset_index()
    )

    # Step 2: true target-labeled user-weeks, joined with the detection flag
    true_target = truelabels_wy[truelabels_wy["true_location_type"] == target]
    true_with_flag = true_target.merge(has_detected, on=key, how="inner")

    # Step 3: one row per (useruuid, s_woy, s_yy, loc) -- prefer the row
    # where this loc WAS the detected target that week (on any day), if any
    labeled = detectlocs_wy.copy()
    labeled["_is_target"] = labeled["loc"] == labeled[detect_col]
    detect_per_loc = labeled.sort_values("_is_target", ascending=False).drop_duplicates(
        subset=key + ["loc"], keep="first"
    )

    # Step 4: match true label to the resolved per-(week, loc) detection
    matched = true_with_flag.merge(
        detect_per_loc[key + ["loc", detect_col]], on=key + ["loc"], how="inner"
    )
    matched[f"match_{target}"] = matched["loc"] == matched[detect_col]

    # Step 5: aggregate
    count_ = len(matched)
    detected_ = int(matched[f"hasdetected_{target}_uw"].sum())
    match_sum = int(matched[f"match_{target}"].sum())
    acc = 100 * match_sum / detected_ if detected_ else float("nan")
    none_pct = 100 * (count_ - detected_) / count_ if count_ else float("nan")
    return {"count": count_, "detected": detected_, "acc": acc, "none": none_pct}


def compare_weekly_accuracy(spark, max_users=WEEKLY_MAX_USERS, seed=42):
    stops_df, truelabels_wy = load_weekly_stops_and_labels(
        max_users=max_users, seed=seed
    )
    forward, reverse = build_coord_lookup(stops_df, seed=seed)

    mpd_homes = run_movingpandas_home_detection(stops_df, forward, reverse)
    mpd_wy = movingpandas_weekly_labels(stops_df, mpd_homes)
    mpd_metrics = evaluate_weekly_home_accuracy(mpd_wy, truelabels_wy)

    howde_wy = run_howde_weekly_labels(spark, stops_df)
    howde_metrics = evaluate_weekly_home_accuracy(howde_wy, truelabels_wy)

    return mpd_metrics, howde_metrics


# ===========================================================================
# pytest -- synthetic (always runs; comparison assertions are HAVE_HOWDE-gated)
# ===========================================================================
def test_movingpandas_always_returns_a_home_even_on_gappy_data():
    stops_df, _true_home = build_synthetic_stops("gappy")
    forward, reverse = build_coord_lookup(stops_df)
    result = run_movingpandas_home_detection(stops_df, forward, reverse)
    assert result["synthetic_user"] is not None, (
        "home_location() has no data-quality filter -- it should always "
        "return a candidate, even from sparse data"
    )


def test_movingpandas_finds_correct_home_on_regular_pattern():
    stops_df, true_home = build_synthetic_stops("regular")
    forward, reverse = build_coord_lookup(stops_df)
    result = run_movingpandas_home_detection(stops_df, forward, reverse)
    assert result["synthetic_user"] == true_home


@pytest.mark.skipif(not HAVE_HOWDE, reason="pip install pyspark HoWDe")
def test_howde_finds_correct_home_on_regular_pattern(spark):
    stops_df, true_home = build_synthetic_stops("regular")
    result, _daily = run_howde_home_detection(spark, stops_df)
    assert result["synthetic_user"] == true_home


@pytest.mark.skipif(not HAVE_HOWDE, reason="pip install pyspark HoWDe")
def test_howde_can_fail_to_detect_home_on_gappy_data(spark):
    """HoWDe's data-quality gates (C_days_H, f_hours_H) mean it can
    legitimately report NO home for some days when coverage is too sparse
    -- movingpandas' home_location() has no equivalent concept and never
    does this (see the companion test above).
    """
    stops_df, _true_home = build_synthetic_stops("gappy")
    _result, daily = run_howde_home_detection(spark, stops_df)
    assert daily["detect_H_loc"].isna().any(), (
        "expected at least one day with no detected home on sparse data -- "
        "if this fails, the gappy scenario needs to be sparser to actually "
        "trigger HoWDe's C_days_H/f_hours_H gates"
    )


@pytest.mark.skipif(not HAVE_HOWDE, reason="pip install pyspark HoWDe")
def test_ambiguous_nights_report_runs(spark, capsys):
    """No single correct answer here by construction -- just confirm both
    detectors run to completion and report what each picked, for the
    __main__ report / -s output to show.
    """
    stops_df, _true_home = build_synthetic_stops("ambiguous_nights")
    forward, reverse = build_coord_lookup(stops_df)
    mpd_result = run_movingpandas_home_detection(stops_df, forward, reverse)
    howde_result, _daily = run_howde_home_detection(spark, stops_df)
    print(
        f"\n[ambiguous_nights] movingpandas picked {mpd_result['synthetic_user']!r}, "
        f"HoWDe picked {howde_result['synthetic_user']!r}"
    )
    assert mpd_result["synthetic_user"] in {"home_a", "home_b"}


# ===========================================================================
# pytest -- weekly ground truth (optional, off-repo data; skips cleanly if
# WEEKLY_STOPS_PATH/WEEKLY_TRUELABELS_PATH aren't set)
# ===========================================================================
requires_weekly = pytest.mark.skipif(
    not (HAVE_HOWDE and WEEKLY_STOPS_PATH and WEEKLY_TRUELABELS_PATH),
    reason="set WEEKLY_STOPS_PATH and WEEKLY_TRUELABELS_PATH (needs pyspark/HoWDe too)",
)


@requires_weekly
def test_weekly_accuracy_reported(spark, capsys):
    """Descriptive (valid range, printed for eyeballing) -- prints both
    methods' user-week accuracy/non-detection.
    """
    mpd_metrics, howde_metrics = compare_weekly_accuracy(spark)
    assert 0 <= mpd_metrics["acc"] <= 100
    assert 0 <= howde_metrics["acc"] <= 100
    print(
        f"\n[weekly] movingpandas: acc={mpd_metrics['acc']:.1f}% "
        f"none={mpd_metrics['none']:.1f}%  (n={mpd_metrics['count']})"
    )
    print(
        f"[weekly] HoWDe:        acc={howde_metrics['acc']:.1f}% "
        f"none={howde_metrics['none']:.1f}%  (n={howde_metrics['count']})"
    )


# ===========================================================================
# Standalone report
# ===========================================================================
if __name__ == "__main__":
    # One SparkSession for the whole script -- repeatedly stop()/getOrCreate()
    # in the same process is flaky (spurious "broken pipe" accumulator
    # errors on shutdown), even though it doesn't affect correctness.
    spark_session = _make_spark() if HAVE_HOWDE else None

    print(f"\n{'#' * 70}\n# Synthetic scenarios\n{'#' * 70}")
    for scenario in ["regular", "gappy", "ambiguous_nights"]:
        stops_df, true_home = build_synthetic_stops(scenario)
        forward, reverse = build_coord_lookup(stops_df)
        mpd_result = run_movingpandas_home_detection(stops_df, forward, reverse)

        print(f"\n--- scenario={scenario!r} (true_home={true_home!r}) ---")
        print(f"movingpandas home_location(): {mpd_result['synthetic_user']!r}")

        if HAVE_HOWDE:
            howde_result, daily = run_howde_home_detection(spark_session, stops_df)
            n_null_days = daily["detect_H_loc"].isna().sum()
            print(
                f"HoWDe HoWDe_labelling():      {howde_result['synthetic_user']!r} "
                f"({n_null_days}/{len(daily)} days with no detected home)"
            )
        else:
            print(
                "[!] pyspark/HoWDe not installed -- pip install pyspark HoWDe to compare"
            )

    print(f"\n{'#' * 70}\n# Weekly ground truth (per-user-week accuracy)\n{'#' * 70}")
    if not HAVE_HOWDE:
        print("[!] pyspark/HoWDe not installed -- skipping. pip install pyspark HoWDe")
    elif not (WEEKLY_STOPS_PATH and WEEKLY_TRUELABELS_PATH):
        print(
            "[!] WEEKLY_STOPS_PATH / WEEKLY_TRUELABELS_PATH not set -- skipping. e.g.:\n"
            "    WEEKLY_STOPS_PATH=/path/to/stops WEEKLY_TRUELABELS_PATH=/path/to/truelabels_uwy \\\n"
            "        python test_home_detection.py"
        )
    else:
        print(
            f"Sampling up to {WEEKLY_MAX_USERS or 'ALL'} users (set WEEKLY_MAX_USERS to change)"
        )
        mpd_metrics, howde_metrics = compare_weekly_accuracy(spark_session)
        print(
            f"\n{'method':<14}{'accuracy':>10}{'non-detected':>16}{'n user-weeks':>15}"
        )
        print(
            f"{'movingpandas':<14}{mpd_metrics['acc']:>9.1f}%{mpd_metrics['none']:>15.1f}%{mpd_metrics['count']:>15}"
        )
        print(
            f"{'HoWDe':<14}{howde_metrics['acc']:>9.1f}%{howde_metrics['none']:>15.1f}%{howde_metrics['count']:>15}"
        )
        print(
            "\n(scored per user-week -- movingpandas' single whole-history home guess is "
            "broadcast across every week it has data for)"
        )

    if spark_session is not None:
        spark_session.stop()
