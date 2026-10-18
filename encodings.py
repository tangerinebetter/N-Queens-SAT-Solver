"""
Encoding module — Implementations of AMO (At-Most-One) and ALO (At-Least-One)
constraint encoding methods for the N-Queens problem.

Supported encoding methods:
  1. Binomial (Pairwise / Naive)
  2. Sequential Counter (Sinz, 2005)
  3. Binary (Bitwise / Bimander)
  4. Commander (Klieber & Kwon, 2007)
  5. Product (Chen, 2010)
"""

import math
import time
from pysat.solvers import Glucose3, Solver


def generate_variables(n):
    return [[i * n + j + 1 for j in range(n)] for i in range(n)]


def at_least_one(clauses, variables):
    clauses.append(list(variables))


def binomial_amo(clauses, variables):
    k = len(variables)
    for i in range(k):
        for j in range(i + 1, k):
            clauses.append([-variables[i], -variables[j]])
    return clauses


def sequential_amo(clauses, variables, n, aux_counter):
    k = len(variables)
    if k <= 1:
        return

    start = n ** 2 + aux_counter[0]
    new_vars = [start + i + 1 for i in range(k - 1)]
    aux_counter[0] += (k - 1)

    clauses.append([-variables[0], new_vars[0]])

    for i in range(1, k - 1):
        clauses.append([-variables[i], new_vars[i]])
        clauses.append([-new_vars[i - 1], new_vars[i]])
        clauses.append([-new_vars[i - 1], -variables[i]])

    clauses.append([-new_vars[k - 2], -variables[k - 1]])


def _generate_binary_combinations(k):
    return [format(i, '0' + str(k) + 'b') for i in range(1 << k)]


def binary_amo(clauses, variables, n, aux_counter):
    k = len(variables)
    if k <= 1:
        return

    m = math.ceil(math.log2(k))
    start = n ** 2 + aux_counter[0]
    temp_new_vars = [start + i + 1 for i in range(m)]
    aux_counter[0] += m

    binary_combinations = _generate_binary_combinations(m)
    for i in range(k):
        comb = binary_combinations[i]
        temp_clause = []
        for j in range(len(comb) - 1, -1, -1):
            idx = len(comb) - j - 1
            bit = temp_new_vars[idx] if comb[j] == '1' else -temp_new_vars[idx]
            temp_clause.append(bit)
        for bit in temp_clause:
            clauses.append([-variables[i], bit])


def _grouping_variables(variables, per_group):
    groups = []
    temp_groups = []
    per_group = max(1, int(per_group))
    for i in range(len(variables)):
        temp_groups.append(variables[i])
        if (i + 1) % per_group == 0 or i == len(variables) - 1:
            groups.append(temp_groups)
            temp_groups = []
    return groups


def commander_amo(clauses, variables, n, aux_counter):
    k = len(variables)
    if k <= 1:
        return

    per_group = max(2, int(n / max(1, math.floor(math.sqrt(n)))))
    groups = _grouping_variables(variables, per_group)

    start = n ** 2 + aux_counter[0]
    commanders = [start + i + 1 for i in range(len(groups))]
    aux_counter[0] += len(groups)

    binomial_amo(clauses, commanders)

    for i in range(len(commanders)):
        grp = groups[i]
        if len(grp) > 4:
            binary_amo(clauses, grp, n, aux_counter)
        else:
            binomial_amo(clauses, grp)

        for j in range(len(grp)):
            clauses.append([commanders[i], -grp[j]])

        clauses.append(grp + [-commanders[i]])


def product_amo(clauses, variables, n, aux_counter):
    k = len(variables)
    if k <= 1:
        return

    p = math.ceil(math.sqrt(k))
    q = math.ceil(k / p)

    start = n ** 2 + aux_counter[0]
    row = [start + i + 1 for i in range(p)]
    col = [start + p + j + 1 for j in range(q)]
    aux_counter[0] += (p + q)

    if k > 10:
        binary_amo(clauses, row, n, aux_counter)
        binary_amo(clauses, col, n, aux_counter)
    else:
        binomial_amo(clauses, row)
        binomial_amo(clauses, col)

    x = 0
    for i in range(p):
        for j in range(q):
            if x < k:
                clauses.append([-variables[x], row[i]])
                clauses.append([-variables[x], col[j]])
                x += 1
            else:
                break
        if x >= k:
            break


ENCODINGS = {
    'binomial': binomial_amo,
    'pairwise': binomial_amo,
    'sequential': sequential_amo,
    'seqcounter': sequential_amo,
    'binary': binary_amo,
    'bitwise': binary_amo,
    'commander': commander_amo,
    'product': product_amo,
}


