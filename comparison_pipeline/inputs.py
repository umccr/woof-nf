import pathlib
import sys


from . import log
from . import umccrise


class InputFile:

    def __init__(self, sample_name, run, filepath, filetype, inputtype, source):
        # TODO: remove version clipping - dev only
        self.sample_name = sample_name.split('__')[1]
        self.run = run
        self.filepath = filepath
        self.filetype = filetype
        self.inputtype = inputtype
        self.source = source

    def __repr__(self):
        data = f'{self.run}:{self.source}:{self.filetype}:{self.sample_name}'
        return f'<{self.__module__}.{type(self).__name__} with {data}>'


class FilePair:

    def __init__(self, file_one, file_two):
        # Transfer some attributes from InputFile after checking consistency, if needed
        self.transfer_attrs(file_one, file_two)
        self.file_one = file_one
        self.file_two = file_two

    def transfer_attrs(self, file_one, file_two):
        check_fields = ('sample_name', 'filetype', 'inputtype', 'source')
        for field in check_fields:
            # Handle absent files appropriately
            if file_one == None and file_two == None:
                # No files present, should never have come here
                assert False
            elif isinstance(file_one, InputFile) and file_two == None:
                # Only file one present
                field_value = getattr(file_one, field)
            elif file_one == None and isinstance(file_two, InputFile):
                # Only file two present
                field_value = getattr(file_two, field)
            elif isinstance(file_one, InputFile) and isinstance(file_two, InputFile):
                # Both present, check data matches
                assert getattr(file_one, field) == getattr(file_two, field)
                field_value = getattr(file_one, field)
            else:
                assert False
            # Set attribute
            setattr(self, field, field_value)

    @property
    def is_matched(self):
        return isinstance(self.file_one, InputFile) and isinstance(self.file_two, InputFile)

    def __repr__(self):
        return f'{self.file_one} and {self.file_two}'


class SourceFiles:

    def __init__(self, file_list, samples_matched, samples_unmatched_one, samples_unmatched_two):
        self.file_list = file_list
        self.samples_matched = samples_matched
        self.samples_unmatched_one = samples_unmatched_one
        self.samples_unmatched_two = samples_unmatched_two
        self.samples_unmatched = (*samples_unmatched_one, *samples_unmatched_two)


def collect(dir_one, dir_two):
    # Log directories to be searched
    log.task_msg_title('Discovering input files')
    log.render('\nDirectories searched:')
    log_input_directories(dir_one, '1')
    log_input_directories(dir_two, '2')
    log.render_newline()
    # Discover all inputs
    inputs_one = discover_run_files(dir_one, run='one')
    inputs_two = discover_run_files(dir_two, run='two')
    # Match files from the two runs
    file_data = match_inputs(inputs_one, inputs_two)
    # Create and render tables displaying results
    for source_name, source_data in file_data.items():
        if source_name == 'umccrise':
            columns = list(umccrise.file_types.keys())
            columns_display_name = [umccrise.column_name_mapping[n] for n in columns]
        elif source_name == 'bcbio':
            raise NotImplemented
        elif source_name == 'dragen':
            raise NotImplemented
        elif source_name == 'rnasum':
            raise NotImplemented
        elif source_name == 'plain':
            raise NotImplemented
        matched_table = create_matched_table(source_data, columns)
        # Print log message and table
        samples_matched_n = len(source_data.samples_matched)
        samples_all_n = len(source_data.samples_matched) + len(source_data.samples_unmatched)
        log.render(log.ftext('UMCCRISE:', f='bold'))
        log.render(f'  Matched {samples_matched_n} of {samples_all_n} samples:')
        render_matched_table(matched_table, columns_display_name)
    return file_data


def log_input_directories(dirpaths, n):
    log.render(f'  set {n}:')
    for dirpath in dirpaths:
        log.render(f'    {dirpath}')


def discover_run_files(dirpaths, run):
    input_collection = dict()
    for dirpath in dirpaths:
        # Discover files for each input directory
        # NOTE: this will be a branch point for process different input directory types
        # NOTE: `source` will be autodetected from input structure
        source = 'umccrise'
        if source == 'umccrise':
            directory_inputs = umccrise.process_input_directory(dirpath, run=run)
        elif source == 'bcbio':
            raise NotImplemented
        elif source == 'dragen':
            raise NotImplemented
        elif source == 'rnasum':
            raise NotImplemented
        elif source == 'plain':
            raise NotImplemented
        if source not in input_collection:
            input_collection[source] = list()
        input_collection[source].extend(directory_inputs)
    return input_collection


def match_inputs(inputs_one, inputs_two):
    matched = dict()
    sources = set(inputs_one) | set(inputs_two)
    for source in sources:
        source_one = dict() if source not in inputs_one else inputs_one[source]
        source_two = dict() if source not in inputs_two else inputs_two[source]
        matched[source] = perform_matching(source_one, source_two)
    return matched


