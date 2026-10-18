"""
Run all experiments for N-Queens BTL.
Compares:
  - Different AMO encodings (Pairwise, SeqCounter, Bitwise, Totalizer, CardNetwrk)
  - Different SAT solvers (CaDiCaL, Glucose, MiniSat, Lingeling)
  - SAT vs CP-SAT vs Backtracking

Results are saved as CSV files for easy plotting.
"""

import csv
import os
import sys
import time
import platform

from nqueens_sat import solve_nqueens_sat, verify_solution, ENCODINGS, SOLVERS
from nqueens_other import (
    solve_nqueens_cpsat, solve_nqueens_backtracking,
    solve_nqueens_gurobi, solve_nqueens_cplex_mip, solve_nqueens_cplex_cp,
    get_available_solvers,
    HAS_ORTOOLS, HAS_GUROBI, HAS_CPLEX_MIP, HAS_CPLEX_CP
)


RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')
TIMEOUT = 100
DEFAULT_REPEATS = 3

SIZES_SMALL = [4, 8, 16, 25, 32, 49, 64]
SIZES_MEDIUM = [100, 125, 200, 256]
SIZES_LARGE = [300, 400, 500]

ALL_SIZES = SIZES_SMALL + SIZES_MEDIUM + SIZES_LARGE

KEY_ENCODINGS = list(ENCODINGS.keys())

FAST_ENCODINGS = ['seqcounter', 'bitwise', 'cardnetwrk']


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def get_system_info():
    print(f"  Python:    {platform.python_version()}")
    print(f"  Platform:  {platform.platform()}")
    print(f"  Processor: {platform.processor()}")
    try:
        import pysat
        print(f"  PySAT:     {pysat.__version__}")
    except Exception:
        print(f"  PySAT:     (version unknown)")
    try:
        from ortools import __version__ as ort_ver
        print(f"  OR-Tools:  {ort_ver}")
    except Exception:
        pass


import importlib.util

_enc_path = os.path.join(os.path.dirname(__file__), 'encodings.py')
_spec = importlib.util.spec_from_file_location("local_custom_encodings", _enc_path)
_custom_enc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_custom_enc)
solve_custom_encodings = _custom_enc.solve_n_queens

EXP1_ENCODINGS = ['binomial', 'sequential', 'binary', 'commander', 'product']
FAST_EXP1_ENCODINGS = ['sequential', 'binary', 'commander', 'product']


def exp1_compare_encodings(sizes=None, solver='cadical195', repeats=DEFAULT_REPEATS):
    if sizes is None:
        sizes = ALL_SIZES

    print("\n" + "=" * 70)
    print("EXPERIMENT 1: Compare AMO Encoding Methods (from encodings.py)")
    print(f"Encodings: {', '.join(EXP1_ENCODINGS)}")
    print(f"SAT Solver: {solver} | Timeout: {TIMEOUT}s | Repeats: {repeats}")
    print("=" * 70)

    results = []
    header = ['n', 'encoding', 'status', 'encoding_time', 'solving_time',
              'total_time', 'num_vars', 'num_clauses', 'valid']

    for n in sizes:
        if n >= 300:
            encodings_to_test = FAST_EXP1_ENCODINGS
        else:
            encodings_to_test = EXP1_ENCODINGS

        for enc_name in encodings_to_test:
            rep_label = f" ({repeats}x avg)" if repeats > 1 else ""
            print(f"  N={n:>5}, Encoding={enc_name:<12}{rep_label} ... ", end='', flush=True)
            try:
                times_enc = []
                times_solve = []
                times_total = []
                final_res = None
                status = 'UNKNOWN'

                for rep in range(repeats):
                    res = solve_custom_encodings(n, encoding=enc_name,
                                                 solver_name=solver, timeout=TIMEOUT)
                    final_res = res
                    status = res['status']
                    if status != 'SAT':
                        break
                    times_enc.append(res['encoding_time'])
                    times_solve.append(res['solving_time'])
                    times_total.append(res['total_time'])

                if status == 'SAT' and times_total:
                    avg_enc = round(sum(times_enc) / len(times_enc), 6)
                    avg_solve = round(sum(times_solve) / len(times_solve), 6)
                    avg_total = round(sum(times_total) / len(times_total), 6)
                else:
                    avg_enc = final_res['encoding_time'] if final_res else 0
                    avg_solve = final_res['solving_time'] if final_res else 0
                    avg_total = final_res['total_time'] if final_res else 0

                valid = verify_solution(n, final_res.get('solution')) if (final_res and final_res.get('solution')) else False
                num_vars = final_res['num_vars'] if final_res else 0
                num_clauses = final_res['num_clauses'] if final_res else 0

                row = [n, enc_name, status, avg_enc, avg_solve, avg_total,
                       num_vars, num_clauses, valid]
                results.append(row)
                print(f"{status:>7} | {avg_total:.4f}s | "
                      f"Vars: {num_vars:>10} | Cls: {num_clauses:>12}")
            except Exception as e:
                print(f"ERROR: {e}")
                results.append([n, enc_name, 'ERROR', 0, 0, 0, 0, 0, False])

    csv_path = os.path.join(RESULTS_DIR, 'exp1_encodings.csv')
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(results)
    print(f"\nResults saved to: {csv_path}")
    return results


