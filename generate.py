#!/usr/bin/env python3
"""
Console-style GitHub contribution dashboard -> standalone SVG (dark + light).

    python generate.py --sample              # design with sample-data.json
    python generate.py --sample --variants   # also write every palette/motion variant
    python generate.py                       # real data via GitHub GraphQL API
    python generate.py --make-sample         # regenerate sample-data.json (seeded)

Standard library only. Output: out/dashboard-dark.svg, out/dashboard-light.svg
"""
import argparse
import datetime as dt
import glob
import json
import math
import os
import random
import re
import subprocess
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

# =============================================================================
# CONFIG  (everything you might want to tweak lives here)
# =============================================================================

USER_DEFAULT = "hannesgook"
OUT_DIR = "out"

PALETTE = "warm"            # key of PALETTES below
MOTION = "blink"            # "blink" (blinking terminal cursor after the caption) | "none"
TOTAL = "contributions"     # the big number: "contributions" (matches your profile, includes private
                            # contributions as anonymous counts) | "commits" (public commits only unless
                            # the token can read your private repos)
CAPTIONS = {
    "commits": "commits past year",
    "contributions": "contributions past year",
}

WIDTH = 850                 # viewBox width; README column is ~850px
FONT_SANS = '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif'
FONT_MONO = 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace'

BLINK_SECONDS = 1.06        # terminal cursor blink period
STATS_PITCH = 7.0           # dot size on the separate stats card (main panel uses 8)
STATS_IN_DASHBOARD = True   # draw the all time / this week row at the bottom of the dashboard
STATS_ROW_PITCH = 5.0       # dot size of that row: clearly secondary to the big total
BAR_HEIGHT = 38             # height of the weekly bars, px

# ASCII flame next to the streak. Its size follows the current streak; the characters
# re-roll every frame (SMIL frame swap), so it flickers without moving.
FIRE = True
FIRE_FULL_STREAK = 30       # streak (days) at which the flame reaches full size
FIRE_FRAMES = 8             # distinct flicker frames in the loop
FIRE_FRAME_SECONDS = 0.11   # time per frame
FIRE_CHARS = ":;=+*#%@"     # flame interior, cool -> hot (edges use ( and ))
FIRE_GHOST = 0.2           # opacity of the full-size flame drawn faintly behind the current one (0 = off)
FIRE_COLS, FIRE_ROWS = 12, 9   # character grid the flame is drawn on
FIRE_HALF_WIDTH = 4.0      # half width of the full-size flame at its belly, in characters. The cell is
                           # 6.6 x 8.2 px, so 4.0 is about 53 px wide for 72 px tall: a flame, not a ball
FIRE_WEIGHT = 400          # 400 = fine strokes, 700 = heavy
PANEL = False              # False: no panel fill or frame, so the graphics sit directly on the README page
PAD = 28 if PANEL else 4   # side margin inside the SVG
FIRE_COLORS = None          # None = use the palette's heatmap ramp; or a list of 4 colours dim -> hot

# Header (replaces the typing SVG): a small terminal-style line. Each line holds, then the next
# one sweeps in from the left behind a short front of ASCII noise. Static first frame = the first line.
HEADER_LINES = [
    "I build real-time control systems from scratch",
    "Custom ESP32 flight controllers",
    "Stereo vision and visual odometry",
    "Reinforcement learning on real hardware",
]
HEADER_HOLD = 2.6           # seconds each line stays readable
HEADER_SWEEP_STEP = 0.045   # seconds per sweep frame
HEADER_SWEEP_CHARS = 3      # characters the sweep advances per frame
HEADER_FRONT = 4            # width of the noise front, characters
HEADER_NOISE_CHARS = "/|-_=+<>[]"
HERO_NAME = "Hannes Göök"   # big title at the top of hero.svg
HERO_BG = "#000000"         # hero.svg is one black slab: name, header animation, dashboard, stats
HEADER_SIZE = 14            # font size, px

# Optional dot-matrix titles: (slug, "NAME", "small line under it") writes
# out/title-<slug>-dark|light.svg. Empty: the README uses plain text headings.
PROJECT_TITLES = []
TITLE_PITCH = 4.0           # dot size of the project names (the dashboard total uses 8)

# Heatmap intensity. Both are fixed rules applied to every day; neither changes any number.
#   "quartiles": rank among your active days (each level holds about a quarter of them)
#   "github":    GitHub's own contributionLevel per day, relative to your busiest days, so a
#                few spikes keep most days dim. Falls back to quartiles if the data has no levels.
HEAT_MODE = "quartiles"
HEAT_QUANTILES = (0.25, 0.50, 0.75)
GH_LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}

# Each palette has a dark and a light theme. Keys:
#   surface/border      panel fill and hairlines
#   text/text2/text3    primary, secondary, tertiary text
#   dot_on/dot_off      lit and unlit dot-matrix pixels of the total
#   bar/peak            weekly bars and the busiest week
#   streak              streak rulers (one cell per day)
#   cursor              blinking block cursor
#   heat                heatmap: [zero day, level 1 .. level 4]
_NAVY = {"surface": "#0f141b", "border": "#222a34",
         "text": "#e6edf3", "text2": "#9aa7b6", "text3": "#5f6d7e", "dot_off": "#161c24"}
_MONO_D = {"surface": "#0a0a0a", "border": "#262626",
           "text": "#f2f2f2", "text2": "#a3a3a3", "text3": "#616161", "dot_on": "#f2f2f2", "dot_off": "#181818"}
_MONO_L = {"surface": "#ffffff", "border": "#d6d6d6",
           "text": "#0a0a0a", "text2": "#525252", "text3": "#8c8c8c", "dot_on": "#0a0a0a", "dot_off": "#efefef"}
# Translucent black and white: the same ink on GitHub's dark (#0d1117) or light page, or pure black.
_W = lambda a: f"rgba(255,255,255,{a})"
_K = lambda a: f"rgba(0,0,0,{a})"


def _ink(rgb, solid):
    """One ink colour at several opacities; whatever page it sits on shows through the faint parts."""
    t = lambda o: f"rgba({rgb[0]},{rgb[1]},{rgb[2]},{o})"
    return {"surface": "transparent", "border": t(.16), "text": solid, "text2": t(.7), "text3": t(.45),
            "dot_on": solid, "dot_off": t(.07), "bar": t(.5), "peak": solid, "streak": solid, "cursor": solid,
            "heat": [t(.08), t(.24), t(.45), t(.7), solid]}

