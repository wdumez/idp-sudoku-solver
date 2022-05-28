"""Explain solutions is a visual manner.
A better solution would be to use a tool like Penpa edit.
https://github.com/swaroopg92/penpa-edit
"""
import PIL.Image
from PIL.Image import Image
import PIL.ImageFont
import PIL.ImageDraw
from solution import Solution

# 9x9
SIZE = 9

# dimensions
IMG_SIZE = 1000  # pixels along one edge
RIGHT_PADDING = int(0.45 * IMG_SIZE)
MARGIN = 0.01 * IMG_SIZE
TOPLEFT = (MARGIN, MARGIN)
GRID_SIZE = IMG_SIZE-2*MARGIN-1
BLOCK_SIZE = GRID_SIZE / (SIZE/3)
CELL_SIZE = GRID_SIZE / SIZE
TEXT_TOPLEFT = (0.95*IMG_SIZE, 0.4*IMG_SIZE)

# thermo sudoku
THERMO_OFFSET = CELL_SIZE * 0.35
THERMO_BULB_OFFSET = THERMO_OFFSET * 0.4

# killer sudoku
CAGE_LINE_WIDTH = 2
CAGE_OFFSET = CELL_SIZE * 0.1
NW = 0
NE = 1
EN = 2
ES = 3
SE = 4
SW = 5
WS = 6
WN = 7
N = 8
E = 9
S = 10
W = 11

# fonts
NUMBER_FONT = PIL.ImageFont.truetype(
    font='./fonts/arial.ttf', size=int(0.6 * CELL_SIZE))
CAGE_FONT = PIL.ImageFont.truetype(
    font='./fonts/arial.ttf', size=int(0.2 * CELL_SIZE))
TEXT_FONT = PIL.ImageFont.truetype(
    font='./fonts/arial.ttf', size=int(0.03 * GRID_SIZE))

# line widths
BOX_LINEWIDTH = 3  # boxes
CELL_LINEWIDTH = 1  # cells
CROSS_LINEWIDTH = 2  # number strike-through

# colors
RED = (255, 0, 0, 0)
GREEN = (128, 255, 128, 0)
BLUE = (128, 128, 255, 0)
ORANGE = (210, 105, 30, 0)
PURPLE = (138, 43, 226, 0)
MAGENTA = (255, 0, 255, 0)
YELLOW = (255, 215, 0, 0)
CYAN = (0, 255, 255, 0)
SALMON = (233, 150, 122, 0)
OLIVE = (85, 107, 47, 0)
BEIGE = (200, 200, 275, 0)
BLACK = (0, 0, 0, 0)
WHITE = (255, 255, 255, 0)
GRAY = (200, 200, 200, 0)


def get_blank_img() -> Image:
    """Create and return a blank image."""
    return PIL.Image.new(
        'RGB',
        (IMG_SIZE+RIGHT_PADDING, IMG_SIZE),
        WHITE)


def draw_sudoku_grid(img) -> Image:
    """Draw a sudoku grid on the image."""
    draw = PIL.ImageDraw.Draw(img)
    # draw block outlines
    for y in range(int(SIZE/3)):
        for x in range(int(SIZE/3)):
            block_topleft = (TOPLEFT[0]+x*BLOCK_SIZE,
                             TOPLEFT[1]+y*BLOCK_SIZE)
            block_botright = (block_topleft[0] + BLOCK_SIZE,
                              block_topleft[1] + BLOCK_SIZE)
            draw.rectangle(xy=(block_topleft, block_botright),
                           outline=BLACK, width=BOX_LINEWIDTH)
    # draw cell outlines
    for y in range(SIZE):
        for x in range(SIZE):
            cell_topleft = (TOPLEFT[0]+x*CELL_SIZE,
                            TOPLEFT[1]+y*CELL_SIZE)
            cell_botright = (cell_topleft[0] + CELL_SIZE,
                             cell_topleft[1] + CELL_SIZE)
            draw.rectangle(xy=(cell_topleft, cell_botright),
                           outline=BLACK, width=CELL_LINEWIDTH)
    return img


