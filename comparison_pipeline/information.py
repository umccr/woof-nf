from . import __version__
from . import log
from . import table


def render_info_table(args):
    yes_green = log.ftext('yes', c='green')
    no_black = log.ftext('no', c='black')
    n_a_black = log.ftext('n/a', c='black')

    header_tokens = ('Variable', 'Value')
    rows = (
        ('version', __version__),
        ('executor', args.executor),
        ('docker', yes_green if args.docker else no_black),
        ('s3_bucket', log.ftext(args.s3_bucket, c='green') if args.s3_bucket else n_a_black),
        ('resume', yes_green if args.resume else no_black),
    )

    csizes = table.get_column_sizes(rows)
    log.render('  ', end='')
    for token, csize in zip(header_tokens, csizes):
        log.render(log.ftext(token.ljust(csize), f='underline'), end='')
    log.render_newline()
    for row in rows:
        row_just = list()
        for text, csize in zip(row, csizes):
            # Adjust csize padding to account for ansi escape codes
            ansi_ec_size = len(text) - len(log.ANSI_ESCAPE.sub('', text))
            csize += ansi_ec_size
            # Justify
            row_just.append(text.ljust(csize))
        row_text = ''.join(row_just)
        log.render('  ' + row_text)