PALETTES = {
    "amber": {   # amber gradient on GitHub navy
        "dark": {**_NAVY, "dot_on": "#ffc24f", "bar": "#c98516", "peak": "#ffd27a", "streak": "#ffb020",
                 "cursor": "#ffe2a8",
                 "heat": ["#161c24", "#4a3410", "#8a5a12", "#d08a17", "#ffc24f"]},
        "light": {"surface": "#fcfbf8", "border": "#e4ded4", "text": "#1d1a16", "text2": "#5c554b",
                  "text3": "#958c7f", "dot_on": "#1d1a16", "dot_off": "#efebe4", "bar": "#d18a1f",
                  "peak": "#8a4f00", "streak": "#c47710", "cursor": "#8a4f00",
                  "heat": ["#eeeae3", "#f6d9a2", "#e9a945", "#c47710", "#8a4f00"]},
    },
    "amber_crt": {   # everything amber on pure black, like an old amber terminal
        "dark": {"surface": "#050505", "border": "#2b2112", "text": "#ffc24f", "text2": "#c48b2c",
                 "text3": "#7c5a20", "dot_on": "#ffc24f", "dot_off": "#16110a", "bar": "#c98516",
                 "peak": "#ffe0a0", "streak": "#ffb020", "cursor": "#ffe0a0",
                 "heat": ["#130e08", "#3d2a0b", "#7a5010", "#c27e15", "#ffc94f"]},
        "light": {"surface": "#fff7e8", "border": "#edd9b4", "text": "#4a2f06", "text2": "#7a5419",
                  "text3": "#a8834a", "dot_on": "#4a2f06", "dot_off": "#f6e8cc", "bar": "#d08a1c",
                  "peak": "#6b3d00", "streak": "#b86a00", "cursor": "#6b3d00",
                  "heat": ["#f5e9d2", "#f6d9a2", "#e09a2e", "#bb7210", "#6b3d00"]},
    },
    "mono": {   # pure black and white, translucent so it takes on the page behind it
        "dark": {"surface": "#0a0a0a", "border": _W(.14), "text": "#f2f2f2", "text2": _W(.66), "text3": _W(.4),
                 "dot_on": "#f2f2f2", "dot_off": _W(.07), "bar": _W(.5), "peak": "#ffffff",
                 "streak": "#f2f2f2", "cursor": "#ffffff",
                 "heat": [_W(.07), _W(.2), _W(.4), _W(.66), "#f2f2f2"]},
        "light": {"surface": "#ffffff", "border": _K(.14), "text": "#0a0a0a", "text2": _K(.66), "text3": _K(.45),
                  "dot_on": "#0a0a0a", "dot_off": _K(.06), "bar": _K(.45), "peak": "#0a0a0a",
                  "streak": "#0a0a0a", "cursor": "#0a0a0a",
                  "heat": [_K(.06), _K(.2), _K(.42), _K(.68), "#0a0a0a"]},
    },
    "warm": {   # GitHub ink for text, amber for activity, a real red-to-yellow fire
        "dark": {**_ink((230, 237, 243), "#e6edf3"),
                 "dot_on": "#ffb347", "streak": "#ffb347", "cursor": "#ffb347", "peak": "#ffd27a",
                 "bar": "rgba(255,170,70,.5)", "accent": "#ff9a3c",
                 "heat": ["rgba(230,237,243,.07)", "rgba(255,130,30,.28)", "rgba(255,150,40,.58)",
                          "#f7a23b", "#ffd27a"],
                 "fire": ["#c0392b", "#f0641e", "#ffa733", "#ffe7a3"], "fire_ghost": "#f0641e"},
        "light": {**_ink((31, 35, 40), "#1f2328"),
                  "dot_on": "#c4570b", "streak": "#c4570b", "cursor": "#c4570b", "peak": "#8f3f00",
                  "bar": "rgba(214,110,15,.5)", "accent": "#d9640f",
                  "heat": ["rgba(31,35,40,.06)", "rgba(240,140,30,.3)", "rgba(225,115,15,.58)",
                           "#d36b0c", "#8f3f00"],
                  "fire": ["#9b1c1c", "#d9400f", "#f0860a", "#f5b300"], "fire_ghost": "#d9400f"},
    },
    "github": {   # mono, but inked in GitHub's own text colours so it reads as part of the README
        "dark": _ink((230, 237, 243), "#e6edf3"),
        "light": _ink((31, 35, 40), "#1f2328"),
    },
    "mono_amber": {   # black and white, amber only for peak, streaks and the hottest days
        "dark": {**_MONO_D, "bar": "#8c8c8c", "peak": "#ffb020", "streak": "#ffb020", "cursor": "#ffb020",
                 "heat": ["#181818", "#333333", "#808080", "#c4c4c4", "#ffb020"]},
        "light": {**_MONO_L, "bar": "#9a9a9a", "peak": "#c26a00", "streak": "#c26a00", "cursor": "#c26a00",
                  "heat": ["#efefef", "#d4d4d4", "#7a7a7a", "#474747", "#e08a00"]},
    },
    "ember": {   # deep red through orange to amber
        "dark": {**_NAVY, "dot_on": "#ffd9a0", "bar": "#d8541c", "peak": "#ffd27a", "streak": "#ff7a2e",
                 "cursor": "#ffd27a",
                 "heat": ["#161c24", "#3a1511", "#b23a12", "#f06a1d", "#ffc04d"]},
        "light": {"surface": "#fcfaf8", "border": "#e6ddd7", "text": "#1d1714", "text2": "#5e524b",
                  "text3": "#978a81", "dot_on": "#1d1714", "dot_off": "#f0ebe7", "bar": "#e8693a",
                  "peak": "#8a2a0c", "streak": "#c4441a", "cursor": "#8a2a0c",
                  "heat": ["#eeeae6", "#fbd3c2", "#e8693a", "#c4441a", "#8a2a0c"]},
    },
    "cyan": {   # cyan with amber hot spots (previous round)
        "dark": {**_NAVY, "dot_on": "#e6edf3", "bar": "#1fb6ff", "peak": "#ffb020", "streak": "#ffb020",
                 "cursor": "#ffb020",
                 "heat": ["#161d26", "#0e2d42", "#1a82b8", "#1fb6ff", "#ffb020"]},
        "light": {"surface": "#f8f9fb", "border": "#d5dae1", "text": "#16202b", "text2": "#4a5563",
                  "text3": "#7c8796", "dot_on": "#16202b", "dot_off": "#edf0f3", "bar": "#0072b8",
                  "peak": "#b85f00", "streak": "#b85f00", "cursor": "#b85f00",
                  "heat": ["#e9edf1", "#cfe6f4", "#3a9ed6", "#0a70ad", "#e08a00"]},
    },
    "steel": {   # cool blue-grey, white peaks
        "dark": {**_NAVY, "dot_on": "#dbe6f2", "bar": "#5d7a99", "peak": "#dbe6f2", "streak": "#9fb8d4",
                 "cursor": "#dbe6f2",
                 "heat": ["#161c24", "#1e2a38", "#4a6582", "#7b98b8", "#dbe6f2"]},
        "light": {"surface": "#f8f9fb", "border": "#d5dae1", "text": "#16202b", "text2": "#4a5563",
                  "text3": "#7c8796", "dot_on": "#16202b", "dot_off": "#edf0f3", "bar": "#7389a3",
                  "peak": "#1c2a3c", "streak": "#465c78", "cursor": "#1c2a3c",
                  "heat": ["#eceff3", "#d3dbe5", "#7389a3", "#465c78", "#1c2a3c"]},
    },
}

MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]

# =============================================================================
# DATA
# =============================================================================

GRAPHQL = """query($login: String!) {
  user(login: $login) {
    createdAt
    contributionsCollection {
      totalCommitContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
  }
}"""


def load_dotenv(path=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")):
    """Read KEY=VALUE lines from a local .env (git-ignored). Real environment variables win."""
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    v = v.strip().strip('"').strip("'")
                    if v and not os.environ.get(k.strip()):
                        os.environ[k.strip()] = v
    except FileNotFoundError:
        pass


def get_token():
    load_dotenv()
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if tok:
        return tok.strip()
    try:
        r = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=15)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    sys.exit("No token: put GITHUB_TOKEN=... in .env, set the GITHUB_TOKEN env var, or run `gh auth login`.")


def gql(query, variables, token):
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=body,
        headers={"Authorization": "bearer " + token,
                 "Content-Type": "application/json",
                 "User-Agent": "contribution-dashboard-generator"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = json.load(resp)
    except urllib.error.HTTPError as e:
        sys.exit(f"GitHub API error {e.code}: {e.read().decode(errors='replace')[:300]}")
    if raw.get("errors"):
        sys.exit("GraphQL errors: " + json.dumps(raw["errors"])[:500])
    return raw


def fetch_calendar(user):
    """Two read-only GraphQL requests: the last-year calendar, then the all-time total
    (one contributionsCollection per calendar year since the account was created, summed).
    Private contributions are included as anonymous counts if the profile shows them."""
    token = get_token()
    raw = gql(GRAPHQL, {"login": user}, token)
    u = raw.get("data", {}).get("user")
    if not u:
        sys.exit(f"User '{user}' not found.")
    now = dt.datetime.now(dt.timezone.utc)
    parts = []
    for y in range(int(u["createdAt"][:4]), now.year + 1):
        end = now.strftime("%Y-%m-%dT%H:%M:%SZ") if y == now.year else f"{y}-12-31T23:59:59Z"
        parts.append(f'y{y}: contributionsCollection(from: "{y}-01-01T00:00:00Z", to: "{end}") '
                     "{ contributionCalendar { totalContributions } }")
    years = gql("query($login: String!) { user(login: $login) { " + " ".join(parts) + " } }",
                {"login": user}, token)["data"]["user"]
    raw["all_time"] = sum(v["contributionCalendar"]["totalContributions"] for v in years.values())
    return raw


def calendar_of(raw):
    return raw["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def gh_row(d):
    """GitHub calendar row: Sunday = 0 ... Saturday = 6."""
    return (d.weekday() + 1) % 7


def compute_stats(cal):
    weeks = []
    for w in cal["weeks"]:
        days = [(dt.date.fromisoformat(d["date"]), int(d["contributionCount"]))
                for d in w["contributionDays"]]
        if days:
            weeks.append(days)
    levels = {dt.date.fromisoformat(d["date"]): GH_LEVELS[d["contributionLevel"]]
              for w in cal["weeks"] for d in w["contributionDays"] if d.get("contributionLevel") in GH_LEVELS}
    flat = []  # (date, count, week_index, row)
    for wi, w in enumerate(weeks):
        for d, c in w:
            flat.append((d, c, wi, gh_row(d)))
    counts = [c for _, c, _, _ in flat]
    n = len(counts)

    # Streak rules:
    #   longest = longest run of consecutive days with >= 1 contribution.
    #   current = run ending on the last day in the data; if that day is still 0
    #             (the day isn't over), count back from the day before.
    runs, start = [], None
    for i, c in enumerate(counts):
        if c > 0 and start is None:
            start = i
        if c == 0 and start is not None:
            runs.append((start, i - 1))
            start = None
    if start is not None:
        runs.append((start, n - 1))
    longest = max(runs, key=lambda r: (r[1] - r[0], r[0]), default=None)
    end = n - 1 if counts and counts[-1] > 0 else n - 2
    current = next((r for r in runs if r[1] == end), None)

    weekly = [sum(c for _, c in w) for w in weeks]
    # A week is "partial" if it has fewer than 7 days (calendar edges).
    partial = [len(w) < 7 for w in weeks]
    peak_i = max(range(len(weekly)), key=lambda i: weekly[i])

    nz = sorted(c for c in counts if c > 0)

    def q(p):
        return nz[min(len(nz) - 1, int(p * (len(nz) - 1) + 0.5))] if nz else 0

    thresholds = [q(p) for p in HEAT_QUANTILES]

    return {
        "total": int(cal["totalContributions"]),
        "flat": flat, "weeks": weeks, "weekly": weekly, "partial": partial,
        "ndays": n, "active": sum(1 for c in counts if c > 0),
        "max_day": max(counts) if counts else 0,
        "first": flat[0][0], "last": flat[-1][0],
        "runs": runs,
        "longest": longest, "longest_len": (longest[1] - longest[0] + 1) if longest else 0,
        "current": current, "current_len": (current[1] - current[0] + 1) if current else 0,
        "peak_i": peak_i, "peak": weekly[peak_i],
        "thresholds": thresholds,
        "levels": levels,
    }


def level(c, thresholds):
    return 0 if c <= 0 else 1 + sum(1 for t in thresholds if c > t)


# ---------------------------------------------------------------- sample data

def make_sample(path="sample-data.json", seed=1729, end=dt.date(2026, 11, 10), target=1050,
                commits=880, all_time=1412):
    rnd = random.Random(seed)
    start = end - dt.timedelta(days=364)
    days = [start + dt.timedelta(i) for i in range(365)]

    # Shaped loosely like a real profile: a quiet winter, then busy stretches from May on.
    stretches = [  # (centre, width in days, amplitude)
        (dt.date(2026, 5, 8), 12, 1.8),
        (dt.date(2026, 8, 12), 14, 1.6),
        (dt.date(2026, 10, 22), 18, 2.2),
    ]
    quiet = [(dt.date(2026, 2, 2), dt.date(2026, 2, 22)), (dt.date(2026, 6, 8), dt.date(2026, 6, 20))]

    def poisson(lam):
        L, k, p = math.exp(-lam), 0, 1.0
        while True:
            p *= rnd.random()
            if p <= L:
                return k
            k += 1

    drift = 0.0
    counts = []
    for d in days:
        drift = 0.85 * drift + 0.15 * rnd.gauss(0, 0.6)          # slow week-to-week wander
        weekday = d.weekday() < 5
        lam = (3.0 if weekday else 1.1) * math.exp(drift * 0.5)
        lam *= 0.4 if d < dt.date(2026, 4, 15) else 1.0                # quieter first half
        lam *= 1 + sum(a * math.exp(-(((d - c).days) / w) ** 2) for c, w, a in stretches)
        if any(a <= d <= b for a, b in quiet):
            lam *= 0.06
        p0 = (0.45 if weekday else 0.7) if d < dt.date(2026, 4, 15) else (0.22 if weekday else 0.5)
        counts.append(0 if rnd.random() < p0 else poisson(lam))
    for _ in range(3):                                            # a few big single days
        i = rnd.randrange(180, 360)
        counts[i] += rnd.randint(10, 18)

    idx = {d: i for i, d in enumerate(days)}
    protected = set()
    # longest streak: 27 days in the summer stretch
    ls, ll = idx[dt.date(2026, 7, 29)], 27
    for i in range(ls, ls + ll):
        counts[i] = max(1, counts[i])
        protected.add(i)
    counts[ls - 1] = counts[ls + ll] = 0
    # current streak: last 12 days
    for i in range(365 - 12, 365):
        counts[i] = max(1, counts[i])
        protected.add(i)
    counts[365 - 13] = 0
    protected |= {ls - 1, ls + ll, 365 - 13}
    # break any other run that would rival the longest
    run = 0
    for i in range(365):
        run = run + 1 if counts[i] > 0 else 0
        if run >= 20 and i not in protected:
            counts[i] = 0
            run = 0
    # scale to the target total without creating/removing active days
    tot = sum(counts)
    while tot != target:
        i = rnd.randrange(365)
        if tot > target and counts[i] > 1:
            counts[i] -= 1
            tot -= 1
        elif tot < target and counts[i] > 0:
            counts[i] += 1
            tot += 1

    weeks, cur = [], []
    for d, c in zip(days, counts):
        if gh_row(d) == 0 and cur:
            weeks.append({"contributionDays": cur})
            cur = []
        cur.append({"date": d.isoformat(), "contributionCount": c})
    weeks.append({"contributionDays": cur})
    raw = {"data": {"user": {"contributionsCollection": {
        "totalCommitContributions": commits,   # made up: commits are a subset of contributions
        "contributionCalendar": {"totalContributions": sum(counts), "weeks": weeks}}}},
        "all_time": all_time}                  # made up for the sample
    with open(path, "w", encoding="utf-8") as f:
        json.dump(raw, f, indent=1)
    print(f"wrote {path}: {sum(counts)} contributions over {len(days)} days")



# =============================================================================
# RENDERING
# Everything sits on one visual unit, the square cell: the total on a 5x7 dot
# matrix, weekly volume as block bars, days as heatmap cells, streaks as one
# cell per day. No glow, no gradients.
# =============================================================================

DOT_FONT = {  # 5x7 dot-matrix glyphs, squared VFD style ("1" = lit)
    "0": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["11110", "00001", "00001", "01110", "10000", "10000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["10001", "10001", "10001", "11111", "00001", "00001", "00001"],
    "5": ["11111", "10000", "10000", "11110", "00001", "00001", "11110"],
    "6": ["01110", "10000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00001", "00010", "00100", "00100", "00100"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00001", "01110"],
    ",": ["00", "00", "00", "00", "00", "01", "10"],
    " ": ["00"] * 7,
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01110"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
}


def f(v):
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def style(P):
    r = f"""
.c{{font-family:{FONT_MONO};font-size:12px;font-variant-numeric:tabular-nums}}
.c1{{fill:{P['text']}}} .c2{{fill:{P['text2']}}} .c3{{fill:{P['text3']}}}
.cv{{font-size:15px;font-weight:600;fill:{P['streak']}}}
.dv{{stroke:{P['border']};stroke-width:1}}
.on{{fill:{P['dot_on']}}} .off{{fill:{P['dot_off']}}}
.bar{{fill:{P['bar']}}} .pk{{fill:{P['peak']}}} .pt{{fill:{P['bar']};opacity:.45}}
.st{{fill:{P['streak']}}} .cu{{fill:{P['cursor']}}}
"""
    for i, c in enumerate(P["heat"]):
        r += f".h{i}{{fill:{c}}}\n"
    return "<style>" + " ".join(x.strip() for x in r.strip().splitlines()) + "</style>"


def dot_matrix(text, x, y, pitch, on_cls="on"):
    glyphs = [DOT_FONT[ch] for ch in text]
    lit, cx = set(), 0
    for g in glyphs:
        for r, row in enumerate(g):
            for c, bit in enumerate(row):
                if bit == "1":
                    lit.add((cx + c, r))
        cx += len(g[0]) + 1
    on, off, s = [], [], pitch * 0.85
    rx = f(pitch / 10)
    for c in range(cx - 1):
        for r in range(7):
            rect = f'<rect x="{f(x + c * pitch)}" y="{f(y + r * pitch)}" width="{f(s)}" height="{f(s)}" rx="{rx}"/>'
            (on if (c, r) in lit else off).append(rect)
    return [f'<g class="off">{"".join(off)}</g>', f'<g class="{on_cls}">{"".join(on)}</g>']


def matrix_cols(text):
    return sum(len(DOT_FONT[ch][0]) for ch in text) + len(text) - 1


def fire_frames(streak, cols, rows, seed=7):
    """Return FIRE_FRAMES grids of (char, level) or None: an upright, filled ASCII flame with
    ( ) edges. Height and width follow the streak; every frame re-rolls the characters and the
    flame's sway, so it flickers in place. Deterministic: same streak -> same frames."""
    rnd = random.Random(seed)
    s = min(1.0, streak / FIRE_FULL_STREAK)
    h = 2.2 + (rows - 2.4) * s ** 0.6          # flame height, rows (grows faster than the width)
    hw = 1.4 + (FIRE_HALF_WIDTH - 1.4) * s ** 0.7   # half width at the belly, columns
    if streak == 0:
        h, hw = 1.2, 0.8                        # no streak: a small ember
    base_y, cx = rows - 0.2, cols / 2
    belly = 0.26                                # how far up the widest point sits (0 base .. 1 tip)
    frames = []
    for _ in range(FIRE_FRAMES):
        phase = rnd.uniform(0, 6.28)
        grid = [[None] * cols for _ in range(rows)]
        for y in range(rows):
            v = (base_y - (y + 0.5)) / h                # 0 at the base, 1 at the tip
            if v < 0:
                continue
            sway = 0.3 * hw * v ** 1.5 * math.sin(phase + v * 4.5)   # the tip licks, the base stays put
            if v < belly:                               # round bottom
                w = hw * (1 - ((belly - v) / belly) ** 2) ** 0.4
            elif v < 1:                                 # teardrop: slightly concave taper to a point
                w = hw * (1 - (v - belly) / (1 - belly)) ** 1.25
            else:
                w = 0
            w *= 1 + rnd.uniform(-0.12, 0.12)           # ragged, flickering edge
            for x in range(cols):
                dx = abs(x + 0.5 - cx - sway)
                if w > 0.25 and dx < w:
                    heat = (1 - dx / w) ** 0.6 * (1 - 0.5 * v) + rnd.uniform(-0.16, 0.16)
                    heat = max(0.05, min(1.0, heat))
                    ch = FIRE_CHARS[min(len(FIRE_CHARS) - 1, int(heat * len(FIRE_CHARS)))]
                    grid[y][x] = (ch, 1 + min(3, int(heat * 4)))
                elif 1 <= v < 1.35 and dx < 1.2 and rnd.random() < 0.25 * s:
                    grid[y][x] = (rnd.choice("'.`"), 1)  # sparks above the tip
        for row in grid:                                # outline: ( on the left, ) on the right
            for x, c in enumerate(row):
                if not c or c[0] in "'.`":
                    continue
                left = x == 0 or not row[x - 1] or row[x - 1][0] in "'.`"
                right = x == cols - 1 or not row[x + 1] or row[x + 1][0] in "'.`"
                if left and right:
                    row[x] = ("^", 2)
                elif left:
                    row[x] = ("(", 2)
                elif right:
                    row[x] = (")", 2)
        frames.append(grid)
    return frames


def fire_svg(frames, x0, y0, cw, lh, size, motion, colors):
    out = []
    n = len(frames)
    dur = n * FIRE_FRAME_SECONDS
    for k, grid in enumerate(frames):
        if motion == "none" and k:
            break
        rows = []
        for r, line in enumerate(grid):
            idx = [i for i, c in enumerate(line) if c]
            if not idx:
                continue
            a, b = idx[0], idx[-1]
            runs, cur, buf = [], None, ""
            for c in line[a:b + 1]:
                lv = c[1] if c else 0
                ch = escape(c[0]) if c else " "
                if lv != cur and buf:
                    runs.append((cur, buf))
                    buf = ""
                cur, buf = lv, buf + ch
            runs.append((cur, buf))
            spans = "".join(f'<tspan fill="{colors[4]}" fill-opacity="{FIRE_GHOST}" style="font-weight:400">{t}</tspan>'
                            if lv == 5 else f'<tspan fill="{colors[lv - 1]}">{t}</tspan>' if lv else t
                            for lv, t in runs)
            rows.append(f'<text x="{f(x0 + a * cw)}" y="{f(y0 + (r + 1) * lh)}" textLength="{f((b - a + 1) * cw)}" '
                        f'lengthAdjust="spacingAndGlyphs" xml:space="preserve">{spans}</text>')
        anim = ""
        if motion != "none" and n > 1:
            if k == 0:
                anim = (f'<animate attributeName="visibility" calcMode="discrete" dur="{f(dur)}s" '
                        f'repeatCount="indefinite" values="visible;hidden" keyTimes="0;{1 / n:.4f}"/>')
            else:
                anim = (f'<animate attributeName="visibility" calcMode="discrete" dur="{f(dur)}s" '
                        f'repeatCount="indefinite" values="hidden;visible;hidden" '
                        f'keyTimes="0;{k / n:.4f};{(k + 1) / n:.4f}"/>')
        vis = "visible" if k == 0 else "hidden"
        out.append(f'<g class="c" style="font-size:{size}px;font-weight:{FIRE_WEIGHT}" visibility="{vis}">{anim}{"".join(rows)}</g>')
    return out


def panel(P, H):
    if not PANEL:
        return ""
    return f'<rect x=".5" y=".5" width="{WIDTH - 1}" height="{H - 1}" rx="6" fill="{P["surface"]}" stroke="{P["border"]}"/>'


def render(S, palette=None, theme="dark", motion=None, total=None, stats=None):
    P = PALETTES[palette or PALETTE][theme]
    motion, total = motion or MOTION, total or TOTAL
    n = len(S["weeks"])
    L, R = PAD, WIDTH - PAD
    pitch = 8.0
    o = [style(P)]

    # ---- the big number (dot matrix) + caption with blinking cursor
    value = {"commits": S["commits"], "contributions": S["total"]}[total]
    o += dot_matrix(f"{value:,}", L, 28, pitch)
    cap, cap_y = CAPTIONS[total], 28 + 7 * pitch + 22
    cap_w = len(cap) * 12 * 0.6            # textLength pins the width on every OS/font
    o.append(f'<text class="c c2" x="{L}" y="{f(cap_y)}" textLength="{f(cap_w)}" '
             f'lengthAdjust="spacing">{cap}</text>')
    if motion == "blink":
        o.append(f'<rect class="cu" x="{f(L + cap_w + 4)}" y="{f(cap_y - 9.5)}" width="6.5" height="12">'
                 f'<animate attributeName="opacity" calcMode="discrete" values="1;0" keyTimes="0;.5" '
                 f'dur="{BLINK_SECONDS}s" repeatCount="indefinite"/></rect>')

    # ---- current streak: number on the same dot matrix, last 14 days as cells under it
    streak = str(S["current_len"])
    sw = matrix_cols(streak) * pitch - 1.2
    o += dot_matrix(streak, R - sw, 28, pitch, on_cls="st")
    days = S["flat"][-14:]
    run = set(range(S["current"][0], S["current"][1] + 1)) if S["current"] else set()
    first = len(S["flat"]) - len(days)
    label = "day streak"
    lab_w = len(label) * 12 * 0.6
    o.append(f'<text class="c c2" x="{f(R)}" y="{f(cap_y)}" text-anchor="end" textLength="{f(lab_w)}" '
             f'lengthAdjust="spacing">{label}</text>')
    cx1 = R - lab_w - 14
    lit, dim, off = [], [], []
    for k, (_, c, _, _) in enumerate(days):
        x = cx1 - (len(days) - k) * 10 + 2
        rect = f'<rect x="{f(x)}" y="{f(cap_y - 8.5)}" width="8" height="8" rx="1.2"/>'
        (lit if first + k in run else dim if c > 0 else off).append(rect)
    o += [f'<g class="st">{"".join(lit)}</g>', f'<g class="h1">{"".join(dim)}</g>',
          f'<g class="off">{"".join(off)}</g>']

    # ---- ASCII fireball beside the streak, sized by it
    if FIRE:
        cw, lh, fsize, rows, cols = 6.6, 8.2, 11, FIRE_ROWS, FIRE_COLS
        fx1 = R - sw - 18                       # just left of the streak number
        fx0 = fx1 - cols * cw
        colors = FIRE_COLORS or P.get("fire") or [P["heat"][2], P["heat"][3], P["heat"][4], P["peak"]]
        frames = fire_frames(S["current_len"], cols, rows)
        if FIRE_GHOST and S["current_len"] < FIRE_FULL_STREAK:
            full = fire_frames(FIRE_FULL_STREAK, cols, rows)
            frames = [[[c or (g and (g[0], 5)) for c, g in zip(rc, rg)] for rc, rg in zip(fc, fg)]
                      for fc, fg in zip(frames, full)]
            colors = colors + [P.get("fire_ghost", P["text"])]
        o += fire_svg(frames, fx0, 18, cw, lh, fsize, motion, colors)

    # ---- the year: GitHub-style calendar, one column per week, Sunday on top
    px = (R - L) / n

    # ---- weekly totals as block bars, same columns as the calendar below
    bar_top, bar_h = cap_y + 30, BAR_HEIGHT
    base = bar_top + bar_h
    vmax = max(S["weekly"]) or 1
    q = bar_h / 64                     # quantised like terminal block elements
    for i, v in enumerate(S["weekly"]):
        if v == 0:
            continue
        hgt = max(q, round(v / vmax * bar_h / q) * q)
        cls = "pk" if i == S["peak_i"] else "pt" if S["partial"][i] else "bar"
        o.append(f'<rect class="{cls}" x="{f(L + i * px + 1.2)}" y="{f(base - hgt)}" '
                 f'width="{f(px - 2.4)}" height="{f(hgt)}" rx="1"/>')

    hy0 = base + 30
    first_month = next((L + wi * px for wi, w in enumerate(S["weeks"]) for d, _ in w if d.day == 1), R)
    last_x = -99
    if first_month - L > 30:               # label the partial month at the left edge, like GitHub
        last_x = L
        o.append(f'<text class="c c3" style="font-size:11px" x="{L}" y="{f(hy0 - 8)}">'
                 f'{MONTHS[S["first"].month - 1]}</text>')
    for wi, w_days in enumerate(S["weeks"]):
        for d, _ in w_days:
            if d.day == 1 and L + wi * px - last_x > 30:
                last_x = L + wi * px
                o.append(f'<text class="c c3" style="font-size:11px" x="{f(last_x)}" y="{f(hy0 - 8)}">'
                         f'{MONTHS[d.month - 1]}</text>')
    cs = px - 2.4
    groups = {}
    for d, c, wi, row in S["flat"]:
        lv = level(c, S["thresholds"])
        if HEAT_MODE == "github" and S["levels"]:
            lv = S["levels"].get(d, lv)
        groups.setdefault(lv, []).append(
            f'<rect x="{f(L + wi * px + 1.2)}" y="{f(hy0 + row * px)}" width="{f(cs)}" height="{f(cs)}" rx="2"/>')
    o += [f'<g class="h{lv}">{"".join(r)}</g>' for lv, r in sorted(groups.items())]
    H = round(hy0 + 7 * px + 22)
    summary = f"{value:,} {cap.replace(' past', ' in the past')}; current streak {S['current_len']} days."
    if STATS_IN_DASHBOARD if stats is None else stats:
        row, row_cap_y, row_summary = stats_row(S, L, R, hy0 + 7 * px + 26, STATS_ROW_PITCH)
        o += row
        H = round(row_cap_y + 10)
        summary += " " + row_summary
    return "".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {H}" width="{WIDTH}" height="{H}" '
        f'role="img" aria-label="{escape(summary)}">',
        f"<title>{escape(summary)}</title>",
        panel(P, H),
        *o,
        "</svg>",
    ])


def stats_row(S, L, R, top, pitch):
    """All-time and this-week counts in equal columns.
    Returns (markup, caption baseline y, plain-text summary)."""
    cap_y = top + 7 * pitch + 20
    readouts = [("contributions all time", S["all_time"]),
                ("contributions this week", S["weekly"][-1])]
    col = (R - L) / len(readouts)
    o = []
    for k, (lab, num) in enumerate(readouts):
        x = L + k * col + (24 if k else 0)
        if k:
            o.append(f'<path class="dv" d="M{f(L + k * col + 0.5)} {f(top)}V{f(cap_y + 2)}"/>')
        o += dot_matrix(f"{num:,}", x, top, pitch)
        lw = len(lab) * 12 * 0.6
        o.append(f'<text class="c c2" x="{f(x)}" y="{f(cap_y)}" textLength="{f(lw)}" '
                 f'lengthAdjust="spacing">{lab}</text>')
    return o, cap_y, "; ".join(f"{num:,} {lab}" for lab, num in readouts) + "."


def render_stats(S, palette=None, theme="dark"):
    """Separate card with the same counts (not used when STATS_IN_DASHBOARD is on)."""
    P = PALETTES[palette or PALETTE][theme]
    row, cap_y, summary = stats_row(S, PAD, WIDTH - PAD, 28, STATS_PITCH)
    H = round(cap_y + 24)
    return "".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {H}" width="{WIDTH}" height="{H}" '
        f'role="img" aria-label="{escape(summary)}">',
        f"<title>{escape(summary)}</title>",
        panel(P, H),
        style(P), *row,
        "</svg>",
    ])


