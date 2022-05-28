"""Solve Sudokus."""
from __future__ import annotations
from queue import Queue
from threading import Thread, Event, Timer
import logging
import math
import random
import copy
from solution import Solution
from sudoku_kb import SudokuKB, find_cells
from sudoku_utility import log_time


class Worker(Thread):
    """Processes function calls from an input queue and
    submits the results to an output queue.
    """

    def __init__(self, input_queue: Queue, output_queue: Queue, daemon=True):
        super().__init__()
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.daemon = daemon
        self.stop_event = Event()

    def run(self):
        while not self.input_queue.empty() and not self.stop_event.is_set():
            item = self.input_queue.get()
            result = item[0](*item[1])
            self.output_queue.put(result)


def stop_workers(workers: list[Worker]):
    """Set the stop event for all workers."""
    if __debug__:
        logging.debug('Stopping workers...')
    for worker in workers:
        worker.stop_event.set()


class SudokuSolver:
    """Solver that uses a SudokuKB to solve Sudokus."""

    def __init__(self, given: list[tuple[int, int, int]],
                 solution_filename: str,
                 solution: Solution = None,
                 nr_threads=1,
                 core_timeout=3600,
                 step_timeout=10*3600,
                 selective_threshold=100,
                 do_precalculate=True,
                 max_steps=100,
                 **kwargs) -> None:
        self.kb = SudokuKB(kwargs)
        self.initial_struct: list[tuple[int, int, int]] = given
        self.complete_struct: list[tuple[int, int, int]] = []
        self.to_calculate = None
        self.first_step_done = False
        self.solution_filename = solution_filename
        self.nr_threads = nr_threads
        self.core_timeout = core_timeout
        self.step_timeout = step_timeout
        self.selective_threshold = selective_threshold
        self.do_precalculate = do_precalculate
        self.max_steps = max_steps
        if solution:
            self.solution = solution
            last_step = self.solution.get_last_step()
            self.current_struct = last_step['current_structure']
            self.step_nr = last_step['step_nr'] + 1
        else:
            self.solution = Solution()
            self.current_struct: list[tuple[int, int, int]] = []
            self.step_nr = 1
        for key, value in kwargs.items():
            self.solution[key] = value

    def __str__(self) -> str:
        return 'Sudoku solver with rules:\n' + str(self.kb)

    def save_solution(self) -> None:
        """Save the solution object."""
        self.solution.save(self.solution_filename)