def perform_matching(inputs_one, inputs_two):
    # Group files by sample name and input type
    file_groups = dict()
    for f in (*inputs_one, *inputs_two):
        key = (f.sample_name, f.filetype)
        if key not in file_groups:
            file_groups[key] = list()
        file_groups[key].append(f)
    # Check grouped files match
    sample_files = dict()
    for file_group in file_groups.values():
        # Set file from run one and run two
        assert len(file_group) <= 2
        file_one = file_two = None
        for i, f in enumerate(file_group):
            if f.run == 'one':
                assert file_one == None
                file_one = f
            elif f.run == 'two':
                assert file_two == None
                file_two = f
        file_pair = FilePair(file_one, file_two)
        sample_name = file_pair.sample_name
        if sample_name not in sample_files:
            sample_files[sample_name] = dict()
        sample_files[sample_name][file_pair.filetype] = file_pair
    # Get matched and unmatched samples
    samples_matched, samples_unmatched_one, samples_unmatched_two = determine_match_status(sample_files)
    return SourceFiles(sample_files, samples_matched, samples_unmatched_one, samples_unmatched_two)


def determine_match_status(sample_files):
    samples_matched = set()
    samples_unmatched_one = set()
    samples_unmatched_two = set()
    for sample, file_dict in sample_files.items():
        if any(f.is_matched for f in file_dict.values()):
            samples_matched.add(sample)
        else:
            # Assign run by taking majority, break by preference for run one
            run_one = 0
            run_two = 0
            for file_set in file_dict.values():
                if isinstance(file_set.file_one, InputFile):
                    run_one += 1
                elif isinstance(file_set.file_one, InputFile):
                    run_two += 1
                else:
                    assert False
            if run_one >= run_two:
                samples_unmatched_one.add(sample)
            else:
                samples_unmatched_two.add(sample)
    return samples_matched, samples_unmatched_one, samples_unmatched_two


def create_matched_table(source_data, columns):
    # Define symbols
    tick_green = log.ftext('✓', c='green')
    tick_grey = log.ftext('✓', c='black')
    cross = log.ftext('⨯', c='red')
    # Create rows for matched pairs
    rows = list()
    for sample_name in sorted(source_data.samples_matched):
        # Only have sample appear on first line for matched pairs
        row_one = [sample_name, '1', tick_green]
        row_two = ['', '2', '']
        sample_files = source_data.file_list[sample_name]
        for filetype in columns:
            exist_one = isinstance(sample_files[filetype].file_one, InputFile)
            exist_two = isinstance(sample_files[filetype].file_two, InputFile)
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
    for sample_name in sorted(source_data.samples_unmatched):
        # Get appropriate set
        row = [log.ftext(sample_name, c='red')]
        if sample_name in source_data.samples_unmatched_one:
            row.append('1')
        elif sample_name in source_data.samples_unmatched_two:
            row.append('2')
        # Cross to indicate match status
        row.append(cross)
        for file_type in columns:
            row.append(tick_green if file_type in source_data.file_list[sample_name] else cross)
        rows.append((row, ))
    return rows


def render_matched_table(rows, file_columns_display):
    # Set header
    header_tokens = ('Sample name', 'Set', 'Matched', *file_columns_display)
    # Min file column width; then set to header token
    # Get column sizes
    largest_sample = max(len(r[0]) for rs in rows for r in rs)
    csize_first = largest_sample + (4 - largest_sample % 4)
    csizes = [csize_first]
    for file_type in ['Set', 'Matched', *file_columns_display]:
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


def write(input_data, output_fp):
    # Create output directory if it does not already exist
    output_dir = output_fp.parent
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    # NOTE: only umccrise currently implemented
    sources_unimpl = {'umccrise'} ^ set(input_data)
    if sources_unimpl:
        print('error: got unimplemented comparison types:', file=sys.stderr)
        print(*sources_unimpl, sep='\n', file=sys.stderr)
        sys.exit(1)
    # Write file
    header_tokens = ('sample_name', 'file_type', 'file_source', 'run_number', 'filepath')
    inputs_fp = pathlib.Path(output_fp)
    source_data = input_data['umccrise']
    file_set_gen = (f for sample_files in source_data.file_list.values() for f in sample_files.values())
    with inputs_fp.open('w') as fh:
        print(*header_tokens, sep='\t', file=fh)
        for fs in file_set_gen:
            if not fs .is_matched:
                continue
            for input_file in (fs.file_one, fs.file_two):
                print(
                    input_file.sample_name,
                    input_file.inputtype,
                    input_file.filetype,
                    input_file.run,
                    input_file.filepath,
                    sep='\t',
                    file=fh
                )
    return inputs_fp
