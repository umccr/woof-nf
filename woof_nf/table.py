from typing import List


from . import log


class Cell:

    def __init__(self, text, just='l', csize=None, c=None, f=None):
        assert isinstance(text, str)
        self.text = text
        self.just = just
        self.csize = csize
        self.c = c if c != None else str()
        self.f = f if f != None else list()


class Row:

    def __init__(self, cells, header=False, inset='  '):
        # Arg cells can be list of Cells or str
        self.cells = list()
        for item in cells:
            if isinstance(item, str):
                cell = Cell(item)
            elif isinstance(item, Cell):
                cell = item
            else:
                assert False
            if header:
                cell.f.append('underline')
            self.cells.append(cell)
        self.inset = inset


def set_row_colour(row: Row, colour: str) -> None:
    for cell in row.cells:
        cell.c = colour


def set_column_sizes(rows: List[Row]) -> None:
    for column_cells in zip(*[row.cells for row in rows]):
        clargest = max(len(log.ANSI_ESCAPE.sub('', c.text)) for c in column_cells)
        # Set to be at least n character in length
        # Otherwise, round up to closest multiple of 4
        for cell in column_cells:
            cell.csize = max(12, clargest + (4 - clargest % 4))


def render_row(row: Row) -> List[str]:
    texts = list()
    for cell in row.cells:
        # Text justification
        if cell.just == 'l':
            text = cell.text.ljust(cell.csize)
        elif cell.just == 'r':
            text = cell.text.rjust(cell.csize)
        elif cell.just == 'c':
            text = cell.text.center(cell.csize - 1)
        else:
            assert False
        # Text format
        text = log.ftext(text, c=cell.c, f=cell.f)
        texts.append(text)
    return texts


def render_table(rows: List[Row]) -> None:
    set_column_sizes(rows)
    for row in rows:
        texts = render_row(row)
        log.render(row.inset + ''.join(texts))
