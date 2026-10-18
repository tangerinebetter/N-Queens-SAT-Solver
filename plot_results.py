"""
Generate plots from experiment results (CSV files).

Chart types:
  - Line charts (runtime scaling)
  - Bar charts (comparison at specific N)
  - Stacked bar (encoding vs solving time)
  - Heatmap (encoding × N → time)
  - Grouped bar (paradigm comparison)
"""

import csv
import os
import sys

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')
    import numpy as np
    HAS_MPL = True
except ImportError:
    HAS_MPL = False
    print("WARNING: matplotlib not installed. Run: pip install matplotlib")

RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')

COLORS = [
    '#2196F3',
    '#FF5722',
    '#4CAF50',
    '#9C27B0',
    '#FF9800',
    '#00BCD4',
    '#E91E63',
    '#795548',
    '#607D8B',
]


def read_csv(filename):
    path = os.path.join(RESULTS_DIR, filename)
    if not os.path.exists(path):
        print(f"  [SKIP] File not found: {path}")
        return []
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)


def setup_style():
    plt.rcParams.update({
        'font.size': 12,
        'axes.titlesize': 15,
        'axes.titleweight': 'bold',
        'axes.labelsize': 13,
        'legend.fontsize': 10,
        'figure.facecolor': 'white',
        'axes.facecolor': '#FAFAFA',
        'axes.grid': True,
        'grid.alpha': 0.3,
        'grid.linestyle': '--',
    })


def plot_exp1_runtime():
    data = read_csv('exp1_encodings.csv')
    if not data:
        return

    encodings = list(dict.fromkeys(row['encoding'] for row in data))

    fig, ax = plt.subplots(figsize=(12, 7))

    for i, enc in enumerate(encodings):
        enc_data = [row for row in data if row['encoding'] == enc]
        ns = [int(row['n']) for row in enc_data]
        times = [float(row['total_time']) for row in enc_data]
        ax.plot(ns, times, 'o-', label=enc, linewidth=2, markersize=5,
                color=COLORS[i % len(COLORS)])

    ax.set_xlabel('Board Size (N)')
    ax.set_ylabel('Total Time (seconds)')
    ax.set_title('Runtime Comparison of AMO Encoding Methods')
    ax.legend(loc='upper left', ncol=2)
    ax.set_yscale('log')
    ax.set_xscale('log')
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'exp1_runtime.png'), dpi=150)
    print("  Saved: exp1_runtime.png")
    plt.close()


def plot_exp1_vars_clauses():
    data = read_csv('exp1_encodings.csv')
    if not data:
        return

    encodings = list(dict.fromkeys(row['encoding'] for row in data))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    for i, enc in enumerate(encodings):
        enc_data = [row for row in data if row['encoding'] == enc]
        ns = [int(row['n']) for row in enc_data]
        vars_ = [int(row['num_vars']) for row in enc_data]
        cls_ = [int(row['num_clauses']) for row in enc_data]

        c = COLORS[i % len(COLORS)]
        ax1.plot(ns, vars_, 'o-', label=enc, linewidth=2, markersize=4, color=c)
        ax2.plot(ns, cls_, 'o-', label=enc, linewidth=2, markersize=4, color=c)

    ax1.set_xlabel('Board Size (N)')
    ax1.set_ylabel('Number of Variables')
    ax1.set_title('Variables by Encoding Method')
    ax1.legend(fontsize=9, ncol=2)
    ax1.set_yscale('log')
    ax1.set_xscale('log')

    ax2.set_xlabel('Board Size (N)')
    ax2.set_ylabel('Number of Clauses')
    ax2.set_title('Clauses by Encoding Method')
    ax2.legend(fontsize=9, ncol=2)
    ax2.set_yscale('log')
    ax2.set_xscale('log')

    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'exp1_vars_clauses.png'), dpi=150)
    print("  Saved: exp1_vars_clauses.png")
    plt.close()


