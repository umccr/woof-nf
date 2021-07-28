import collections
import pathlib
import re
import sys
from typing import Dict, List, Tuple


from . import inputs_bcbio as bcbio
from . import inputs_umccrise as umccrise
from . import log
from . import table
from . import utility


IGNORE_PATHS_RE = [
    re.compile('^.+/umccrised/log(?:/.*)?$'),
    re.compile('^.+/umccrised/work(?:/.*)?$'),
    re.compile('^.+/umccrised/benchmarks(?:/.*)?$'),
    re.compile('^.+/umccrised/.snakemake(?:/.*)?$'),
]


class InputFile:

    def __init__(self, sample_name, run_type, run_number, filepath, data_source, data_type):
        self.sample_name = sample_name
        self.run_type = run_type
        self.run_number = run_number
        self.filepath = filepath
        self.data_source = data_source
        self.data_type = data_type

    def __repr__(self):
        fields = [
            self.sample_name,
            self.run_type,
            self.run_number,
            self.data_type,
            self.data_source
        ]
        data = ':'.join(fields)
        return f'<{self.__module__}.{type(self).__name__} with {data}>'


class FilePair:

    def __init__(self, file_one, file_two):
        self.file_one = file_one
        self.file_two = file_two
        # Transfer some attributes from InputFile after checking consistency, if needed
        self.sample_name = None
        self.data_source = None
        self.transfer_attrs(file_one, file_two)

    def transfer_attrs(self, file_one: InputFile, file_two: InputFile) -> None:
        check_fields = ('sample_name', 'run_type', 'data_type', 'data_source')
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
    inputs_one = discover_run_files(dir_one, run_number='one')
    inputs_two = discover_run_files(dir_two, run_number='two')
    # Match files from the two runs
    file_data = match_inputs(inputs_one, inputs_two)
    # Create and render tables displaying results
    render_table(file_data)
    # Ensure we have some files to match
    for run_type, files in file_data.items():
        if files.samples_matched:
            break
    else:
        log.render(log.ftext('error: no samples matched', c='red'))
        sys.exit(1)
    return file_data


def log_input_directories(dirpaths: List[pathlib.Path], n: str) -> None:
    log.render(f'  Set {n}:')
    for dirpath in dirpaths:
        log.render(f'    {dirpath}')


def discover_run_files(dirpaths: List[pathlib.Path], run_number: str) -> Dict:
    # Discover files for each input directory
    detected_dirpaths = find_input_directories(dirpaths)
    input_collection: Dict[str, List] = dict()
    for run_type, dirpath in detected_dirpaths:
        if run_type == 'umccrise':
            input_module = umccrise
        elif run_type == 'bcbio':
            input_module = bcbio
        elif run_type == 'dragen':
            raise NotImplemented
        elif run_type == 'rnasum':
            raise NotImplemented
        elif run_type == 'plain':
            raise NotImplemented
        else:
            assert False
        directory_inputs = process_input_directory(
            dirpath,
            run_number,
            input_module,
            run_type
        )
        if run_type not in input_collection:
            input_collection[run_type] = list()
        input_collection[run_type].extend(directory_inputs)
    return input_collection


def find_input_directories(input_dirpaths):
    # Find input directories and input types
    detected_dirpaths = list()
    for input_dirpath in input_dirpaths:
        # NOTE: we may want to consider limiting recursion into deep directories
        dirpaths = [input_dirpath]
        for dirpath in dirpaths:
            # Skip non-directories and ignorable paths
            if not (dirpath.is_dir()):
                continue
            if any(path_re.match(str(dirpath)) for path_re in IGNORE_PATHS_RE):
                continue
            # Detect directory input type, if any
            run_type = None
            input_modules = [umccrise, bcbio]
            for input_module in input_modules:
                if is_dir_type(
                    dirpath,
                    input_module.DIRECTORY_FINGERPRINT,
                    input_module.FINGREPRINT_SCORE_THRESHOLD
                ):
                    run_type = input_module.RUN_TYPE
                    break
            # If directory type detected halt recursion, otherwise add dir contents to iterate
            if run_type is None:
                iterdirs = list(dirpath.iterdir())
                dirpaths.extend(iterdirs)
            else:
                detected_dirpaths.append((run_type, dirpath))
    return detected_dirpaths


def is_dir_type(dirpath, directory_fingerprint, threshold):
    score = 0
    for regex, value in directory_fingerprint.items():
        matches = utility.regex_glob(regex, dirpath)
        if matches:
            score += value
    return score >= threshold


def process_input_directory(
    dirpath: pathlib.Path,
    run_number: str,
    input_module,
    run_type
) -> List:
    # Iterate files and match using regex
    directory_inputs = list()
    for data_source, regex in input_module.DATA_SOURCES.items():
        # Attempt to match known inputs
        if filepaths := utility.regex_glob(regex, dirpath, data_source):
            [filepath] = filepaths
        else:
            continue
        # Get sample name and create InputFile instance
        sample_name = input_module.get_sample_name(dirpath)
        input_file = InputFile(
            sample_name,
            run_type,
            run_number,
            filepath,
            data_source,
            input_module.DATA_TYPES[data_source]
        )
        directory_inputs.append(input_file)
    return directory_inputs


def match_inputs(inputs_one: Dict, inputs_two: Dict) -> Dict[str, SourceFiles]:
    matched = dict()
    run_types = set(inputs_one) | set(inputs_two)
    for run_type in sorted(run_types):
        run_type_one = dict() if run_type not in inputs_one else inputs_one[run_type]
        run_type_two = dict() if run_type not in inputs_two else inputs_two[run_type]
        matched[run_type] = perform_matching(run_type_one, run_type_two)
    return matched


