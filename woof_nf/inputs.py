import collections
import pathlib
import sys
from typing import Dict, List, Tuple


from . import log
from . import table
from . import umccrise


class InputFile:

    def __init__(self, sample_name, run, filepath, filetype, inputtype, source):
        self.sample_name = sample_name
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
        self.file_one = file_one
        self.file_two = file_two
        # Transfer some attributes from InputFile after checking consistency, if needed
        self.sample_name = None
        self.filetype = None
        self.transfer_attrs(file_one, file_two)

    def transfer_attrs(self, file_one: InputFile, file_two: InputFile) -> None:
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
    def is_matched(self) -> bool:
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


def collect(dir_one: List[pathlib.Path], dir_two: List[pathlib.Path]) -> Dict:
    # Check input directories are not the same
    paths_duplicated = list()
    for path, count in collections.Counter(dir_one + dir_two).items():
        if count > 1:
            paths_duplicated.append(path)
    if paths_duplicated:
        log.render(log.ftext('error: same input directory provided as run one and run two:', c='red'))
        for path in paths_duplicated:
            log.render(log.ftext(f'  - {path}', c='red'))
        sys.exit(1)
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
    # Ensure we have some files to match
    for source, files in file_data.items():
        if files.samples_matched:
            break
    else:
        log.render(log.ftext('error: no samples matched', c='red'))
        sys.exit(1)
    # Create and render tables displaying results
    for source_name, source_data in file_data.items():
        if source_name == 'umccrise':
            columns = list(umccrise.FILE_TYPES.keys())
            columns_display_name = [umccrise.COLUMN_NAME_MAPPING[n] for n in columns]
        elif source_name == 'bcbio':
            raise NotImplemented
        elif source_name == 'dragen':
            raise NotImplemented
        elif source_name == 'rnasum':
            raise NotImplemented
        elif source_name == 'plain':
            raise NotImplemented
        rows = prepare_rows(source_data, columns, columns_display_name)
        # Print log message and table
        samples_matched_n = len(source_data.samples_matched)
        samples_all_n = len(source_data.samples_matched) + len(source_data.samples_unmatched)
        log.render(log.ftext('UMCCRISE:', f='bold'))
        log.render(f'  Matched {samples_matched_n} of {samples_all_n} samples:')
        table.render_table(rows)
        log.render_newline()
    return file_data


def log_input_directories(dirpaths: List[pathlib.Path], n: str) -> None:
    log.render(f'  Set {n}:')
    for dirpath in dirpaths:
        log.render(f'    {dirpath}')


def discover_run_files(dirpaths: List[pathlib.Path], run: str) -> Dict:
    input_collection: Dict[str, List] = dict()
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
        else:
            assert False
        if source not in input_collection:
            input_collection[source] = list()
        input_collection[source].extend(directory_inputs)
    return input_collection


def match_inputs(inputs_one: Dict, inputs_two: Dict) -> Dict[str, SourceFiles]:
    matched = dict()
    sources = set(inputs_one) | set(inputs_two)
    for source in sources:
        source_one = dict() if source not in inputs_one else inputs_one[source]
        source_two = dict() if source not in inputs_two else inputs_two[source]
        matched[source] = perform_matching(source_one, source_two)
    return matched


def perform_matching(inputs_one: Dict, inputs_two: Dict) -> SourceFiles:
    # Group files by sample name and input type
    file_groups: Dict[Tuple[str, str], List] = dict()
    for f in (*inputs_one, *inputs_two):
        key = (f.sample_name, f.filetype)
        if key not in file_groups:
            file_groups[key] = list()
        file_groups[key].append(f)
    # Check grouped files match
    sample_files: Dict[str, Dict[str, FilePair]] = dict()
    for (sample_name, inputtype), file_group in file_groups.items():
        # Set file from run one and run two
        if len(file_group) > 2:
            msg = log.ftext(f'error: matched more than two files for {sample_name}:{inputtype}:', c='red')
            log.render(msg)
            for f in file_group:
                log.render(log.ftext(f'  {f.filepath}', c='red'))
            sys.exit(1)
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


def determine_match_status(sample_files: Dict) -> Tuple:
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
                elif isinstance(file_set.file_two, InputFile):
                    run_two += 1
                else:
                    assert False
            if run_one >= run_two:
                samples_unmatched_one.add(sample)
            else:
                samples_unmatched_two.add(sample)
    return samples_matched, samples_unmatched_one, samples_unmatched_two


def prepare_rows(source_data: SourceFiles, columns: List, file_columns_display: List) -> List[table.Row]:
    # Define symbols
    tick_green = table.Cell('✓', just='c', c='green')
    tick_grey = table.Cell('✓', just='c', c='black')
    cross = table.Cell('⨯', just='c', c='red')
    # Header
    rows = list()
    file_column_header_cells = [table.Cell(t, just='c') for t in file_columns_display]
    header_cells = [
        'Sample name',
        table.Cell('Set', just='c'),
        table.Cell('Matched', just='c'),
        *file_column_header_cells
    ]
    header_row = table.Row(header_cells, header=True)
    rows.append(header_row)
    # Body
    # Create rows for matched pairs
    for sample_name in sorted(source_data.samples_matched):
        # Only have sample appear on first line for matched pairs
        row_one = [sample_name, table.Cell('1', just='c'), tick_green]
        row_two = ['', table.Cell('2', just='c'), table.Cell('', just='c')]
        sample_files = source_data.file_list[sample_name]
        for filetype in columns:
            exist_one = filetype in sample_files and isinstance(sample_files[filetype].file_one, InputFile)
            exist_two = filetype in sample_files and isinstance(sample_files[filetype].file_two, InputFile)
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
        rows.append(table.Row(row_one))
        rows.append(table.Row(row_two))
    # Create rows for samples without matches
    for sample_name in sorted(source_data.samples_unmatched):
        # Get appropriate set
        cell_list = [table.Cell(sample_name, c='red')]
        if sample_name in source_data.samples_unmatched_one:
            cell_list.append(table.Cell('1', just='c'))
        elif sample_name in source_data.samples_unmatched_two:
            cell_list.append(table.Cell('2', just='c'))
        # Cross to indicate match status
        cell_list.append(cross)
        for file_type in columns:
            if file_type in source_data.file_list[sample_name]:
                cell_list.append(tick_green)
            else:
                cell_list.append(cross)
        rows.append(table.Row(cell_list))
    return rows


def write(input_data: Dict, output_fp: pathlib.Path) -> pathlib.Path:
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
