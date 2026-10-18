"""
N-Queens SAT Solver using PySAT
Supports multiple AMO encoding methods and SAT solver backends.
"""

import time
from pysat.solvers import Solver
from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool


ENCODINGS = {
    'pairwise':   EncType.pairwise,
    'seqcounter': EncType.seqcounter,
    'sortnetwrk': EncType.sortnetwrk,
    'totalizer':  EncType.totalizer,
    'mtotalizer': EncType.mtotalizer,
    'kmtotalizer':EncType.kmtotalizer,
    'ladder':     EncType.ladder,
    'cardnetwrk': EncType.cardnetwrk,
    'bitwise':    EncType.bitwise,
}

SOLVERS = ['cadical195', 'glucose42', 'minisat22', 'lingeling']


def encode_nqueens(n, encoding_type=EncType.seqcounter):
    cnf = CNF()
    vpool = {}
    top_id = 0

    for i in range(n):
        for j in range(n):
            top_id += 1
            vpool[(i, j)] = top_id

    for i in range(n):
        row_vars = [vpool[(i, j)] for j in range(n)]
        cnf.append(row_vars)
        amo = CardEnc.atmost(row_vars, bound=1, top_id=top_id, encoding=encoding_type)
        top_id = amo.nv
        cnf.extend(amo.clauses)

    for j in range(n):
        col_vars = [vpool[(i, j)] for i in range(n)]
        cnf.append(col_vars)
        amo = CardEnc.atmost(col_vars, bound=1, top_id=top_id, encoding=encoding_type)
        top_id = amo.nv
        cnf.extend(amo.clauses)

    for k in range(-(n - 1), n):
        diag_vars = [vpool[(i, i - k)] for i in range(n) if 0 <= i - k < n]
        if len(diag_vars) > 1:
            amo = CardEnc.atmost(diag_vars, bound=1, top_id=top_id, encoding=encoding_type)
            top_id = amo.nv
            cnf.extend(amo.clauses)

    for k in range(2 * n - 1):
        anti_vars = [vpool[(i, k - i)] for i in range(n) if 0 <= k - i < n]
        if len(anti_vars) > 1:
            amo = CardEnc.atmost(anti_vars, bound=1, top_id=top_id, encoding=encoding_type)
            top_id = amo.nv
            cnf.extend(amo.clauses)

    stats = {
        'num_vars': cnf.nv,
        'num_clauses': len(cnf.clauses),
        'original_vars': n * n,
        'auxiliary_vars': cnf.nv - n * n,
    }

    return cnf, vpool, stats


def solve_nqueens_sat(n, solver_name='cadical195', encoding_name='seqcounter', timeout=100):
    encoding_type = ENCODINGS.get(encoding_name, EncType.seqcounter)

    t_enc_start = time.perf_counter()
    cnf, vpool, stats = encode_nqueens(n, encoding_type)
    t_enc = time.perf_counter() - t_enc_start

    t_solve_start = time.perf_counter()
    solution = None
    status = 'UNKNOWN'

    try:
        with Solver(name=solver_name, bootstrap_with=cnf) as solver:
            solved = solver.solve()
            t_solve = time.perf_counter() - t_solve_start

            if t_solve > timeout:
                status = 'TIMEOUT'
            elif solved:
                status = 'SAT'
                model = solver.get_model()
                queens = []
                for i in range(n):
                    for j in range(n):
                        var_id = vpool[(i, j)]
                        if var_id <= len(model) and model[var_id - 1] > 0:
                            queens.append((i, j))
                solution = queens
            else:
                status = 'UNSAT'
    except Exception as e:
        t_solve = time.perf_counter() - t_solve_start
        status = f'ERROR: {e}'

    total_time = t_enc + t_solve

    return {
        'n': n,
        'solver': solver_name,
        'encoding': encoding_name,
        'status': status,
        'encoding_time': round(t_enc, 6),
        'solving_time': round(t_solve, 6),
        'total_time': round(total_time, 6),
        'num_vars': stats['num_vars'],
        'num_clauses': stats['num_clauses'],
        'original_vars': stats['original_vars'],
        'auxiliary_vars': stats['auxiliary_vars'],
        'solution': solution,
    }


def print_board(n, queens):
    if queens is None:
        print("No solution found.")
        return
    queen_set = set(queens)
    print(f"\n{'='*3} N={n} Solution {'='*3}")
    for i in range(n):
        row = ""
        for j in range(n):
            if (i, j) in queen_set:
                row += " Q"
            else:
                row += " ."
        print(row)
    print()


def verify_solution(n, queens):
    if queens is None or len(queens) != n:
        return False

    rows = set()
    cols = set()
    diag1 = set()
    diag2 = set()

    for r, c in queens:
        if r in rows or c in cols or (r - c) in diag1 or (r + c) in diag2:
            return False
        rows.add(r)
        cols.add(c)
        diag1.add(r - c)
        diag2.add(r + c)

    return True


if __name__ == '__main__':
    print("=" * 60)
    print("N-Queens SAT Solver - Quick Test")
    print("=" * 60)

    for n in [4, 8, 16]:
        result = solve_nqueens_sat(n, solver_name='cadical195', encoding_name='seqcounter')
        valid = verify_solution(n, result['solution'])
        print(f"N={n:>4} | {result['status']:>5} | "
              f"Time: {result['total_time']:.4f}s | "
              f"Vars: {result['num_vars']:>8} | "
              f"Clauses: {result['num_clauses']:>10} | "
              f"Valid: {valid}")
        if n <= 8:
            print_board(n, result['solution'])
