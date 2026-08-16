"""Tests a core question: does movingpandas' TrajectoryStopDetector produce
a stop list where revisits to the same physical place share a location id
and identical coordinates -- and how does that compare to InfoStop, which
is explicitly built to do that?

--------------------------------------------------------------------------
FINDINGS
--------------------------------------------------------------------------
1. TrajectoryStopDetector.get_stop_points() gives one row per VISIT, never
   per LOCATION. There is no location-id column at all -- its `stop_id` is
   `f'{traj_id}_{start_time}'`, unique per visit by construction.
2. Two visits to the literal same physical place get independently
   computed centroids (median of that visit's own raw pings) that are
   close, but NOT identical.
3. InfoStop's `loc` (an Infomap community label) IS a location id: every
   visit sharing a `loc` gets the SAME coordinate, because it comes from
   `compute_label_medians()` -- one canonical value per label, not
   recomputed per visit.
4. Downstream consequence: feeding TrajectoryStopDetector's own output
   straight into movingpandas' own MobilityMetricsCalculator inflates
   entropy metrics, because every revisit looks like a new location.
5. TrajectoryStopDetector has no gap-length protection -- a multi-day data
   gap bracketed by two short stays at the same place is silently reported
   as ONE stop spanning the entire gap. InfoStop's `max_time_between`
   splits it into two correctly-short stays that still get linked to the
   same `loc`.

Self-contained on purpose: no imports from anything else in this repo, so
this single file can be handed to a colleague and run on its own.

--------------------------------------------------------------------------
SETUP
--------------------------------------------------------------------------
    python3.10 -m venv .venv && source .venv/bin/activate
    pip install pytest pandas numpy geopandas shapely \
        "movingpandas @ git+https://github.com/movingpandas/movingpandas.git@skm"
    pip install infostop   # optional: InfoStop-comparison tests skip cleanly
                            # without it, but you want it installed to see
                            # the actual point of this file.

--------------------------------------------------------------------------
RUN -- synthetic data (default; no extra setup, safe to run anywhere)
--------------------------------------------------------------------------
    pytest test_stop_detection_comparison.py -v
    python test_stop_detection_comparison.py              # prints a full report

--------------------------------------------------------------------------
RUN -- real data
--------------------------------------------------------------------------
Both detectors need DENSE RAW GPS PINGS as input, not pre-aggregated stops
(that's the whole thing being tested -- stop detection itself). Point
REAL_PINGS_PATH at a CSV/parquet (or directory of *.parquet files) with
columns: useruuid, latitude, longitude, timestamp (unix seconds).

Detection parameters are also env-overridable; the defaults below were
tuned/validated on synthetic Vienna-scale data (~100m stay radius, ~20min
minimum stay) -- re-tune to match your data's actual GPS noise and expected
stay durations before trusting the numbers on real data:

    REAL_PINGS_PATH=/path/to/pings.parquet \
    REAL_MAX_USERS=25 \
    MPD_MAX_DIAMETER_M=100 MPD_MIN_DURATION_MIN=20 \
    INFOSTOP_R1_M=100 INFOSTOP_R2_M=100 \
    INFOSTOP_MIN_STAYING_S=1200 INFOSTOP_MAX_TIME_BETWEEN_S=86400 \
    INFOSTOP_MIN_SIZE=2 \
        pytest test_stop_detection_comparison.py -v

    (same env vars) python test_stop_detection_comparison.py    # prints a full report

REAL_MAX_USERS=0 runs every user in the file (default samples 25).
"""

import glob
import os
import random
from datetime import timedelta
from pathlib import Path

import geopandas as gpd
import movingpandas as mpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import Point

try:
    from infostop import Infostop

    HAVE_INFOSTOP = True
except ImportError:
    HAVE_INFOSTOP = False

try:
    import matplotlib

    matplotlib.use("Agg")  # save to file, no display needed
    import matplotlib.pyplot as plt

    HAVE_MATPLOTLIB = True
except ImportError:
    HAVE_MATPLOTLIB = False

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)

# ===========================================================================
# Config -- env-overridable, same knobs for synthetic and real data
# ===========================================================================
MPD_MAX_DIAMETER_M = float(os.environ.get("MPD_MAX_DIAMETER_M", 100))
MPD_MIN_DURATION = timedelta(minutes=float(os.environ.get("MPD_MIN_DURATION_MIN", 20)))

INFOSTOP_R1_M = float(os.environ.get("INFOSTOP_R1_M", 100))
INFOSTOP_R2_M = float(os.environ.get("INFOSTOP_R2_M", 100))
INFOSTOP_MIN_STAYING_S = float(os.environ.get("INFOSTOP_MIN_STAYING_S", 1200))
INFOSTOP_MAX_TIME_BETWEEN_S = float(
    os.environ.get("INFOSTOP_MAX_TIME_BETWEEN_S", 86400)
)
INFOSTOP_MIN_SIZE = int(os.environ.get("INFOSTOP_MIN_SIZE", 2))

