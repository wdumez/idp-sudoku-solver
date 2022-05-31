"""Knowledge base for Sudokus."""
from __future__ import annotations
import time
from copy import copy
from pathlib import Path
import logging
import re
from pyidp3.typedIDP import IDP


def find_cells(core: str, keywords: list[str]) -> list[tuple[int, int]]:
    """Find all different cells used in the core based on the keywords.

    Keywords are names of functions or predicates whose arguments
    must be pairs of cells, e.g. `sameRow(Row,Col,Row,Col)`

    A single extra argument will be ignored,
    e.g. `cage(Row,Col,CageID)` will ignore CageID

    `gridValue` is always used.
    """
    keywords = copy(keywords)
    keywords.append('gridValue')
    used_cells = []
    for keyword in keywords:
        matches = re.findall(rf'{keyword}\([\,,\d]+\)', core)
        for match in matches:
            numbers = match.lstrip(f'{keyword}(').rstrip(')').split(',')
            numbers = [int(x) for x in numbers]
            # assume cells come in pairs
            for i in range(0, len(numbers)-1, 2):
                row = numbers[i]
                col = numbers[i+1]
                if (row, col) not in used_cells:
                    used_cells.append((row, col))
    return used_cells


def cost_function(core: str, keywords: list[str]) -> int:
    """Calculate the cost for the core.

    `keywords` holds keywords with which to calculate the cost
    """
    number_cells = len(find_cells(core, keywords))
    print(f'N: {number_cells}')
    cost = number_cells
    for keyword in keywords:
        nr_of_keywords = len(re.findall(keyword, core))
        print(f'{keyword}: {nr_of_keywords} + 1')
        cost *= nr_of_keywords + 1
    return cost