class ZebraTutorSolver(SudokuSolver):
    """Sudoku solver that makes use of unsat cores.
    Implementation of the high-level greedy sequence generating algorithm
    used in the ZebraTutor application.
    https://bartbog.github.io/zebra/
    """

    def fill_input_queue(self, to_calculate: list[dict]) -> Queue:
        """Returns a Queue filled with functions to call."""
        input_queue = Queue()
        max_nr_cores = int(
            math.ceil(self.selective_threshold / 100 * len(to_calculate)))
        if __debug__ and self.first_step_done:
            logging.debug('Submitting %d cores', max_nr_cores)
        for i, item in enumerate(to_calculate, start=1):
            if self.first_step_done \
                    and i > max_nr_cores:
                if __debug__:
                    logging.debug('Submitted %d cores.', i-1)
                break
            cell = item['cell']
            input_queue.put(
                (
                    # function
                    self.kb.get_unsat_core,
                    # args
                    [
                        cell,
                        self.current_struct,
                        self.step_nr,
                        True,
                        self.core_timeout
                    ]
                )
            )
        return input_queue

    def process_output_queue(self, output_queue, to_calculate) -> None:
        """Processes the contents of the output queue."""
        easiest_step = {
            'core': '',
            'cost': math.inf,
            'cell': (0, 0, 0)
        }
        while not output_queue.empty():
            core, cell = output_queue.get()
            cost = self.kb.get_core_cost(core)
            if __debug__:
                logging.debug(
                    'Generated core for %d-%d-%d-%d with cost %d',
                    self.step_nr, cell[0], cell[1], cell[2], cost)
            # Test for failed core
            if cost == 0:
                if __debug__:
                    logging.debug(
                        'Core %d-%d-%d-%d failed to calculate.',
                        self.step_nr, cell[0], cell[1], cell[2])
                # Use previous cost
                continue
            # Use new cost
            for other_cell in to_calculate:
                if other_cell['cell'] == cell:
                    other_cell['cost'] = cost
            if cost < easiest_step['cost']:
                easiest_step['core'] = core
                easiest_step['cost'] = cost
                easiest_step['cell'] = cell
        return easiest_step

    def add_solution_step(self, step) -> None:
        """Adds a step to the solution sequence."""
        step_nr = self.step_nr
        cell = step['cell']
        used_cells = [
            {
                'value': cell[2],
                'cells': find_cells(
                    step['core'], self.kb.get_cost_keywords()
                )
            }
        ]
        current_structure = copy.deepcopy(self.current_struct)
        self.solution.add_step(
            step_nr, cell, used_cells, current_structure
        )

    @log_time
    def next_step(self) -> None:
        """Take one step in the solving process."""
        # Sort to_calculate by cost for timeout optimization
        self.to_calculate = sorted(
            self.to_calculate, key=lambda x: x['cost'])
        input_queue = self.fill_input_queue(self.to_calculate)
        output_queue = Queue()
        workers = []
        for dummy in range(self.nr_threads):
            worker = Worker(input_queue, output_queue)
            workers.append(worker)
        for worker in workers:
            worker.start()

        # only use step timeout if properly sorted
        if self.first_step_done:
            timer = Timer(self.step_timeout, stop_workers, args=[workers])
            timer.daemon = True
            timer.start()
        for worker in workers:
            worker.join()
        if self.first_step_done:
            timer.cancel()

        easiest_step = self.process_output_queue(
            output_queue, self.to_calculate)
        # Test for no successful cores
        if easiest_step['cell'] is None:
            # pick the so far easiest one
            easiest_step['core'] = 'All failed cores, picking easiest'
            easiest_step['cell'] = self.to_calculate[0]['cell']
            easiest_step['cost'] = self.to_calculate[0]['cost']
        self.add_solution_step(easiest_step)
        self.current_struct.append(easiest_step['cell'])
        self.to_calculate = [
            item for item in self.to_calculate
            if item['cell'] != easiest_step['cell']]
        if __debug__:
            logging.debug('Step %d done, fills in %d-%d-%d-%d with cost %f.',
                          self.step_nr,
                          self.step_nr,
                          easiest_step['cell'][0],
                          easiest_step['cell'][1],
                          easiest_step['cell'][2],
                          easiest_step['cost']
                          )
        self.step_nr += 1
        self.first_step_done = True
        # Save solution after every step
        self.save_solution()

    @log_time
    def solve_stepwise(self) -> None:
        """
        Solves the Sudoku in a step-wise manner.

        Implementation of the high-level greedy sequence-generating algorithm
        as used in the ZebraTutor application, with some optimizations.
        """
        if __debug__:
            logging.debug('Starting stepwise solving process.')
            logging.debug('Nr. threads: %d', self.nr_threads)
            logging.debug(str(self.kb))
        if self.do_precalculate and not self.kb.predefined:
            self.kb.predefine(self.initial_struct)
        self.current_struct = self.initial_struct
        self.complete_struct = self.kb.get_solution(
            self.initial_struct)
        self.current_struct.sort()
        self.complete_struct.sort()
        to_calculate_list = list(set(self.complete_struct) -
                                 set(self.current_struct))
        self.to_calculate = [{'cell': cell, 'cost': math.inf}
                             for cell in to_calculate_list]
        while len(self.current_struct) != len(self.complete_struct):
            if self.step_nr > self.max_steps:
                break
            self.next_step()