def exp2_compare_solvers(sizes=None, encoding='seqcounter', repeats=DEFAULT_REPEATS):
    if sizes is None:
        sizes = SIZES_SMALL + SIZES_MEDIUM

    print("\n" + "=" * 70)
    print("EXPERIMENT 2: Compare SAT Solvers")
    print(f"Encoding: {encoding} | Timeout: {TIMEOUT}s | Repeats: {repeats}")
    print("=" * 70)

    results = []
    header = ['n', 'solver', 'status', 'encoding_time', 'solving_time',
              'total_time', 'num_vars', 'num_clauses', 'valid']

    for n in sizes:
        for solver_name in SOLVERS:
            rep_label = f" ({repeats}x avg)" if repeats > 1 else ""
            print(f"  N={n:>5}, Solver={solver_name:<15}{rep_label} ... ", end='', flush=True)
            try:
                times_enc = []
                times_solve = []
                times_total = []
                final_res = None
                status = 'UNKNOWN'

                for rep in range(repeats):
                    res = solve_nqueens_sat(n, solver_name=solver_name,
                                            encoding_name=encoding, timeout=TIMEOUT)
                    final_res = res
                    status = res['status']
                    if status != 'SAT':
                        break
                    times_enc.append(res['encoding_time'])
                    times_solve.append(res['solving_time'])
                    times_total.append(res['total_time'])

                if status == 'SAT' and times_total:
                    avg_enc = round(sum(times_enc) / len(times_enc), 6)
                    avg_solve = round(sum(times_solve) / len(times_solve), 6)
                    avg_total = round(sum(times_total) / len(times_total), 6)
                else:
                    avg_enc = final_res['encoding_time'] if final_res else 0
                    avg_solve = final_res['solving_time'] if final_res else 0
                    avg_total = final_res['total_time'] if final_res else 0

                valid = verify_solution(n, final_res.get('solution')) if (final_res and final_res.get('solution')) else False
                num_vars = final_res['num_vars'] if final_res else 0
                num_clauses = final_res['num_clauses'] if final_res else 0

                row = [n, solver_name, status, avg_enc, avg_solve, avg_total,
                       num_vars, num_clauses, valid]
                results.append(row)
                print(f"{status:>7} | {avg_total:.4f}s")
            except Exception as e:
                print(f"ERROR: {e}")
                results.append([n, solver_name, 'ERROR', 0, 0, 0, 0, 0, False])

    csv_path = os.path.join(RESULTS_DIR, 'exp2_solvers.csv')
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(results)
    print(f"\nResults saved to: {csv_path}")
    return results