REAL_PINGS_PATH = os.environ.get("REAL_PINGS_PATH")
REAL_MAX_USERS = int(os.environ.get("REAL_MAX_USERS", 25))
REQUIRED_REAL_COLS = {"useruuid", "latitude", "longitude", "timestamp"}


def _default_out_dir():
    """`test-results/` is this repo's convention for checked-in run output,
    but a colleague running this file standalone (copied elsewhere, no repo
    around it) won't have that directory. Use it if present; otherwise fall
    back to the folder this script itself lives in, rather than creating a
    `test-results/` wherever the script happens to be invoked from.
    """
    env = os.environ.get("STOP_VIZ_OUT_DIR")
    if env:
        return Path(env)
    conventional = Path("test-results")
    if conventional.is_dir():
        return conventional
    return Path(__file__).resolve().parent


OUT_DIR = _default_out_dir()
VIZ_ZOOM_RADIUS_DEG = float(
    os.environ.get("VIZ_ZOOM_RADIUS_DEG", 0.0008)
)  # ~90m at this latitude


# ===========================================================================
# Synthetic data
# ===========================================================================
HOME = (48.2082, 16.3738)  # lat, lon -- Vienna
WORK = (48.1867, 16.3378)


def _jittered_pings(lat, lon, n, start, step_minutes, spread=0.0002, rng=None):
    rng = rng or random.Random(0)
    times = pd.date_range(start, periods=n, freq=f"{step_minutes}min")
    pts = [
        (lat + rng.uniform(-spread, spread), lon + rng.uniform(-spread, spread))
        for _ in range(n)
    ]
    return list(times), pts


def _transit(p_from, p_to, start, step_minutes=5, n=4):
    times = pd.date_range(start, periods=n, freq=f"{step_minutes}min")
    pts = [
        (p_from[0] + (p_to[0] - p_from[0]) * f, p_from[1] + (p_to[1] - p_from[1]) * f)
        for f in [0.25, 0.5, 0.75, 1.0]
    ]
    return list(times), pts


def build_synthetic_pings(seed=0):
    """One user, 2 days, repeatedly visiting the SAME two real places (home,
    work): 4 home visits + 2 work visits total, dense raw GPS pings (not
    pre-aggregated stops -- that's the input shape both detectors actually
    expect). This is the exact scenario the "same place -> same id/coords?"
    question is about.
    """
    rng = random.Random(seed)
    times, pts = [], []
    for day in range(2):
        base = pd.Timestamp("2024-03-04") + pd.Timedelta(days=day)

        t, p = _jittered_pings(
            *HOME, n=10, start=base + pd.Timedelta(hours=8), step_minutes=5, rng=rng
        )
        times += t
        pts += p
        t, p = _transit(HOME, WORK, base + pd.Timedelta(hours=8, minutes=50))
        times += t
        pts += p
        t, p = _jittered_pings(
            *WORK,
            n=10,
            start=base + pd.Timedelta(hours=9, minutes=15),
            step_minutes=5,
            rng=rng,
        )
        times += t
        pts += p
        t, p = _transit(WORK, HOME, base + pd.Timedelta(hours=10, minutes=5))
        times += t
        pts += p
        t, p = _jittered_pings(
            *HOME,
            n=8,
            start=base + pd.Timedelta(hours=10, minutes=45),
            step_minutes=5,
            rng=rng,
        )
        times += t
        pts += p

    df = pd.DataFrame(
        {
            "useruuid": "synthetic_user",
            "latitude": [p[0] for p in pts],
            "longitude": [p[1] for p in pts],
            "timestamp": [int(t.timestamp()) for t in times],
        }
    )
    return df.sort_values("timestamp").reset_index(drop=True)


def build_gap_pings():
    """3 pings at home, a 3-day data gap, 3 more pings at home. Real-world
    equivalent: dead battery / poor signal spanning a stop's boundary.
    """
    times = list(pd.date_range("2024-01-01 08:00", periods=3, freq="12min30s")) + list(
        pd.date_range("2024-01-04 08:00", periods=3, freq="12min30s")
    )
    pts = [(HOME[0] + i * 1e-6, HOME[1] + i * 1e-6) for i in range(6)]
    df = pd.DataFrame(
        {
            "useruuid": "gap_user",
            "latitude": [p[0] for p in pts],
            "longitude": [p[1] for p in pts],
            "timestamp": [int(t.timestamp()) for t in times],
        }
    )
    return df


