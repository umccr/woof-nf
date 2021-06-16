import datetime
import re


# Formatting
BOLD        = '\033[1m'
DIM         = '\033[2m'
ITALIC      = '\033[4m'
UNDERLINE   = '\033[4m'
# Colours
BLACK       = '\033[90m'
RED         = '\033[91m'
GREEN       = '\033[92m'
YELLOW      = '\033[93m'
BLUE        = '\033[94m'
MAGENTA     = '\033[95m'
CYAN        = '\033[96m'
WHITE       = '\033[97m'
# Misc
END         = '\033[0m'


VERBOSITY = 1
NO_ANSI = False
ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


def ftext(text, c=None, f=None):
    ftext = f'{text}{END}'
    # Colour
    if c == 'black':
        ftext = BLACK + ftext
    elif c == 'red':
        ftext = RED + ftext
    elif c == 'green':
        ftext = GREEN + ftext
    elif c == 'yellow':
        ftext = YELLOW + ftext
    elif c == 'blue':
        ftext = BLUE + ftext
    elif c == 'magenta':
        ftext = MAGENTA + ftext
    elif c == 'cyan':
        ftext = CYAN + ftext
    elif c == 'white':
        ftext = WHITE + ftext
    # Typeface
    if not isinstance(f, list):
        f = [f]
    if 'bold' in f:
        ftext = BOLD + ftext
    if 'underline' in f:
        ftext = UNDERLINE + ftext
    if 'ITALIC' in f:
        ftext = ITALIC + ftext
    if 'DIM' in f:
        ftext = DIM + ftext
    return ftext


def render(text, ts=False, **kargs):
    if ts:
        text = f'{text} {get_timestamp()}'
    if NO_ANSI:
        print(ANSI_ESCAPE.sub('', text), **kargs)
    else:
        print(text, **kargs)


def task_msg_title(text):
    render(ftext(text, c='blue', f='underline'), ts=True)


def task_msg_body(text):
    render(ftext('  ' + text, c='black', f='dim'))


def render_newline():
    render('\n', end='')


def get_timestamp():
    ts = '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())
    return ftext(f'({ts})', c='black', f='dim')