def exp3_compare_paradigms(sizes=None, repeats=DEFAULT_REPEATS):
    if sizes is None:
        sizes = ALL_SIZES

    print("\n" + "=" * 70)
    print("EXPERIMENT 3: SAT vs ILP vs CP vs Backtracking")
    print(f"Timeout: {TIMEOUT}s | Repeats: {repeats}")
    print("=" * 70)

    avail = get_available_solvers()
    print("Available solvers:")
    for name, ok in avail.items():
        print(f"  {name:<15} {'OK' if ok else 'NOT INSTALLED'}")
    print()

    results = []
    header = ['n', 'method', 'status', 'total_time', 'valid']

    solver_configs = [
        ('SAT-SeqCounter',  lambda n, t: solve_nqueens_sat(n, solver_name='cadical195',
                                                            encoding_name='seqcounter', timeout=t),
         True),
        ('SAT-Bitwise',     lambda n, t: solve_nqueens_sat(n, solver_name='cadical195',
                                                            encoding_name='bitwise', timeout=t),
         True),
        ('CP-SAT',          lambda n, t: solve_nqueens_cpsat(n, timeout=t),
         HAS_ORTOOLS),
        ('Gurobi-MIP',      lambda n, t: solve_nqueens_gurobi(n, timeout=t),
         HAS_GUROBI),
        ('CPLEX-MIP',       lambda n, t: solve_nqueens_cplex_mip(n, timeout=t),
         HAS_CPLEX_MIP),
        ('CPLEX-CP',        lambda n, t: solve_nqueens_cplex_cp(n, timeout=t),
         HAS_CPLEX_CP),
        ('Backtracking',    lambda n, t: solve_nqueens_backtracking(n, timeout=t),
         True),
    ]

    for n in sizes:
        for method_name, solver_func, is_available in solver_configs:
            if not is_available:
                results.append([n, method_name, 'NOT_AVAILABLE', 0, False])
                continue

            t = min(TIMEOUT, 30) if method_name == 'Backtracking' and n <= 64 else \
                (5 if method_name == 'Backtracking' else TIMEOUT)

            rep_label = f" ({repeats}x avg)" if repeats > 1 else ""
            print(f"  N={n:>5}, {method_name:<20}{rep_label} ... ", end='', flush=True)
            try:
                times_total = []
                final_res = None
                status = 'UNKNOWN'

                for rep in range(repeats):
                    res = solver_func(n, t)
                    final_res = res
                    status = res.get('status', 'UNKNOWN')
                    if status != 'SAT':
                        break
                    times_total.append(res['total_time'])

                if status == 'SAT' and times_total:
                    avg_total = round(sum(times_total) / len(times_total), 6)
                else:
                    avg_total = final_res['total_time'] if final_res else 0

                valid = verify_solution(n, final_res.get('solution')) if (final_res and final_res.get('solution')) else False
                results.append([n, method_name, status, avg_total, valid])
                print(f"{status:>7} | {avg_total:.4f}s")
            except Exception as e:
                results.append([n, method_name, 'ERROR', 0, False])
                print(f"ERROR: {e}")

        print()

    csv_path = os.path.join(RESULTS_DIR, 'exp3_paradigms.csv')
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(results)
    print(f"\nResults saved to: {csv_path}")
    return results


if __name__ == '__main__':
    ensure_dir(RESULTS_DIR)

    repeats = DEFAULT_REPEATS
    exps = []
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg in ('--repeats', '-r') and i + 1 < len(sys.argv):
            try:
                repeats = int(sys.argv[i + 1])
                i += 2
                continue
            except ValueError:
                pass
        if arg.isdigit():
            exps.append(arg)
        i += 1

    if not exps:
        exps = ['1', '2', '3']

    print("=" * 62)
    print("  N-Queens SAT Solver -- Experimental Evaluation")
    print("  Course: INT3131 -- Cac van de hien dai KHMT")
    print("=" * 62)
    print(f"  Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Timeout:   {TIMEOUT}s per instance")
    print(f"  Repeats:   {repeats} runs per instance (average reported)")
    print(f"  Results:   {RESULTS_DIR}")
    get_system_info()
    print()

    t_start = time.perf_counter()

    if '1' in exps:
        exp1_compare_encodings(repeats=repeats)

    if '2' in exps:
        exp2_compare_solvers(repeats=repeats)

    if '3' in exps:
        exp3_compare_paradigms(repeats=repeats)

    t_total = time.perf_counter() - t_start
    print(f"\nAll experiments completed in {t_total:.1f}s")
    print(f"Results saved in: {RESULTS_DIR}")
