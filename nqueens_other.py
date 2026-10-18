"""
N-Queens Solvers for comparison with SAT encoding approach.

Implements:
  - Google OR-Tools CP-SAT  (Constraint Programming)
  - Gurobi MIP              (Integer Linear Programming)
  - CPLEX MIP               (Integer Linear Programming)
  - CPLEX CP                (Constraint Programming)
  - Backtracking            (Classical baseline)
"""

import time

try:
    from ortools.sat.python import cp_model
    HAS_ORTOOLS = True
except ImportError:
    HAS_ORTOOLS = False


def solve_nqueens_cpsat(n, timeout=100):
    if not HAS_ORTOOLS:
        return {'n': n, 'method': 'CP-SAT', 'status': 'NOT_AVAILABLE',
                'total_time': 0, 'solution': None}

    model = cp_model.CpModel()
    queens = [model.new_int_var(0, n - 1, f'q{i}') for i in range(n)]

    model.add_all_different(queens)
    model.add_all_different([queens[i] + i for i in range(n)])
    model.add_all_different([queens[i] - i for i in range(n)])

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = timeout

    t_start = time.perf_counter()
    status_code = solver.solve(model)
    t_total = time.perf_counter() - t_start

    solution = None
    if status_code in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        status = 'SAT'
        solution = [(i, solver.value(queens[i])) for i in range(n)]
    elif status_code == cp_model.INFEASIBLE:
        status = 'UNSAT'
    else:
        status = 'TIMEOUT'

    return {'n': n, 'method': 'CP-SAT', 'status': status,
            'total_time': round(t_total, 6), 'solution': solution}


try:
    import gurobipy as gp
    from gurobipy import GRB
    HAS_GUROBI = True
except ImportError:
    HAS_GUROBI = False


def solve_nqueens_gurobi(n, timeout=100):
    if not HAS_GUROBI:
        return {'n': n, 'method': 'Gurobi-MIP', 'status': 'NOT_AVAILABLE',
                'total_time': 0, 'solution': None}

    t_start = time.perf_counter()
    try:
        env = gp.Env(empty=True)
        env.setParam('OutputFlag', 0)
        env.start()

        m = gp.Model(env=env)
        m.setParam('TimeLimit', timeout)

        x = m.addVars(n, n, vtype=GRB.BINARY, name='x')

        for i in range(n):
            m.addConstr(gp.quicksum(x[i, j] for j in range(n)) == 1)

        for j in range(n):
            m.addConstr(gp.quicksum(x[i, j] for i in range(n)) == 1)

        for k in range(-(n - 1), n):
            diag_vars = [x[i, i - k] for i in range(n) if 0 <= i - k < n]
            if len(diag_vars) > 1:
                m.addConstr(gp.quicksum(diag_vars) <= 1)

        for k in range(2 * n - 1):
            anti_vars = [x[i, k - i] for i in range(n) if 0 <= k - i < n]
            if len(anti_vars) > 1:
                m.addConstr(gp.quicksum(anti_vars) <= 1)

        m.setObjective(0, GRB.MINIMIZE)

        m.optimize()
        t_total = time.perf_counter() - t_start

        solution = None
        if m.status == GRB.OPTIMAL or m.status == GRB.SUBOPTIMAL:
            status = 'SAT'
            solution = []
            for i in range(n):
                for j in range(n):
                    if x[i, j].X > 0.5:
                        solution.append((i, j))
        elif m.status == GRB.INFEASIBLE:
            status = 'UNSAT'
        elif m.status == GRB.TIME_LIMIT:
            status = 'TIMEOUT'
        else:
            status = f'GUROBI_{m.status}'

        m.dispose()
        env.dispose()

    except gp.GurobiError as e:
        t_total = time.perf_counter() - t_start
        status = f'ERROR: {e}'
        solution = None

    return {'n': n, 'method': 'Gurobi-MIP', 'status': status,
            'total_time': round(t_total, 6), 'solution': solution}


try:
    from docplex.mp.model import Model as CplexMipModel
    HAS_CPLEX_MIP = True
except ImportError:
    HAS_CPLEX_MIP = False


