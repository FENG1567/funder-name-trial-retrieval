"""Generate two publication figures from the supplied aggregate source data.

The source CSV files remain unchanged. Run with --source-dir or explicit
--figure1-csv/--figure2-csv paths. Pass --font-path to use the specified font.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties, findfont, fontManager
from matplotlib.ft2font import FT2Font
from matplotlib.lines import Line2D
from matplotlib.text import Text
import pandas as pd


HERE = Path(__file__).resolve().parent
DEFAULT_SOURCE_DIR = HERE / "data" / "aggregate"
DEFAULT_OUTPUT_DIR = HERE / "results" / "figures"

parser = argparse.ArgumentParser(description="Generate the two manuscript figures")
parser.add_argument(
    "--source-dir",
    type=Path,
    default=DEFAULT_SOURCE_DIR,
    help="directory containing figure1_source_data.csv and figure2_source_data.csv",
)
parser.add_argument("--figure1-csv", type=Path, help="explicit Figure 1 source-data CSV")
parser.add_argument("--figure2-csv", type=Path, help="explicit Figure 2 source-data CSV")
parser.add_argument(
    "--output-dir",
    type=Path,
    default=DEFAULT_OUTPUT_DIR,
    help="directory for Figure_1 and Figure_2 exports",
)
parser.add_argument("--paper-names", action="store_true", help="use Figure_1 and Figure_2 output names")
parser.add_argument(
    "--font-path",
    type=Path,
    help="path to the Arial Bold TrueType font used for every text element",
)
args = parser.parse_args()

FIGURE1_CSV = (args.figure1_csv or args.source_dir / "figure1_source_data.csv").resolve()
FIGURE2_CSV = (args.figure2_csv or args.source_dir / "figure2_source_data.csv").resolve()
OUT = args.output_dir.resolve()
OUT.mkdir(parents=True, exist_ok=True)

WIDTH_IN = 6.9
INK = "#1D2730"
BLUE = "#356E8C"
BLUE_DARK = "#28566F"
REF = "#58646E"
LINK = "#B7C1C8"
GRID = "#E3E8EC"
WHITE = "#FFFFFF"
BASE_TEXT_PT = 10.5


def resolve_font() -> tuple[Path, str, str]:
    """Resolve and verify an Arial Bold font; never silently fall back."""
    if args.font_path is not None:
        font_path = args.font_path.expanduser().resolve()
        if not font_path.is_file():
            raise FileNotFoundError(f"Arial font file does not exist: {font_path}")
        ft_font = FT2Font(str(font_path))
        family = ft_font.family_name
        style = ft_font.style_name
        if family.casefold() != "arial" or "bold" not in style.casefold():
            raise RuntimeError(
                f"--font-path must point to Arial Bold; found family={family!r}, style={style!r}"
            )
        fontManager.addfont(str(font_path))
        resolved = Path(
            findfont(
                FontProperties(family=family, weight="bold"),
                fallback_to_default=False,
            )
        ).resolve()
        if resolved != font_path:
            raise RuntimeError(
                f"Matplotlib resolved Arial Bold to {resolved}, not the requested font {font_path}"
            )
        return font_path, family, style

    try:
        resolved = Path(
            findfont(
                FontProperties(family="Arial", weight="bold"),
                fallback_to_default=False,
            )
        ).resolve()
    except Exception as exc:
        raise RuntimeError(
            "Arial Bold is unavailable; pass --font-path to an Arial Bold TrueType file."
        ) from exc
    ft_font = FT2Font(str(resolved))
    family = ft_font.family_name
    style = ft_font.style_name
    if family.casefold() != "arial" or "bold" not in style.casefold():
        raise RuntimeError(
            f"Resolved font is not Arial Bold: family={family!r}, style={style!r}, path={resolved}"
        )
    return resolved, family, style


FONT_PATH, FONT_FAMILY, FONT_STYLE = resolve_font()

mpl.rcParams.update(
    {
        "font.family": FONT_FAMILY,
        "font.sans-serif": [FONT_FAMILY],
        "font.weight": "bold",
        "font.size": BASE_TEXT_PT,
        "axes.labelweight": "bold",
        "axes.labelsize": BASE_TEXT_PT,
        "axes.titleweight": "bold",
        "axes.edgecolor": "#7E8992",
        "axes.linewidth": 0.75,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "axes.labelcolor": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "text.color": INK,
        "legend.frameon": False,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "savefig.facecolor": WHITE,
        "figure.facecolor": WHITE,
        "savefig.transparent": False,
    }
)


def pct(n: int, d: int) -> float:
    if d <= 0:
        raise ValueError(f"Denominator must be positive, got {d}")
    return 100.0 * n / d


def add_panel_heading(fig: plt.Figure, x_in: float, letter: str, title: str) -> None:
    """Set a separate 18 pt panel marker and 12 pt title in the header band."""
    fig.text(
        x_in / WIDTH_IN,
        0.972,
        letter,
        ha="left",
        va="top",
        fontsize=18,
        fontweight="bold",
        color=INK,
    )
    fig.text(
        (x_in + 0.29) / WIDTH_IN,
        0.965,
        title,
        ha="left",
        va="top",
        fontsize=12,
        fontweight="bold",
        color=INK,
    )


def collect_text_qa(fig: plt.Figure, figure_name: str) -> dict[str, object]:
    """Save rendered text boxes and report text-to-text collisions/clipping."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    width_in, height_in = fig.get_size_inches()
    text_records: list[dict[str, object]] = []
    boxes: list[tuple[Text, tuple[float, float, float, float]]] = []

    for artist in fig.findobj(match=Text):
        text = artist.get_text()
        if not artist.get_visible() or not text.strip():
            continue
        bbox = artist.get_window_extent(renderer=renderer)
        x0, y0, x1, y1 = (float(v) / fig.dpi for v in (bbox.x0, bbox.y0, bbox.x1, bbox.y1))
        if x1 <= x0 or y1 <= y0:
            continue
        props = artist.get_fontproperties()
        record = {
            "text": text,
            "bbox_inches": [round(x0, 4), round(y0, 4), round(x1, 4), round(y1, 4)],
            "font_family": props.get_name(),
            "font_size_pt": round(float(props.get_size_in_points()), 2),
            "font_weight": str(props.get_weight()),
        }
        text_records.append(record)
        boxes.append((artist, (x0, y0, x1, y1)))

    collisions: list[dict[str, object]] = []
    for index, (first, first_box) in enumerate(boxes):
        ax0, ay0, ax1, ay1 = first_box
        for second, second_box in boxes[index + 1 :]:
            bx0, by0, bx1, by1 = second_box
            overlap_w = min(ax1, bx1) - max(ax0, bx0)
            overlap_h = min(ay1, by1) - max(ay0, by0)
            if overlap_w > 0.015 and overlap_h > 0.015:
                collisions.append(
                    {
                        "first": first.get_text(),
                        "second": second.get_text(),
                        "overlap_inches": [round(overlap_w, 4), round(overlap_h, 4)],
                    }
                )

    clipped = []
    for record in text_records:
        x0, y0, x1, y1 = record["bbox_inches"]
        if x0 < -0.01 or y0 < -0.01 or x1 > width_in + 0.01 or y1 > height_in + 0.01:
            clipped.append(record)

    report = {
        "figure": figure_name,
        "canvas_inches": [round(width_in, 4), round(height_in, 4)],
        "text_artist_count": len(text_records),
        "text_bboxes": text_records,
        "text_overlaps": collisions,
        "out_of_canvas_text": clipped,
    }
    (OUT / f"{figure_name}_text_bboxes.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if collisions:
        samples = "; ".join(
            f"{item['first']!r} / {item['second']!r}" for item in collisions[:5]
        )
        raise RuntimeError(f"{figure_name} has overlapping text boxes: {samples}")
    if clipped:
        samples = "; ".join(repr(item["text"]) for item in clipped[:5])
        raise RuntimeError(f"{figure_name} has text outside the fixed canvas: {samples}")
    return report


def save_figure(fig: plt.Figure, stem: str, title: str) -> None:
    if not args.paper_names:
        stem = {
            "Figure_1": "figure1_coverage_and_current_posting",
            "Figure_2": "figure2_mrc_historical_selection",
        }.get(stem, stem)

    figure_name = "Figure_1" if "Figure_1" in stem or stem.startswith("figure1_") else "Figure_2"
    bbox_report = collect_text_qa(fig, figure_name)

    metadata = {"Title": title, "Creator": "Matplotlib"}
    fig.savefig(OUT / f"{stem}.svg", format="svg", metadata=metadata)
    fig.savefig(OUT / f"{stem}.pdf", format="pdf", metadata=metadata)
    fig.savefig(OUT / f"{stem}.png", format="png", dpi=600)
    fig.savefig(
        OUT / f"{stem}.tiff",
        format="tiff",
        dpi=600,
        pil_kwargs={"compression": "tiff_lzw"},
    )
    plt.close(fig)
    print(
        f"{figure_name}: canvas={bbox_report['canvas_inches']} in; "
        f"text_artists={bbox_report['text_artist_count']}; "
        f"text_overlaps={len(bbox_report['text_overlaps'])}; "
        f"out_of_canvas={len(bbox_report['out_of_canvas_text'])}"
    )


def prepare_figure1_data() -> tuple[pd.DataFrame, dict[str, tuple[int, int, float]]]:
    data = pd.read_csv(FIGURE1_CSV)
    expected_rows = [
        ("SU2C", "Core"),
        ("SU2C", "Expanded aliases"),
        ("MRC", "Core"),
        ("MRC", "Expanded aliases"),
        ("KCE", "Official full name"),
        ("KCE", "Official aliases"),
        ("KCE", "Aliases plus documented variant"),
    ]
    observed_rows = list(zip(data["source"], data["strategy"]))
    if observed_rows != expected_rows:
        raise ValueError(f"Figure 1 source rows/order differ from the 7-row contract: {observed_rows!r}")
    if len(data) != 7:
        raise ValueError(f"Figure 1 requires all 7 source rows; found {len(data)}")

    data = data.copy()
    data["coverage_pct"] = [
        pct(int(n), int(d)) for n, d in zip(data["coverage_num"], data["coverage_den"])
    ]
    data["query_pct"] = [
        pct(int(n), int(d)) if status == "estimable" else float("nan")
        for n, d, status in zip(data["query_posted"], data["query_eligible"], data["posting_status"])
    ]
    reference_counts: dict[str, tuple[int, int, float]] = {}
    for source, group in data.groupby("source", sort=False):
        unique_counts = group[["reference_posted", "reference_eligible"]].drop_duplicates()
        if len(unique_counts) != 1:
            raise ValueError(f"Figure 1 has inconsistent current-reference counts for {source}")
        n, d = unique_counts.iloc[0]
        reference_counts[source] = (int(n), int(d), pct(int(n), int(d)))
    if sum(data["posting_status"].eq("NE")) != 1:
        raise ValueError("Figure 1 must preserve exactly one NE query row.")
    return data, reference_counts


def figure1() -> None:
    data, reference_counts = prepare_figure1_data()
    row_labels = [
        "SU2C: core",
        "SU2C: expanded\naliases",
        "MRC: core",
        "MRC: expanded\naliases",
        "KCE: full name",
        "KCE: official\naliases",
        "KCE: exploratory\nvariant",
    ]
    y_positions = [6.0, 5.05, 3.95, 3.0, 1.9, 0.95, 0.0]
    data = data.copy()
    data["y"] = y_positions

    fig = plt.figure(figsize=(6.9, 4.7))
    ax_names = fig.add_axes([0.08 / WIDTH_IN, 0.15, 1.68 / WIDTH_IN, 0.67])
    ax_cov = fig.add_axes([1.88 / WIDTH_IN, 0.15, 1.45 / WIDTH_IN, 0.67])
    ax_post = fig.add_axes([3.54 / WIDTH_IN, 0.15, 1.55 / WIDTH_IN, 0.67])
    ax_ref = fig.add_axes([5.18 / WIDTH_IN, 0.15, 0.69 / WIDTH_IN, 0.67])
    ax_query = fig.add_axes([5.99 / WIDTH_IN, 0.15, 0.88 / WIDTH_IN, 0.67])

    axes = [ax_names, ax_cov, ax_post, ax_ref, ax_query]
    for ax in axes:
        ax.set_ylim(-0.55, 6.55)
        ax.set_yticks(y_positions)
        ax.set_axisbelow(True)
        for boundary in (4.50, 2.45):
            ax.axhline(boundary, color=GRID, linewidth=0.75, zorder=0)
    ax_names.set_xlim(0, 1)
    ax_names.axis("off")
    for y, label in zip(y_positions, row_labels):
        ax_names.text(
            1.0,
            y,
            label,
            ha="right",
            va="center",
            fontsize=10.5,
            fontweight="bold",
            color=INK,
            linespacing=1.05,
        )

    ax_cov.set_xlim(0, 100)
    ax_cov.set_xticks([0, 25, 50, 75, 100])
    ax_cov.set_xticklabels(["0", "25", "50", "75", "100"])
    ax_cov.set_yticklabels([])
    ax_cov.xaxis.grid(True, color=GRID, linewidth=0.65)
    ax_cov.tick_params(axis="x", labelsize=10.5, length=3, width=0.7, pad=4)
    ax_cov.tick_params(axis="y", length=0)
    ax_cov.set_xlabel("Known NCT\ncoverage (%)", fontsize=10.5, labelpad=7, fontweight="bold")

    for row in data.itertuples(index=False):
        x = float(row.coverage_pct)
        ax_cov.hlines(row.y, 0, x, color=LINK, linewidth=1.15, zorder=1)
        ax_cov.plot(x, row.y, marker="o", markersize=5.8, color=BLUE, zorder=2, clip_on=False)
        ax_cov.annotate(
            f"{int(row.coverage_num)}/{int(row.coverage_den)}",
            xy=(x, row.y),
            xytext=(5, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=11.2,
            fontweight="bold",
            color=INK,
            clip_on=False,
        )

    ax_post.set_xlim(0, 100)
    ax_post.set_xticks([0, 25, 50, 75, 100])
    ax_post.set_xticklabels(["0", "25", "50", "75", "100"])
    ax_post.set_yticklabels([])
    ax_post.xaxis.grid(True, color=GRID, linewidth=0.65)
    ax_post.tick_params(axis="x", labelsize=10.5, length=3, width=0.7, pad=4)
    ax_post.tick_params(axis="y", length=0)
    ax_post.set_xlabel("Eligible NCTs with results\nposted (%)", fontsize=10.5, labelpad=7, fontweight="bold")

    for row in data.itertuples(index=False):
        ref_n, ref_d, ref_pct = reference_counts[row.source]
        if row.posting_status == "estimable":
            query_x = float(row.query_pct)
            ax_post.hlines(
                row.y,
                min(ref_pct, query_x),
                max(ref_pct, query_x),
                color=LINK,
                linewidth=1.2,
                zorder=1,
            )
        ax_post.plot(
            ref_pct,
            row.y,
            marker="D",
            markersize=6.0,
            markerfacecolor=WHITE,
            markeredgecolor=REF,
            markeredgewidth=1.1,
            linestyle="None",
            zorder=3,
            clip_on=False,
        )
        if row.posting_status == "estimable":
            ax_post.plot(
                query_x,
                row.y,
                marker="o",
                markersize=5.8,
                markerfacecolor=BLUE,
                markeredgecolor=BLUE,
                linestyle="None",
                zorder=4,
                clip_on=False,
            )

    for ax, header in ((ax_ref, "Ref n/N"), (ax_query, "Query n/N")):
        ax.set_xlim(0, 1)
        ax.set_xticks([])
        ax.set_yticklabels([])
        ax.tick_params(axis="both", length=0)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.text(
            0.5,
            6.42,
            header,
            ha="center",
            va="bottom",
            fontsize=10.5,
            fontweight="bold",
            color=INK,
        )

    for row in data.itertuples(index=False):
        ref_n, ref_d, _ = reference_counts[row.source]
        ax_ref.text(
            0.5,
            row.y,
            f"{ref_n}/{ref_d}",
            ha="center",
            va="center",
            fontsize=11.2,
            fontweight="bold",
            color=REF,
        )
        query_label = (
            f"{int(row.query_posted)}/{int(row.query_eligible)}"
            if row.posting_status == "estimable"
            else "NE"
        )
        ax_query.text(
            0.5,
            row.y,
            query_label,
            ha="center",
            va="center",
            fontsize=11.2,
            fontweight="bold",
            color=INK,
        )

    add_panel_heading(fig, 0.08, "A", "Source-list coverage")
    add_panel_heading(fig, 3.54, "B", "Current results posting")
    legend_handles = [
        Line2D(
            [0],
            [0],
            marker="D",
            color="none",
            markerfacecolor=WHITE,
            markeredgecolor=REF,
            markeredgewidth=1.1,
            markersize=6.0,
            label="Reference",
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=BLUE,
            markeredgecolor=BLUE,
            markersize=5.8,
            label="Query",
        ),
    ]
    fig.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.69, 0.91),
        ncol=2,
        frameon=False,
        prop=FontProperties(fname=str(FONT_PATH), size=10.5),
        handletextpad=0.42,
        columnspacing=0.8,
        borderaxespad=0,
    )
    save_figure(fig, "Figure_1", "Source-list coverage and current registry results posting")