def draw_cell_color(img, row, column, color) -> None:
    """Draws the cell (row,column) on the image in the given color."""
    draw = PIL.ImageDraw.Draw(img)
    x = TOPLEFT[0] + column * CELL_SIZE
    y = TOPLEFT[1] + row * CELL_SIZE
    draw.rectangle(xy=(x, y, x+CELL_SIZE, y+CELL_SIZE),
                   fill=color, width=1)


def draw_cell_value(img, cell, color) -> None:
    """Draws the value of the cell on the image in the given color."""
    row, column, value = cell
    draw = PIL.ImageDraw.Draw(img)
    x = TOPLEFT[0] + (column + 1) * \
        CELL_SIZE - CELL_SIZE/2
    y = TOPLEFT[1] + (row + 1) * \
        CELL_SIZE - CELL_SIZE/2
    draw.text(
        xy=(x, y),
        text=str(value),
        anchor='mm',
        fill=color,
        font=NUMBER_FONT)
    return


def draw_cell_cross(img, row, column, color) -> None:
    """Draws a cross on the cell in the given color."""
    draw = PIL.ImageDraw.Draw(img)
    x_start = TOPLEFT[0] + (column + 1) * \
        CELL_SIZE - CELL_SIZE/4
    y_start = TOPLEFT[1] + (row + 1) * \
        CELL_SIZE - 3*CELL_SIZE/4
    x_end = TOPLEFT[0] + (column + 1) * \
        CELL_SIZE - 3*CELL_SIZE/4
    y_end = TOPLEFT[1] + (row + 1) * \
        CELL_SIZE - CELL_SIZE/4
    draw.line(
        xy=(x_start, y_start, x_end, y_end),
        fill=color,
        width=CROSS_LINEWIDTH
    )
    x_start = TOPLEFT[0] + (column + 1) * \
        CELL_SIZE - 3*CELL_SIZE/4
    y_start = TOPLEFT[1] + (row + 1) * \
        CELL_SIZE - 3*CELL_SIZE/4
    x_end = TOPLEFT[0] + (column + 1) * \
        CELL_SIZE - CELL_SIZE/4
    y_end = TOPLEFT[1] + (row + 1) * \
        CELL_SIZE - CELL_SIZE/4
    draw.line(
        xy=(x_start, y_start, x_end, y_end),
        fill=color,
        width=CROSS_LINEWIDTH
    )


def draw_thermo_bulb(img, row, column, color) -> None:
    """Draws a thermometer bulb on the cell in the given color."""
    draw = PIL.ImageDraw.Draw(img)
    x = TOPLEFT[0] + column * \
        CELL_SIZE + THERMO_BULB_OFFSET
    y = TOPLEFT[1] + row * \
        CELL_SIZE + THERMO_BULB_OFFSET
    draw.ellipse(xy=(x, y, x+(CELL_SIZE-2*THERMO_BULB_OFFSET),
                     y+(CELL_SIZE-2*THERMO_BULB_OFFSET)), fill=color)


def draw_thermo_connect(
        img, src_row, src_col, dst_row, dst_col, color) -> None:
    """Draws a thermometer connection between the
    two cells in the given color.
    """
    row = src_row if src_row < dst_row else dst_row
    col = src_col if src_col < dst_col else dst_col
    draw = PIL.ImageDraw.Draw(img)
    x = TOPLEFT[0] + col * \
        CELL_SIZE + THERMO_OFFSET
    y = TOPLEFT[1] + row * \
        CELL_SIZE + THERMO_OFFSET
    width = (abs(src_col-dst_col) *
             CELL_SIZE+(CELL_SIZE-2*THERMO_OFFSET))
    height = (abs(src_row-dst_row) *
              CELL_SIZE+(CELL_SIZE-2*THERMO_OFFSET))
    draw.rectangle(xy=(x, y, x+width,
                       y+height), fill=color, width=1)