# ===========================================================================
# Real data loader
# ===========================================================================
def _read_any(path):
    if os.path.isdir(path):
        files = sorted(glob.glob(os.path.join(path, "*.parquet")))
        if not files:
            raise FileNotFoundError(f"No parquet files found under {path}")
        return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    if path.endswith(".parquet"):
        return pd.read_parquet(path)
    return pd.read_csv(path)


def load_real_pings(path=None, max_users=None, seed=42):
    path = path or REAL_PINGS_PATH
    max_users = REAL_MAX_USERS if max_users is None else max_users
    if not path:
        raise RuntimeError(
            "Set REAL_PINGS_PATH to a CSV/parquet (or directory of *.parquet) of "
            "raw GPS pings with columns: useruuid, latitude, longitude, timestamp "
            "(unix seconds)."
        )
    df = _read_any(path)
    missing = REQUIRED_REAL_COLS - set(df.columns)
    if missing:
        raise ValueError(f"Input is missing required columns: {missing}")

    df = df.sort_values(["useruuid", "timestamp"]).reset_index(drop=True)
    all_users = sorted(df["useruuid"].unique().tolist())
    if max_users and max_users < len(all_users):
        sample = pd.Series(all_users).sample(n=max_users, random_state=seed).tolist()
        df = df[df["useruuid"].isin(sample)]
    return df.reset_index(drop=True)


# ===========================================================================
# Detector 1: movingpandas' TrajectoryStopDetector
# ===========================================================================
def run_movingpandas_stop_detection(
    pings_df, max_diameter_m=MPD_MAX_DIAMETER_M, min_duration=MPD_MIN_DURATION
):
    """One row per stop, per user. Columns: useruuid, stop_id, start_time,
    end_time, duration_s, latitude, longitude.

    `stop_id` is `f'{traj_id}_{start_time}'` -- a per-VISIT label, never a
    location id. Nothing here links two visits to the same physical place.
    """
    rows = []
    for uid, g in pings_df.groupby("useruuid"):
        g = g.sort_values("timestamp")
        if len(g) < 2:
            continue
        gdf = gpd.GeoDataFrame(
            {
                "geometry": [
                    Point(lon, lat) for lat, lon in zip(g["latitude"], g["longitude"])
                ]
            },
            index=pd.to_datetime(g["timestamp"], unit="s"),
            crs="EPSG:4326",
        )
        traj = mpd.Trajectory(gdf, traj_id=uid)
        stops = mpd.TrajectoryStopDetector(traj).get_stop_points(
            max_diameter_m, min_duration
        )
        for stop_id, row in stops.iterrows():
            rows.append(
                {
                    "useruuid": uid,
                    "stop_id": stop_id,
                    "start_time": row["start_time"],
                    "end_time": row["end_time"],
                    "duration_s": row["duration_s"],
                    "latitude": row["geometry"].y,
                    "longitude": row["geometry"].x,
                }
            )
    return pd.DataFrame(
        rows,
        columns=[
            "useruuid",
            "stop_id",
            "start_time",
            "end_time",
            "duration_s",
            "latitude",
            "longitude",
        ],
    )


# ===========================================================================
# Detector 2: InfoStop
# ===========================================================================
def _group_consecutive_stops(labels, times, max_time_between):
    """Collapse per-ping InfoStop labels into one row per stop: cuts a new
    group on a label change OR a time gap >= max_time_between, same logic as
    infostop.postprocess.compute_intervals().

    Deliberately NOT using compute_intervals() itself: its source has a bug
    where the trailing group is only flushed when it happens to be a -1
    ("moving") run --
        if loc_prev == -1: final_trajectory.append([loc_prev, t_start, t_end])
    -- silently dropping the final real stop otherwise. Confirmed against
    infostop==<installed version>'s own postprocess.py. Reimplemented here
    so the comparison in this file doesn't inherit that bug.
    """
    labels = np.asarray(labels)
    times = np.asarray(times)
    out = []
    loc_prev, t_start = labels[0], times[0]
    t_end = t_start
    for loc, t in zip(labels[1:], times[1:]):
        if loc == loc_prev and (t - t_end) < max_time_between:
            t_end = t
        else:
            out.append((loc_prev, t_start, t_end))
            t_start = t
            t_end = t
        loc_prev = loc
    out.append((loc_prev, t_start, t_end))
    return out


