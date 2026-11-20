"""Reproduce HybridPilot Figure 2 from the two release CSVs."""

import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


HERE = Path(__file__).resolve().parent
INK = '#171717'
PHYSICAL = '#315a82'
LOGICAL = '#11766c'
UPDATE_STYLE = {'physical': ('s', PHYSICAL), 'logical': ('o', LOGICAL)}
SCALE = (100, 145)
TICKS = (100, 110, 120, 130, 140)


def read_rows(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def read_experiments(directory):
    factorial = read_rows(directory / 'accounting.csv')
    slices = read_rows(directory / 'slices.csv')
    sample_sizes = {int(r['queries']) for r in factorial + slices}
    if len(sample_sizes) != 1 or min(sample_sizes) <= 0:
        raise ValueError('The two experiments need one nonempty matched sample size.')

    timing = {(r['grouping'], r['update']): float(r['geomean_ms']) for r in factorial}
    keys = {(group, update) for group in ('separate', 'joint') for update in UPDATE_STYLE}
    if set(timing) != keys or len(factorial) != len(keys):
        raise ValueError('Expected one observation for each grouping/update combination.')
    sweep = {
        float(r['budget_ms']): {u: float(r[f'{u}_geomean_ms']) for u in UPDATE_STYLE}
        for r in slices
    }
    if set(sweep) != {0.25, 1, 4} or len(slices) != 3:
        raise ValueError('Expected the reported 0.25, 1, and 4 ms slice targets.')
    if any(timing['joint', u] != sweep[1][u] for u in UPDATE_STYLE):
        raise ValueError('The 1 ms joint data must agree across panels.')
    values = [*timing.values(), *(v for row in sweep.values() for v in row.values())]
    if any(not (SCALE[0] < v < SCALE[1]) for v in values):
        raise ValueError('A plotted timing falls outside the published axis limits.')
    return timing, sweep, sample_sizes.pop()


def style_axes(axis):
    axis.set_xlim(*SCALE)
    axis.set_ylim(0.05, 3.32)
    axis.set_xticks(TICKS)
    axis.set_yticks([])
    axis.tick_params(axis='x', color='#78848b', pad=3, length=3, width=0.65)
    for edge in ('top', 'left', 'right'):
        axis.spines[edge].set_visible(False)
    axis.spines['bottom'].set(color='#78848b', linewidth=0.7)
    axis.set_axisbelow(True)
    axis.grid(axis='x', color='#e3e8eb', linewidth=0.65)


def endpoint(axis, value, row, update, filled):
    marker, color = UPDATE_STYLE[update]
    axis.plot(value, row, marker=marker, linestyle='', markersize=5.8,
              markerfacecolor=color if filled else 'white', markeredgecolor=color,
              markeredgewidth=1.25, zorder=4)
    axis.annotate(f'{value:g}', (value, row), xytext=(0, 7), textcoords='offset points',
                  ha='center', va='bottom', fontsize=8.6, fontweight='semibold',
                  bbox={'facecolor': 'white', 'edgecolor': 'none', 'pad': 0.35}, zorder=5)


def row_label(axis, label, row, bold=False):
    axis.text(-0.042, row, label, transform=axis.get_yaxis_transform(),
              ha='right', va='center', fontsize=8.5, fontweight='bold' if bold else 'normal')


def plot(timing, sweep, n, output):
    plt.rcParams.update({
        'font.family': 'DejaVu Sans', 'font.size': 8.6, 'text.color': INK,
        'xtick.color': INK, 'ytick.color': INK, 'axes.labelcolor': INK,
        'pdf.fonttype': 42, 'svg.fonttype': 'none',
    })
    fig = plt.figure(figsize=(7, 2.34), facecolor='white')
    left = fig.add_axes((0.138, 0.235, 0.344, 0.482))
    right = fig.add_axes((0.630, 0.235, 0.344, 0.482), sharex=left)
    for axis in (left, right):
        style_axes(axis)

    fig.text(0.024, 0.941, f'Same {n} Media completion states in every cell',
             ha='left', va='center', fontsize=9.2, fontweight='bold')
    fig.add_artist(Line2D([0.024, 0.974], [0.881, 0.881], transform=fig.transFigure,
                          linewidth=0.7, color='#cfd7dc'))
    fig.text(0.024, 0.820, '(a) Separate vs. joint histories', fontsize=9.3, fontweight='bold')
    fig.text(0.024, 0.744, 'Same lane dispatcher, 1 ms target', fontsize=8.3)
    fig.text(0.536, 0.820, '(b) Joint histories', fontsize=9.3, fontweight='bold')
    fig.text(0.536, 0.744, 'Target slice budget', fontsize=8.3)
    fig.text(0.55, 0.043, 'Geometric mean completion time (ms)',
             ha='center', va='bottom', fontsize=8.9)

    filled_legend = [
        Line2D([], [], marker='o', markersize=5.2, linestyle='', markeredgecolor=INK,
               markerfacecolor='white', label='Separate V/P'),
        Line2D([], [], marker='o', markersize=5.2, linestyle='', markeredgecolor=INK,
               markerfacecolor=INK, label='Joint VP'),
    ]
    legend_style = dict(ncol=2, frameon=False, fontsize=8.4, columnspacing=1.08,
                        handletextpad=0.27, handlelength=0.85, borderaxespad=0, borderpad=0.12)
    fig.legend(handles=filled_legend, loc='upper right', bbox_to_anchor=(0.977, 0.981),
               **legend_style)
    update_legend = [
        Line2D([], [], marker=marker, markersize=5.2, linestyle='', markeredgecolor=color,
               markerfacecolor=color, label=update.capitalize())
        for update, (marker, color) in UPDATE_STYLE.items()
    ]
    fig.legend(handles=update_legend, loc='upper right', bbox_to_anchor=(0.977, 0.800),
               **legend_style)

    for update, row in [('physical', 2.46), ('logical', 1.05)]:
        before, after = timing['separate', update], timing['joint', update]
        _, color = UPDATE_STYLE[update]
        row_label(left, update.capitalize(), row, bold=True)
        left.plot([after, before], [row, row], color=color, lw=2.05, alpha=0.63, zorder=2)
        endpoint(left, after, row, update, filled=True)
        endpoint(left, before, row, update, filled=False)
        left.annotate(f'{after - before:+g} ms', ((before + after) / 2, row),
                      xytext=(0, -8), textcoords='offset points', va='top', ha='center',
                      fontsize=8.3, bbox={'facecolor': 'white', 'edgecolor': 'none', 'pad': 0.35})

    right.axhspan(1.30, 2.08, facecolor='#edf4f6', zorder=0)
    for budget, row in [(0.25, 2.73), (1, 1.69), (4, 0.65)]:
        values = sweep[budget]
        row_label(right, f'{budget:g} ms', row, bold=budget == 1)
        right.plot([values['logical'], values['physical']], [row, row],
                   color='#81959a', lw=1.55, zorder=2)
        for update, value in values.items():
            endpoint(right, value, row, update, filled=True)

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, required=True, help='directory containing the two CSV inputs')
    parser.add_argument('--output', type=Path, default=HERE.parent / 'figures/accounting.pdf',
                        help='destination vector PDF or SVG')
    args = parser.parse_args()
    plot(*read_experiments(args.results), args.output)