def perform_matching(inputs_one: Dict, inputs_two: Dict) -> SourceFiles:
    # Group files by sample name and input type
    file_groups: Dict[Tuple[str, str], List] = dict()
    for f in (*inputs_one, *inputs_two):
        key = (f.sample_name, f.data_source)
        if key not in file_groups:
            file_groups[key] = list()
        file_groups[key].append(f)
    # Check grouped files match
    sample_files: Dict[str, Dict[str, FilePair]] = dict()
    for (sample_name, data_type), file_group in file_groups.items():
        # Set file from run one and run two
        if len(file_group) > 2:
            msg = log.ftext(f'error: matched more than two files for {sample_name}:{data_type}:', c='red')
            log.render(msg)
            for f in file_group:
                log.render(log.ftext(f'  {f.filepath}', c='red'))
            sys.exit(1)
        file_one = file_two = None
        for i, f in enumerate(file_group):
            if f.run_number == 'one':
                assert file_one == None
                file_one = f
            elif f.run_number == 'two':
                assert file_two == None
                file_two = f
        file_pair = FilePair(file_one, file_two)
        sample_name = file_pair.sample_name
        if sample_name not in sample_files:
            sample_files[sample_name] = dict()
        sample_files[sample_name][file_pair.data_source] = file_pair
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


def render_table(file_data):
    for run_type, run_type_data in file_data.items():
        if run_type == 'umccrise':
            table_title = 'UMCCRISE'
            columns = list(umccrise.DATA_TYPES.keys())
            columns_display_name = [umccrise.COLUMN_NAME_MAPPING[n] for n in columns]
        elif run_type == 'bcbio':
            table_title = 'bcbio-nextgen'
            columns = list(bcbio.DATA_TYPES.keys())
            columns_display_name = [bcbio.COLUMN_NAME_MAPPING[n] for n in columns]
        elif run_type == 'dragen':
            raise NotImplemented
        elif run_type == 'rnasum':
            raise NotImplemented
        elif run_type == 'plain':
            raise NotImplemented
        rows = prepare_rows(run_type_data, columns, columns_display_name)
        # Print log message and table
        samples_matched_n = len(run_type_data.samples_matched)
        samples_all_n = len(run_type_data.samples_matched) + len(run_type_data.samples_unmatched)
        log.render(log.ftext(f'{table_title}:', f='bold'), end=' ')
        log.render(f'matched {samples_matched_n} of {samples_all_n} samples:')
        table.render_table(rows)
        log.render_newline()


def prepare_rows(run_type_data: SourceFiles, columns: List, file_columns_display: List) -> List[table.Row]:
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
    for sample_name in sorted(run_type_data.samples_matched):
        # Only have sample appear on first line for matched pairs
        row_one = [sample_name, table.Cell('1', just='c'), table.cell_green('✓')]
        row_two = ['', table.Cell('2', just='c'), table.Cell('', just='c')]
        sample_files = run_type_data.file_list[sample_name]
        for data_source in columns:
            exist_one = data_source  in sample_files and isinstance(sample_files[data_source].file_one, InputFile)
            exist_two = data_source  in sample_files and isinstance(sample_files[data_source].file_two, InputFile)
            # Set symbol and symbol colour
            if exist_one and not exist_two:
                sym_one = table.cell_grey('✓')
                sym_two = table.cell_red('⨯')
            elif not exist_one and exist_two:
                sym_one = table.cell_red('⨯')
                sym_two = table.cell_grey('✓')
            elif exist_one and exist_two:
                sym_one = table.cell_green('✓')
                sym_two = table.cell_green('✓')
            elif not exist_one and not exist_two:
                sym_one = table.cell_red('⨯')
                sym_two = table.cell_red('⨯')
            row_one.append(sym_one)
            row_two.append(sym_two)
        rows.append(table.Row(row_one))
        rows.append(table.Row(row_two))
    # Create rows for samples without matches
    for sample_name in sorted(run_type_data.samples_unmatched):
        # Get appropriate set
        cell_list = [table.Cell(sample_name, c='red')]
        if sample_name in run_type_data.samples_unmatched_one:
            cell_list.append(table.Cell('1', just='c'))
        elif sample_name in run_type_data.samples_unmatched_two:
            cell_list.append(table.Cell('2', just='c'))
        # Cross to indicate match status
        cell_list.append(table.cell_red('⨯'))
        for file_type in columns:
            if file_type in run_type_data.file_list[sample_name]:
                cell_list.append(table.cell_green('✓'))
            else:
                cell_list.append(table.cell_red('⨯'))
        rows.append(table.Row(cell_list))
    return rows


def write(input_data: Dict, output_fp: pathlib.Path) -> pathlib.Path:
    header_tokens = (
        'sample_name',
        'run_type',
        'run_number',
        'data_source',
        'data_type',
        'filepath'
    )
    # Create directory if required
    if not output_fp.parent.exists():
        output_fp.parent.mkdir(mode=0o700)
    # Write inputs
    with output_fp.open('w') as fh:
        print(*header_tokens, sep='\t', file=fh)
        for source_files in input_data.values():
            # Unpack into flat list of intput files. Sheesh, need to refactor...
            input_files = list()
            for file_type_pair in source_files.file_list.values():
                for file_pair in file_type_pair.values():
                    if not file_pair.is_matched:
                        continue
                    input_files.extend((file_pair.file_one, file_pair.file_two))
            # Write input file info to disk
            for input_file in input_files:
                print(
                    input_file.sample_name,
                    input_file.run_type,
                    input_file.run_number,
                    input_file.data_source,
                    input_file.data_type,
                    input_file.filepath,
                    sep='\t',
                    file=fh
                )
    return output_fp
