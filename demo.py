"""
Interactive demo — run from command line to test individual configurations.

Usage:
    python demo.py                     # Default: N=8, CaDiCaL, SeqCounter
    python demo.py 16                  # N=16
    python demo.py 32 glucose42        # N=32 with Glucose solver
    python demo.py 8 cadical195 pairwise  # N=8 with pairwise encoding
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from nqueens_sat import solve_nqueens_sat, verify_solution, print_board, ENCODINGS, SOLVERS
from nqueens_other import solve_nqueens_cpsat, solve_nqueens_backtracking


def demo(n=8, solver='cadical195', encoding='seqcounter'):
    print("=" * 60)
    print(f"  N-Queens SAT Solver Demo")
    print(f"  N = {n} | Solver = {solver} | Encoding = {encoding}")
    print("=" * 60)

    print(f"\n[1] SAT Solver ({solver} + {encoding})...")
    res = solve_nqueens_sat(n, solver_name=solver, encoding_name=encoding)
    valid = verify_solution(n, res['solution']) if res['solution'] else False

    print(f"    Status:    {res['status']}")
    print(f"    Time:      {res['total_time']:.6f}s")
    print(f"      Encoding:  {res['encoding_time']:.6f}s")
    print(f"      Solving:   {res['solving_time']:.6f}s")
    print(f"    Variables: {res['num_vars']:,}")
    print(f"    Clauses:   {res['num_clauses']:,}")
    print(f"    Valid:     {valid}")

    if n <= 32 and res['solution']:
        print_board(n, res['solution'])

    print(f"\n[2] CP-SAT (Google OR-Tools)...")
    res_cp = solve_nqueens_cpsat(n)
    valid_cp = verify_solution(n, res_cp['solution']) if res_cp['solution'] else False
    print(f"    Status: {res_cp['status']} | Time: {res_cp['total_time']:.6f}s | Valid: {valid_cp}")

    if n <= 30:
        print(f"\n[3] Backtracking...")
        res_bt = solve_nqueens_backtracking(n, timeout=10)
        valid_bt = verify_solution(n, res_bt['solution']) if res_bt['solution'] else False
        print(f"    Status: {res_bt['status']} | Time: {res_bt['total_time']:.6f}s | Valid: {valid_bt}")

    print(f"\n{'=' * 60}")
    print(f"  Summary for N={n}:")
    print(f"    SAT ({encoding}):  {res['total_time']:.6f}s")
    print(f"    CP-SAT:          {res_cp['total_time']:.6f}s")
    if n <= 30:
        print(f"    Backtracking:    {res_bt['total_time']:.6f}s")
    print(f"{'=' * 60}")


def show_help():
    print("N-Queens SAT Solver — Interactive Demo")
    print()
    print("Usage: python demo.py [N] [solver] [encoding]")
    print()
    print("Arguments:")
    print(f"  N         Board size (default: 8)")
    print(f"  solver    SAT solver: {', '.join(SOLVERS)}")
    print(f"  encoding  AMO encoding: {', '.join(ENCODINGS.keys())}")
    print()
    print("Examples:")
    print("  python demo.py")
    print("  python demo.py 16")
    print("  python demo.py 32 glucose42 pairwise")
    print("  python demo.py 100 cadical195 bitwise")


if __name__ == '__main__':
    if '--help' in sys.argv or '-h' in sys.argv:
        show_help()
        sys.exit(0)

    n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    solver = sys.argv[2] if len(sys.argv) > 2 else 'cadical195'
    encoding = sys.argv[3] if len(sys.argv) > 3 else 'seqcounter'

    demo(n, solver, encoding)