class DetailedZebraTutorSolver(ZebraTutorSolver):
    """Sudoku solver that makes uses detailed ZebraTutor sub-explanations."""

    def fill_input_queue(self, to_calculate) -> Queue:
        input_queue = Queue()
        max_nr_cores = int(
            math.ceil(self.selective_threshold / 100 * len(to_calculate)))
        if __debug__ and self.first_step_done:
            logging.debug('Submitting %d cores', max_nr_cores)
        for i, item in enumerate(to_calculate, start=1):
            if self.first_step_done \
                    and i > max_nr_cores:
                if __debug__:
                    logging.debug('Submitted %d cores.', i-1)
                break
            cell = item['cell']
            for j in range(1, 10):
                if j == cell[2]:
                    continue
                input_queue.put(
                    (
                        # function
                        self.kb.get_unsat_core,
                        # args
                        [
                            (cell[0], cell[1], j),
                            self.current_struct,
                            self.step_nr,
                            False,
                            self.core_timeout
                        ]
                    )
                )
        return input_queue

    def process_output_queue(self, output_queue, to_calculate) -> None:
        """Processes the contents of the output queue."""
        core_map = {(r, c, v): None
                    for r in range(0, 9)
                    for c in range(0, 9)
                    for v in range(1, 10)}
        while not output_queue.empty():
            core, cell = output_queue.get()
            core_map[cell] = core
        core_map = {cell: core for cell, core in core_map.items()
                    if core is not None}
        single_core_map = {cell['cell']: '' for cell in to_calculate}
        for cell, core in core_map.items():
            for other_cell in single_core_map:
                if cell[0] == other_cell[0] and cell[1] == other_cell[1]:
                    single_core_map[other_cell] += core
        easiest_step = {
            'core': '',
            'cost': math.inf,
            'cell': (0, 0, 0)
        }
        for cell, core in single_core_map.items():
            cost = self.kb.get_core_cost(core)
            if __debug__:
                logging.debug(
                    'Generated core for %d-%d-%d-%d with cost %d',
                    self.step_nr, cell[0], cell[1], cell[2], cost)
            # Test for failed core
            if cost == 0:
                if __debug__:
                    logging.debug(
                        'Core %d-%d-%d-%d failed to calculate.',
                        self.step_nr, cell[0], cell[1], cell[2])
                # Use previous cost
                continue
            # Use new cost
            for other_cell in to_calculate:
                if other_cell['cell'] == cell:
                    other_cell['cost'] = cost
            if cost < easiest_step['cost']:
                easiest_step['cost'] = cost
                easiest_step['cell'] = cell
                easiest_step['core'] = core
        easiest_step['used_cells'] = []
        for cell, core in core_map.items():
            if cell[0] == easiest_step['cell'][0] and \
                    cell[1] == easiest_step['cell'][1]:
                easiest_step['used_cells'].append(
                    {
                        'value': cell[2],
                        'cells': find_cells(
                            core, self.kb.get_cost_keywords()
                        )
                    }
                )
        return easiest_step

    def add_solution_step(self, step) -> None:
        """Adds a step to the solution sequence."""
        step_nr = self.step_nr
        cell = step['cell']
        used_cells = step['used_cells']
        current_structure = copy.deepcopy(self.current_struct)
        self.solution.add_step(
            step_nr, cell, used_cells, current_structure
        )


class AlternativeSolver(ZebraTutorSolver):
    """Sudoku solver that uses minimize tasks instead of unsat cores."""

    def cost_function(self, ignored_cells) -> int:
        """Calculate the cost for ignored cells."""
        return len(ignored_cells)

    def fill_input_queue(self, to_calculate) -> Queue:
        """Returns a Queue filled with functions to call."""
        input_queue = Queue()
        for item in to_calculate:
            cell = item['cell']
            input_queue.put((
                # function
                self.kb.get_ignored_cells,
                # args
                [
                    cell,
                    self.current_struct,
                    self.step_nr
                ]
            ))
        return input_queue

    def process_output_queue(self, output_queue, to_calculate) -> None:
        """Processes the contents of the output queue."""
        easiest_step = {
            'core': '',
            'cost': math.inf,
            'cell': (0, 0, 0)
        }
        while not output_queue.empty():
            ignored_cells, cell = output_queue.get()
            cost = self.cost_function(ignored_cells)
            if __debug__:
                logging.debug(
                    'Got ignored cells for %d-%d-%d-%d with cost %d',
                    self.step_nr, cell[0], cell[1], cell[2], cost)
            # Test for failed minimize
            if cost == 0:
                if __debug__:
                    logging.debug(
                        'Ignored cells %d-%d-%d-%d failed to calculate.',
                        self.step_nr, cell[0], cell[1], cell[2])
                # Use previous cost
                continue
            # Use new cost
            for other_cell in to_calculate:
                if other_cell['cell'] == cell:
                    other_cell['cost'] = cost
            if cost < easiest_step['cost']:
                easiest_step['used_cells'] = ignored_cells
                easiest_step['cost'] = cost
                easiest_step['cell'] = cell
        return easiest_step

    def add_solution_step(self, step) -> None:
        """Adds a step to the solution sequence."""
        step_nr = self.step_nr
        cell = step['cell']
        used_cells = [
            {
                'value': cell[2],
                'cells': step['used_cells']
            }
        ]
        current_structure = copy.deepcopy(self.current_struct)
        self.solution.add_step(
            step_nr, cell, used_cells, current_structure
        )


