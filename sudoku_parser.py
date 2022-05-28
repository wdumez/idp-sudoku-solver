"""Utility functions for parsing sudokus and files."""
import re


def parse_sudoku(sudoku: str) -> list[tuple[int, int, int]]:
    """Parses a sudoku string.
    Valid strings contain digits and non-digits for empty cells.
    Line breaks are optional.

    Example:
    '...4....9.38..' etc.

    Returns a list of tuples containing (row, col, value).
    """
    sudoku = sudoku.strip().replace('\n', '')
    grid = []
    row, col = (0, 0)
    for char in sudoku:
        if col >= 9:
            col = 0
            row += 1
        if char.isdigit():
            grid.append((row, col, int(char)))
        col += 1
    return grid


def parse_sudoku_file(filename: str):
    """Parses a sudoku from a file."""
    with open(filename, 'r', encoding='utf-8') as file_in:
        sudoku = file_in.read()
    return parse_sudoku(sudoku)


def parse_thermo(thermo: str) -> list[tuple[int, int, int, int]]:
    """Parses a thermo cells string.

    Format:

    thermo = { 0,0,0,1; ... }
    """
    thermo = thermo[thermo.find('{')+1:thermo.find('}')]
    thermo = re.sub(r'\s+', '', thermo)
    thermo = thermo.rstrip(';').split(';')
    thermo_cells = []
    for item in thermo:
        row1, col1, row2, col2 = item.split(',')
        thermo_cells.append((int(row1), int(col1), int(row2), int(col2)))
    return thermo_cells


def parse_thermo_file(filename: str):
    """Parses the thermo cells from a file."""
    with open(filename, 'r', encoding='utf-8') as file_in:
        thermo = file_in.read()
    return parse_thermo(thermo)


def parse_killer(killer) -> tuple[list[tuple[int, int, int]], dict[int, int]]:
    """Parses the cages and cage sums strings.

    Returns a tuple of a list and a dictionary: (cages, cage_sums).
    """
    cages: 'list[tuple[int,int,int]]' = []
    cage_sums: 'dict[int,int]' = {}
    cages_str, cage_sums_str = killer.split('cageSum')

    cages_str = cages_str[cages_str.find('{')+1:cages_str.find('}')]
    cages_str = re.sub(r'\s+', '', cages_str)
    cages_str = cages_str.rstrip(';').split(';')
    for cage in cages_str:
        cage_id, row, col = cage.split(',')
        cage_id, row, col = (int(cage_id), int(row), int(col))
        cages.append((cage_id, row, col))

    cage_sums_str = cage_sums_str[cage_sums_str.find(
        '{')+1:cage_sums_str.find('}')]
    cage_sums_str = re.sub(r'\s+', '', cage_sums_str)
    cage_sums_str = cage_sums_str.rstrip(';').split(';')
    for cage in cage_sums_str:
        cage_id, cage_sum = cage.split(',')
        cage_id, cage_sum = (int(cage_id), int(cage_sum))
        cage_sums[cage_id] = cage_sum

    return cages, cage_sums


def parse_killer_file(filename: str):
    """Parses the killer cells from a file.

    Returns a tuple (cages, cage_sums).
    """
    with open(filename, 'r', encoding='utf-8') as file_in:
        killer = file_in.read()
    return parse_killer(killer)


def py2idp(sudoku: list[tuple[int, int, int]]) -> str:
    """Converts python format to IDP format."""
    txt = '{ '
    for r, c, v in sudoku:
        txt += f'{r},{c},{v}; '
    txt += '}'
    return txt


def idp2py(sudoku: str) -> list[tuple[int, int, int]]:
    """Converts IDP format to python format."""
    sudoku = sudoku.strip().lstrip('{').rstrip('}').strip().split(';')
    sudoku_list = []
    for cell_str in sudoku:
        r, c, v = cell_str.strip().split(',')
        r, c, v = (int(r), int(c), int(v))
        sudoku_list.append((r, c, v))
    return sudoku_list


if __name__ == '__main__':
    parse_killer_file('./sudokus/killer.killer')