def plot_exp1_bar_at_N():
    data = read_csv('exp1_encodings.csv')
    if not data:
        return

    encodings = list(dict.fromkeys(row['encoding'] for row in data))

    sizes_per_enc = {}
    for row in data:
        enc = row['encoding']
        if enc not in sizes_per_enc:
            sizes_per_enc[enc] = set()
        sizes_per_enc[enc].add(int(row['n']))

    common_sizes = set.intersection(*sizes_per_enc.values()) if sizes_per_enc else set()
    if not common_sizes:
        return
    target_n = max(common_sizes)

    times = []
    labels = []
    for enc in encodings:
        row = [r for r in data if r['encoding'] == enc and int(r['n']) == target_n]
        if row:
            times.append(float(row[0]['total_time']))
            labels.append(enc)

    sorted_pairs = sorted(zip(labels, times), key=lambda x: x[1])
    labels, times = zip(*sorted_pairs)

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.barh(range(len(labels)), times, color=COLORS[:len(labels)], edgecolor='white')
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    ax.set_xlabel('Total Time (seconds)')
    ax.set_title(f'Encoding Runtime Comparison at N = {target_n}')

    for bar, t in zip(bars, times):
        ax.text(bar.get_width() + max(times) * 0.01, bar.get_y() + bar.get_height() / 2,
                f'{t:.2f}s', va='center', fontsize=10)

    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, f'exp1_bar_N{target_n}.png'), dpi=150)
    print(f"  Saved: exp1_bar_N{target_n}.png")
    plt.close()


def plot_exp1_stacked_time():
    data = read_csv('exp1_encodings.csv')
    if not data:
        return

    all_n = sorted(set(int(row['n']) for row in data))
    target_ns = [n for n in [64, 125, 200, 256] if n in all_n]
    if not target_ns:
        target_ns = all_n[-3:] if len(all_n) >= 3 else all_n

    encodings = list(dict.fromkeys(row['encoding'] for row in data))

    for target_n in target_ns:
        enc_labels = []
        enc_times = []
        solve_times = []

        for enc in encodings:
            row = [r for r in data if r['encoding'] == enc and int(r['n']) == target_n]
            if row:
                enc_labels.append(enc)
                enc_times.append(float(row[0]['encoding_time']))
                solve_times.append(float(row[0]['solving_time']))

        if not enc_labels:
            continue

        total = [e + s for e, s in zip(enc_times, solve_times)]
        sorted_idx = sorted(range(len(total)), key=lambda i: total[i])
        enc_labels = [enc_labels[i] for i in sorted_idx]
        enc_times = [enc_times[i] for i in sorted_idx]
        solve_times = [solve_times[i] for i in sorted_idx]

        fig, ax = plt.subplots(figsize=(12, 6))
        x = range(len(enc_labels))

        bars1 = ax.barh(x, enc_times, label='Encoding Time', color='#2196F3', edgecolor='white')
        bars2 = ax.barh(x, solve_times, left=enc_times, label='Solving Time', color='#FF5722', edgecolor='white')

        ax.set_yticks(x)
        ax.set_yticklabels(enc_labels)
        ax.set_xlabel('Time (seconds)')
        ax.set_title(f'Encoding vs Solving Time at N = {target_n}')
        ax.legend()

        plt.tight_layout()
        plt.savefig(os.path.join(RESULTS_DIR, f'exp1_stacked_N{target_n}.png'), dpi=150)
        print(f"  Saved: exp1_stacked_N{target_n}.png")
        plt.close()


def plot_exp1_heatmap():
    data = read_csv('exp1_encodings.csv')
    if not data:
        return

    encodings = list(dict.fromkeys(row['encoding'] for row in data))
    all_n = sorted(set(int(row['n']) for row in data))

    matrix = []
    for enc in encodings:
        row_times = []
        for n in all_n:
            match = [r for r in data if r['encoding'] == enc and int(r['n']) == n]
            if match:
                t = float(match[0]['total_time'])
                row_times.append(t)
            else:
                row_times.append(float('nan'))
        matrix.append(row_times)

    matrix = np.array(matrix)
    log_matrix = np.log10(matrix + 1e-6)

    fig, ax = plt.subplots(figsize=(14, 7))
    im = ax.imshow(log_matrix, cmap='YlOrRd', aspect='auto')

    ax.set_xticks(range(len(all_n)))
    ax.set_xticklabels(all_n, rotation=45)
    ax.set_yticks(range(len(encodings)))
    ax.set_yticklabels(encodings)
    ax.set_xlabel('Board Size (N)')
    ax.set_ylabel('Encoding Method')
    ax.set_title('Runtime Heatmap (log₁₀ scale)')

    for i in range(len(encodings)):
        for j in range(len(all_n)):
            val = matrix[i, j]
            if not np.isnan(val):
                text = f'{val:.2f}' if val < 10 else f'{val:.1f}'
                color = 'white' if log_matrix[i, j] > np.nanmean(log_matrix) else 'black'
                ax.text(j, i, text, ha='center', va='center', fontsize=7, color=color)

    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('log₁₀(time in seconds)')

    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'exp1_heatmap.png'), dpi=150)
    print("  Saved: exp1_heatmap.png")
    plt.close()