def run_infostop_stop_detection(
    pings_df,
    r1_m=INFOSTOP_R1_M,
    r2_m=INFOSTOP_R2_M,
    min_staying_s=INFOSTOP_MIN_STAYING_S,
    max_time_between_s=INFOSTOP_MAX_TIME_BETWEEN_S,
    min_size=INFOSTOP_MIN_SIZE,
):
    """One row per stop, per user. Columns: useruuid, loc, start_time,
    end_time, duration_s, latitude, longitude.

    `loc` IS a location id (Infomap community label, prefixed by useruuid).
    Every visit sharing a `loc` gets IDENTICAL latitude/longitude, because
    they come from Infostop.compute_label_medians() -- one canonical value
    per label, not recomputed per visit.

    Processes each user independently (a loop of single-user fit_predict
    calls), matching TrajectoryStopDetector's per-trajectory scope. InfoStop
    also supports a `multiuser` mode that pools stationary points across
    users before clustering (so users sharing a physical place get the same
    `loc`) -- not exercised here, to keep this an apples-to-apples,
    per-trajectory comparison.
    """
    if not HAVE_INFOSTOP:
        raise RuntimeError("pip install infostop to run this")

    rows = []
    for uid, g in pings_df.groupby("useruuid"):
        g = g.sort_values("timestamp")
        if len(g) < min_size:
            continue
        t_unix = g["timestamp"].to_numpy(dtype=float)
        latlon = g[["latitude", "longitude"]].to_numpy(dtype=float)
        data = np.column_stack([latlon, t_unix])

        model = Infostop(
            r1=r1_m,
            r2=r2_m,
            min_staying_time=min_staying_s,
            max_time_between=max_time_between_s,
            min_size=min_size,
            distance_metric="haversine",
        )
        try:
            labels = model.fit_predict(data)
        except Exception:
            continue  # e.g. "No stop events found" -- too few/short stays for this user
        medians = model.compute_label_medians()

        for loc, t_start, t_end in _group_consecutive_stops(
            labels, t_unix, max_time_between_s
        ):
            if loc == -1:
                continue  # moving, not a stop
            lat, lon = medians[loc]
            rows.append(
                {
                    "useruuid": uid,
                    "loc": f"{uid}_{loc}",
                    "start_time": pd.to_datetime(int(t_start), unit="s"),
                    "end_time": pd.to_datetime(int(t_end), unit="s"),
                    "duration_s": t_end - t_start,
                    "latitude": lat,
                    "longitude": lon,
                }
            )
    return pd.DataFrame(
        rows,
        columns=[
            "useruuid",
            "loc",
            "start_time",
            "end_time",
            "duration_s",
            "latitude",
            "longitude",
        ],
    )


# ===========================================================================
# Shared assertions
# ===========================================================================
def assert_no_location_linking(stops_df):
    """movingpandas-shaped output: no column links revisits to the same
    place; `stop_id` is unique per visit by construction."""
    assert "loc" not in stops_df.columns
    assert stops_df["stop_id"].is_unique


def assert_location_linking(stops_df):
    """infostop-shaped output: grouping by `loc`, every stop at a given
    location has identical coordinates (one canonical value per label)."""
    for _loc, g in stops_df.groupby("loc"):
        assert g["latitude"].nunique() == 1
        assert g["longitude"].nunique() == 1


def _near(stops_df, place, tol_deg=0.01):
    return stops_df[
        (stops_df["latitude"].sub(place[0]).abs() < tol_deg)
        & (stops_df["longitude"].sub(place[1]).abs() < tol_deg)
    ]


def _readable_pings(pings_df):
    """Raw pings only carry `timestamp` as unix seconds -- unreadable at a
    glance. For quick visual inspection (e.g. eyeballing build_gap_pings()'s
    case study), add a human-readable `datetime` column and, per user, the
    gap since the previous ping -- the gap column makes a multi-day jump
    between pings immediately obvious in a print, instead of having to do
    unix-second arithmetic in your head.
    """
    df = pings_df.copy()
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="s")
    df["gap_since_prev"] = df.groupby("useruuid")["datetime"].diff()
    return df[
        ["useruuid", "datetime", "gap_since_prev", "latitude", "longitude", "timestamp"]
    ]


# ===========================================================================
# Downstream consequence: feed each detector's own output into
# MobilityMetricsCalculator, which needs identical coordinates for repeat
# visits to register as the same location (see point 1/3 above)
# ===========================================================================
def stops_to_calculator(stops_df):
    gdf = gpd.GeoDataFrame(
        {"useruuid": stops_df["useruuid"].to_numpy()},
        geometry=[
            Point(lon, lat)
            for lat, lon in zip(stops_df["latitude"], stops_df["longitude"])
        ],
        index=pd.to_datetime(stops_df["start_time"]),
        crs="EPSG:4326",
    )
    gdf = gdf.sort_index()
    collection = mpd.TrajectoryCollection(gdf, traj_id_col="useruuid")
    return mpd.MobilityMetricsCalculator(collection)


# ===========================================================================
# Visualization: one user's raw pings + both detectors' stops, side by side
# with a zoomed-in panel -- makes the "same place, same/different coords?"
# question visible at a glance instead of only assertable.
# ===========================================================================
_LABEL_OFFSETS = [(8, 8), (8, -14), (-46, 8), (-46, -14), (8, 22), (-46, 22)]