class StrategiesSolver(ZebraTutorSolver):
    """Sudoku solver that uses simple strategies and candidate reduction."""

    def get_value(self, cell: 'tuple[int,int]') -> int:
        """Returns the value of the cell in the complete structure."""
        for other_cell in self.complete_struct:
            if cell[0] == other_cell[0] and cell[1] == other_cell[1]:
                return other_cell[2]
        return 0

    def is_empty(self, cell: 'tuple[int,int]') -> bool:
        """Returns True if the cell is empty in the current step,
        False otherwise.
        """
        for other_cell in self.current_struct:
            if cell[0] == other_cell[0] and cell[1] == other_cell[1]:
                return False
        return True

    def try_strategy(self, strategy: str) -> bool:
        """Try to fill in a cell with a certain strategy.

        Return True if succesful, False otherwise.

        Supported strategies:
        - `'naked_single'`
        - `'hidden_single'`
        """
        if strategy == 'naked_single':
            cells_to_fill_in = self.kb.get_naked_singles(
                self.current_struct)
        elif strategy == 'hidden_single':
            cells_to_fill_in = self.kb.get_hidden_singles(
                self.current_struct)
        else:
            raise Exception(f'Did not recognize strategy, got: {strategy}')
        if len(cells_to_fill_in) == 0:
            return False
        for row, column in cells_to_fill_in:
            input_queue = Queue()
            value = self.get_value((row, column))
            cell = (row, column, value)
            for i in range(1, 10):
                if i == cell[2]:
                    continue
                input_queue.put(
                    (
                        # function
                        self.kb.get_unsat_core,
                        # args
                        [
                            (cell[0], cell[1], i),
                            self.current_struct,
                            self.step_nr,
                            False,
                            self.core_timeout
                        ]
                    )
                )
            output_queue = Queue()
            workers = []
            for dummy in range(self.nr_threads):
                worker = Worker(input_queue, output_queue)
                workers.append(worker)
            for worker in workers:
                worker.start()
            for worker in workers:
                worker.join()
            used_cells = []
            while not output_queue.empty():
                item = output_queue.get()
                core = item[0]
                value = item[1][2]
                used_cells.append(
                    {
                        'value': value,
                        'cells': find_cells(
                            core, self.kb.get_cost_keywords())
                    }
                )
            step = {
                'cell': cell,
                'used_cells': used_cells
            }
            self.add_solution_step(step)
            self.current_struct.append(cell)
            self.to_calculate = [
                item for item in self.to_calculate if item['cell'] != cell]
            if __debug__:
                logging.debug(
                    'Filled in %d-%d-%d-%d with strategy %s.',
                    self.step_nr,
                    cell[0],
                    cell[1],
                    cell[2],
                    strategy)
            self.step_nr += 1
            # ! Only fill in one for hidden singles,
            # ! even if more were found,
            # ! because now there might be new naked singles which are easier!
            if strategy in ['hidden_single']:
                break
        return True

    def fill_random(self) -> None:
        """Fill in a random cell."""
        cell = random.choice(self.to_calculate)['cell']
        step = {
            'cell': cell,
            'used_cells': [
                {"value": x, "cells": []} for x in range(1, 10) if x != cell[2]
            ]
        }
        self.add_solution_step(step)
        self.current_struct.append(cell)
        self.to_calculate = [
            item for item in self.to_calculate if item['cell'] != cell]
        if __debug__:
            logging.debug('Filled in %d-%d-%d-%d at random.',
                          self.step_nr, cell[0], cell[1], cell[2])
        self.step_nr += 1

    def add_solution_step(self, step) -> None:
        """Adds a step to the solution sequence."""
        step_nr = self.step_nr
        cell = step['cell']
        used_cells = step['used_cells']
        current_structure = copy.deepcopy(self.current_struct)
        self.solution.add_step(
            step_nr, cell, used_cells, current_structure
        )

    @ log_time
    def next_step(self) -> None:
        """Take one step in the solving process."""
        if self.try_strategy('naked_single'):
            pass
        elif self.try_strategy('hidden_single'):
            pass
        else:
            self.fill_random()
        self.save_solution()


class HybridSolver(StrategiesSolver, ZebraTutorSolver):
    """Hybrid of Strategies and ZebraTutor.

    Uses ZebraTutor method when no strategies could be detected.
    """

    def do_unsat_cores(self) -> None:
        """Use unsat cores to do this step."""
        ZebraTutorSolver.next_step(self)

    @ log_time
    def next_step(self) -> None:
        """Take one step in the solving process."""
        if self.try_strategy('naked_single'):
            pass
        elif self.try_strategy('hidden_single'):
            pass
        else:
            self.do_unsat_cores()
        self.save_solution()