def plot_exp2_solvers():
    data = read_csv('exp2_solvers.csv')
    if not data:
        return

    solvers = list(dict.fromkeys(row['solver'] for row in data))

    fig, ax = plt.subplots(figsize=(12, 7))

    for i, solver in enumerate(solvers):
        s_data = [row for row in data if row['solver'] == solver]
        ns = [int(row['n']) for row in s_data]
        times = [float(row['total_time']) for row in s_data]
        ax.plot(ns, times, 'o-', label=solver, linewidth=2.5, markersize=6,
                color=COLORS[i % len(COLORS)])

    ax.set_xlabel('Board Size (N)')
    ax.set_ylabel('Total Time (seconds)')
    ax.set_title('Runtime Comparison of SAT Solvers (SeqCounter encoding)')
    ax.legend(fontsize=12)
    ax.set_yscale('log')
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'exp2_solvers.png'), dpi=150)
    print("  Saved: exp2_solvers.png")
    plt.close()


def plot_exp2_bar():
    data = read_csv('exp2_solvers.csv')
    if not data:
        return

    solvers = list(dict.fromkeys(row['solver'] for row in data))
    sizes_per = {}
    for row in data:
        s = row['solver']
        if s not in sizes_per:
            sizes_per[s] = set()
        sizes_per[s].add(int(row['n']))

    common = set.intersection(*sizes_per.values()) if sizes_per else set()
    if not common:
        return
    target_n = max(common)

    labels = []
    times = []
    for solver in solvers:
        row = [r for r in data if r['solver'] == solver and int(r['n']) == target_n]
        if row:
            labels.append(solver)
            times.append(float(row[0]['total_time']))

    sorted_pairs = sorted(zip(labels, times), key=lambda x: x[1])
    labels, times = zip(*sorted_pairs)

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(range(len(labels)), times, color=COLORS[:len(labels)], edgecolor='white', width=0.6)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=15)
    ax.set_ylabel('Total Time (seconds)')
    ax.set_title(f'SAT Solver Comparison at N = {target_n}')

    for bar, t in zip(bars, times):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(times) * 0.02,
                f'{t:.2f}s', ha='center', fontsize=10)

    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, f'exp2_bar_N{target_n}.png'), dpi=150)
    print(f"  Saved: exp2_bar_N{target_n}.png")
    plt.close()


def plot_exp3_paradigms():
    data = read_csv('exp3_paradigms.csv')
    if not data:
        return

    methods = list(dict.fromkeys(row['method'] for row in data))

    fig, ax = plt.subplots(figsize=(12, 7))

    for i, method in enumerate(methods):
        m_data = [row for row in data if row['method'] == method and row['status'] == 'SAT']
        if not m_data:
            continue
        ns = [int(row['n']) for row in m_data]
        times = [float(row['total_time']) for row in m_data]
        ax.plot(ns, times, 'o-', label=method, linewidth=2.5, markersize=7,
                color=COLORS[i % len(COLORS)])

    ax.set_xlabel('Board Size (N)')
    ax.set_ylabel('Total Time (seconds)')
    ax.set_title('SAT vs ILP vs CP vs Backtracking')
    ax.legend(fontsize=11)
    ax.set_yscale('log')
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'exp3_paradigms.png'), dpi=150)
    print("  Saved: exp3_paradigms.png")
    plt.close()


