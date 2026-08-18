"""Generate README charts from real, verified project data.

Every number here was actually observed during this project's build, not
estimated:
- Phase-by-phase test counts are the exact `pytest` totals reported at
  each milestone (Phase 1 through Phase 9).
- Per-layer statement counts are aggregated from a fresh
  `pytest --cov=app --cov-report=term-missing` run, grouped by package to
  match app's own directory structure.
- Per-file test counts are a direct `grep -c` of `def test_` across
  tests/*.py.

Run from the repo root (`python scripts/generate_charts.py`) to regenerate
assets/*.png after the test suite or coverage numbers actually change --
not part of the app itself, and not run in CI.

Needs matplotlib (`pip install matplotlib`), deliberately *not* added to
pyproject.toml's dependencies: nothing about running, testing, or
deploying this app needs it, only occasionally regenerating these charts
does. Adding it to the real dependency set would mean every `uv sync` on
every machine pulls in a plotting library for that.
"""

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

matplotlib.use("Agg")

# Color palette matches the Mermaid diagrams already in the README, so the
# PNGs and the diagrams read as one consistent visual system rather than
# two unrelated styles bolted together.
INDIGO = "#4338ca"   # transport layer
ORANGE = "#c2410c"   # adapter layer (tools/api)
GREEN = "#047857"    # core layer (services/models)
RED = "#b91c1c"      # security
SLATE = "#64748b"    # cross-cutting (config/utils)
BG = "#f8fafc"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.edgecolor": "#cbd5e1",
    "axes.labelcolor": "#1e293b",
    "text.color": "#1e293b",
    "xtick.color": "#334155",
    "ytick.color": "#334155",
    "axes.titleweight": "bold",
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})


def savefig(fig, name):
    fig.savefig(f"assets/{name}.png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote assets/{name}.png")


# --- Chart 1: test suite growth across phases -----------------------------
# Real pytest totals observed at each milestone in this build. Phases 5-7
# (Docker, docs, CI) genuinely added no new Python tests -- shown as a flat
# plateau rather than smoothed away, because that's what actually happened.
phases = [
    "P1\nInit", "P2\nTools", "P3\nFastAPI", "P4\nFull suite",
    "P5\nDocker", "P6\nDocs", "P7\nCI/CD", "P8\nAuth",
    "P8+\nHardening", "P9\nDeploy",
]
counts = [3, 20, 22, 32, 32, 32, 32, 45, 50, 53]

fig, ax = plt.subplots(figsize=(10, 4.5))
ax.plot(phases, counts, color=INDIGO, linewidth=2.5, marker="o", markersize=7,
        markerfacecolor="white", markeredgewidth=2.5, zorder=3)
ax.fill_between(range(len(phases)), counts, color=INDIGO, alpha=0.08, zorder=1)
for i, c in enumerate(counts):
    if i == 0 or c != counts[i - 1]:
        ax.annotate(str(c), (i, c), textcoords="offset points", xytext=(0, 10),
                    ha="center", fontsize=9, fontweight="bold", color=INDIGO)
ax.set_ylabel("Passing tests")
ax.set_title("Test suite growth across all 9 phases")
ax.spines[["top", "right"]].set_visible(False)
ax.yaxis.set_major_locator(MaxNLocator(integer=True))
ax.grid(axis="y", color="#e2e8f0", linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
fig.tight_layout()
savefig(fig, "test_growth")


# --- Chart 2: statements by architectural layer (100% covered, all of it) -
layers = ["services", "tools", "models", "transport\n(server/asgi)",
          "config", "security", "api", "utils"]
statements = [59, 42, 38, 35, 32, 28, 11, 9]
colors = [GREEN, ORANGE, GREEN, INDIGO, SLATE, RED, ORANGE, SLATE]

fig, ax = plt.subplots(figsize=(9, 5))
y_pos = range(len(layers))
bars = ax.barh(y_pos, statements, color=colors, height=0.62, zorder=3)
ax.set_yticks(y_pos, labels=layers)
ax.invert_yaxis()
ax.set_xlabel("Statements (all covered — 255/255, 100%)")
ax.set_title("Test coverage by architectural layer")
for bar, val in zip(bars, statements, strict=True):
    ax.text(val + 1, bar.get_y() + bar.get_height() / 2, f"{val}  •  100%",
            va="center", fontsize=9, color="#1e293b")
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="x", color="#e2e8f0", linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
ax.set_xlim(0, max(statements) * 1.28)
fig.tight_layout()
savefig(fig, "coverage_by_layer")


# --- Chart 3: tests per file ------------------------------------------
files = [
    ("test_auth.py", 15), ("test_config_settings.py", 11),
    ("test_tools_registration.py", 6), ("test_conversion_service.py", 5),
    ("test_web_service.py", 5), ("test_text_analysis_service.py", 4),
    ("test_bootstrap.py", 3), ("test_asgi.py", 2), ("test_main_entrypoint.py", 2),
]
files.sort(key=lambda x: x[1])
names = [f[0] for f in files]
vals = [f[1] for f in files]

fig, ax = plt.subplots(figsize=(9, 5))
y_pos = range(len(names))
ax.barh(y_pos, vals, color=INDIGO, height=0.6, zorder=3, alpha=0.85)
ax.set_yticks(y_pos, labels=names, fontfamily="monospace", fontsize=9)
ax.set_xlabel("Number of tests  (53 total)")
ax.set_title("Tests per file")
for i, v in enumerate(vals):
    ax.text(v + 0.15, i, str(v), va="center", fontsize=9, fontweight="bold")
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="x", color="#e2e8f0", linewidth=0.8, zorder=0)
ax.set_axisbelow(True)
ax.xaxis.set_major_locator(MaxNLocator(integer=True))
ax.set_xlim(0, max(vals) * 1.25)
fig.tight_layout()
savefig(fig, "tests_per_file")
