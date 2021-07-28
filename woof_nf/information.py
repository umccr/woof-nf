import argparse
from typing import List


from . import __version__
from . import log
from . import table


def render_table(args: argparse.Namespace) -> None:
    rows = prepare_rows(args)
    table.render_table(rows)


def prepare_rows(args: argparse.Namespace) -> List[table.Row]:
    texts = (
        ('version', __version__),
        ('executor', args.executor),
        ('output type', args.output_type),
        ('docker', table.Cell('yes', c='green') if args.docker else table.Cell('no', c='black')),
        ('resume', table.Cell('yes', c='green') if args.resume else table.Cell('no', c='black'))
    )
    rows = list()
    header_row = table.Row(('Variable', 'Value'), header=True)
    rows.append(header_row)
    for text in texts:
        rows.append(table.Row(text))
    return rows