class SudokuKB:
    """Knowledge base for performing IDP operations related to Sudokus.

    The following rules are currently supported:
    - Thermo Sudoku
    - Killer Sudoku
    """

    def __init__(self, rule_constructs: dict = None) -> None:
        if rule_constructs is None:
            self.rule_constructs = {}
        else:
            self.rule_constructs = rule_constructs
        self.idp_path = str(Path.home()) + \
            '/idp/usr/local/bin/idp'
        self.rules: dict[str, bool] = {
            'normal': False,
            'thermo': False,
            'killer': False
            # etc.
        }
        self.rule_functions: dict[str, object] = {
            'normal': self.add_normal_idp,
            'thermo': self.add_thermo_idp,
            'killer': self.add_killer_idp
        }
        self.rule_keywords: dict[str, list] = {
            'normal': ['sameRow', 'sameCol', 'sameBox'],
            'thermo': ['thermo'],
            'killer': ['cage']
        }
        # Some predicates/functions can be precalculated to save
        # time during unsat core calculation.
        self.predefined: bool = False
        self.precalc_structures: dict[str, list] = {
            'sameRow': None,
            'sameCol': None,
            'sameBox': None
        }

    def __str__(self) -> str:
        txt = 'SudokuKB rules: '
        for rule, state in self.rules.items():
            if state:
                txt += f'{rule}, '
        txt = txt.rstrip(', ')
        return txt

    def add_rule(self, rule: str) -> None:
        """Add a rule to the Sudoku.

        `rule` must be a valid identifier.
        """
        if rule in self.rules:
            self.rules[rule] = True
        else:
            raise UnsupportedRule(f'Rule \'{rule}\' is not supported.')

    def get_cost_keywords(self) -> list[str]:
        """Returns all keywords for cost calculation
        based on the added rules.
        """
        res = []
        for rule, keywords in self.rule_keywords.items():
            if self.rules.get(rule):
                res.extend(keywords)
        return res

    def get_idp(self) -> IDP:
        """Returns a new empty IDP object."""
        idp = IDP(self.idp_path)
        idp.xsb = 'true'
        return idp

    def model_expand(self, idp: IDP, keyword: str) -> list:
        """Model expand the idp object and return the values of keyword."""
        model = idp.model_expand()[0]
        values = model[keyword]
        # If there are no values, IDP returns an empty string as only item
        if values[0] == '':
            return []
        return values

    def minimize(self, idp: IDP, term: str, keyword: str) -> list:
        """Minimize the idp object with the term and
        return the values of keyword."""
        model = idp.minimize(term)[0]
        values = model[keyword]
        # If there are no values, IDP returns an empty string as only item
        if values[0] == '':
            return []
        return values

    def printunsatcore(self, idp: IDP, timeout: int = 0) -> str:
        """Call printunsatcore on the IDP object and return the unsat core.
        The call will end early after `timeout` seconds.
        """
        if __debug__:
            print('Calling unsat script...')
        core = idp.printunsatcore(timeout)
        if __debug__:
            print('Done calling unsat script.')
        return core

    def add_required_idp(self, idp, given) -> IDP:
        """Add IDP code required for any Sudoku."""
        idp.Type(name='Row', enumeration=(0, 8), isa='nat')
        idp.Type(name='Col', enumeration=(0, 8), isa='nat')
        idp.Type(name='Value', enumeration=(1, 9), isa='nat')
        idp.Predicate('sameRow(Row,Col,Row,Col)',
                      self.precalc_structures.get('sameRow'))
        idp.Predicate('sameCol(Row,Col,Row,Col)',
                      self.precalc_structures.get('sameCol'))
        idp.Predicate('sameBox(Row,Col,Row,Col)',
                      self.precalc_structures.get('sameBox'))
        # Specify only certainly true tuples.
        idp.Predicate('gridValue(Row,Col,Value)',
                      enumeration=given, ct=True)
        idp.Define(
            '!r1,c1,r2,c2 : sameRow(r1,c1,r2,c2) <- r1 = r2 & c1 ~= c2.',
            True
        )
        idp.Define(
            '!r1, c1, r2, c2: sameCol(r1, c1, r2, c2) <- r1 ~=r2 & c1=c2.',
            True
        )
        idp.Define(
            '!r1,c1,r2,c2 : sameBox(r1,c1,r2,c2) <-' +
            '( r1 - r1 % 3 = r2 - r2 % 3 ) &' +
            '( c1 - c1 % 3 = c2 - c2 % 3 ) &' +
            '( r1 ~= r2 | c1 ~= c2 ).',
            True
        )
        idp.Constraint('!r,c : ?v : gridValue(r,c,v)', True)
        return idp

    def add_normal_idp(self, idp: IDP) -> IDP:
        """Add IDP code for normal Sudoku rules."""
        idp.Constraint(
            '!r1,c1,v1,r2,c2,v2 : sameRow(r1,c1,r2,c2) &' +
            'gridValue(r1,c1,v1) &' +
            'gridValue(r2,c2,v2) => v1 ~= v2.',
            True
        )
        idp.Constraint(
            '!r1,c1,v1,r2,c2,v2 : sameCol(r1,c1,r2,c2) &' +
            'gridValue(r1,c1,v1) &' +
            'gridValue(r2,c2,v2) => v1 ~= v2.',
            True
        )
        idp.Constraint(
            '!r1,c1,v1,r2,c2,v2 : sameBox(r1,c1,r2,c2) &' +
            'gridValue(r1,c1,v1) &' +
            'gridValue(r2,c2,v2) => v1 ~= v2.',
            True
        )
        return idp

    def add_thermo_idp(self, idp: IDP) -> IDP:
        """Add IDP code for Thermo Sudoku rules."""
        thermo_cells = self.rule_constructs.get('thermo_cells')
        idp.Predicate(
            'thermo(Row,Col,Row,Col)', enumeration=thermo_cells)
        idp.Constraint(
            '!r1,c1,v1,r2,c2,v2 : thermo(r1,c1,r2,c2) &' +
            'gridValue(r1,c1,v1) &' +
            'gridValue(r2,c2,v2) => v1 < v2.',
            True
        )
        return idp

    def add_killer_idp(self, idp) -> IDP:
        """Add IDP code for Killer Sudoku rules."""
        killer_cages = self.rule_constructs.get('killer_cages')
        killer_cage_sums = self.rule_constructs.get('killer_cage_sums')
        max_cage_id = max(killer_cage_sums.keys())
        idp.Type(name='MaxCageNr', enumeration=(1, 100),  isa='nat')
        idp.Type(name='CageID', enumeration=(1, max_cage_id), isa='nat')
        idp.Predicate('cage(Row,Col,CageID)', enumeration=killer_cages)
        idp.Function('cageSum(CageID) : MaxCageNr',
                     enumeration=killer_cage_sums)
        idp.Constraint(
            '!id : sum{r,c,v : cage(r,c,id) & gridValue(r,c,v) : v}' +
            '= cageSum(id).',
            True
        )
        return idp

    def add_active_idp(self, idp) -> IDP:
        """Add IDP code for all active rules."""
        for rule, is_active in self.rules.items():
            if is_active:
                idp = self.rule_functions.get(rule)(idp)
        return idp

    def get_solution(self, given: list[tuple[int, int, int]]) \
            -> list[tuple[int, int, int]]:
        """Get the solution to the Sudoku."""
        idp = self.get_idp()
        idp = self.add_required_idp(idp, given)
        idp = self.add_active_idp(idp)
        solution = self.model_expand(idp, 'gridValue')
        return solution

    def get_unsat_core(
        self, cell: tuple[int, int, int], current_structure,
        step: int, negate=True, timeout=3600) \
            -> tuple[str, tuple[int, int, int]]:
        """Returns the unsat core for that cell."""
        if __debug__:
            logging.debug('Getting unsat core for %d-%d-%d-%d.',
                          step, cell[0], cell[1], cell[2])
            start_time = time.time()
        idp = self.get_idp()
        idp = self.add_required_idp(idp, current_structure)
        idp = self.add_active_idp(idp)
        row, col, value = cell
        if negate:
            idp.Constraint(f'~gridValue({row},{col},{value}).', True)
        else:
            idp.Constraint(f'gridValue({row},{col},{value}).', True)
        # Starting calculation. This can take a while!
        core = self.printunsatcore(idp, timeout)
        # Calculation is finished.
        if __debug__:
            end_time = time.time()
            delta_time = end_time - start_time
            logging.debug('Core %d-%d-%d-%d took %.3f seconds.',
                          step, cell[0], cell[1], cell[2], delta_time)
        return core, cell

    def get_core_cost(self, core: str) -> int:
        """Get the cost of the unsat core core."""
        return cost_function(core, self.get_cost_keywords())

    def get_ignored_cells(
        self, cell, current_structure, step: int) \
            -> tuple[list[tuple[int, int, int]], tuple[int, int, int]]:
        """Return ignored cells for that cell using a minimize task."""
        if __debug__:
            start_time = time.time()
            logging.debug('Getting ignored cells...')
        row, col, value = cell
        idp = IDP(self.idp_path)
        idp.xsb = 'true'
        idp.Type(name='Row', enumeration=(0, 8), isa='nat')
        idp.Type(name='Col', enumeration=(0, 8), isa='nat')
        idp.Type(name='Value', enumeration=(1, 9), isa='nat')
        idp.Predicate('sameRow(Row,Col,Row,Col)',
                      self.precalc_structures.get('sameRow'))
        idp.Predicate('sameCol(Row,Col,Row,Col)',
                      self.precalc_structures.get('sameCol'))
        idp.Predicate('sameBox(Row,Col,Row,Col)',
                      self.precalc_structures.get('sameBox'))
        # Specify only certainly true tuples.
        idp.Predicate('gridValue(Row,Col,Value)',
                      enumeration=current_structure, ct=True)
        idp.Define(
            '!r1,c1,r2,c2 : sameRow(r1,c1,r2,c2) <- r1 = r2 & c1 ~= c2.',
            True
        )
        idp.Define(
            '!r1, c1, r2, c2: sameCol(r1, c1, r2, c2) <- r1 ~=r2 & c1=c2.',
            True
        )
        idp.Define(
            '!r1,c1,r2,c2 : sameBox(r1,c1,r2,c2) <-' +
            '( r1 - r1 % 3 = r2 - r2 % 3 ) &' +
            '( c1 - c1 % 3 = c2 - c2 % 3 ) &' +
            '( r1 ~= r2 | c1 ~= c2 ).',
            True
        )
        # The following line was changed dramatically
        idp.Constraint('!r[Row],c[Col] : #{v : gridValue(r,c,v)} =< 1 |' +
                       f'(r = {row} & c = {col}).', True)
        if self.rules['normal']:
            idp.Constraint(
                '!r1,c1,v1,r2,c2,v2 : ~( ignored(r1,c1) & ignored(r2,c2) ) &' +
                'sameRow(r1,c1,r2,c2) &' +
                'gridValue(r1,c1,v1) &' +
                'gridValue(r2,c2,v2) => v1 ~= v2.',
                True
            )
            idp.Constraint(
                '!r1,c1,v1,r2,c2,v2 : ~( ignored(r1,c1) & ignored(r2,c2) ) &' +
                'sameCol(r1,c1,r2,c2) &' +
                'gridValue(r1,c1,v1) &' +
                'gridValue(r2,c2,v2) => v1 ~= v2.',
                True
            )
            idp.Constraint(
                '!r1,c1,v1,r2,c2,v2 : ~( ignored(r1,c1) & ignored(r2,c2) ) &' +
                'sameBox(r1,c1,r2,c2) &' +
                'gridValue(r1,c1,v1) &' +
                'gridValue(r2,c2,v2) => v1 ~= v2.',
                True
            )
        if self.rules['thermo']:
            thermo_cells = self.rule_constructs.get('thermo_cells')
            idp.Predicate(
                'thermo(Row,Col,Row,Col)', enumeration=thermo_cells)
            idp.Constraint(
                '!r1,c1,v1,r2,c2,v2 : ~( ignored(r1,c1) & ignored(r2,c2) ) &' +
                'thermo(r1,c1,r2,c2) &' +
                'gridValue(r1,c1,v1) &' +
                'gridValue(r2,c2,v2) => v1 < v2.',
                True
            )
        if self.rules['killer']:
            killer_cages = self.rule_constructs.get('killer_cages')
            killer_cage_sums = self.rule_constructs.get('killer_cage_sums')
            max_cage_id = max(killer_cage_sums.keys())
            idp.Type(name='MaxCageNr', enumeration=(1, 100),  isa='nat')
            idp.Type(name='CageID', enumeration=(1, max_cage_id), isa='nat')
            idp.Predicate('cage(Row,Col,CageID)', enumeration=killer_cages)
            idp.Function('cageSum(CageID) : MaxCageNr',
                         enumeration=killer_cage_sums)
            idp.Constraint(
                '!id : (?r1,c1 : cage(r1,c1,id) & ignored(r1,c1)) <=>' +
                '~(sum{r2,c2,v2 : cage(r2,c2,id) & gridValue(r2,c2,v2) : v2}' +
                '= cageSum(id)).',
                True
            )
        # 'Ignored' rules
        # Look for naked single
        for i in range(1, 10):
            if i == value:
                continue
            idp.Constraint(f'gridValue({row},{col},{i}).', True)
        # Look for hidden single
        for r2, c2 in self.get_empty_related_cells(cell, current_structure):
            idp.Constraint(f'gridValue({r2},{c2},{value}).', True)

        idp.Predicate('ignored(Row,Col)')
        term = '#{r,c : ignored(r,c)}'
        ignored_cells = self.minimize(idp, term, 'ignored')
        if __debug__:
            end_time = time.time()
            delta_time = end_time - start_time
            logging.debug('Ignored cells %d-%d-%d-%d took %.3f seconds.',
                          step, cell[0], cell[1], cell[2], delta_time)
        return ignored_cells, cell

    def get_naked_singles(
        self, current_structure: list[tuple[int, int, int]]) \
            -> list:
        """Detect and return a list of naked single cells (row,col)."""
        return self.get_candidates('nakedSingle', current_structure)

    def get_hidden_singles(
        self, current_structure: list[tuple[int, int, int]]) \
            -> list:
        """Detect and return a list of hidden single cells (row,col)."""
        return self.get_candidates('hiddenSingle', current_structure)

    def get_denied_candidates(
        self, current_structure: list[tuple[int, int, int]]) \
            -> list:
        """Return all denied candidates for the current structure."""
        return self.get_candidates('denyCandidate', current_structure)

    def get_empty_related_cells(self, cell, current_structure) -> list:
        """Return all empty directly related cells."""
        dir_rel = self.get_candidates('directRelation', current_structure)
        filled_cells = self.get_candidates('hasValue', current_structure)
        related_cells = []
        for item in dir_rel:
            if (item[0], item[1]) == (cell[0], cell[1]):
                related_cells.append((item[2], item[3]))
            if (item[2], item[3]) == (cell[0], cell[1]):
                related_cells.append((item[0], item[1]))
        # remove duplicates
        related_cells = list(dict.fromkeys(related_cells))
        empty_cells = [x for x in related_cells if x not in filled_cells]
        return empty_cells

    def get_candidates(
        self, keyword, current_structure: list[tuple[int, int, int]]) \
            -> list:
        """Detect and return values matching the keyword. 
        Applies candidate reduction and finds strategies.
        """
        idp = IDP(self.idp_path)
        idp.xsb = 'true'
        idp.Type(name='Row', enumeration=(0, 8), isa='nat')
        idp.Type(name='Col', enumeration=(0, 8), isa='nat')
        idp.Type(name='Value', enumeration=(1, 9), isa='nat')
        idp.Predicate('sameRow(Row,Col,Row,Col)',
                      self.precalc_structures.get('sameRow'))
        idp.Predicate('sameCol(Row,Col,Row,Col)',
                      self.precalc_structures.get('sameCol'))
        idp.Predicate('sameBox(Row,Col,Row,Col)',
                      self.precalc_structures.get('sameBox'))
        # No <ct> this time
        idp.Predicate('gridValue(Row,Col,Value)',
                      enumeration=current_structure)
        idp.Define(
            '!r1,c1,r2,c2 : sameRow(r1,c1,r2,c2) <- r1 = r2 & c1 ~= c2.',
            True
        )
        idp.Define(
            '!r1, c1, r2, c2: sameCol(r1, c1, r2, c2) <- r1 ~=r2 & c1=c2.',
            True
        )
        idp.Define(
            '!r1,c1,r2,c2 : sameBox(r1,c1,r2,c2) <-' +
            '( r1 - r1 % 3 = r2 - r2 % 3 ) &' +
            '( c1 - c1 % 3 = c2 - c2 % 3 ) &' +
            '( r1 ~= r2 | c1 ~= c2 ).',
            True
        )
        # Now =< instead of =
        idp.Constraint('!r,c : #{v : gridValue(r,c,v)} =< 1.', True)
        direct_relation_def = (
            '!r1,c1,r2,c2: directRelation(r1,c1,r2,c2) <-' +
            'sameRow(r1,c1,r2,c2).' +
            '!r1,c1,r2,c2: directRelation(r1,c1,r2,c2) <-' +
            'sameCol(r1,c1,r2,c2).' +
            '!r1,c1,r2,c2: directRelation(r1,c1,r2,c2) <-' +
            'sameBox(r1,c1,r2,c2).'
        )
        candidate_constraint = (
            '!r1,c1,v : candidate(r1,c1,v) <=>' +
            '(~hasValue(r1,c1))' +
            '& (?=0 r2,c2 : gridValue(r2,c2,v)' +
            '& directRelation(r1,c1,r2,c2))'
        )
        if self.rules['normal']:
            idp.Constraint(
                '!r1,c1,v1,r2,c2,v2 : sameRow(r1,c1,r2,c2) &' +
                'gridValue(r1,c1,v1) &' +
                'gridValue(r2,c2,v2) => v1 ~= v2.',
                True
            )
            idp.Constraint(
                '!r1,c1,v1,r2,c2,v2 : sameCol(r1,c1,r2,c2) &' +
                'gridValue(r1,c1,v1) &' +
                'gridValue(r2,c2,v2) => v1 ~= v2.',
                True
            )
            idp.Constraint(
                '!r1,c1,v1,r2,c2,v2 : sameBox(r1,c1,r2,c2) &' +
                'gridValue(r1,c1,v1) &' +
                'gridValue(r2,c2,v2) => v1 ~= v2.',
                True
            )
        if self.rules['thermo']:
            thermo_cells = self.rule_constructs.get('thermo_cells')
            idp.Predicate(
                'thermo(Row,Col,Row,Col)', enumeration=thermo_cells)
            idp.Predicate('sameThermo(Row,Col,Row,Col)')
            idp.Predicate('afterInThermo(Row,Col,Row,Col)')
            idp.Predicate('beforeInThermo(Row,Col,Row,Col)')
            idp.Constraint(
                '!r1,c1,v1,r2,c2,v2 : thermo(r1,c1,r2,c2) &' +
                'gridValue(r1,c1,v1) &' +
                'gridValue(r2,c2,v2) => v1 < v2.',
                True
            )
            idp.Define(
                '!r1,c1,r2,c2 : sameThermo(r1,c1,r2,c2) <-' +
                'thermo(r1,c1,r2,c2).' +
                '!r1,c1,r2,c2 : sameThermo(r1,c1,r2,c2) <-' +
                '?r3,c3 : sameThermo(r1,c1,r3,c3) & sameThermo(r3,c3,r2,c2)' +
                '& (r1 ~= r2 | c1 ~= c2).'
                '!r1,c1,r2,c2 : sameThermo(r1,c1,r2,c2) <-' +
                'sameThermo(r2,c2,r1,c1).',
                True
            )
            idp.Define(
                '!r1,c1,r2,c2 : beforeInThermo(r1,c1,r2,c2) <-' +
                'thermo(r1,c1,r2,c2).' +
                '!r1,c1,r2,c2,r3,c3 : beforeInThermo(r1,c1,r2,c2) <-' +
                'beforeInThermo(r1,c1,r3,c3) & beforeInThermo(r3,c3,r2,c2).',
                True
            )
            idp.Constraint(
                '!r1,c1,r2,c2 : afterInThermo(r1,c1,r2,c2) <=>' +
                'sameThermo(r1,c1,r2,c2) &' +
                '~beforeInThermo(r1,c1,r2,c2) & ~(r1 = r2 & c1 = c2).',
                True
            )
            direct_relation_def += (
                '!r1,c1,r2,c2 : directRelation(r1,c1,r2,c2) <-' +
                'sameThermo(r1,c1,r2,c2).'
            )
            candidate_constraint += (
                '& (#{r2,c2 : afterInThermo(r2,c2,r1,c1)} + v < 10)' +
                '& (#{r2,c2 : beforeInThermo(r2,c2,r1,c1)} - v < 0 )' +
                '& (?=0 r2,c2,v2 : gridValue(r2,c2,v2) &' +
                'beforeInThermo(r2,c2,r1,c1) & v < v2)' +
                '& (?=0 r2,c2,v2 : gridValue(r2,c2,v2) &' +
                'afterInThermo(r2,c2,r1,c1) & v > v2)'
            )
        if self.rules['killer']:
            killer_cages = self.rule_constructs.get('killer_cages')
            killer_cage_sums = self.rule_constructs.get('killer_cage_sums')
            max_cage_id = max(killer_cage_sums.keys())
            idp.Type(name='MaxCageNr', enumeration=(1, 100),  isa='nat')
            idp.Type(name='CageID', enumeration=(1, max_cage_id), isa='nat')
            idp.Predicate('cage(Row,Col,CageID)', enumeration=killer_cages)
            idp.Function('cageSum(CageID) : MaxCageNr',
                         enumeration=killer_cage_sums)
            candidate_constraint += (
                '& (!id : cage(r1,c1,id) => v =< cageSum(id))'
            )
        # Specific rules
        idp.Predicate('directRelation(Row,Col,Row,Col)')
        idp.Predicate('hasValue(Row,Col)')
        idp.Predicate('candidate(Row,Col,Value)')
        idp.Predicate('denyCandidate(Row,Col,Value,Row,Col)')
        idp.Predicate('nakedSingle(Row,Col)')
        idp.Predicate('hiddenSingle(Row,Col)')
        idp.Constraint(
            '!r,c : hasValue(r,c) <=> #{v : gridValue(r,c,v)} = 1.',
            True
        )
        idp.Define(
            '!r1,c1 : nakedSingle(r1,c1) <- ?=1 v : candidate(r1,c1,v).',
            True
        )
        idp.Define(
            '!r1,c1 : hiddenSingle(r1,c1) <-' +
            '?=1 v : candidate(r1,c1,v) & (!r2,c2 : sameRow(r1,c1,r2,c2)' +
            '=> ~candidate(r2,c2,v)).'
            '!r1,c1 : hiddenSingle(r1,c1) <-' +
            '?=1 v : candidate(r1,c1,v) & (!r2,c2 : sameCol(r1,c1,r2,c2)' +
            '=> ~candidate(r2,c2,v)).'
            '!r1,c1 : hiddenSingle(r1,c1) <-' +
            '?=1 v : candidate(r1,c1,v) & (!r2,c2 : sameBox(r1,c1,r2,c2)' +
            '=> ~candidate(r2,c2,v)).',
            True
        )
        idp.Define(
            '!r1,c1,v,r2,c2 : denyCandidate(r1,c1,v,r2,c2) <-' +
            '~candidate(r1,c1,v) & gridValue(r2,c2,v) &' +
            'directRelation(r1,c1,r2,c2).',
            True
        )
        idp.Define(direct_relation_def, True)
        idp.Constraint(candidate_constraint + '.', True)
        model_values = self.model_expand(idp, keyword)
        return model_values

    def predefine(self, given: list[tuple[int, int, int]]) -> None:
        """Predefine keywords that have been marked as such.

        This function should be called once after adding all rules,
        and before doing any calculations.
        """
        if self.predefined:
            return
        idp = self.get_idp()
        idp = self.add_required_idp(idp, given)
        idp = self.add_active_idp(idp)
        for keyword in self.precalc_structures:
            values = self.model_expand(idp, keyword)
            self.precalc_structures[keyword] = values
        self.predefined = True


class UnsupportedRule(Exception):
    """Sudoku rule is not supported by the knowledge base."""


def main():
    """Main."""
    from sudoku_parser import parse_sudoku_file
    sudoku = parse_sudoku_file('./sudokus/easy.sudoku')
    kb = SudokuKB()
    kb.add_rule('normal')
    print(kb)
    kb.predefine(sudoku)
    core, cell = kb.get_unsat_core((3, 3, 8), sudoku, 0)
    print(cell, core)


if __name__ == '__main__':
    main()
