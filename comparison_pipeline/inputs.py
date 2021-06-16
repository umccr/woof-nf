import pathlib


from . import log
from . import umccrise


def create_matched_table(inputs_one, inputs_two, samples_matched):
    # NOTE: assuming all umccrise files; refactor will be required for extending to bcbio.
    #       I will want to have separate sections for umccrise and bcbio match tables
    file_columns = list(umccrise.file_types.keys())
    # Define symbols
    tick_green = log.ftext('✓', c='green')
    tick_grey = log.ftext('✓', c='black')
    cross = log.ftext('⨯', c='red')
    # Create rows for matched pairs
    rows = list()
    for sample in sorted(samples_matched):
        # Only have sample appear on first line for matched pairs
        row_one = [sample, '1', tick_green]
        row_two = ['', '2', '']
        for file_type in file_columns:
            exist_one = file_type in inputs_one[sample]
            exist_two = file_type in inputs_two[sample]
            # Set symbol and symbol colour
            if exist_one and not exist_two:
                sym_one = tick_grey
                sym_two = cross
            elif not exist_one and exist_two:
                sym_one = cross
                sym_two = tick_grey
            elif exist_one and exist_two:
                sym_one = sym_two = tick_green
            elif not exist_one and not exist_two:
                sym_one = sym_two = cross
            row_one.append(sym_one)
            row_two.append(sym_two)
        rows.append((row_one, row_two))
    # Create rows for samples without matches
    samples_no_matched = samples_matched ^ (set(inputs_one) | set(inputs_two))
    for sample in samples_no_matched:
        # Get appropriate set
        row = [log.ftext(sample, c='red')]
        if sample in inputs_one:
            inputs = inputs_one
            row.append('1')
        elif sample in inputs_two:
            inputs = inputs_two
            row.append('2')
        # Cross to indicate match status
        row.append(cross)
        for file_type in file_columns:
            row.append(tick_green if file_type in inputs[sample] else cross)
        rows.append((row, ))
    return rows


def render_matched_table(rows):
    # Set header
    file_name_mapping = {
        'cpsr': 'CPSR',
        'pcgr': 'PCGR',
        'manta': 'Manta',
        'purple': 'PURPLE',
    }
    file_columns = [file_name_mapping[n] for n in umccrise.file_types.keys()]
    header_tokens = ('Sample name', 'Set', 'Matched', *file_columns)
    # Min file column width; then set to header token
    # Get column sizes
    largest_sample = max(len(r[0]) for rs in rows for r in rs)
    csize_first = largest_sample + (4 - largest_sample % 4)
    csizes = [csize_first]
    for file_type in ['Set', 'Matched', *file_columns]:
        # Subtracting one for left-dominant centering on even lengths
        if len(file_type) < 8:
            csizes.append(8 - 1)
        else:
            csize = len(file_type) + (4 - len(file_type) % 4) - 1
            csizes.append(csize)
    # Render header
    log.render('  ', end='')
    for token, csize in zip(header_tokens, csizes):
        log.render(log.ftext(token.center(csize), f='underline'), end='')
    log.render_newline()
    # Render rows
    for row_set in rows:
        for row in row_set:
            # Adjust csize padding to account for ansi escape codes
            # NOTE: some further considerations may be required here when log.ANSI_CODES = False
            row_just = list()
            column_number = 0
            for csize, text in zip(csizes, row):
                # Exclude second matched sample name from table; replace with empty space
                column_number += 1
                ansi_ec_size = len(text) - len(log.ANSI_ESCAPE.sub('', text))
                csize += ansi_ec_size
                if column_number == 1:
                    row_just.append(text.ljust(csize))
                else:
                    row_just.append(text.center(csize))
            row_text = ''.join(row_just)
            log.render('  ' + row_text)
    log.render_newline()


def write(input_list, output_fp):
    # Create output directory if it does not already exist
    output_dir = output_fp.parent
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    # Write file
    header_tokens  = ('sample_name', 'file_type', 'file_source', 'run_number', 'filepath')
    inputs_fp = pathlib.Path(output_fp)
    with inputs_fp.open('w') as fh:
        print(*header_tokens, sep='\t', file=fh)
        for input_entry in input_list:
            print(*input_entry, sep='\t', file=fh)
    return inputs_fp
