"""Run the solver."""
import argparse
import logging
from solution import Solution
from sudoku_solver import ZebraTutorSolver, DetailedZebraTutorSolver, \
    AlternativeSolver, StrategiesSolver, HybridSolver
from sudoku_parser import parse_sudoku_file, \
    parse_thermo_file, parse_killer_file


def main():
    """Main."""
    parser = argparse.ArgumentParser(
        description='Run the Sudoku solver.'
    )
    # Required
    parser.add_argument(
        'method',
        type=str,
        choices=['zebratutor', 'detailed',
                 'strategies', 'hybrid', 'alternative'],
        help='which method the solver should use'
    )
    parser.add_argument(
        'sudoku',
        type=str,
        help='filename containing the Sudoku'
    )
    parser.add_argument(
        'solution',
        type=str,
        help='filename of the generated JSON solution'
    )
    parser.add_argument(
        'logfile',
        type=str,
        help='filename of the logfile'
    )
    # Positional
    parser.add_argument(
        '--threads',
        type=int,
        default=1,
        help='number of threads for calculating unsat cores'
    )
    parser.add_argument(
        '--core-timeout',
        type=int,
        default=3600,
        help='timeout in seconds for unsat core calls'
    )
    parser.add_argument(
        '--step-timeout',
        type=int,
        default=10*3600,
        help='timeout in seconds for solving steps'
    )
    parser.add_argument(
        '--selective-threshold',
        type=float,
        default=100,
        help='percentage of cores to calculate each step (0 - 100)'
    )
    parser.add_argument(
        '--from-partial',
        type=str,
        help='start from a partial JSON solution'
    )
    parser.add_argument(
        '--no-predefine',
        action='store_true',
        help='do not use predicate predefining (not recommended)'
    )
    parser.add_argument(
        '--max-steps',
        type=int,
        help='maximum number of steps (default: all)'
    )

    # Variant additions
    parser.add_argument(
        '--thermo',
        type=str,
        help='filename containing the thermometers in IDP format'
    )
    parser.add_argument(
        '--killer',
        type=str,
        help='filename containing the killer cages and cage sums in IDP format'
    )
    # ! Add your own variants here

    # Parse
    args = parser.parse_args()
    logging.basicConfig(
        filename=args.logfile, filemode='w',
        # encoding='utf-8',
        level=logging.DEBUG,
        format='[%(asctime)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    given = parse_sudoku_file(args.sudoku)
    solution_filename = args.solution
    solution = None
    if args.from_partial:
        solution = Solution.from_file(args.from_partial)
    selective_threshold = args.selective_threshold
    if not 0 <= selective_threshold <= 100:
        raise ValueError(
            f'Selective threshold is invalid, got: {selective_threshold}')
    if args.no_predefine:
        do_predefine = False
    else:
        do_predefine = True
    if args.max_steps:
        max_steps = args.max_steps
    else:
        max_steps = 100

    # Variant parse
    kwargs = {}
    if args.thermo:
        thermo_cells = parse_thermo_file(args.thermo)
        kwargs['thermo_cells'] = thermo_cells
    if args.killer:
        killer_cages, killer_cage_sums = parse_killer_file(args.killer)
        kwargs['killer_cages'] = killer_cages
        kwargs['killer_cage_sums'] = killer_cage_sums
    # ! Add your own variants here
    solver_args = {
        'given': given,
        'solution_filename': solution_filename,
        'solution': solution,
        'nr_threads': args.threads,
        'core_timeout': args.core_timeout,
        'step_timeout': args.step_timeout,
        'selective_threshold': selective_threshold,
        'do_precalculate': do_predefine,
        'max_steps': max_steps,
        **kwargs
    }

    # Run the solver
    if args.method == 'zebratutor':
        solver = ZebraTutorSolver(**solver_args)
    if args.method == 'detailed':
        solver = DetailedZebraTutorSolver(**solver_args)
    if args.method == 'strategies':
        solver = StrategiesSolver(**solver_args)
    if args.method == 'hybrid':
        solver = HybridSolver(**solver_args)
    if args.method == 'alternative':
        solver = AlternativeSolver(**solver_args)

    # Add rules to the knowledge base
    solver.kb.add_rule('normal')
    if args.thermo:
        solver.kb.add_rule('thermo')
    if args.killer:
        solver.kb.add_rule('killer')

    # Generate a stepwise explanation
    solver.solve_stepwise()

    # Save the solution
    solver.save_solution()


if __name__ == '__main__':
    main()