def apply_amo(clauses, variables, encoding, n, aux_counter):
    if len(variables) <= 1:
        return
    if encoding in ('binomial', 'pairwise'):
        binomial_amo(clauses, variables)
    elif encoding in ('sequential', 'seqcounter'):
        sequential_amo(clauses, variables, n, aux_counter)
    elif encoding in ('binary', 'bitwise'):
        binary_amo(clauses, variables, n, aux_counter)
    elif encoding == 'commander':
        commander_amo(clauses, variables, n, aux_counter)
    elif encoding == 'product':
        product_amo(clauses, variables, n, aux_counter)
    else:
        raise ValueError(f"Unknown encoding: {encoding}. Choose from {list(ENCODINGS.keys())}")


def exactly_one(clauses, variables, encoding, n, aux_counter):
    at_least_one(clauses, variables)
    apply_amo(clauses, variables, encoding, n, aux_counter)


def generate_clauses(n, encoding='binomial'):
    variables = generate_variables(n)
    clauses = []
    aux_counter = [0]

    for row in range(n):
        exactly_one(clauses, variables[row], encoding, n, aux_counter)

    for col in range(n):
        col_vars = [variables[row][col] for row in range(n)]
        exactly_one(clauses, col_vars, encoding, n, aux_counter)

    for i in range(1, n):
        diag = []
        r, c = i, 0
        while r >= 0 and c < n:
            diag.append(variables[r][c])
            r -= 1
            c += 1
        apply_amo(clauses, diag, encoding, n, aux_counter)

    for j in range(1, n - 1):
        diag = []
        r, c = n - 1, j
        while r >= 0 and c < n:
            diag.append(variables[r][c])
            r -= 1
            c += 1
        apply_amo(clauses, diag, encoding, n, aux_counter)

    for i in range(n - 1):
        diag = []
        r, c = i, 0
        while r < n and c < n:
            diag.append(variables[r][c])
            r += 1
            c += 1
        apply_amo(clauses, diag, encoding, n, aux_counter)

    for j in range(1, n - 1):
        diag = []
        r, c = 0, j
        while r < n and c < n:
            diag.append(variables[r][c])
            r += 1
            c += 1
        apply_amo(clauses, diag, encoding, n, aux_counter)

    return clauses, aux_counter[0]


def solve_n_queens(n, encoding='binomial', solver_name='glucose3', timeout=100):
    t_start = time.perf_counter()
    try:
        clauses, num_aux = generate_clauses(n, encoding)
    except Exception as e:
        return {
            'n': n, 'encoding': encoding, 'solver': solver_name,
            'status': f'ERROR: {e}', 'encoding_time': 0, 'solving_time': 0,
            'total_time': 0, 'num_vars': 0, 'num_clauses': 0, 'solution': None,
        }
    t_encode = time.perf_counter() - t_start

    t_solve_start = time.perf_counter()
    solution = None
    status = 'UNKNOWN'

    try:
        with Solver(name=solver_name, bootstrap_with=clauses) as solver:
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
                        var_id = i * n + j + 1
                        if var_id <= len(model) and model[var_id - 1] > 0:
                            queens.append((i, j))
                solution = queens
            else:
                status = 'UNSAT'
    except Exception as e:
        t_solve = time.perf_counter() - t_solve_start
        status = f'ERROR: {e}'

    return {
        'n': n,
        'encoding': encoding,
        'solver': solver_name,
        'status': status,
        'encoding_time': round(t_encode, 6),
        'solving_time': round(t_solve, 6),
        'total_time': round(t_encode + t_solve, 6),
        'num_vars': n * n + num_aux,
        'num_clauses': len(clauses),
        'solution': solution,
    }


def print_solution(solution, n=None):
    if not solution:
        print("No solution found.")
        return
    if n is None:
        n = max(max(r, c) for r, c in solution) + 1
    board = [['.' for _ in range(n)] for _ in range(n)]
    for r, c in solution:
        board[r][c] = 'Q'
    for row in board:
        print(" ".join(row))


if __name__ == '__main__':
    print("=" * 70)
    print("N-Queens SAT Solver -- AMO Encodings Test")
    print("=" * 70)

    test_encodings = ['binomial', 'sequential', 'binary', 'commander', 'product']
    n = 8
    print(f"\nTesting N = {n} on all 5 encodings:")
    for enc in test_encodings:
        res = solve_n_queens(n, encoding=enc, solver_name='glucose3')
        print(f"  - {enc:<12}: Status={res['status']}, Time={res['total_time']:.4f}s, "
              f"Vars={res['num_vars']}, Clauses={res['num_clauses']}")

    print("\nSample 8-Queens solution (Binary encoding):")
    res = solve_n_queens(8, encoding='binary')
    print_solution(res['solution'])