def _plot_layer(ax, pings_u, mpd_u, infostop_u):
    ax.plot(
        pings_u["longitude"],
        pings_u["latitude"],
        "-",
        color="lightgray",
        linewidth=0.8,
        zorder=1,
    )
    ax.scatter(
        pings_u["longitude"],
        pings_u["latitude"],
        s=12,
        color="gray",
        zorder=1,
        label="raw pings",
    )

    if infostop_u is not None and len(infostop_u):
        ax.scatter(
            infostop_u["longitude"],
            infostop_u["latitude"],
            marker="o",
            s=220,
            facecolors="none",
            edgecolors="steelblue",
            linewidths=2,
            zorder=2,
            label="InfoStop stop (shared coords per loc)",
        )
        for _, r in infostop_u.iterrows():
            ax.annotate(
                str(r["loc"]).rsplit("_", 1)[-1],
                (r["longitude"], r["latitude"]),
                color="steelblue",
                fontsize=8,
                fontweight="bold",
                ha="center",
                va="center",
            )

    if len(mpd_u):
        ax.scatter(
            mpd_u["longitude"],
            mpd_u["latitude"],
            marker="x",
            s=110,
            color="crimson",
            linewidths=2,
            zorder=3,
            label="movingpandas stop (own coords per visit)",
        )
        for i, (_, r) in enumerate(mpd_u.iterrows()):
            ax.annotate(
                r["start_time"].strftime("%m-%d %H:%M"),
                (r["longitude"], r["latitude"]),
                color="crimson",
                fontsize=6,
                xytext=_LABEL_OFFSETS[i % len(_LABEL_OFFSETS)],
                textcoords="offset points",
            )


def plot_stop_detection(
    pings_df,
    mpd_stops,
    infostop_stops,
    user,
    out_path,
    zoom_radius_deg=VIZ_ZOOM_RADIUS_DEG,
):
    """Save a 2-panel PNG for one user: full trajectory (left) + a zoomed-in
    panel (right) centered on their most-visited InfoStop location, at a
    scale small enough to actually see whether movingpandas' per-visit 'x'
    marks land on top of each other or not, next to InfoStop's single 'o'.

    Returns the saved Path. No-ops (returns None) if matplotlib isn't
    installed.
    """
    if not HAVE_MATPLOTLIB:
        return None

    pings_u = pings_df[pings_df["useruuid"] == user].sort_values("timestamp")
    mpd_u = mpd_stops[mpd_stops["useruuid"] == user] if len(mpd_stops) else mpd_stops
    infostop_u = (
        infostop_stops[infostop_stops["useruuid"] == user]
        if infostop_stops is not None and len(infostop_stops)
        else None
    )

    fig, (ax_full, ax_zoom) = plt.subplots(1, 2, figsize=(15, 6.5))
    _plot_layer(ax_full, pings_u, mpd_u, infostop_u)
    ax_full.set_title("Full trajectory")
    ax_full.set_xlabel("longitude")
    ax_full.set_ylabel("latitude")
    ax_full.set_aspect("equal", adjustable="datalim")
    ax_full.legend(loc="best", fontsize=8)

    # zoom on whichever place was visited most often (by InfoStop's loc if
    # available, else just the first movingpandas stop)
    zoom_center = None
    if infostop_u is not None and len(infostop_u):
        top_loc = infostop_u["loc"].value_counts().idxmax()
        top = infostop_u[infostop_u["loc"] == top_loc].iloc[0]
        zoom_center = (top["longitude"], top["latitude"])
    elif len(mpd_u):
        zoom_center = (mpd_u.iloc[0]["longitude"], mpd_u.iloc[0]["latitude"])

    _plot_layer(ax_zoom, pings_u, mpd_u, infostop_u)
    if zoom_center is not None:
        cx, cy = zoom_center
        # correct the longitude radius for latitude compression (1 deg lon
        # covers fewer meters than 1 deg lat away from the equator), so a
        # true equal-aspect square ends up representing an equal-meters box
        lon_radius_deg = zoom_radius_deg / max(np.cos(np.radians(cy)), 1e-6)
        ax_zoom.set_xlim(cx - lon_radius_deg, cx + lon_radius_deg)
        ax_zoom.set_ylim(cy - zoom_radius_deg, cy + zoom_radius_deg)
    ax_zoom.set_title(
        f"Zoomed on most-visited place (±{zoom_radius_deg * 111_000:.0f}m)"
    )
    ax_zoom.set_xlabel("longitude")
    ax_zoom.set_ylabel("latitude")
    # adjustable="box" resizes the subplot box to fit the aspect ratio
    # instead of silently expanding the xlim/ylim we just set (which
    # "datalim" does, and which was making the zoom window wider than
    # requested)
    ax_zoom.set_aspect("equal", adjustable="box")

    n_mpd = len(mpd_u)
    # movingpandas has no location id -- the only way to count "unique
    # locations" is by exact coordinate equality (the same grouping
    # MobilityMetricsCalculator itself uses, e.g. uncorrelated_entropy()).
    # Expect this to come out ~= n_mpd, i.e. every visit looks like its own
    # location -- that IS the finding, not a display bug.
    n_mpd_unique_locs = (
        mpd_u[["latitude", "longitude"]].drop_duplicates().shape[0] if n_mpd else 0
    )

    n_infostop = len(infostop_u) if infostop_u is not None else 0
    n_infostop_unique_locs = (
        infostop_u["loc"].nunique() if infostop_u is not None and len(infostop_u) else 0
    )

    fig.suptitle(
        f"user={user!r}   |   "
        f"movingpandas (x): {n_mpd} stops, {n_mpd_unique_locs} unique coord(s)   |   "
        f"InfoStop (o): {n_infostop} stops, {n_infostop_unique_locs} unique loc(s)"
    )
    fig.tight_layout()

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return out_path


