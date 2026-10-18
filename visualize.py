"""
Visualize N-Queens solution on a chessboard.
Generates publication-quality board images for the report.
"""

import os
import sys

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    import matplotlib
    matplotlib.use('Agg')
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results')


def draw_board(n, queens, title=None, save_path=None):
    if not HAS_MPL:
        print("matplotlib not available")
        return

    fig, ax = plt.subplots(1, 1, figsize=(max(6, n * 0.6), max(6, n * 0.6)))

    queen_set = set(queens) if queens else set()

    for i in range(n):
        for j in range(n):
            color = '#F0D9B5' if (i + j) % 2 == 0 else '#B58863'
            rect = patches.Rectangle((j, n - 1 - i), 1, 1,
                                     linewidth=0.5,
                                     edgecolor='#666',
                                     facecolor=color)
            ax.add_patch(rect)

            if (i, j) in queen_set:
                ax.text(j + 0.5, n - 1 - i + 0.5, '♛',
                        fontsize=max(8, min(36, 300 // n)),
                        ha='center', va='center',
                        color='#1a1a2e', fontweight='bold')

    if n <= 32:
        ax.set_xticks([i + 0.5 for i in range(n)])
        ax.set_xticklabels([str(i) for i in range(n)], fontsize=max(6, 10 - n // 8))
        ax.set_yticks([i + 0.5 for i in range(n)])
        ax.set_yticklabels([str(n - 1 - i) for i in range(n)], fontsize=max(6, 10 - n // 8))
    else:
        ax.set_xticks([])
        ax.set_yticks([])

    ax.set_xlim(0, n)
    ax.set_ylim(0, n)
    ax.set_aspect('equal')

    if title:
        ax.set_title(title, fontsize=14, fontweight='bold', pad=10)
    else:
        ax.set_title(f'{n}-Queens Solution', fontsize=14, fontweight='bold', pad=10)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    else:
        plt.show()

    plt.close()


def draw_attack_lines(n, queens, highlight_queen=None, save_path=None):
    if not HAS_MPL:
        return

    fig, ax = plt.subplots(1, 1, figsize=(max(6, n * 0.8), max(6, n * 0.8)))

    queen_set = set(queens) if queens else set()

    for i in range(n):
        for j in range(n):
            color = '#F0D9B5' if (i + j) % 2 == 0 else '#B58863'
            rect = patches.Rectangle((j, n - 1 - i), 1, 1,
                                     linewidth=0.5,
                                     edgecolor='#666',
                                     facecolor=color)
            ax.add_patch(rect)

    if highlight_queen and highlight_queen in queen_set:
        qi, qj = highlight_queen
        for i in range(n):
            for j in range(n):
                if (i, j) == (qi, qj):
                    continue
                if i == qi or j == qj or abs(i - qi) == abs(j - qj):
                    rect = patches.Rectangle((j, n - 1 - i), 1, 1,
                                             linewidth=0, alpha=0.35,
                                             facecolor='#e74c3c')
                    ax.add_patch(rect)

    for (i, j) in queen_set:
        color = '#e74c3c' if (i, j) == highlight_queen else '#1a1a2e'
        ax.text(j + 0.5, n - 1 - i + 0.5, '♛',
                fontsize=max(8, min(36, 300 // n)),
                ha='center', va='center',
                color=color, fontweight='bold')

    ax.set_xlim(0, n)
    ax.set_ylim(0, n)
    ax.set_aspect('equal')
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(f'{n}-Queens: Attack Lines', fontsize=14, fontweight='bold')

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    plt.close()


def generate_report_figures():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    sys.path.insert(0, os.path.dirname(__file__))
    from nqueens_sat import solve_nqueens_sat

    res4 = solve_nqueens_sat(4)
    draw_board(4, res4['solution'],
               title='4-Queens Solution (SAT)',
               save_path=os.path.join(RESULTS_DIR, 'board_4queens.png'))

    res8 = solve_nqueens_sat(8)
    draw_board(8, res8['solution'],
               title='8-Queens Solution (SAT)',
               save_path=os.path.join(RESULTS_DIR, 'board_8queens.png'))

    if res8['solution']:
        draw_attack_lines(8, res8['solution'],
                          highlight_queen=res8['solution'][0],
                          save_path=os.path.join(RESULTS_DIR, 'board_8queens_attacks.png'))

    res16 = solve_nqueens_sat(16)
    draw_board(16, res16['solution'],
               title='16-Queens Solution (SAT)',
               save_path=os.path.join(RESULTS_DIR, 'board_16queens.png'))

    res64 = solve_nqueens_sat(64)
    draw_board(64, res64['solution'],
               title='64-Queens Solution (SAT)',
               save_path=os.path.join(RESULTS_DIR, 'board_64queens.png'))

    print("\n✅ All report figures generated!")


if __name__ == '__main__':
    generate_report_figures()
