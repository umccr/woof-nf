import distutils.version
import re
import shutil
import subprocess
import sys
import textwrap
from typing import List, Dict, Tuple


from . import log
from . import table


SOFTWARE_DEPENDENCIES: Dict[str, Dict] = {
    'aws': {
        'min': '2.0.0',
        'max': None,
        'arg': '--version',
        'regex': '^aws-cli/([0-9.]+)',
        'context': {'aws_executor'},
    },
    'bcftools': {
        'min': '1.12',
        'max': None,
        'arg': '-v',
        'regex': '^^bcftools ([0-9.]+)',
        'dockerised': True,
    },
    'circos': {
        'min': '0.69-8',
        'max': None,
        'arg': '-v',
        'regex': '^circos \| v ([0-9.-]+)',
        'dockerised': True,
    },
    'docker': {
        'min': '20.00.0',
        'max': None,
        'arg': '--version',
        'regex': '^Docker version ([0-9.]+)',
        'context': {'docker'},
    },
    'nextflow': {
        # Strictly requiring this version as I've rigidly coded streaming of nf stdout
        # May break between even minor releases
        'min': '21.04.0',
        'max': '21.04.0',
        'arg': '-version',
        'regex': '^.+version ([0-9.]+) build',
    },
    'R': {
        'min': '3.5',
        'max': None,
        'arg': '--version',
        'regex': '^R version ([0-9.]+)',
        'dockerised': True,
    },
}

# NOTE: not currently requiring specific versions
R_PACKAGES = (
    'bedr',
    'DT',
    'glue',
    'kableExtra',
    'rock',
    'tidyverse',
    # Required for external data
    'woofr',
)


def check(executor: str, docker: bool) -> None:
    # Check software tools and then R packages. Logic to determine presence of R packages
    # considerably different and so is separated
    # When docker is set to be used, only check for dependencies required to launch tasks
    log.task_msg_title('Checking dependencies')
    check_tools(executor, docker)
    check_rpackages(docker)


def check_tools(executor: str, docker: bool) -> None:
    log.render('\nTool status:')
    tool_status_results = list()
    for tool in SOFTWARE_DEPENDENCIES:
        # aws-cli: aws executor only
        if executor != 'aws' and 'aws_executor' in SOFTWARE_DEPENDENCIES[tool].get('context', set()):
            tool_status = (tool, '-', 'not used')
        # docker: with local executor + docker only
        elif executor != 'local' and 'docker' in SOFTWARE_DEPENDENCIES[tool].get('context', set()):
            tool_status = (tool, '-', 'not used')
        elif not docker and 'docker' in SOFTWARE_DEPENDENCIES[tool].get('context', set()):
            tool_status = (tool, '-', 'not used')
        # dockerised software: with local executor + *not* docker only
        elif docker and SOFTWARE_DEPENDENCIES[tool].get('dockerised', False):
            tool_status = (tool, '-', 'docker')
        else:
            tool_status = get_tool_status(tool)
        tool_status_results.append(tool_status)
    # Prepare rows and render
    rows, missing_errors = prepare_tool_status_rows(tool_status_results)
    table.render_table(rows)
    log.render_newline()
    if missing_errors:
        print_missing_error(missing_errors)


def get_tool_status(tool: str) -> Tuple[str, str, str]:
    version_arg = SOFTWARE_DEPENDENCIES[tool]['arg']
    version_regex = SOFTWARE_DEPENDENCIES[tool]['regex']
    min_version = SOFTWARE_DEPENDENCIES[tool]['min']
    max_version = SOFTWARE_DEPENDENCIES[tool]['max']
    # Check tool is in PATH
    tool_path = shutil.which(tool)
    if tool_path == None:
        return tool, '-', 'not found'
    # Run command to get version
    command = f'{tool} {version_arg}'
    process_result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        encoding='utf-8'
    )
    if process_result.returncode != 0:
        log.render(log.ftext(f'error: got bad return code for {command}', c='red'))
        log.render(log.ftext(f'\ncommand used:', f='bold'))
        log.render(command)
        log.render(log.ftext(f'\nresult:', f='bold'))
        log.render(process_result.stdout)
        sys.exit(1)
    regex_result = re.search(version_regex, process_result.stdout, re.MULTILINE)
    if regex_result:
        version = regex_result.group(1)
    else:
        log.render(log.ftext(f'\nerror: failed to get software version for {tool}', c='red'))
        log.render(log.ftext(f'\ncommand used:', f='bold'))
        log.render(command)
        log.render(log.ftext(f'\nresult:', f='bold'))
        log.render(process_result.stdout)
        sys.exit(1)
    # Check tool version
    if min_version and distutils.version.LooseVersion(version) < min_version:
        status = 'too old'
    elif max_version and distutils.version.LooseVersion(version) > max_version:
        status = 'too new'
    else:
        status = 'good'
    return tool, version, status