# ===========================================================================
# pytest -- synthetic data (always runs)
# ===========================================================================
def test_movingpandas_stop_points_have_no_location_id_synthetic():
    pings = build_synthetic_pings()
    stops = run_movingpandas_stop_detection(pings)
    assert len(stops) >= 4
    assert_no_location_linking(stops)


def test_movingpandas_revisits_get_different_coordinates_synthetic():
    pings = build_synthetic_pings()
    stops = run_movingpandas_stop_detection(pings)
    near_home = _near(stops, HOME)
    assert len(near_home) >= 3, "expected multiple independently-detected home visits"
    # the whole point: revisits to literally the same place do NOT get
    # identical coordinates -- each stop's centroid is computed independently
    assert near_home["latitude"].nunique() > 1
    assert near_home["longitude"].nunique() > 1


@pytest.mark.skipif(not HAVE_INFOSTOP, reason="pip install infostop")
def test_infostop_links_revisits_to_same_loc_synthetic():
    pings = build_synthetic_pings()
    stops = run_infostop_stop_detection(pings)
    assert "loc" in stops.columns
    near_home = _near(stops, HOME)
    assert len(near_home) >= 3
    # the whole point: InfoStop assigns the SAME loc id, and therefore the
    # SAME coordinates, to every home visit
    assert near_home["loc"].nunique() == 1
    assert_location_linking(stops)


@pytest.mark.skipif(not HAVE_MATPLOTLIB, reason="pip install matplotlib")
def test_visualization_saved_for_one_user_synthetic():
    pings = build_synthetic_pings()
    mpd_stops = run_movingpandas_stop_detection(pings)
    infostop_stops = run_infostop_stop_detection(pings) if HAVE_INFOSTOP else None
    out = plot_stop_detection(
        pings,
        mpd_stops,
        infostop_stops,
        "synthetic_user",
        OUT_DIR / "stop_detection_synthetic_user.png",
    )
    assert out is not None and out.exists() and out.stat().st_size > 0


def test_movingpandas_silently_spans_data_gap():
    pings = build_gap_pings()
    stops = run_movingpandas_stop_detection(
        pings, max_diameter_m=50, min_duration=timedelta(minutes=20)
    )
    assert len(stops) == 1
    assert (
        stops.iloc[0]["duration_s"] > 2.5 * 86400
    ), "should silently count the whole 3-day gap as one stop"


@pytest.mark.skipif(not HAVE_INFOSTOP, reason="pip install infostop")
def test_infostop_does_not_span_data_gap():
    pings = build_gap_pings()
    stops = run_infostop_stop_detection(
        pings,
        r1_m=50,
        r2_m=50,
        min_staying_s=1200,
        max_time_between_s=86400,
        min_size=2,
    )
    assert len(stops) == 2, "expected the gap to split into two separate stay events"
    assert (
        stops["duration_s"] < 3600
    ).all(), "each side of the gap should be a short, correctly-bounded stop"
    assert (
        stops["loc"].nunique() == 1
    ), "but both sides should still be linked as the same place"