def draw_thermometers(img, thermo_cells, color) -> None:
    """Draws all thermometers in thermo_cells in the given color."""
    prev_row, prev_col = (-1, -1)
    for thermo in thermo_cells:
        if prev_row != thermo[0] or prev_col != thermo[1]:
            draw_thermo_bulb(
                img, thermo[0], thermo[1], color)
        draw_thermo_connect(
            img, thermo[0], thermo[1], thermo[2], thermo[3], color)
        prev_row, prev_col = (thermo[2], thermo[3])


def draw_cage_part(img, row, column, part_nr):
    """Draw the part of a cage on the cell with that part number."""
    cell = (TOPLEFT[0] + column * CELL_SIZE,
            TOPLEFT[1] + row * CELL_SIZE)
    horizontal_advance = (4, 0)
    vertical_advance = (0, 4)
    horizontal_offset_advance = (10, 0)
    vertical_offset_advance = (0, 10)
    if part_nr == NW:
        start = (cell[0] + CAGE_OFFSET, cell[1])
        end = (start[0], cell[1] + CAGE_OFFSET)
        advance = vertical_advance
        offset_advance = vertical_offset_advance
    elif part_nr == NE:
        start = (cell[0] + CELL_SIZE - CAGE_OFFSET,
                 cell[1])
        end = (start[0], cell[1] + CAGE_OFFSET)
        advance = vertical_advance
        offset_advance = vertical_offset_advance
    elif part_nr == EN:
        start = (cell[0] + CELL_SIZE - CAGE_OFFSET,
                 cell[1] + CAGE_OFFSET)
        end = (cell[0]+CELL_SIZE, start[1])
        advance = horizontal_advance
        offset_advance = horizontal_offset_advance
    elif part_nr == ES:
        start = (cell[0] + CELL_SIZE - CAGE_OFFSET,
                 cell[1] + CELL_SIZE - CAGE_OFFSET)
        end = (cell[0] + CELL_SIZE,
               start[1])
        advance = horizontal_advance
        offset_advance = horizontal_offset_advance
    elif part_nr == SE:
        start = (cell[0] + CELL_SIZE - CAGE_OFFSET,
                 cell[1] + CELL_SIZE - CAGE_OFFSET)
        end = (start[0], cell[1] + CELL_SIZE)
        advance = vertical_advance
        offset_advance = vertical_offset_advance
    elif part_nr == SW:
        start = (cell[0] + CAGE_OFFSET,
                 cell[1] + CELL_SIZE - CAGE_OFFSET)
        end = (start[0], cell[1] + CELL_SIZE)
        advance = vertical_advance
        offset_advance = vertical_offset_advance
    elif part_nr == WS:
        start = (cell[0],
                 cell[1] + CELL_SIZE - CAGE_OFFSET)
        end = (cell[0] + CAGE_OFFSET, start[1])
        advance = horizontal_advance
        offset_advance = horizontal_offset_advance
    elif part_nr == WN:
        start = (cell[0], cell[1] + CAGE_OFFSET)
        end = (cell[0] + CAGE_OFFSET, start[1])
        advance = horizontal_advance
        offset_advance = horizontal_offset_advance
    elif part_nr == N:
        start = (cell[0] + CAGE_OFFSET,
                 cell[1] + CAGE_OFFSET)
        end = (cell[0] + CELL_SIZE - CAGE_OFFSET,
               start[1])
        advance = horizontal_advance
        offset_advance = horizontal_offset_advance
    elif part_nr == E:
        start = (cell[0] + CELL_SIZE - CAGE_OFFSET,
                 cell[1] + CAGE_OFFSET)
        end = (start[0],
               cell[1] + CELL_SIZE - CAGE_OFFSET)
        advance = vertical_advance
        offset_advance = vertical_offset_advance
    elif part_nr == S:
        start = (cell[0] + CAGE_OFFSET,
                 cell[1] + CELL_SIZE - CAGE_OFFSET)
        end = (cell[0] + CELL_SIZE - CAGE_OFFSET,
               cell[1] + CELL_SIZE - CAGE_OFFSET)
        advance = horizontal_advance
        offset_advance = horizontal_offset_advance
    elif part_nr == W:
        start = (cell[0] + CAGE_OFFSET,
                 cell[1] + CAGE_OFFSET)
        end = (start[0],
               cell[1] + CELL_SIZE - CAGE_OFFSET)
        advance = vertical_advance
        offset_advance = vertical_offset_advance
    draw = PIL.ImageDraw.Draw(img)
    offset = (0, 0)
    while start[0] + offset[0] < end[0] or start[1] + offset[1] < end[1]:
        draw.line(xy=(
            start[0] + offset[0],
            start[1] + offset[1],
            start[0] + offset[0] + advance[0],
            start[1] + offset[1] + advance[1]
        ),
            fill=BLACK,
            width=CAGE_LINE_WIDTH)
        offset = (offset[0] + offset_advance[0],
                  offset[1] + offset_advance[1])


