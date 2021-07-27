import argparse
from typing import List


from . import __version__
from . import log
from . import table


def render_table(args: argparse.Namespace) -> None:
    rows = prepare_rows(args)
    table.render_table(rows)


def prepare_rows(args: argparse.Namespace) -> List[table.Row]:
    yes_green = table.Cell('yes', c='green')
    no_black = table.Cell('no', c='black')
    n_a_black = table.Cell('n/a', c='black')
    texts = (
        ('version', __version__),
        ('executor', args.executor),
        ('output type', args.output_type),
        ('docker', yes_green if args.docker else no_black),
        ('resume', yes_green if args.resume else no_black),
    )
    rows = list()
    header_row = table.Row(('Variable', 'Value'), header=True)
    rows.append(header_row)
    for text in texts:
        rows.append(table.Row(text))
    return rows