def test_downstream_entropy_inflated_without_location_linking():
    """Practical consequence of points 1-3 above: feed each detector's own
    stop list straight into movingpandas' own MobilityMetricsCalculator.
    """
    pings = build_synthetic_pings()

    mpd_stops = run_movingpandas_stop_detection(pings)
    # NOTE: MobilityMetricsCalculator returns a plain float (not a Series)
    # when the collection has only a single trajectory -- see
    # movingpandas/mobility_metrics.py::uncorrelated_entropy, `if
    # len(self._trajectories) == 1: return results[...]`.
    entropy_mpd = stops_to_calculator(mpd_stops).uncorrelated_entropy()
    # ground truth: only 2 real places were ever visited (home, work) -- but
    # movingpandas' own stop list has 6 unlinked visits, so this should read
    # close to log2(6) =~ 2.58, not log2(2) = 1.0
    assert (
        entropy_mpd > 1.5
    ), "expected artificially inflated entropy from unlinked revisits"

    if HAVE_INFOSTOP:
        infostop_stops = run_infostop_stop_detection(pings)
        entropy_infostop = stops_to_calculator(infostop_stops).uncorrelated_entropy()
        assert entropy_infostop < entropy_mpd
        assert (
            abs(entropy_infostop - 1.0) < 0.3
        ), "expected close to log2(2)=1.0 once revisits are linked"


# ===========================================================================
# pytest -- real data (skips cleanly unless REAL_PINGS_PATH is set)
# ===========================================================================
pytestmark_real = pytest.mark.skipif(
    not REAL_PINGS_PATH,
    reason="REAL_PINGS_PATH not set -- no real ping dataset available yet",
)


@pytestmark_real
def test_real_movingpandas_stop_list_has_no_location_id():
    pings = load_real_pings()
    stops = run_movingpandas_stop_detection(pings)
    assert len(stops) > 0
    assert_no_location_linking(stops)


@pytestmark_real
@pytest.mark.skipif(not HAVE_INFOSTOP, reason="pip install infostop")
def test_real_infostop_locations_have_consistent_coordinates():
    pings = load_real_pings()
    stops = run_infostop_stop_detection(pings)
    assert len(stops) > 0
    assert_location_linking(stops)


@pytestmark_real
@pytest.mark.skipif(not HAVE_MATPLOTLIB, reason="pip install matplotlib")
def test_visualization_saved_for_one_user_real():
    pings = load_real_pings()
    user = sorted(pings["useruuid"].unique())[0]
    mpd_stops = run_movingpandas_stop_detection(pings)
    infostop_stops = run_infostop_stop_detection(pings) if HAVE_INFOSTOP else None
    out = plot_stop_detection(
        pings,
        mpd_stops,
        infostop_stops,
        user,
        OUT_DIR / f"stop_detection_real_{user}.png",
    )
    assert out is not None and out.exists() and out.stat().st_size > 0


@pytestmark_real
def test_real_downstream_entropy_comparison_runs():
    """No ground truth on real data, so this only checks the pipeline runs
    end to end and produces a per-user entropy inflation ratio >= 1
    (unlinked can never look LESS diverse than linked, only more or equal) --
    see the __main__ report below for the actual numbers to eyeball.
    """
    pings = load_real_pings()
    mpd_stops = run_movingpandas_stop_detection(pings)
    entropy_mpd = stops_to_calculator(mpd_stops).uncorrelated_entropy()
    # a single sampled user collapses this to a float, not a Series -- see
    # the _fmt_entropy() note in the __main__ block below. Re-run with
    # REAL_MAX_USERS >= 2 to exercise the comparison in this test.
    assert isinstance(entropy_mpd, float) or len(entropy_mpd) > 0

    if HAVE_INFOSTOP and not isinstance(entropy_mpd, float):
        infostop_stops = run_infostop_stop_detection(pings)
        entropy_infostop = stops_to_calculator(infostop_stops).uncorrelated_entropy()
        if not isinstance(entropy_infostop, float):
            common = entropy_mpd.index.intersection(entropy_infostop.index)
            assert len(common) > 0
            assert (entropy_mpd[common] >= entropy_infostop[common] - 1e-9).all()