def render_header(palette=None, theme="dark", motion=None):
    """Transparent one-line banner in small monospace. Lines swap with a left-to-right sweep: the
    new line appears behind a short front of amber noise while the old one dims ahead of it.
    Every line is centred and every character sits on a fixed grid, so nothing shifts. SMIL only."""
    P = PALETTES[palette or PALETTE][theme]
    motion = motion or MOTION
    rnd = random.Random(11)
    lines = HEADER_LINES
    cw = HEADER_SIZE * 0.6                      # grid cell; textLength pins it on every OS/font
    # Only as wide as the longest line, so the README shows it at its natural size and a phone
    # shrinks it far less than a full-width image would.
    W, H = math.ceil(max(len(x) for x in lines) * cw + 24), HEADER_SIZE + 14
    y = H / 2 + HEADER_SIZE * 0.35

    def run(text, cell, cls=""):
        """One run of characters starting `cell` cells right of the centre line."""
        lead = len(text) - len(text.lstrip())
        text = text.strip()
        if not text:
            return ""
        return (f'<text{cls} x="{f(W / 2 + (cell + lead) * cw)}" textLength="{f(len(text) * cw)}">'
                f'{escape(text)}</text>')

    frames = []                                 # (markup, duration)
    for k, line in enumerate(lines):
        frames.append((run(line, -len(line) / 2), HEADER_HOLD))
        nxt = lines[(k + 1) % len(lines)]
        m = max(len(line), len(nxt))
        oa, ob = (m - len(line)) / 2, (m - len(nxt)) / 2     # each line centred on an m-cell grid
        p = HEADER_SWEEP_CHARS
        while p < m + HEADER_FRONT:
            lo = max(0, p - HEADER_FRONT)
            new = nxt[:max(0, math.ceil(lo - ob))]
            old_from = max(0, math.ceil(p - oa))
            front = "".join(rnd.choice(HEADER_NOISE_CHARS) for _ in range(lo, min(p, m)))
            frames.append((run(new, ob - m / 2) + run(front, lo - m / 2, ' class="n"')
                           + run(line[old_from:], oa + old_from - m / 2, ' class="d"'), HEADER_SWEEP_STEP))
            p += HEADER_SWEEP_CHARS
    total = sum(d for _, d in frames)
    o = [f'<style>text{{font-family:{FONT_MONO};font-size:{HEADER_SIZE}px;fill:{P["text"]}}} '
         f'.n{{fill:{P.get("accent", P["text"])}}} .d{{fill:{P["text3"]}}}</style>',
         '<g xml:space="preserve">']
    t = 0.0
    for k, (body, d) in enumerate(frames):
        if motion == "none" and k:
            break
        anim = ""
        if motion != "none":
            if k == 0:
                anim = (f'<animate attributeName="visibility" calcMode="discrete" dur="{f(total)}s" '
                        f'repeatCount="indefinite" values="visible;hidden" keyTimes="0;{d / total:.4f}"/>')
            else:
                anim = (f'<animate attributeName="visibility" calcMode="discrete" dur="{f(total)}s" '
                        f'repeatCount="indefinite" values="hidden;visible;hidden" '
                        f'keyTimes="0;{t / total:.4f};{min(1.0, (t + d) / total):.4f}"/>')
        o.append(f'<g transform="translate(0 {f(y)})" visibility="{"visible" if k == 0 else "hidden"}">{anim}{body}</g>')
        t += d
    o.append("</g>")
    label = " / ".join(lines)
    return "".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>',
        *o, "</svg>"])


