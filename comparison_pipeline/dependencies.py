import distutils.version
import re
import shutil
import subprocess
import sys


from . import log


software_dependencies = {
    'circos': {
        'min': '0.69-8',
        'max': None,
        'arg': '-v',
        'regex': '^circos \| v ([0-9.-]+)',
        'dockerised': True,
    },
    'bcftools': {
        'min': '1.12',
        'max': None,
        'arg': '-v',
        'regex': '^^bcftools ([0-9.]+)',
        'dockerised': True,
    },
    'nextflow': {
        'min': '21.04.0',
        'max': None,
        'arg': '-version',
        'regex': '^.+version ([0-9.]+) build',
        'dockerised': False,
    },
}


def check(docker):
    # Get tool status and render table
    log.task_msg_title('Checking dependencies')
    log.render('\nTool status:')
    tool_status_results = list()
    for tool in software_dependencies:
        if docker and software_dependencies[tool]['dockerised']:
            tool_status = (tool, '-', 'docker')
        else:
            tool_status = get_tool_status(tool)
        tool_status_results.append(tool_status)
    csizes = get_column_sizes(tool_status_results)
    missing_errors = render_dependency_table(tool_status_results, csizes)
    # If incompatible/missing tools, print info and exit
    if missing_errors:
        if len(missing_errors) == 1:
            [msg] = missing_errors
            log.render(f'\nError: {msg} is required')
            sys.exit(1)
        log.render(f'\nError: {len(tools_missing_errors)} tools incompatible/missing. ', end='')
        log.render('Unfulfilled requirements:')
        for msg in missing_errors:
            log.render(f'\t{msg}')
        sys.exit(1)


def get_tool_status(tool):
    version_arg = software_dependencies[tool]['arg']
    version_regex = software_dependencies[tool]['regex']
    min_version = software_dependencies[tool]['min']
    max_version = software_dependencies[tool]['max']
    # Check tool is in PATH
    tool_path = shutil.which(tool)
    if tool_path == None:
        return tool, '-', 'not found'
    # Run command to get version
    process_result = subprocess.run(
        f'{tool} {version_arg}',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        encoding='utf-8'
    )
    regex_result = re.search(version_regex, process_result.stdout, re.MULTILINE)
    version = regex_result.group(1)
    # Check tool version
    if min_version and distutils.version.LooseVersion(version) < min_version:
        status = 'too old'
    elif max_version and distutils.version.LooseVersion(version) > max_version:
        status = 'too new'
    else:
        status = 'good'
    return tool, version, status


def get_column_sizes(rows):
    # Calculate column size
    csizes = list()
    for column_items in zip(*rows):
        clargest = max(len(t) for t in column_items)
        # Set to be at least n character in length
        # Otherwise, round up to closest multiple of 4
        if clargest < 12:
            csizes.append(12)
        else:
            csize = clargest + (4 - clargest % 4)
            csizes.append(csize)
    return csizes


def render_dependency_table(tool_status_results, csizes):
    # Render header
    header_tokens = ('Program', 'Version', 'Status')
    log.render('  ', end='')
    for token, csize in zip(header_tokens, csizes):
        log.render(log.ftext(token.ljust(csize), f='underline'), end='')
    log.render_newline()
    # Render rows
    missing_errors = list()
    for row in tool_status_results:
        row_just = [text.ljust(csize) for csize, text in zip(csizes, row)]
        if row[-1] == 'good':
            row_just[-1] = log.ftext(row_just[-1], c='green')
            log.render('  ' + ''.join(row_just))
        elif row[-1] == 'docker':
            row_just[-1] = log.ftext(row_just[-1], c='black')
            log.render('  ' + ''.join(row_just))
        elif row[-1] in {'not found', 'too old', 'too new'}:
            # Output text
            row_text = log.ftext(''.join(row_just), c='red')
            log.render('  ' + row_text)
            # Record error
            tool = row[0]
            tool_reqs = software_dependencies[tool]
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
    log.render_newline()
    return missing_errors
