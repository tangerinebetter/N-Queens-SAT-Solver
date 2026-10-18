# N-Queens Problem: SAT Encodings & Solver Benchmarks

This is my course project for **Assignment 1** in **INT3131 - Advanced Topics in Computer Science** at **VNU University of Engineering and Technology (VNU-UET)**.

The project explores how to solve the classic $N$-Queens problem using **SAT (Boolean Satisfiability)** encoding, compares 5 different ways to encode the "At-Most-One" (AMO) constraint on diagonals, and benchmarks SAT against other popular solvers (Google OR-Tools CP-SAT, Gurobi, IBM CPLEX, and standard Backtracking).

---

## Student & Course Info

* **Student**: Đỗ Huy Hiếu (Do Huy Hieu)
* **Student ID**: `24021470`
* **Email**: `24021470@vnu.edu.vn`
* **Supervisor**: Dr. Tô Văn Khánh (Dr. To Van Khanh)
* **Course**: INT3131 — Advanced Topics in Computer Science (HK1, 2026–2027)
* **Faculty**: Faculty of Information Technology, VNU-UET

---

## What's in this Project?

### 1. Five At-Most-One (AMO) Encodings
The hardest part of formulating $N$-Queens in SAT is preventing queens from attacking on the diagonal lines without creating millions of clauses. I implemented and evaluated 5 different AMO methods:
1. **Binomial (Pairwise / Naive)**: Forbids every pair with $(\neg u \vee \neg v)$. Simple and needs 0 extra variables, but creates $O(k^2)$ clauses per diagonal.
2. **Sequential Counter (Sinz, 2005)**: Uses an auxiliary counting chain to pass prefix sums ($O(k)$ variables, $O(k)$ clauses).
3. **Binary (Bitwise)**: Assigns each queen a binary index using logarithmic auxiliary variables ($O(\log k)$ variables, $O(k \log k)$ clauses).
4. **Commander Variable (Klieber & Kwon, 2007)**: Splits queens into groups of 3 with a "commander" variable for each group.
5. **Product (Chen, 2010)**: Maps queens onto a 2D grid of size $\approx \sqrt{k} \times \sqrt{k}$ to keep clauses low ($2\sqrt{k}$ variables, $O(k)$ clauses).