def _embed(svg, x, y, w):
    """Re-seat a standalone SVG as a nested <svg> at (x, y), scaled to width w. Returns (markup, height)."""
    m = re.match(r'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ([\d.]+) ([\d.]+)" width="[\d.]+" height="[\d.]+"', svg)
    vw, vh = float(m.group(1)), float(m.group(2))
    h = vh * w / vw
    return (f'<svg x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" viewBox="0 0 {f(vw)} {f(vh)}"'
            + svg[m.end():]), h


def render_hero(S, palette=None, motion=None, total=None):
    """Everything above the README text as one black image, so that part of the profile is solid black.
    Built from the dark versions of the header, dashboard and stats; no new data."""
    pad, w = 40, WIDTH - 80
    y = 66
    parts = [f'<style>.hn{{font-family:{FONT_SANS};font-size:38px;font-weight:600;letter-spacing:-.01em;'
             f'fill:#f2f2f2}}</style>',
             f'<text class="hn" x="{WIDTH / 2}" y="{y}" text-anchor="middle">{escape(HERO_NAME)}</text>']
    y += 18
    for svg, gap in ((render_header(palette, "dark", motion), 30),
                     (render(S, palette, "dark", motion, total, stats=False), 22),
                     (render_stats(S, palette, "dark"), 0)):
        nat = float(re.search(r'viewBox="0 0 ([\d.]+)', svg).group(1))
        ew = min(w, nat)                        # the header keeps its natural width, centred
        mk, h = _embed(svg, (WIDTH - ew) / 2, y, ew)
        parts.append(mk)
        y += h + gap
        if gap == 30:   # hairline between the intro and the numbers
            parts.append(f'<path d="M{pad} {f(y - 14.5)}H{WIDTH - pad}" stroke="rgba(255,255,255,.12)"/>')
            y += 8
    H = round(y + 30)
    label = f"{HERO_NAME}. " + " / ".join(HEADER_LINES) + ". " + (
        f"{S['total']:,} contributions in the past year, current streak {S['current_len']} days, "
        f"{S['all_time']:,} contributions all time.")
    return "".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {H}" width="{WIDTH}" height="{H}" '
        f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>',
        f'<rect width="{WIDTH}" height="{H}" rx="10" fill="{HERO_BG}"/>', *parts, "</svg>"])


