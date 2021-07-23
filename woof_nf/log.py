import datetime
import pathlib
import re
from typing import Dict, List, Optional, Tuple, Union


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


# In order to capture log messages prior to setting up the log file, we buffer them here
BUFFER_LOG_MESSAGES = True
LOG_BUFFER: List[Tuple[str, bool, Dict]] = list()
LOG_FH = None


def setup_log_file(log_fp: pathlib.Path) -> None:
    global BUFFER_LOG_MESSAGES
    global LOG_FH
    LOG_FH = log_fp.open('w')
    BUFFER_LOG_MESSAGES = False
    for text, title, kargs in LOG_BUFFER:
        render(text, title=title, **kargs, log_file_only=True)


def ftext(text: str, c: str = None, f: Optional[Union[List[str], str]] = None) -> str:
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
    elif c in {None, ''}:
        # Allow c to be none or an empty str
        pass
    else:
        assert False
    # Typeface
    if isinstance(f, list):
        f_list = f
    elif isinstance(f, str):
        f_list = [f]
    else:
        f_list = list()
    if 'bold' in f_list:
        ftext = BOLD + ftext
    if 'underline' in f_list:
        ftext = UNDERLINE + ftext
    if 'ITALIC' in f_list:
        ftext = ITALIC + ftext
    if 'DIM' in f_list:
        ftext = DIM + ftext
    return ftext


def render(
    text: str,
    ts: bool = False,
    title: bool = False,
    log_file_only: bool = False,
    **kargs
) -> None:
    if ts:
        text = f'{text} {get_timestamp()}'
    # Log file
    if BUFFER_LOG_MESSAGES:
        LOG_BUFFER.append((text, title, kargs))
    else:
        text_log = ANSI_ESCAPE.sub('', text)
        # Remove flush if it was previously provided; forcefully enable
        if 'flush' in kargs:
            del kargs['flush']
        print(text_log, **kargs, file=LOG_FH, flush=True)
        if title:
            print('-' * len(text_log), file=LOG_FH, flush=True)
    if log_file_only:
        return
    # Console
    if NO_ANSI:
        print(ANSI_ESCAPE.sub('', text), **kargs)
    else:
        print(text, **kargs)


def task_msg_title(text: str) -> None:
    render(ftext(text, c='blue', f='underline'), ts=True, title=True)


def task_msg_body(text: str) -> None:
    render(ftext('  ' + text, c='black', f='dim'))


def render_newline() -> None:
    render('\n', end='')


def get_timestamp() -> str:
    ts = '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())
    return ftext(f'({ts})', c='black', f='dim')