def prepare_figure2_data() -> tuple[pd.Series, pd.Series, pd.DataFrame]:
    data = pd.read_csv(FIGURE2_CSV)
    required_stages = [
        "All historical eligible rows",
        "Rows with any recorded NCT",
        "Core name query",
        "Expanded-alias name query",
    ]
    if len(data) != 4 or list(data["stage"]) != required_stages:
        raise ValueError(
            "Figure 2 requires the historical reference followed by both parallel name-query branches."
        )
    all_rows = data.loc[data.stage == "All historical eligible rows"].iloc[0]
    id_rows = data.loc[data.stage == "Rows with any recorded NCT"].iloc[0]
    branches = data.loc[data.stage.isin(["Core name query", "Expanded-alias name query"])].copy()
    branches = branches.set_index("stage").loc[["Core name query", "Expanded-alias name query"]]
    if (
        int(all_rows.reported_n) != 53
        or int(all_rows.reported_denominator) != 58
        or int(id_rows.reported_n) != 27
        or int(id_rows.reported_denominator) != 27
    ):
        raise ValueError("Figure 2 historical comparison differs from 53/58 versus 27/27.")
    expected_branches = [(9, 27, 9, 9), (12, 27, 12, 12)]
    observed_branches = [
        (
            int(row.retained_n),
            int(row.selection_base_n),
            int(row.reported_n),
            int(row.reported_denominator),
        )
        for row in branches.itertuples()
    ]
    if observed_branches != expected_branches:
        raise ValueError(f"Figure 2 parallel query-branch counts differ: {observed_branches!r}")
    return all_rows, id_rows, branches