AWARD_TEXT = "YSEA MOST OUTSTANDING STEM EXHIBIT  ·  UNGA FORSKARE 2026"


def render_award(palette=None, theme="dark"):
    """One line of amber small caps with a dot-matrix star either side (README text can't be coloured)."""
    P = PALETTES[palette or PALETTE][theme]
    acc = P.get("accent", P["text"])
    size, cw = 12, 7.4
    tw = len(AWARD_TEXT) * cw
    W, H = round(tw + 64), 26
    star = ["00100", "01110", "11111", "01110", "00100"]
    def glyph(x0):
        return "".join(f'<rect x="{f(x0 + c * 2.6)}" y="{f(6.5 + r * 2.6)}" width="2" height="2"/>'
                       for r, row in enumerate(star) for c, b in enumerate(row) if b == "1")
    return "".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="{escape(AWARD_TEXT)}"><title>{escape(AWARD_TEXT)}</title>',
        f'<g fill="{acc}">{glyph(4)}{glyph(W - 17)}</g>',
        f'<text x="{W / 2}" y="17.5" text-anchor="middle" textLength="{f(tw)}" lengthAdjust="spacing" '
        f'xml:space="preserve" style="font-family:{FONT_MONO.replace(chr(34), chr(39))};font-size:{size}px;'
        f'font-weight:600;letter-spacing:.06em" fill="{acc}">{escape(AWARD_TEXT)}</text></svg>'])


