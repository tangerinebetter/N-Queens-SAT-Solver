"""
Benchmark analysis — load CSV results and generate summary statistics.
Produces LaTeX-ready tables for the report.
"""

import csv
import os
import sys

RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')


def read_csv(filename):
    path = os.path.join(RESULTS_DIR, filename)
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return []
    with open(path, 'r') as f:
        return list(csv.DictReader(f))


def print_summary_table(data, group_by, value_col='total_time', title=''):
    if not data:
        return

    sizes = sorted(set(int(row['n']) for row in data))
    groups = list(dict.fromkeys(row[group_by] for row in data))

    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}")

    header = f"{'N':>6}"
    for g in groups:
        header += f" | {g:>14}"
    print(header)
    print("-" * len(header))

    for n in sizes:
        row_str = f"{n:>6}"
        for g in groups:
            matches = [r for r in data if int(r['n']) == n and r[group_by] == g]
            if matches:
                val = float(matches[0][value_col])
                status = matches[0].get('status', 'SAT')
                if status == 'TIMEOUT':
                    row_str += f" | {'TIMEOUT':>14}"
                else:
                    row_str += f" | {val:>14.4f}"
            else:
                row_str += f" | {'N/A':>14}"
        print(row_str)


def generate_latex_table(data, group_by, value_col='total_time', caption='', label=''):
    if not data:
        return ""

    sizes = sorted(set(int(row['n']) for row in data))
    groups = list(dict.fromkeys(row[group_by] for row in data))

    lines = []
    lines.append(r"\begin{table}[htbp]")
    lines.append(r"\centering")
    lines.append(f"\\caption{{{caption}}}")
    if label:
        lines.append(f"\\label{{{label}}}")

    col_spec = "r" + "r" * len(groups)
    lines.append(f"\\begin{{tabular}}{{{col_spec}}}")
    lines.append(r"\hline")

    header = "N"
    for g in groups:
        header += f" & {g}"
    header += r" \\"
    lines.append(header)
    lines.append(r"\hline")

    for n in sizes:
        row_str = str(n)
        for g in groups:
            matches = [r for r in data if int(r['n']) == n and r[group_by] == g]
            if matches:
                val = float(matches[0][value_col])
                status = matches[0].get('status', 'SAT')
                if status == 'TIMEOUT':
                    row_str += " & TO"
                else:
                    row_str += f" & {val:.4f}"
            else:
                row_str += " & --"
        row_str += r" \\"
        lines.append(row_str)

    lines.append(r"\hline")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{table}")

    return "\n".join(lines)


def analyze_all():
    exp1 = read_csv('exp1_encodings.csv')
    if exp1:
        print_summary_table(exp1, 'encoding', 'total_time',
                            'Exp 1: Runtime by Encoding (seconds)')
        print_summary_table(exp1, 'encoding', 'num_vars',
                            'Exp 1: Number of Variables by Encoding')
        print_summary_table(exp1, 'encoding', 'num_clauses',
                            'Exp 1: Number of Clauses by Encoding')

        latex1 = generate_latex_table(exp1, 'encoding', 'total_time',
                                       'Runtime comparison of AMO encoding methods (seconds)',
                                       label='tab:exp1_runtime')
        with open(os.path.join(RESULTS_DIR, 'table_exp1_runtime.tex'), 'w') as f:
            f.write(latex1)
        print("\nSaved: table_exp1_runtime.tex")

    exp2 = read_csv('exp2_solvers.csv')
    if exp2:
        print_summary_table(exp2, 'solver', 'total_time',
                            'Exp 2: Runtime by SAT Solver (seconds)')

        latex2 = generate_latex_table(exp2, 'solver', 'total_time',
                                       'Runtime comparison of SAT solvers (seconds)',
                                       label='tab:exp2_solvers')
        with open(os.path.join(RESULTS_DIR, 'table_exp2_solvers.tex'), 'w') as f:
            f.write(latex2)
        print("\nSaved: table_exp2_solvers.tex")

    exp3 = read_csv('exp3_paradigms.csv')
    if exp3:
        print_summary_table(exp3, 'method', 'total_time',
                            'Exp 3: SAT vs CP-SAT vs Backtracking (seconds)')

        latex3 = generate_latex_table(exp3, 'method', 'total_time',
                                       'Runtime comparison of solving paradigms (seconds)',
                                       label='tab:exp3_paradigms')
        with open(os.path.join(RESULTS_DIR, 'table_exp3_paradigms.tex'), 'w') as f:
            f.write(latex3)
        print("\nSaved: table_exp3_paradigms.tex")

    if exp1:
        print(f"\n{'=' * 60}")
        print("  Best Encoding for Each N")
        print(f"{'=' * 60}")
        sizes = sorted(set(int(row['n']) for row in exp1))
        for n in sizes:
            n_data = [r for r in exp1 if int(r['n']) == n and r['status'] == 'SAT']
            if n_data:
                best = min(n_data, key=lambda r: float(r['total_time']))
                print(f"  N={n:>5}: {best['encoding']:<15} ({float(best['total_time']):.4f}s)")


if __name__ == '__main__':
    analyze_all()