def draw_cage_sum(img, row: int, column: int, cage_sum: int, color) -> None:
    """Draws a cage sum in the top left of the cell."""
    draw = PIL.ImageDraw.Draw(img)
    x = TOPLEFT[0] + (column) * \
        CELL_SIZE + CAGE_OFFSET * 1.3
    y = TOPLEFT[1] + (row) * \
        CELL_SIZE + CAGE_OFFSET * 1.3
    draw.text(
        xy=(x, y),
        text=str(cage_sum),
        anchor='lt',
        fill=color,
        font=CAGE_FONT)


def draw_cage(img, cage: 'list[tuple[int,int]]', cage_sum: int) -> None:
    """Draws a single cage with its sum."""
    def adjacency(cell, other):
        res = -1
        if cell[1] == other[1]-1:
            if cell[0] == other[0]-1:
                res = 4
            if cell[0] == other[0]:
                res = 3
            if cell[0] == other[0]+1:
                res = 2
        if cell[1] == other[1]+1:
            if cell[0] == other[0]-1:
                res = 6
            if cell[0] == other[0]:
                res = 7
            if cell[0] == other[0]+1:
                res = 0
        if cell[1] == other[1]:
            if cell[0] == other[0]-1:
                res = 5
            if cell[0] == other[0]+1:
                res = 1
        return res

    for cell in cage:
        cage_parts = {i: False for i in range(0, 12)}
        adj = {i: False for i in range(0, 8)}
        for other_cell in cage:
            if cell == other_cell:
                continue
            adj_nr = adjacency(cell, other_cell)
            if adj_nr != -1:
                adj[adj_nr] = True
        if not adj[1]:
            cage_parts[N] = True
        else:
            cage_parts[NE] = True
            cage_parts[NW] = True
        if not adj[3]:
            cage_parts[E] = True
        else:
            cage_parts[EN] = True
            cage_parts[ES] = True
        if not adj[5]:
            cage_parts[S] = True
        else:
            cage_parts[SE] = True
            cage_parts[SW] = True
        if not adj[7]:
            cage_parts[W] = True
        else:
            cage_parts[WN] = True
            cage_parts[WS] = True
        # Check for larger squares
        if adj[0] and adj[1] and adj[7]:
            cage_parts[NW] = False
            cage_parts[WN] = False
        if adj[1] and adj[2] and adj[3]:
            cage_parts[NE] = False
            cage_parts[EN] = False
        if adj[3] and adj[4] and adj[5]:
            cage_parts[ES] = False
            cage_parts[SE] = False
        if adj[5] and adj[6] and adj[7]:
            cage_parts[SW] = False
            cage_parts[WS] = False
        for part_nr, do_draw in cage_parts.items():
            if do_draw:
                draw_cage_part(img, cell[0], cell[1], part_nr)
    # Cage number in most top-left cage
    distance = {cell: cell[0]*cell[0]+cell[1]*cell[1] for cell in cage}
    distance = sorted(distance)
    draw_cage_sum(
        img, distance[0][0], distance[0][1], cage_sum, BLACK)