def render_title(name, meta, palette=None, theme="dark"):
    """Project heading: the name on the dot matrix, one line of small monospace under it.
    Only as wide as its content, so a phone shows it at full size."""
    P = PALETTES[palette or PALETTE][theme]
    pitch = TITLE_PITCH
    nw = matrix_cols(name) * pitch
    mw = len(meta) * 12 * 0.6
    W, H = math.ceil(max(nw, mw) + 2), round(7 * pitch + (26 if meta else 4))
    o = [style(P)] + dot_matrix(name, 0, 2, pitch)
    if meta:
        o.append(f'<text class="c c2" x="0" y="{f(7 * pitch + 20)}" textLength="{f(mw)}" '
                 f'lengthAdjust="spacing">{escape(meta)}</text>')
    label = f"{name}, {meta}" if meta else name
    return "".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>', *o, "</svg>"])


def render_divider(palette=None, theme="dark"):
    """Section rule: a row of dots that warms from faint to amber and back, with a hot centre."""
    P = PALETTES[palette or PALETTE][theme]
    heat = P["heat"]
    W, H, n = WIDTH, 12, 85
    pitch = W / n
    o = []
    for i in range(n):
        d = abs(i - (n - 1) / 2) / ((n - 1) / 2)          # 0 centre .. 1 edge
        lv = 4 if d < 0.04 else 3 if d < 0.16 else 2 if d < 0.4 else 1 if d < 0.75 else 0
        o.append(f'<rect x="{f(i * pitch + 1)}" y="4" width="{f(pitch - 3)}" height="4" rx="1" fill="{heat[lv]}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
            f'role="presentation">{"".join(o)}</svg>')