def plot_exp3_grouped_bar():
    data = read_csv('exp3_paradigms.csv')
    if not data:
        return

    methods_with_data = []
    for method in dict.fromkeys(row['method'] for row in data):
        sat_rows = [r for r in data if r['method'] == method and r['status'] == 'SAT']
        if sat_rows:
            methods_with_data.append(method)

    if not methods_with_data:
        return

    all_n = sorted(set(int(row['n']) for row in data))
    target_ns = [n for n in [8, 25, 32, 64, 125, 200] if n in all_n]
    if not target_ns:
        target_ns = all_n[:5]

    good_ns = []
    for n in target_ns:
        count = sum(1 for m in methods_with_data
                    if any(r['method'] == m and int(r['n']) == n and r['status'] == 'SAT' for r in data))
        if count >= 2:
            good_ns.append(n)

    if not good_ns:
        return

    fig, ax = plt.subplots(figsize=(14, 7))
    x = np.arange(len(good_ns))
    width = 0.8 / len(methods_with_data)

    for i, method in enumerate(methods_with_data):
        times = []
        for n in good_ns:
            row = [r for r in data if r['method'] == method and int(r['n']) == n and r['status'] == 'SAT']
            if row:
                times.append(float(row[0]['total_time']))
            else:
                times.append(0)

        offset = (i - len(methods_with_data) / 2 + 0.5) * width
        bars = ax.bar(x + offset, times, width * 0.9, label=method,
                      color=COLORS[i % len(COLORS)], edgecolor='white')

    ax.set_xticks(x)
    ax.set_xticklabels([f'N={n}' for n in good_ns])
    ax.set_ylabel('Total Time (seconds)')
    ax.set_title('Solving Paradigm Comparison (grouped by N)')
    ax.legend(loc='upper left')
    ax.set_yscale('log')

    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'exp3_grouped_bar.png'), dpi=150)
    print("  Saved: exp3_grouped_bar.png")
    plt.close()


def plot_exp3_scalability():
    data = read_csv('exp3_paradigms.csv')
    if not data:
        return

    methods = list(dict.fromkeys(row['method'] for row in data))
    all_n = sorted(set(int(row['n']) for row in data))

    fig, ax = plt.subplots(figsize=(13, 7))

    for i, method in enumerate(methods):
        ns_ok = []
        times_ok = []
        ns_fail = []

        for n in all_n:
            row = [r for r in data if r['method'] == method and int(r['n']) == n]
            if not row:
                continue
            r = row[0]
            if r['status'] == 'SAT':
                ns_ok.append(n)
                times_ok.append(float(r['total_time']))
            else:
                ns_fail.append(n)

        c = COLORS[i % len(COLORS)]
        if ns_ok:
            ax.plot(ns_ok, times_ok, 'o-', label=method, linewidth=2.5,
                    markersize=7, color=c)
        if ns_fail:
            ax.scatter(ns_fail, [100] * len(ns_fail), marker='x', s=100,
                       color=c, linewidths=2.5, zorder=5)

    ax.axhline(y=100, color='red', linestyle=':', alpha=0.5, label='Timeout (100s)')
    ax.set_xlabel('Board Size (N)')
    ax.set_ylabel('Total Time (seconds)')
    ax.set_title('Scalability Analysis: Which Methods Scale?')
    ax.legend(loc='upper left', fontsize=9)
    ax.set_yscale('log')
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, 'exp3_scalability.png'), dpi=150)
    print("  Saved: exp3_scalability.png")
    plt.close()


if __name__ == '__main__':
    if not HAS_MPL:
        print("Cannot generate plots without matplotlib.")
        sys.exit(1)

    setup_style()

    print("=" * 60)
    print("  Generating plots from experiment results...")
    print("=" * 60)

    print("\n--- Experiment 1: Encoding Comparison ---")
    plot_exp1_runtime()
    plot_exp1_vars_clauses()
    plot_exp1_bar_at_N()
    plot_exp1_stacked_time()
    plot_exp1_heatmap()

    print("\n--- Experiment 2: SAT Solver Comparison ---")
    plot_exp2_solvers()
    plot_exp2_bar()

    print("\n--- Experiment 3: Paradigm Comparison ---")
    plot_exp3_paradigms()
    plot_exp3_grouped_bar()
    plot_exp3_scalability()

    print("\n" + "=" * 60)
    print("  All plots generated!")
    print("=" * 60)
