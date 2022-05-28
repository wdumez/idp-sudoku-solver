"""Run the explainer."""
import argparse
from explainer import generate_explanation
from solution import Solution

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Run the Sudoku explainer.'
    )
    parser.add_argument(
        'solution',
        type=str,
        help='filename of the JSON solution'
    )
    parser.add_argument(
        'explanations',
        type=str,
        help='folder in which to save the explanation'
    )
    args = parser.parse_args()
    solution = Solution.from_file(args.solution)
    generate_explanation(solution, args.explanations)