def write(path, svg):
    ET.fromstring(svg)  # self-test: must be well-formed XML
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(svg)
    return len(svg.encode())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sample", action="store_true", help="use sample-data.json instead of the API")
    ap.add_argument("--make-sample", action="store_true", help="regenerate sample-data.json and exit")
    ap.add_argument("--user", default=os.environ.get("GH_USER", USER_DEFAULT))
    ap.add_argument("--out", default=OUT_DIR)
    ap.add_argument("--palette", choices=PALETTES, default=PALETTE)
    ap.add_argument("--motion", choices=("blink", "none"), default=MOTION)
    ap.add_argument("--total", choices=CAPTIONS, default=TOTAL)
    ap.add_argument("--variants", action="store_true", help="also write all variants to <out>/variants/")
    a = ap.parse_args()

    if a.make_sample:
        make_sample()
        return
    if a.sample:
        with open("sample-data.json", encoding="utf-8") as fh:
            raw = json.load(fh)
    else:
        raw = fetch_calendar(a.user)
    S = compute_stats(calendar_of(raw))
    S["commits"] = int(raw["data"]["user"]["contributionsCollection"].get("totalCommitContributions") or 0)
    S["all_time"] = int(raw.get("all_time") or S["total"])

    for theme in ("dark", "light"):
        size = write(os.path.join(a.out, f"dashboard-{theme}.svg"), render(S, a.palette, theme, a.motion, a.total))
        print(f"{a.out}/dashboard-{theme}.svg  {size / 1024:.1f} KB")
        write(os.path.join(a.out, f"header-{theme}.svg"), render_header(a.palette, theme, a.motion))
        write(os.path.join(a.out, f"award-{theme}.svg"), render_award(a.palette, theme))
        write(os.path.join(a.out, f"divider-{theme}.svg"), render_divider(a.palette, theme))
        for slug, name, meta in PROJECT_TITLES:
            write(os.path.join(a.out, f"title-{slug}-{theme}.svg"), render_title(name, meta, a.palette, theme))
        if theme == "dark":
            write(os.path.join(a.out, "hero.svg"), render_hero(S, a.palette, a.motion, a.total))
        size = write(os.path.join(a.out, f"stats-{theme}.svg"), render_stats(S, a.palette, theme))
        print(f"{a.out}/stats-{theme}.svg      {size / 1024:.1f} KB")
    if a.variants:
        vd = os.path.join(a.out, "variants")
        for old in glob.glob(os.path.join(vd, "*.svg")):
            os.remove(old)
        for theme in ("dark", "light"):
            for p in PALETTES:
                write(os.path.join(vd, f"palette-{p}-{theme}.svg"), render(S, p, theme, a.motion, a.total))
                write(os.path.join(vd, f"stats-{p}-{theme}.svg"), render_stats(S, p, theme))
            for st in (0, 3, 10, 20, 30):
                write(os.path.join(vd, f"fire-{st}-{theme}.svg"),
                      render({**S, "current_len": st}, a.palette, theme, a.motion, a.total))
            for m in ("blink", "none"):
                write(os.path.join(vd, f"motion-{m}-{theme}.svg"), render(S, a.palette, theme, m, a.total))
            for t in CAPTIONS:
                write(os.path.join(vd, f"total-{t}-{theme}.svg"), render(S, a.palette, theme, a.motion, t))
        print(f"variants -> {vd}/")
    print(f"total {S['total']:,} | current {S['current_len']} d | longest {S['longest_len']} d | "
          f"peak {S['peak']}/wk | active {S['active']}/{S['ndays']} d")


if __name__ == "__main__":
    main()