### 2. Four SAT Solvers (CDCL)
Tested using [PySAT](https://pysathq.github.io/):
* **CaDiCaL 1.9.5**
* **Glucose 4.2**
* **MiniSat 2.2**
* **Lingeling**

### 3. Cross-Paradigm Solvers
I also built solvers using other approaches to compare against SAT:
* **Constraint Programming**: Google OR-Tools (CP-SAT) and IBM ILOG CPLEX CP Optimizer using `AllDifferent` constraints.
* **Integer Linear Programming (MIP)**: 0-1 binary integer model running on Gurobi 12.0 and CPLEX MIP 22.1.
* **Classical Backtracking**: Standard recursive depth-first search with column and diagonal bitmasks.

---

## Project Structure

```text
nqueens-sat/
├── encodings.py           # Clean implementation of the 5 AMO encodings + ALO
├── nqueens_sat.py         # PySAT wrapper supporting different encodings & solvers
├── nqueens_other.py       # Solvers for CP-SAT, Gurobi, CPLEX, and Backtracking
├── run_experiments.py     # Runs experiments with 3-run averaging protocol
├── plot_results.py        # Generates charts and plots from CSV results
├── analyze.py             # Generates summary tables and LaTeX table snippets
├── visualize.py           # Plots chessboard solutions and queen attack vectors
├── demo.py                # Quick interactive CLI demo
├── requirements.txt       # Dependencies list
├── results/               # CSV benchmark logs, generated PNG plots, and .tex tables
└── report/                # Complete LaTeX report package (Elsevier cas-sc template)
    ├── main.tex           # Academic report manuscript (INT3131 Assignment 1)
    ├── cas-sc.cls         # Elsevier CAS Single Column document class
    ├── cas-common.sty     # Elsevier CAS common layout and styling package
    ├── cas-model2-names.bst # Elsevier BibTeX style specification
    └── figs/              # 18 figures including chessboard states, attack vectors, and benchmark charts
```

---

## Getting Started

### 1. Installation
Clone the repository and install the required Python libraries:
```bash
git clone https://github.com/tangerinebetter/N-Queens-SAT-Solver.git
cd N-Queens-SAT-Solver
pip install -r requirements.txt
```

*(Core dependencies: `python-sat`, `ortools`, `matplotlib`, `numpy`, `pandas`).*

> **Note on Gurobi & CPLEX**: If you want to run the commercial MIP/CP solvers in Experiment 3, install `gurobipy` and `docplex` with an active academic license. If they aren't installed, the runner will safely skip them.

### 2. Quick Demo
Try solving $N$-Queens directly from the terminal:
```bash
# Solve 8-Queens (default: CaDiCaL + Sequential Counter)
python demo.py

# Solve 16-Queens
python demo.py 16

# Solve 100-Queens with bitwise encoding
python demo.py 100 cadical195 bitwise
```

### 3. Test the Encodings
You can run a quick check on all 5 AMO encodings on small boards ($N = 4$ to $64$):
```bash
python encodings.py
```

### 4. Running the Full Experiments
To minimize CPU frequency noise, each test is run 3 times and averages the runtime:
```bash
# Exp 1: Compare the 5 AMO encodings (up to N = 500)
python run_experiments.py 1

# Exp 2: Compare 4 SAT solvers (up to N = 256)
python run_experiments.py 2

# Exp 3: Compare SAT vs CP-SAT vs Gurobi vs CPLEX vs Backtracking
python run_experiments.py 3

# Or run all 3 experiments together
python run_experiments.py
```

### 5. Plotting Results
After running experiments, generate the visual plots:
```bash
python plot_results.py
```
This produces:
* `exp1_runtime.png`: Runtime comparison of the 5 encodings
* `exp1_vars_clauses.png`: Growth of variables and clauses
* `exp2_solvers.png`: Solver performance comparison
* `exp3_scalability.png`: Scalability comparison across all paradigms with 100s timeout cutoff

---

## Summary of Empirical Results

Key takeaways from our rigorous 3-run averaged benchmarks ($N \in [4, 500]$, 100s timeout per run):

1. **At-Most-One (AMO) Encodings (Experiment 1)**:
   * **Binomial (Pairwise) Collapse**: Preserves arc consistency via unit propagation without auxiliary variables, but suffers a severe $\Theta(N^3)$ clause bottleneck ($16.8 \times 10^6$ clauses at $N = 256$, taking $62.62$~s). For $N \ge 300$, it exhausts physical memory and cannot be solved.
   * **Product Encoding Superiority**: Chen's 2D grid encoding introduces $2\sqrt{k}$ auxiliary variables and keeps clauses bounded by $O(N^2)$, achieving the fastest SAT solve times across all large instances (**$9.04$~s at $N = 500$**).
   * **Binary (Bitwise) Scalability**: Logarithmic auxiliary variables ($O(\log k)$) produce $O(N^2 \log N)$ clauses and scale smoothly to **$16.53$~s at $N = 500$**.
   * **Commander Encoding**: Robust performance throughout, solving $N = 256$ in $4.50$~s and $N = 500$ in $31.03$~s.
   * **Sequential Counter**: Sinz's chain encoding reaches $20.33$~s at $N = 256$ and $57.16$~s at $N = 500$, though it encounters localized timeouts near $N = 400$.

2. **SAT Solver Backends (Experiment 2)**:
   * **MiniSat 2.2 & Lingeling Dominance**: Highly effective heuristics for symmetric chessboards, solving $N = 256$ in **$1.95$~s** and **$1.66$~s**, respectively.
   * **Glucose 4.2 LBD Bottleneck**: While competitive for $N \le 25$, Glucose degrades on large boards ($15.48$~s at $N = 64$, $66.36$~s at $N = 125$) and times out at $N \ge 200$ because its aggressive Literal Block Distance (LBD) clause purging prematurely discards valuable conflict clauses in symmetric spaces.
   * **CaDiCaL 1.9.5 Robustness**: Successfully certifies all tested instances up to $N = 256$ ($31.53$~s) without timing out.

3. **Cross-Paradigm Comparison (Experiment 3)**:
   * **ILP / MIP Efficiency**: IBM ILOG CPLEX CP Optimizer (**$0.18$~s at $N = 500$**) and Gurobi Optimizer 12.0 (**$1.42$~s at $N = 500$**) achieve extraordinary performance. The 0-1 constraint matrix exhibits strong LP relaxation bounds, allowing branch-and-cut presolvers to eliminate fractional branches almost instantaneously.
   * **SAT vs. CP-SAT**: SAT with compact encodings (Bitwise, Product) comfortably scales to $N = 500$, outperforming Google OR-Tools CP-SAT which encounters timeouts at $N \ge 300$ due to domain propagation overhead.
   * **Classical Backtracking Combinatorial Cliff**: Backtracking is fastest for small boards ($N \le 16$, $< 0.012$~s) due to zero modeling setup, but its $O(N!)$ complexity collapses at $N = 32$ (exceeding 30s cutoff) and fails for all subsequent sizes.

---

## Written Report

The complete academic manuscript submitted for Assignment 1 is located in the [`report/`](report/) folder:
* **[`report/main.tex`](report/main.tex)**: Formatted using Elsevier's official **`cas-sc`** (Single Column) journal class.
* **Layout & Structure**:
  * **Section 1**: Introduction, historical context, and assignment goals.
  * **Section 2**: Problem formulation, 0-1 Integer Linear Programming (MIP), and Constraint Programming (CP) models.
  * **Section 3**: SAT formulation, ALO/EO row-column placement, 5 AMO diagonal encodings with asymptotic complexity comparison (Table 1), and verification procedure.
  * **Section 4**: Computational Experiments with 3-run averaging protocol:
    * *Exp 1*: Comparison of AMO encodings (Table 3, Figure 2).
    * *Exp 2*: Comparison of CDCL SAT backends (Table 4, Figure 3).
    * *Exp 3*: Cross-paradigm benchmark: SAT vs. CP vs. MIP vs. Backtracking (Table 5, Figure 4).
    * *Discussion*: Analytical insights on clause-variable trade-offs, symmetry, and LP relaxations.
  * **Section 5**: Conclusions, Student Declaration, Data & Code Availability, and References.
* **Self-Contained & Reproducible**: Includes all template dependencies (`cas-sc.cls`, `cas-common.sty`, `cas-model2-names.bst`) and vector/PNG figures in `report/figs/`, ready for direct compilation on Overleaf or local LaTeX installations.

---

## Acknowledgments

I would like to express my sincere gratitude to **Dr. Tô Văn Khánh** (Dr. To Van Khanh) for his dedicated lectures, course guidance, problem specifications, and feedback throughout course INT3131 at VNU-UET.