def draw_cages(img, cages, cage_sums) -> None:
    """Draws all cages and their cage sums."""
    dict_of_cages = {i: []
                     for i in range(min(cages, key=lambda x: x[2])[
                         2], max(cages, key=lambda x: x[2])[2]+1)}
    for cage_id in dict_of_cages:
        for entry in cages:
            if entry[2] == cage_id:
                dict_of_cages[cage_id].append((entry[0], entry[1]))
    for cage_id, cage in dict_of_cages.items():
        draw_cage(img, cage, cage_sums[str(cage_id)])


def write_padding_text(img, value, single_cell=False) -> None:
    """Write some text to the right of the image."""
    to_write = [
        ('The ', BLACK),
        ('blue', BLUE),
        ('cells indicate why the', BLACK),
        ('green', GREEN)
    ]
    if single_cell:
        to_write.append((f'cell must be {value}.', BLACK))
    else:
        to_write.append((f'cell cannot be {value}.', BLACK))
    draw = PIL.ImageDraw.Draw(img)
    x = TEXT_TOPLEFT[0] + 50
    y = TEXT_TOPLEFT[1] + 50
    char_offset = 0
    i = 0
    for txt, color in to_write:
        draw.text(
            xy=(x+char_offset, y),
            text=txt,
            anchor='la',
            fill=color,
            font=TEXT_FONT)
        char_offset += len(txt) * 18
        if char_offset/20 >= 20:
            char_offset = 0
            y += 35
        i += 1


def explanation_step(step, explanation_folder, **kwargs) -> None:
    """Generate an explanation for a single step."""
    cell_to_fill = step['cell']
    for used_cells in step['used_cells']:
        value = used_cells['value']
        cells = used_cells['cells']
        img = get_blank_img()
        # background of used cells
        for cell in cells:
            draw_cell_color(
                img,
                cell[0], cell[1],
                BLUE)
        # background of cell
        draw_cell_color(
            img,
            cell_to_fill[0], cell_to_fill[1],
            GREEN
        )
        # thermometers
        if kwargs.get('thermo_cells'):
            draw_thermometers(img, kwargs['thermo_cells'], GRAY)
        # cages
        if kwargs.get('killer_cages') and kwargs.get('killer_cage_sums'):
            draw_cages(img, kwargs['killer_cages'], kwargs['killer_cage_sums'])
        # all numbers
        for cell in step['current_structure']:
            draw_cell_value(
                img,
                cell,
                BLACK
            )
        # cell in question
        draw_cell_value(
            img,
            (cell_to_fill[0], cell_to_fill[1], value),
            BLACK
        )
        single_cell = True
        if len(step['used_cells']) != 1:
            draw_cell_cross(
                img,
                cell_to_fill[0], cell_to_fill[1],
                RED
            )
            single_cell = False
        write_padding_text(img, value, single_cell)
        # sudoku grid
        draw_sudoku_grid(img)
        filename = f'{explanation_folder}/step{step["step_nr"]}-{value}.png'
        img.save(filename)


def generate_explanation(
        solution: Solution, explanation_folder: str) -> None:
    """Generate an explanation for a step-wise solution.
    The resulting images are saved in an explanation folder.
    """
    constructs = {}
    if solution.get('thermo_cells'):
        constructs['thermo_cells'] = solution['thermo_cells']
    if solution.get('killer_cages') and solution.get('killer_cage_sums'):
        constructs['killer_cages'] = solution['killer_cages']
        constructs['killer_cage_sums'] = solution['killer_cage_sums']
    for step in solution['steps']:
        explanation_step(step, explanation_folder, **constructs)


def main() -> None:
    """Main."""


if __name__ == '__main__':
    main()
