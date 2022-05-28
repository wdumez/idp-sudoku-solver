"""Storing solutions of the solver."""
from __future__ import annotations
import json
import jsonschema
import sudoku_parser as sp


class Solution(dict):
    """Stores the explanation of the solver."""

    SCHEMA_FILENAME = './solution-schema.json'

    def __init__(self):
        super().__init__()
        self['steps'] = []

    def __str__(self) -> str:
        txt = f'Solution (with schema: {Solution.SCHEMA_FILENAME}):\n'
        txt += json.dumps(self, sort_keys=True, indent=4)
        return txt

    def add_step(self, step_nr: int, cell: tuple,
                 used_cells: list[dict], current_structure: list[tuple]
                 ) -> None:
        """Adds a step to the solution."""
        step = {}
        step['step_nr'] = step_nr
        step['cell'] = cell
        step['used_cells'] = used_cells
        step['current_structure'] = current_structure
        self['steps'].append(step)

    def get_last_step(self) -> dict:
        """Return the last recorded step."""
        highest_step_nr = 0
        for step in self['steps']:
            if step['step_nr'] > highest_step_nr:
                last_step = step
        return last_step

    def save(self, filename: str) -> None:
        """Save the solution to a JSON file."""
        with open(filename, 'w', encoding='utf-8') as file_out:
            txt = json.dumps(self, sort_keys=True, indent=4)
            file_out.write(txt)

    def is_valid(self) -> bool:
        """Test whether the solution follows a JSON schema."""
        with open(Solution.SCHEMA_FILENAME, 'r', encoding='utf-8') as file_in:
            schema = json.loads(file_in.read())
        try:
            jsonschema.validate(self, schema)
            return True
        except jsonschema.ValidationError as err:
            print(f'ValidationError:\n{err}')
            return False

    @staticmethod
    def from_file(filename: str) -> Solution:
        """Make a solution object from a JSON file."""
        with open(filename, 'r', encoding='utf-8') as file_in:
            sol_str = json.loads(file_in.read())
        sol = Solution()
        for key, value in sol_str.items():
            sol[key] = value
        return sol


def main() -> None:
    """Main."""
    sol = Solution.from_file('./solutions/candidates-thermo-easy.json')
    print(sol.is_valid())
    thermo_cells = sp.parse_thermo_file('./sudokus/thermo-easy.thermo')
    sol['thermo_cells'] = thermo_cells
    print(sol.is_valid())
    sol.save('./alt-sol.json')


if __name__ == '__main__':
    main()