def solve_nqueens_cplex_mip(n, timeout=100):
    if not HAS_CPLEX_MIP:
        return {'n': n, 'method': 'CPLEX-MIP', 'status': 'NOT_AVAILABLE',
                'total_time': 0, 'solution': None}

    t_start = time.perf_counter()
    try:
        mdl = CplexMipModel(name=f'nqueens_{n}')
        mdl.set_time_limit(timeout)

        x = {(i, j): mdl.binary_var(name=f'x_{i}_{j}')
             for i in range(n) for j in range(n)}

        for i in range(n):
            mdl.add_constraint(mdl.sum(x[i, j] for j in range(n)) == 1)

        for j in range(n):
            mdl.add_constraint(mdl.sum(x[i, j] for i in range(n)) == 1)

        for k in range(-(n - 1), n):
            diag = [x[i, i - k] for i in range(n) if 0 <= i - k < n]
            if len(diag) > 1:
                mdl.add_constraint(mdl.sum(diag) <= 1)

        for k in range(2 * n - 1):
            anti = [x[i, k - i] for i in range(n) if 0 <= k - i < n]
            if len(anti) > 1:
                mdl.add_constraint(mdl.sum(anti) <= 1)

        sol = mdl.solve(log_output=False)
        t_total = time.perf_counter() - t_start

        solution = None
        if sol:
            status = 'SAT'
            solution = [(i, j) for i in range(n) for j in range(n)
                        if sol.get_value(x[i, j]) > 0.5]
        else:
            status = 'TIMEOUT' if t_total >= timeout * 0.95 else 'UNSAT'

        mdl.end()

    except Exception as e:
        t_total = time.perf_counter() - t_start
        status = f'ERROR: {e}'
        solution = None

    return {'n': n, 'method': 'CPLEX-MIP', 'status': status,
            'total_time': round(t_total, 6), 'solution': solution}


try:
    from docplex.cp.model import CpoModel
    HAS_CPLEX_CP = True
except ImportError:
    HAS_CPLEX_CP = False


def solve_nqueens_cplex_cp(n, timeout=100):
    if not HAS_CPLEX_CP:
        return {'n': n, 'method': 'CPLEX-CP', 'status': 'NOT_AVAILABLE',
                'total_time': 0, 'solution': None}

    t_start = time.perf_counter()
    try:
        mdl = CpoModel(name=f'nqueens_cp_{n}')

        queens = [mdl.integer_var(0, n - 1, name=f'q{i}') for i in range(n)]

        mdl.add(mdl.all_diff(queens))
        mdl.add(mdl.all_diff([queens[i] + i for i in range(n)]))
        mdl.add(mdl.all_diff([queens[i] - i for i in range(n)]))

        sol = mdl.solve(TimeLimit=timeout, LogVerbosity='Quiet')
        t_total = time.perf_counter() - t_start

        solution = None
        if sol:
            status = 'SAT'
            solution = [(i, sol.get_value(queens[i])) for i in range(n)]
        else:
            status = 'TIMEOUT' if t_total >= timeout * 0.95 else 'UNSAT'

    except Exception as e:
        t_total = time.perf_counter() - t_start
        status = f'ERROR: {e}'
        solution = None

    return {'n': n, 'method': 'CPLEX-CP', 'status': status,
            'total_time': round(t_total, 6), 'solution': solution}


def solve_nqueens_backtracking(n, timeout=100):
    t_start = time.perf_counter()
    cols = set()
    diag1 = set()
    diag2 = set()
    queens = []

    def backtrack(row):
        if time.perf_counter() - t_start > timeout:
            return False
        if row == n:
            return True
        for col in range(n):
            if col not in cols and (row - col) not in diag1 and (row + col) not in diag2:
                cols.add(col)
                diag1.add(row - col)
                diag2.add(row + col)
                queens.append((row, col))
                if backtrack(row + 1):
                    return True
                queens.pop()
                cols.remove(col)
                diag1.remove(row - col)
                diag2.remove(row + col)
        return False

    found = backtrack(0)
    t_total = time.perf_counter() - t_start

    if found:
        status = 'SAT'
    elif t_total >= timeout:
        status = 'TIMEOUT'
    else:
        status = 'UNSAT'

    return {'n': n, 'method': 'Backtracking', 'status': status,
            'total_time': round(t_total, 6),
            'solution': queens if found else None}


def get_available_solvers():
    return {
        'CP-SAT':     HAS_ORTOOLS,
        'Gurobi-MIP': HAS_GUROBI,
        'CPLEX-MIP':  HAS_CPLEX_MIP,
        'CPLEX-CP':   HAS_CPLEX_CP,
        'Backtracking': True,
    }


if __name__ == '__main__':
    print("=" * 65)
    print("  N-Queens Alternative Solvers - Quick Test")
    print("=" * 65)

    avail = get_available_solvers()
    print("\nSolver availability:")
    for name, ok in avail.items():
        mark = "OK" if ok else "NOT INSTALLED"
        print(f"  {name:<15} {mark}")
    print()

    solvers = [
        ('CP-SAT',     solve_nqueens_cpsat,       HAS_ORTOOLS),
        ('Gurobi-MIP', solve_nqueens_gurobi,      HAS_GUROBI),
        ('CPLEX-MIP',  solve_nqueens_cplex_mip,   HAS_CPLEX_MIP),
        ('CPLEX-CP',   solve_nqueens_cplex_cp,    HAS_CPLEX_CP),
        ('Backtrack',  solve_nqueens_backtracking, True),
    ]

    for n in [4, 8, 16, 32]:
        print(f"--- N = {n} ---")
        for name, func, available in solvers:
            if not available:
                print(f"  {name:<15} | SKIPPED (not installed)")
                continue
            bt_timeout = 10 if name == 'Backtrack' else 100
            res = func(n, timeout=bt_timeout)
            print(f"  {name:<15} | {res['status']:>7} | {res['total_time']:.4f}s")
        print()