def prepare_tool_status_rows(tool_status_results: List) -> Tuple:
    rows = list()
    missing_errors = list()
    # Header
    header_row = table.Row(('Program', 'Version', 'Status'), header=True)
    rows.append(header_row)
    # Body text
    for texts in tool_status_results:
        row = table.Row(texts)
        status_cell = row.cells[-1]
        status = status_cell.text
        if status == 'good':
            status_cell.c = 'green'
        elif status == 'docker':
            status_cell.c = 'black'
        elif status == 'not used':
            status_cell.c = 'black'
        elif status in {'not found', 'too old', 'too new'}:
            # Output text
            table.set_row_colour(row, 'red')
            # Record error
            tool = row.cells[0].text
            tool_reqs = SOFTWARE_DEPENDENCIES[tool]
            if tool_reqs['min'] and tool_reqs['max']:
                # between a - b
                msg = f'{tool} version between {tool_reqs["min"]} - {tool_reqs["max"]}'
            elif tool_reqs['min']:
                # a or newer
                msg = f'{tool} version {tool_reqs["min"]} or newer'
            elif tool_reqs['max']:
                # a or older
                msg = f'{tool} version {tool_reqs["max"]} or older'
            missing_errors.append(msg)
        else:
            assert False
        rows.append(row)
    return rows, missing_errors


def check_rpackages(docker: bool) -> None:
    log.render('R package status:')
    if docker:
        missing_errors = None
        rpackage_status_results = list()
        for package in R_PACKAGES:
            rpackage_status_results.append((package, 'docker'))
    else:
        rpackage_status_results, missing_errors = get_rpackage_status()
    # Prepare and then render table rows
    rows = prepare_rpackage_status_rows(rpackage_status_results)
    table.render_table(rows)
    log.render_newline()
    if missing_errors:
        print_missing_error(missing_errors)


def get_rpackage_status() -> Tuple:
    packages_str = 'NULL'
    for package in R_PACKAGES:
        packages_str += f", '{package}'"
    rscript = textwrap.dedent(f'''
        v.packages <- setdiff(c({packages_str}), rownames(installed.packages()))
        for (s.package in v.packages) {{ cat(s.package, '\n', sep='') }}
    ''')
    command = f'Rscript -e "{rscript}"'
    process_result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        encoding='utf-8'
    )
    if process_result.returncode != 0:
        log.render(f'error: got bad return code for {command}')
        sys.exit(1)
    # Get set of missing packages; `split` called on '' produces list with one empty string,
    # handled by manually setting to empty set
    if process_result.stdout:
        missing_packages = set(process_result.stdout.rstrip().split('\n'))
    else:
        missing_packages = set()
    package_status = list()
    for package in R_PACKAGES:
        if package in missing_packages:
            status = 'not found'
        else:
            status = 'good'
        package_status.append((package, status))
    return package_status, missing_packages


def prepare_rpackage_status_rows(rpackage_status_results: List) -> List[table.Row]:
    rows = list()
    # Header
    header_row = table.Row(('R package', 'Status'), header=True)
    rows.append(header_row)
    # Body text
    for texts in rpackage_status_results:
        row = table.Row(texts)
        status_cell = row.cells[-1]
        status = status_cell.text
        if status == 'good':
            status_cell.c = 'green'
        elif status == 'docker':
            status_cell.c = 'black'
        elif status == 'not found':
            status_cell.c = 'red'
        else:
            assert False
        rows.append(row)
    return rows


def print_missing_error(missing_errors: List[str]) -> None:
    if len(missing_errors) == 1:
        [msg] = missing_errors
        log.render(f'\nError: {msg} is required')
        sys.exit(1)
    log.render(f'\nError: {len(missing_errors)} dependencies incompatible/missing. ', end='')
    log.render('Unfulfilled requirements:')
    for msg in missing_errors:
        log.render(f'  {msg}')
    sys.exit(1)