# ===========================================================================
# Standalone report
# ===========================================================================
if __name__ == "__main__":
    using_real = bool(REAL_PINGS_PATH)
    print(
        f"\n{'#' * 70}\n# {'REAL' if using_real else 'SYNTHETIC'} ping data\n{'#' * 70}"
    )
    if not HAVE_INFOSTOP:
        print("\n[!] infostop is not installed -- only running the movingpandas side.")
        print(
            "    pip install infostop   to see the actual comparison this file is for.\n"
        )

    pings = load_real_pings() if using_real else build_synthetic_pings()
    print(f"\n{len(pings)} pings, {pings['useruuid'].nunique()} user(s)")

    print(
        f"\n{'=' * 70}\nmovingpandas TrajectoryStopDetector "
        f"(max_diameter={MPD_MAX_DIAMETER_M}m, min_duration={MPD_MIN_DURATION})\n{'=' * 70}"
    )
    mpd_stops = run_movingpandas_stop_detection(pings)
    print(
        f"{len(mpd_stops)} stops detected. Columns: {list(mpd_stops.columns)} -- no location id."
    )
    print(mpd_stops.head(10).to_string(index=False))

    if not using_real:
        near_home = _near(mpd_stops, HOME)
        print(f"\n{len(near_home)} stops detected near HOME={HOME}:")
        print(near_home[["stop_id", "latitude", "longitude"]].to_string(index=False))
        print(
            f"-> {near_home['latitude'].nunique()} distinct latitude values, "
            f"{near_home['longitude'].nunique()} distinct longitude values among these home visits."
        )
        print(
            "-> CONFIRMS: same physical place, but no shared id, no shared coordinates."
        )

    if HAVE_INFOSTOP:
        print(
            f"\n{'=' * 70}\nInfoStop "
            f"(r1={INFOSTOP_R1_M}m, r2={INFOSTOP_R2_M}m, min_staying={INFOSTOP_MIN_STAYING_S}s, "
            f"max_time_between={INFOSTOP_MAX_TIME_BETWEEN_S}s)\n{'=' * 70}"
        )
        infostop_stops = run_infostop_stop_detection(pings)
        print(
            f"{len(infostop_stops)} stops detected. Columns: {list(infostop_stops.columns)} -- HAS a location id."
        )
        print(infostop_stops.head(10).to_string(index=False))

        if not using_real:
            near_home = _near(infostop_stops, HOME)
            print(f"\n{len(near_home)} stops detected near HOME={HOME}:")
            print(near_home[["loc", "latitude", "longitude"]].to_string(index=False))
            print(
                f"-> {near_home['loc'].nunique()} distinct loc id(s), "
                f"{near_home['latitude'].nunique()} distinct latitude value(s)."
            )
            print(
                "-> CONFIRMS: same physical place -> same loc id -> same coordinates."
            )
    else:
        infostop_stops = None

    print(f"\n{'=' * 70}\nVisualization\n{'=' * 70}")
    if not HAVE_MATPLOTLIB:
        print(
            "[!] matplotlib is not installed -- skipping. pip install matplotlib to get a PNG here."
        )
    else:
        viz_user = (
            "synthetic_user"
            if not using_real
            else sorted(pings["useruuid"].unique())[0]
        )
        viz_path = OUT_DIR / (
            "stop_detection_synthetic_user.png"
            if not using_real
            else f"stop_detection_real_{viz_user}.png"
        )
        saved = plot_stop_detection(
            pings, mpd_stops, infostop_stops, viz_user, viz_path
        )
        print(f"Saved: {saved.resolve()}")
        print(
            "Open it to inspect: full trajectory on the left, zoomed-in on the "
            "most-visited place on the right -- movingpandas' 'x' marks per visit "
            "vs. InfoStop's single 'o' per location."
        )

    print(
        f"\n{'=' * 70}\nGap-length handling ({'real data -- skipped, synthetic-only check' if using_real else '3-day gap, 3 pings each side'})\n{'=' * 70}"
    )
    if not using_real:
        gap_pings = build_gap_pings()
        print("example case:")
        print(_readable_pings(gap_pings).to_string(index=False))

        gap_mpd = run_movingpandas_stop_detection(
            gap_pings, max_diameter_m=50, min_duration=timedelta(minutes=20)
        )
        print("movingpandas:")
        print(gap_mpd.to_string(index=False))

        if HAVE_INFOSTOP:
            gap_infostop = run_infostop_stop_detection(
                gap_pings,
                r1_m=50,
                r2_m=50,
                min_staying_s=1200,
                max_time_between_s=86400,
                min_size=2,
            )
            print("\nInfoStop:")
            print(gap_infostop.to_string(index=False))

    def _fmt_entropy(x):
        # MobilityMetricsCalculator returns a plain float for a single-user
        # collection (synthetic case), a pd.Series (indexed by useruuid)
        # for multi-user collections (real-data case).
        return f"{x:.4f}" if isinstance(x, float) else x.round(4).to_string()

    print(
        f"\n{'=' * 70}\nDownstream: MobilityMetricsCalculator.uncorrelated_entropy()\n{'=' * 70}"
    )
    entropy_mpd = stops_to_calculator(mpd_stops).uncorrelated_entropy()
    print("Fed with movingpandas' own (unlinked) stop list:")
    print(_fmt_entropy(entropy_mpd))
    if HAVE_INFOSTOP:
        entropy_infostop = stops_to_calculator(infostop_stops).uncorrelated_entropy()
        print("\nFed with InfoStop's (linked) stop list:")
        print(_fmt_entropy(entropy_infostop))
        if isinstance(entropy_mpd, float):
            print(
                f"\nInflation ratio (movingpandas / infostop): {entropy_mpd / entropy_infostop:.2f}"
            )
        else:
            common = entropy_mpd.index.intersection(entropy_infostop.index)
            ratio = (
                entropy_mpd[common] / entropy_infostop[common].replace(0, float("nan"))
            ).round(2)
            print("\nInflation ratio (movingpandas / infostop) per user:")
            print(ratio.to_string())