def figure2() -> None:
    all_rows, id_rows, branches = prepare_figure2_data()
    source_rate = pct(int(all_rows.reported_n), int(all_rows.reported_denominator))
    id_rate = pct(int(id_rows.reported_n), int(id_rows.reported_denominator))
    branch_y = [1.05, 0.0]
    retained_pct = [
        pct(int(row.retained_n), int(row.selection_base_n))
        for row in branches.itertuples()
    ]

    fig = plt.figure(figsize=(6.9, 3.6))
    ax_select = fig.add_axes([0.58 / WIDTH_IN, 0.19, 2.10 / WIDTH_IN, 0.57])
    ax_retained = fig.add_axes([3.02 / WIDTH_IN, 0.19, 1.88 / WIDTH_IN, 0.57])
    ax_reported = fig.add_axes([5.12 / WIDTH_IN, 0.19, 1.66 / WIDTH_IN, 0.57])

    ax_select.set_xlim(-0.30, 1.30)
    ax_select.set_ylim(0, 100)
    ax_select.set_xticks([0, 1])
    ax_select.set_xticklabels(
        [
            "All historical\neligible rows\n(n=58)",
            "Rows with any\nrecorded NCT\n(n=27)",
        ]
    )
    ax_select.set_yticks([0, 25, 50, 75, 100])
    ax_select.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax_select.set_axisbelow(True)
    ax_select.yaxis.grid(True, color=GRID, linewidth=0.65)
    ax_select.tick_params(axis="both", labelsize=10.5, length=3, width=0.7, pad=4)
    ax_select.plot(
        [0, 1],
        [source_rate, id_rate],
        color=LINK,
        linewidth=1.6,
        zorder=1,
        clip_on=False,
    )
    ax_select.plot(
        0,
        source_rate,
        marker="o",
        markersize=6.2,
        color=REF,
        zorder=2,
        clip_on=False,
    )
    ax_select.plot(
        1,
        id_rate,
        marker="o",
        markersize=6.2,
        color=BLUE,
        zorder=2,
        clip_on=False,
    )
    ax_select.annotate(
        f"{int(all_rows.reported_n)}/{int(all_rows.reported_denominator)}\n{source_rate:.1f}%",
        xy=(0, source_rate),
        xytext=(0, -24),
        textcoords="offset points",
        ha="center",
        va="top",
        fontsize=11.2,
        fontweight="bold",
        color=INK,
        clip_on=False,
    )
    ax_select.annotate(
        f"{int(id_rows.reported_n)}/{int(id_rows.reported_denominator)}\n{id_rate:.1f}%",
        xy=(1, id_rate),
        xytext=(0, -24),
        textcoords="offset points",
        ha="center",
        va="top",
        fontsize=11.2,
        fontweight="bold",
        color=INK,
        clip_on=False,
    )

    ax_retained.set_xlim(0, 100)
    ax_retained.set_ylim(-0.70, 2.40)
    ax_retained.set_xticks([0, 25, 50, 75, 100])
    ax_retained.set_xticklabels(["0", "25", "50", "75", "100"])
    ax_retained.set_yticks([])
    ax_retained.xaxis.grid(True, color=GRID, linewidth=0.65)
    ax_retained.set_axisbelow(True)
    ax_retained.tick_params(axis="x", labelsize=10.5, length=3, width=0.7, pad=4)
    ax_retained.set_xlabel("Rows retained (%)", fontsize=10.5, labelpad=7, fontweight="bold")
    for y, value, row, label in zip(
        branch_y,
        retained_pct,
        branches.itertuples(),
        ["Core name query", "Expanded aliases"],
    ):
        ax_retained.text(
            2.5,
            y + 0.24,
            label,
            ha="left",
            va="bottom",
            fontsize=10.5,
            fontweight="bold",
            color=INK,
        )
        ax_retained.barh(
            y,
            value,
            height=0.30,
            color=BLUE,
            edgecolor="none",
            zorder=2,
        )
        ax_retained.text(
            value - 2.0,
            y,
            f"{int(row.retained_n)}/{int(row.selection_base_n)}",
            ha="right",
            va="center",
            fontsize=11.2,
            fontweight="bold",
            color=WHITE,
        )

    ax_reported.set_xlim(0, 1)
    ax_reported.set_ylim(ax_retained.get_ylim())
    ax_reported.axis("off")
    ax_reported.text(
        0.0,
        2.18,
        "Reported among\nretained",
        ha="left",
        va="bottom",
        fontsize=10.5,
        fontweight="bold",
        color=INK,
        linespacing=1.0,
    )
    ax_reported.text(
        0.0,
        1.82,
        "Reference: 27/27",
        ha="left",
        va="bottom",
        fontsize=10.5,
        fontweight="bold",
        color=REF,
    )
    ax_reported.text(
        0.0,
        1.46,
        "(100.0%)",
        ha="left",
        va="bottom",
        fontsize=10.5,
        fontweight="bold",
        color=REF,
    )
    for y, row in zip(branch_y, branches.itertuples()):
        rate = pct(int(row.reported_n), int(row.reported_denominator))
        delta = float(row.delta_pp_vs_reference)
        ax_reported.text(
            0.0,
            y,
            f"{int(row.reported_n)}/{int(row.reported_denominator)} ({rate:.1f}%)",
            ha="left",
            va="center",
            fontsize=11.2,
            fontweight="bold",
            color=INK,
        )
        ax_reported.text(
            0.0,
            y - 0.27,
            f"{delta:+.1f} percentage points",
            ha="left",
            va="center",
            fontsize=10.5,
            fontweight="bold",
            color=REF,
        )

    add_panel_heading(fig, 0.08, "A", "Historical MRC reporting")
    add_panel_heading(fig, 2.96, "B", "Parallel name-query branches")
    fig.text(
        0.12 / WIDTH_IN,
        0.86,
        "+8.6 percentage points",
        ha="left",
        va="center",
        fontsize=11.5,
        fontweight="bold",
        color=BLUE_DARK,
    )
    save_figure(fig, "Figure_2", "Historical MRC reporting and parallel name-query branches")


if __name__ == "__main__":
    print(f"Using Arial Bold: family={FONT_FAMILY!r}; style={FONT_STYLE!r}; path={FONT_PATH}")
    print(f"Figure 1 CSV: {FIGURE1_CSV}")
    print(f"Figure 2 CSV: {FIGURE2_CSV}")
    print(f"Output directory: {OUT}")
    figure1()
    figure2()
